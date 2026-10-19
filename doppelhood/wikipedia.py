"""Fetch Wikipedia neighborhood articles and keep the parts that describe character."""

import json
import math
import re
import time
from pathlib import Path

import mwparserfromhell
import requests

from doppelhood.wikivoyage import USER_AGENT, plain_text

API = "https://en.wikipedia.org/w/api.php"
RAW_DIR = Path("data/raw/wikipedia")

# Sections about who lives in a neighborhood, how it is governed, or how to
# reach it say little about what it is like to visit, so they are dropped.
EXCLUDED = re.compile(
    r"demographic|population|education|school|government|politic|police|fire|"
    r"transport|transit|infrastructure|health|notable|people|residents|reference|"
    r"see also|external|notes|further reading|bibliography|sources|gallery|citation|"
    r"in popular culture|media|crime|safety|religion|postal|zip|library|libraries"
)
HISTORY = re.compile(r"history")
HISTORY_CHARS = 1500
MAX_DISTANCE_M = 3000
REJECTED_TITLE = re.compile(r"^List of|disambiguation|station\b", re.IGNORECASE)

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def get(params, attempts=5):
    """GET the API at a polite pace, backing off when Wikipedia asks us to."""
    for attempt in range(attempts):
        time.sleep(0.3)
        response = session.get(API, params=params, timeout=60)
        if response.status_code == 429 and attempt < attempts - 1:
            time.sleep(int(response.headers.get("Retry-After", 10 * (attempt + 1))))
            continue
        response.raise_for_status()
        return response.json()


def fetch(title):
    cache = RAW_DIR / (title.replace("/", "__") + ".json")
    if cache.exists():
        return json.loads(cache.read_text())
    parsed = get({
        "action": "parse", "page": title, "prop": "wikitext|revid",
        "redirects": 1, "format": "json", "formatversion": 2,
    }).get("parse")
    page = {"title": parsed["title"], "revid": parsed["revid"], "wikitext": parsed["wikitext"]} if parsed else None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(page))
    return page


def search(name, city, lat, lon):
    """Find the article for a neighborhood label that has no Wikidata link.

    "Name, City" and the bare name are tried first, following redirects, then
    a title search. A candidate is accepted only if the article's coordinates
    fall within MAX_DISTANCE_M of the label, which rules out same-named places
    elsewhere, and list or disambiguation pages are never accepted.
    """
    cache_path = RAW_DIR / "search.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    key = f"{city['slug']}:{name}"
    if key in cache:
        return cache[key]

    candidates = [f"{name}, {city['wikipedia']}", name]
    found = get({
        "action": "query", "list": "search", "srsearch": f'intitle:"{name}" {city["name"]}',
        "srlimit": 5, "format": "json", "formatversion": 2,
    })
    candidates += [hit["title"] for hit in found["query"]["search"] if title_matches(hit["title"], name)]

    cache[key] = None
    for title, where in coordinates(candidates).items():
        if REJECTED_TITLE.search(title) or where is None:
            continue
        if distance_m(lat, lon, *where) <= MAX_DISTANCE_M:
            cache[key] = title
            break
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache))
    return cache[key]


def coordinates(titles):
    """Resolve titles through redirects and return {final title: (lat, lon) or None}, in order."""
    query = get({
        "action": "query", "prop": "coordinates", "titles": "|".join(titles),
        "redirects": 1, "format": "json", "formatversion": 2,
    })["query"]
    renamed = {r["from"]: r["to"] for r in query.get("normalized", []) + query.get("redirects", [])}
    pages = {p["title"]: p for p in query["pages"] if not p.get("missing") and not p.get("invalid")}
    resolved = {}
    for title in titles:
        while title in renamed:
            title = renamed[title]
        if title in pages and title not in resolved:
            c = (pages[title].get("coordinates") or [None])[0]
            resolved[title] = (c["lat"], c["lon"]) if c else None
    return resolved


def plausible(title, lat, lon):
    """True when an article is not a list, disambiguation, or station page and,
    if it has coordinates, they fall within MAX_DISTANCE_M of the label.

    OpenStreetMap's Wikidata links are occasionally wrong (a neighborhood
    linked to a same-named town elsewhere, or to a railroad station), so
    every article is checked rather than trusted.
    """
    cache_path = RAW_DIR / "coordinates.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    if title not in cache:
        resolved = coordinates([title])
        final, where = next(iter(resolved.items()), (title, None))
        cache[title] = [final, where]
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache))
    final, where = cache[title]
    if REJECTED_TITLE.search(final):
        return False
    return where is None or distance_m(lat, lon, *where) <= MAX_DISTANCE_M


def distance_m(lat1, lon1, lat2, lon2):
    dy = (lat2 - lat1) * 110_540
    dx = (lon2 - lon1) * 111_320 * math.cos(math.radians(lat1))
    return math.hypot(dx, dy)


def title_matches(title, name):
    """True for "Name", "Name, Place", or "Name (qualifier)"."""
    return re.fullmatch(rf"{re.escape(name)}(,\s.+|\s\(.+\))?", title, re.IGNORECASE) is not None


def character(wikitext):
    """Return the lead and the character sections of an article as plain text.

    History stays because it shapes a neighborhood's character, but it is
    capped so long histories do not drown out the rest of the article.
    """
    code = mwparserfromhell.parse(wikitext)
    sections = code.get_sections(levels=[2], include_lead=True)
    lead = plain_text(str(sections[0])) if sections else ""

    parts = [lead]
    for section in sections[1:]:
        heading = section.filter_headings()[0].title.strip().lower()
        if EXCLUDED.search(heading):
            continue
        text = plain_text(str(section).split("\n", 1)[1] if "\n" in str(section) else "")
        if HISTORY.search(heading):
            text = text[:HISTORY_CHARS]
        parts.append(text)
    return lead, " ".join(p for p in parts if p)


def summary(lead, sentences=2):
    """First sentences of the lead, for display next to a match."""
    lead = re.sub(r"\s*\([^)]*\)", "", lead)
    return " ".join(re.split(r"(?<=[.!?])\s+", lead)[:sentences])
