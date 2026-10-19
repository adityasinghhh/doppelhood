"""List a city's neighborhoods from Wikidata, with coordinates and English Wikipedia articles."""

import json
import re
from pathlib import Path

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "doppelhood/0.1 (https://github.com/adityasinghhh/doppelhood)"
RAW_DIR = Path("data/raw/wikidata")

# Walking the class hierarchy server-side times out for large cities, so the
# query returns everything located in the city and types are filtered here.
QUERY = """
SELECT ?n ?nLabel ?coord ?article ?tLabel WHERE {
  ?n wdt:P131+ wd:%s ; wdt:P625 ?coord ; wdt:P31 ?t .
  ?article schema:about ?n ; schema:isPartOf <https://en.wikipedia.org/> .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""

NEIGHBORHOOD_TYPE = re.compile(r"neighbou?rhood|arts district|restaurant district|central business district")
EXCLUDED_TYPE = re.compile(r"former")
POINT = re.compile(r"Point\(([-\d.]+) ([-\d.]+)\)")


def query(qid):
    cache = RAW_DIR / f"{qid}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    response = requests.get(ENDPOINT, params={"query": QUERY % qid},
                            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                            timeout=120)
    response.raise_for_status()
    bindings = response.json()["results"]["bindings"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(bindings))
    return bindings


def display_name(title, city):
    """Use the Wikipedia title, which is already disambiguated ("Chinatown,
    Manhattan" versus "Chinatown, Flushing"), minus a redundant city or state."""
    for suffix in (city["name"], city["wikivoyage"], "New York City", "New York", "California", "Texas"):
        title = re.sub(rf",\s*{re.escape(suffix)}$", "", title)
    return re.sub(r"\s*\((neighborhood|[^)]*{0}[^)]*)\)$".format(re.escape(city["name"])), "", title)


def neighborhoods(city):
    """Return the neighborhoods of a city from config/cities.yaml."""
    by_item = {}
    for row in query(city["wikidata"]):
        qid = row["n"]["value"].rsplit("/", 1)[-1]
        item = by_item.setdefault(qid, {"types": set(), "row": row})
        item["types"].add(row["tLabel"]["value"].lower())

    results = []
    for qid, item in by_item.items():
        types = item["types"]
        if not any(NEIGHBORHOOD_TYPE.search(t) for t in types):
            continue
        if any(EXCLUDED_TYPE.search(t) for t in types):
            continue
        row = item["row"]
        lon, lat = map(float, POINT.match(row["coord"]["value"]).groups())
        article = row["article"]["value"]
        title = requests.utils.unquote(article.rsplit("/", 1)[-1]).replace("_", " ")
        results.append({
            "id": qid,
            "city": city["slug"],
            "name": display_name(title, city),
            "lat": lat,
            "lon": lon,
            "wikipedia": title,
            "source_url": article,
        })
    return sorted(results, key=lambda n: n["name"])
