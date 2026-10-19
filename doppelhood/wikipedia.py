"""Fetch Wikipedia neighborhood articles and keep the parts that describe character."""

import json
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

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def fetch(title):
    cache = RAW_DIR / (title.replace("/", "__") + ".json")
    if cache.exists():
        return json.loads(cache.read_text())
    response = session.get(API, params={
        "action": "parse", "page": title, "prop": "wikitext|revid",
        "redirects": 1, "format": "json", "formatversion": 2,
    })
    response.raise_for_status()
    parsed = response.json().get("parse")
    page = {"title": parsed["title"], "revid": parsed["revid"], "wikitext": parsed["wikitext"]} if parsed else None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(page))
    time.sleep(0.3)
    return page


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
