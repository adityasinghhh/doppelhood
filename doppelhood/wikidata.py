"""Resolve neighborhoods to their English Wikipedia articles through Wikidata."""

import json
import re
from pathlib import Path

import requests

from doppelhood.wikivoyage import USER_AGENT

API = "https://www.wikidata.org/w/api.php"
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
