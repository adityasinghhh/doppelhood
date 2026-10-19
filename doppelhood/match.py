"""Match every neighborhood to its closest equivalents in every other city.

Each neighborhood is described by three kinds of signal:
- **Character**, an embedding of its Wikipedia article without demographics,
  government, and transport sections.
- **Visitor listings**, embeddings of the Wikivoyage Eat, Drink, See, Do, and
  Buy listings whose coordinates fall closest to it.
- **Street life**, counts of OpenStreetMap restaurants, bars, cafes, shops,
  parks, and venues within osm.RADIUS_M of its coordinate.

Every signal is centered within its city before comparing, so a match means
two neighborhoods differ from the rest of their own cities in the same way.
Each signal's similarity is converted to a percentile over all cross-city
pairs, the percentiles are blended by WEIGHTS, and the blend is converted to a
percentile again: a score of 90 means the pairing is more similar than 90% of
all pairings between neighborhoods in different cities.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import yaml

from doppelhood import osm, wikidata, wikipedia, wikivoyage

MODEL = "sentence-transformers/all-mpnet-base-v2"
PASSAGE_CHARS = 800
MIN_ARTICLE_CHARS = 800
LISTING_RADIUS_M = 800
MAIN_VERB = re.compile(r"\b(is|are|was|were)\b", re.IGNORECASE)
ISLAND = re.compile(r"\bis (an?|one of the)\s+(\w+\s+)?islands?\b", re.IGNORECASE)
LIVED_IN = re.compile(r"neighbou?rhood|residential|residents", re.IGNORECASE)


def not_current(lead):
    """True for an article about a place that no longer exists or that nobody lives in.

    The first sentence's main verb gives the first away ("The Barbary Coast was
    a red-light district"), and an island that the lead never calls a
    neighborhood is the second (the Boston Harbor Islands, but not Roosevelt
    Island).
    """
    first = wikipedia.summary(lead, sentences=1)
    verb = MAIN_VERB.search(first)
    if verb and verb.group(1).lower() in ("was", "were"):
        return True
    return bool(ISLAND.search(first)) and not LIVED_IN.search(lead)
# Searching Wikipedia label by label is slow, so cities with thousands of
# labels (Mexico City's colonias) rely on Wikidata matches alone.
SEARCH_LABEL_LIMIT = 600
TOP_MATCHES = 5
EMBED_CACHE = Path("data/cache/embeddings.npz")
OUTPUT = Path("web/data/matches.json")

LISTING_SECTIONS = ["eat", "drink", "see", "do", "buy"]
WEIGHTS = {"character": 0.4, "listings": 0.3, "street": 0.3}


class Embedder:
    """Embed text as the normalized mean of its passages, caching by content hash."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(MODEL)
        self.cache = dict(np.load(EMBED_CACHE)) if EMBED_CACHE.exists() else {}

    def __call__(self, text):
        key = hashlib.sha1(text.encode()).hexdigest()
        if key not in self.cache:
            vectors = self.model.encode(passages(text), normalize_embeddings=True)
            mean = vectors.mean(axis=0)
            self.cache[key] = mean / np.linalg.norm(mean)
        return self.cache[key]

    def save(self):
        EMBED_CACHE.parent.mkdir(parents=True, exist_ok=True)
        np.savez(EMBED_CACHE, **self.cache)


def passages(text):
    chunks, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if current and len(current) + len(sentence) > PASSAGE_CHARS:
            chunks.append(current)
            current = ""
        current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def load_city(city):
    """Current neighborhoods for one city with article text, listings, and OSM counts.

    Neighborhoods without an English Wikipedia article are dropped, since the
    article supplies both the character signal and the summary shown in the app.
    """
    labels = osm.neighborhoods(city)
    titles = wikidata.sitelinks([n["wikidata"] for n in labels])
    local = wikidata.local_articles(city)
    names = [n["name"] for n in labels]

    hoods = []
    for n in labels:
        title = None
        for candidate in (wikidata.article_title(n, titles), local.get(wikidata.normalize(n["name"]))):
            if candidate and wikipedia.plausible(candidate, n["lat"], n["lon"]):
                title = candidate
                break
        if not title and len(labels) <= SEARCH_LABEL_LIMIT:
            title = wikipedia.search(n["name"], city, n["lat"], n["lon"])
        page = wikipedia.fetch(title) if title else None
        if not page:
            continue
        lead, text = wikipedia.character(page["wikitext"])
        if len(text) < MIN_ARTICLE_CHARS:
            continue
        if not_current(lead):
            print(f"  skipped {n['name']}: {wikipedia.summary(lead, sentences=1)[:90]}")
            continue
        name = n["name"] if names.count(n["name"]) == 1 else wikidata.display_name(page["title"], city)
        # A neighborhood's own name would otherwise match on words like
        # "Beach" or "Heights" rather than on what the place is like.
        for alias in {n["name"], page["title"].split(",")[0].split(" (")[0]}:
            text = re.sub(re.escape(alias), "the neighborhood", text, flags=re.IGNORECASE)
        hoods.append({
            "id": f"{city['slug']}:{n['name']}",
            "city": city["slug"],
            "name": name,
            "lat": n["lat"],
            "lon": n["lon"],
            "summary": wikipedia.summary(lead),
            "text": text,
            "source_url": "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_"),
            "revid": page["revid"],
        })

    # Several labels can point at one article. "Condesa" and "Colonia Condesa"
    # are the same place, so labels whose normalized names are equal keep only
    # the shorter one. "Arverne By The Sea" is a development inside Arverne,
    # so a label that extends another label's name is dropped too. "Outer
    # Sunset" survives, since it does not start with "Sunset District".
    by_article = {}
    for n in sorted(hoods, key=lambda n: len(n["name"])):
        by_article.setdefault(n["source_url"], []).append(n)
    kept = []
    for group in by_article.values():
        names = []
        for n in group:
            key = wikidata.normalize(n["name"])
            if not any(key == other or key.startswith(other + " ") for other in names):
                names.append(key)
                kept.append(n)
    hoods = kept

    osm.attach_features(city, hoods)

    # Each listing goes to the nearest neighborhood within LISTING_RADIUS_M.
    coords = np.array([[n["lat"], n["lon"]] for n in hoods])
    for n in hoods:
        n["listings"] = {s: [] for s in LISTING_SECTIONS}
    if city.get("wikivoyage_districts"):
        for listing in wikivoyage.listings(city):
            if listing["section"] not in LISTING_SECTIONS:
                continue
            d = osm.distances_m(listing["lat"], listing["lon"], coords)
            nearest = int(d.argmin())
            if d[nearest] <= LISTING_RADIUS_M:
                hoods[nearest]["listings"][listing["section"]].append(listing["text"])
    return hoods


def centered(matrix, cities, present):
    """Subtract each city's mean row and renormalize; rows not present stay NaN."""
    out = np.full_like(matrix, np.nan)
    for city in set(cities):
        rows = (cities == city) & present
        if rows.sum() < 2:
            continue
        block = matrix[rows] - matrix[rows].mean(axis=0)
        norms = np.linalg.norm(block, axis=1, keepdims=True)
        out[rows] = block / np.where(norms == 0, 1, norms)
    return out


def percentiles(similarity, cross):
    """Convert a similarity matrix to percentiles over valid cross-city pairs."""
    valid = cross & ~np.isnan(similarity)
    pool = np.sort(similarity[valid])
    out = np.full_like(similarity, np.nan)
    out[valid] = 100 * np.searchsorted(pool, similarity[valid]) / len(pool)
    return out


def score(hoods, embed):
    cities = np.array([n["city"] for n in hoods])
    cross = cities[:, None] != cities[None, :]
    everyone = np.ones(len(hoods), dtype=bool)

    parts = {}

    character = np.array([embed(n["text"]) for n in hoods])
    v = centered(character, cities, everyone)
    parts["character"] = percentiles(v @ v.T, cross)

    for section in LISTING_SECTIONS:
        present = np.array([bool(n["listings"][section]) for n in hoods])
        if present.sum() < 4:
            continue
        dim = character.shape[1]
        m = np.array([embed(" ".join(n["listings"][section])) if p else np.zeros(dim)
                      for n, p in zip(hoods, present)])
        v = centered(m, cities, present)
        parts[section] = percentiles(v @ v.T, cross)

    has_osm = np.array([n["osm"] is not None for n in hoods])
    counts = np.log1p(np.array([[n["osm"][f] for f in osm.FEATURES] if n["osm"] else
                                [0] * len(osm.FEATURES) for n in hoods], dtype=float))
    z = np.full_like(counts, np.nan)
    for city in set(cities):
        rows = (cities == city) & has_osm
        if rows.any():
            sd = counts[rows].std(axis=0)
            z[rows] = (counts[rows] - counts[rows].mean(axis=0)) / np.where(sd == 0, 1, sd)
    norms = np.linalg.norm(z, axis=1, keepdims=True)
    v = z / np.where(norms == 0, 1, norms)
    parts["street"] = percentiles(v @ v.T, cross)

    listing_parts = [parts[s] for s in LISTING_SECTIONS if s in parts]
    listings = np.nanmean(np.stack(listing_parts), axis=0) if listing_parts else None

    has_street = ~np.isnan(parts["street"])
    total = WEIGHTS["character"] * parts["character"] + WEIGHTS["street"] * np.nan_to_num(parts["street"])
    weight = WEIGHTS["character"] + np.where(has_street, WEIGHTS["street"], 0)
    if listings is not None:
        has = ~np.isnan(listings)
        total = np.where(has, total + WEIGHTS["listings"] * np.nan_to_num(listings), total)
        weight = np.where(has, weight + WEIGHTS["listings"], weight)
    overall = percentiles(total / weight, cross)
    return overall, parts


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("cities", nargs="*", help="city slugs from config/cities.yaml (default: all)")
    args = parser.parse_args()

    config = yaml.safe_load(Path("config/cities.yaml").read_text())
    cities = [c for c in config["cities"] if not args.cities or c["slug"] in args.cities]

    hoods = []
    for city in cities:
        loaded = load_city(city)
        print(f"{city['name']}: {len(loaded)} neighborhoods")
        hoods.extend(loaded)

    embed = Embedder()
    overall, parts = score(hoods, embed)
    embed.save()

    matches = {}
    for i, n in enumerate(hoods):
        by_city = {}
        for city in cities:
            if city["slug"] == n["city"]:
                continue
            idx = [j for j, m in enumerate(hoods) if m["city"] == city["slug"]]
            idx.sort(key=lambda j: overall[i, j], reverse=True)
            by_city[city["slug"]] = [{
                "id": hoods[j]["id"],
                "score": int(round(overall[i, j])),
                "parts": {k: int(round(p[i, j])) for k, p in parts.items() if not np.isnan(p[i, j])},
            } for j in idx[:TOP_MATCHES]]
        matches[n["id"]] = by_city

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "model": MODEL,
        "license": "Neighborhood summaries and text-derived scores come from Wikipedia and Wikivoyage "
                   "under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/); each "
                   "neighborhood's source_url links to its article and author history. Street-life "
                   "scores are produced from OpenStreetMap data, (c) OpenStreetMap contributors, "
                   "ODbL 1.0 (https://www.openstreetmap.org/copyright), as are the neighborhood "
                   "names and locations. Wikipedia articles are linked through Wikidata (CC0).",
        "cities": [{k: c[k] for k in ("slug", "name", "state")} for c in cities],
        "neighborhoods": [{k: n[k] for k in ("id", "city", "name", "summary", "source_url", "lat", "lon")}
                          for n in hoods],
        "matches": matches,
    }, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {OUTPUT} with {len(hoods)} neighborhoods")


if __name__ == "__main__":
    main()
