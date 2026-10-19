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
