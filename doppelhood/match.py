"""Embed district sections and rank each base-city district's matches in every other city.

Each section of a district is embedded by splitting it into passages, embedding
each passage, and averaging. Before comparing, every city's mean vector is
subtracted from its districts' vectors, per section. That removes what all of
a city's districts share (its name, its landmarks, its general tone) and leaves
how each district differs from the rest of its own city, so a match means two
districts play the same role locally.

Raw similarities between centered vectors are small and hard to read, so
scores are reported as percentiles: a score of 90 means the pairing is more
similar than 90% of all pairings between a base-city district and a district
elsewhere, overall or within one section.
"""

import json
import re
from pathlib import Path

import numpy as np
import yaml
from sentence_transformers import SentenceTransformer

from doppelhood.wikivoyage import SECTIONS, district_records

MODEL = "sentence-transformers/all-mpnet-base-v2"
PASSAGE_CHARS = 800
TOP_MATCHES = 5
OUTPUT = Path("web/data/matches.json")


def passages(text):
    """Split text into sentence-aligned passages of about PASSAGE_CHARS characters."""
    chunks, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if current and len(current) + len(sentence) > PASSAGE_CHARS:
            chunks.append(current)
            current = ""
        current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def embed_sections(model, districts):
    """Attach a unit vector per section to every district."""
    for district in districts:
        district["vectors"] = {}
        for section, text in district["sections"].items():
            vectors = model.encode(passages(text), normalize_embeddings=True)
            mean = vectors.mean(axis=0)
            district["vectors"][section] = mean / np.linalg.norm(mean)


def center_by_city(districts):
    """Subtract each city's mean vector per section, then renormalize."""
    for section in SECTIONS:
        by_city = {}
        for district in districts:
            if section in district["vectors"]:
                by_city.setdefault(district["city"], []).append(district)
        for members in by_city.values():
            mean = np.mean([d["vectors"][section] for d in members], axis=0)
            for d in members:
                centered = d["vectors"][section] - mean
                d["vectors"][section] = centered / np.linalg.norm(centered)


def compare(a, b):
    """Return the raw overall similarity of two districts and its per-section parts."""
    shared = [s for s in SECTIONS if s in a["vectors"] and s in b["vectors"]]
    breakdown = {s: float(a["vectors"][s] @ b["vectors"][s]) for s in shared}
    overall = sum(breakdown.values()) / len(breakdown) if breakdown else -1.0
    return overall, breakdown


def percentile(distribution, value):
    """Percentage of a sorted distribution that falls below value."""
    return round(100 * np.searchsorted(distribution, value) / len(distribution))


def public_record(district):
    return {k: district[k] for k in ("city", "name", "title", "summary", "source_url", "revid")}


def main():
    config = yaml.safe_load(Path("config/cities.yaml").read_text())
    cities = [c for c in config["cities"] if c["wikivoyage_districts"]]

    districts = []
    for city in cities:
        districts.extend(district_records(city))
    print(f"Embedding {len(districts)} districts across {len(cities)} cities")

    embed_sections(SentenceTransformer(MODEL), districts)
    center_by_city(districts)

    base = [d for d in districts if d["city"] == config["base"]]
    others = [d for d in districts if d["city"] != config["base"]]
    pairs = [(b, d, *compare(b, d)) for b in base for d in others]

    overall_dist = np.sort([overall for _, _, overall, _ in pairs])
    section_dist = {s: np.sort([parts[s] for *_, parts in pairs if s in parts]) for s in SECTIONS}

    matches = {b["title"]: {} for b in base}
    for b, d, overall, parts in pairs:
        matches[b["title"]].setdefault(d["city"], []).append({
            "title": d["title"],
            "score": percentile(overall_dist, overall),
            "sections": {s: percentile(section_dist[s], v) for s, v in parts.items()},
        })
    for by_city in matches.values():
        for city, scored in by_city.items():
            scored.sort(key=lambda m: m["score"], reverse=True)
            by_city[city] = scored[:TOP_MATCHES]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "base": config["base"],
        "model": MODEL,
        "license": "District titles and summaries come from Wikivoyage under CC BY-SA 4.0 "
                   "(https://creativecommons.org/licenses/by-sa/4.0/). Each district's "
                   "source_url links to the article and its author history. Scores are "
                   "derived from that text and are shared under the same license.",
        "cities": [{k: c[k] for k in ("slug", "name", "state")} for c in cities],
        "districts": [public_record(d) for d in districts],
        "matches": matches,
    }, indent=1, ensure_ascii=False))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
