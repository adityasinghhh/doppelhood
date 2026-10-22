"""Resolve neighborhoods to their English Wikipedia articles through Wikidata."""

import json
import re
import unicodedata
from pathlib import Path

import requests

from doppelhood.wikivoyage import USER_AGENT

API = "https://www.wikidata.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"
LOCAL_ARTICLES = """
SELECT DISTINCT ?article WHERE {
  ?item wdt:P131+ wd:%s ; wdt:P625 ?coord .
  ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> .
}
"""
# Items in the city with an English article, with every type each is an
# instance of. Filtering by subclass of neighborhood in the query itself times
# out, so the types are checked against NEIGHBORHOOD_TYPES afterward.
TYPED_ITEMS = """
SELECT ?item ?article ?coord ?type WHERE {
  ?item wdt:P131+ wd:%s ; wdt:P625 ?coord ; wdt:P31 ?type .
  ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> .
}
"""
HISTORIC_DISTRICT = "Q15243209"
NEIGHBORHOOD_TYPES = {
    "Q123705",    # neighborhood
    "Q2943502",   # neighborhood of Miami
    HISTORIC_DISTRICT,
    "Q3055075",   # entertainment district
    "Q17343829",  # unincorporated community, the neighborhoods of consolidated Nashville
}
NAME_SUFFIX = re.compile(r"\s+(historic district|neighborhood)$", re.IGNORECASE)
# Prefixes that OpenStreetMap labels or article titles carry but the other may not.
NAME_PREFIX = re.compile(r"^(colonia|barrio|pueblo|unidad habitacional)\s+", re.IGNORECASE)
RAW_DIR = Path("data/raw/wikidata")
BATCH = 50


def sitelinks(qids):
    """Map each Wikidata ID to its English Wikipedia title, caching every lookup."""
    cache_path = RAW_DIR / "sitelinks.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    missing = sorted({q for q in qids if q and q not in cache})
    for i in range(0, len(missing), BATCH):
        response = requests.get(API, params={
            "action": "wbgetentities", "ids": "|".join(missing[i:i + BATCH]),
            "props": "sitelinks", "sitefilter": "enwiki", "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=60)
        response.raise_for_status()
        for qid, entity in response.json()["entities"].items():
            cache[qid] = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache))
    return {q: cache.get(q) for q in qids if q}


def article_title(hood, titles):
    """Prefer the Wikidata link, then the label's own wikipedia=en:... tag."""
    if hood.get("wikidata") and titles.get(hood["wikidata"]):
        return titles[hood["wikidata"]]
    tag = hood.get("wikipedia") or ""
    match = re.match(r"en:(.+)", tag)
    return match.group(1).replace("_", " ") if match else None


def display_name(title, city):
    """Use the Wikipedia title, which is already disambiguated ("Chinatown,
    Manhattan" versus "Chinatown, Flushing"), minus a redundant city or state."""
    for suffix in (city["name"], city["wikivoyage"], "New York City", "New York", "California", "Texas"):
        title = re.sub(rf",\s*{re.escape(suffix)}$", "", title)
    return re.sub(r"\s*\((neighborhood|[^)]*{0}[^)]*)\)$".format(re.escape(city["name"])), "", title)


def normalize(name):
    """Lowercase, strip accents, a leading "Colonia" or similar, and any ", Place" suffix."""
    name = unicodedata.normalize("NFKD", name.split(",")[0].split(" (")[0])
    name = "".join(c for c in name if not unicodedata.combining(c)).strip()
    return NAME_PREFIX.sub("", name).lower()


def query(sparql, cache):
    """Run a SPARQL query once and cache its result rows."""
    if not cache.exists():
        response = requests.get(SPARQL, params={"query": sparql},
                                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                                timeout=300)
        response.raise_for_status()
        # Some labels carry raw control characters that strict parsing rejects.
        rows = json.loads(response.text, strict=False)["results"]["bindings"]
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows))
    return json.loads(cache.read_text())


def neighborhoods(city):
    """Neighborhoods that Wikidata places in the city, in the same shape as osm.neighborhoods.

    OpenStreetMap leaves out many well-known neighborhoods in some cities,
    such as Wynwood in Miami and the Gulch in Nashville, where most of its
    labels are subdivisions and apartment complexes instead.
    """
    rows = query(TYPED_ITEMS % city["wikidata"], RAW_DIR / f"typed-{city['wikidata']}.json")
    types, results = {}, {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        types.setdefault(qid, set()).add(row["type"]["value"].rsplit("/", 1)[-1])
        point = re.fullmatch(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", row["coord"]["value"])
        if qid in results or not point:
            continue
        lon, lat = map(float, point.groups())
        title = requests.utils.unquote(row["article"]["value"].rsplit("/", 1)[-1]).replace("_", " ")
        name = NAME_SUFFIX.sub("", title.split(",")[0].split(" (")[0])
        results[qid] = {"name": name, "lat": lat, "lon": lon, "wikidata": qid, "wikipedia": f"en:{title}"}
    hoods = []
    for qid, n in results.items():
        kinds = types[qid] & NEIGHBORHOOD_TYPES
        if kinds:
            n["wikidata_kind"] = "historic district" if kinds == {HISTORIC_DISTRICT} else "neighborhood"
            hoods.append(n)
    return hoods


def local_articles(city):
    """Map normalized names to the English Wikipedia articles of places located in the city.

    One query covers every label, which matters for cities like Mexico City
    where thousands of labels have no Wikidata link of their own.
    """
    cache = RAW_DIR / f"local-{city['wikidata']}.json"
    if not cache.exists():
        response = requests.get(SPARQL, params={"query": LOCAL_ARTICLES % city["wikidata"]},
                                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                                timeout=180)
        response.raise_for_status()
        titles = [requests.utils.unquote(b["article"]["value"].rsplit("/", 1)[-1]).replace("_", " ")
                  for b in response.json()["results"]["bindings"]]
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(titles))
    by_name = {}
    for title in json.loads(cache.read_text()):
        by_name.setdefault(normalize(title), title)
    return by_name
