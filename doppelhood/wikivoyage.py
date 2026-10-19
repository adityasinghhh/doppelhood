"""Fetch Wikivoyage district articles and split them into visitor-experience sections."""

import json
import re
import time
from pathlib import Path

import mwparserfromhell
import requests

API = "https://en.wikivoyage.org/w/api.php"
USER_AGENT = "doppelhood/0.1 (https://github.com/adityasinghhh/doppelhood)"
RAW_DIR = Path("data/raw/wikivoyage")

# Sections compared across districts. Sleep, Connect and Get in describe
# logistics rather than what a neighborhood is like, so they are skipped.
SECTIONS = ["understand", "see", "do", "buy", "eat", "drink"]

LISTING_TEMPLATES = {"see", "do", "buy", "eat", "drink", "sleep", "listing", "go"}
REGION_PARAM = re.compile(r"region(\d+)(name|items)")

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def fetch_page(title):
    """Return the wikitext and revision of a page, cached under data/raw."""
    cache = RAW_DIR / (title.replace("/", "__") + ".json")
    if cache.exists():
        return json.loads(cache.read_text())

    response = session.get(API, params={
        "action": "parse",
        "page": title,
        "prop": "wikitext|revid",
        "redirects": 1,
        "format": "json",
        "formatversion": 2,
    })
    response.raise_for_status()
    parsed = response.json()["parse"]
    page = {"title": parsed["title"], "revid": parsed["revid"], "wikitext": parsed["wikitext"]}

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(page))
    time.sleep(0.5)
    return page


def region_links(wikitext):
    """Return the (title, description) pairs listed in a page's Regionlists.

    A region links to its article from regionNname, or groups several district
    articles under regionNitems. The description belongs to the region, so only
    a regionNname link inherits it.
    """
    links = {}
    for template in mwparserfromhell.parse(wikitext).filter_templates():
        if template.name.strip().lower() != "regionlist":
            continue
        for param in template.params:
            match = REGION_PARAM.fullmatch(str(param.name).strip())
            if not match:
                continue
            description_key = f"region{match.group(1)}description"
            description = ""
            if match.group(2) == "name" and template.has(description_key):
                description = plain_text(str(template.get(description_key).value))
            for link in param.value.filter_wikilinks():
                links.setdefault(str(link.title).strip(), description)
    return list(links.items())


def plain_text(wikitext):
    """Flatten wikitext to prose, keeping the name and description of each listing."""
    code = mwparserfromhell.parse(wikitext)
    for template in code.filter_templates(recursive=False):
        name = template.name.strip().lower()
        if name in LISTING_TEMPLATES:
            parts = [str(template.get(key).value).strip()
                     for key in ("name", "content") if template.has(key)]
            replacement = ". ".join(p for p in parts if p)
        else:
            replacement = ""
        try:
            code.replace(template, replacement)
        except ValueError:
            pass
    text = mwparserfromhell.parse(str(code)).strip_code()
    return re.sub(r"\s+", " ", text).strip()


def split_sections(wikitext):
    """Map each compared section name to its plain text."""
    sections = {}
    for section in mwparserfromhell.parse(wikitext).get_sections(levels=[2]):
        heading = section.filter_headings()[0].title.strip().lower()
        if heading in SECTIONS:
            body = str(section).split("\n", 1)[1] if "\n" in str(section) else ""
            text = plain_text(body)
            if text:
                sections[heading] = text
    return sections


def districts(city_title, depth=0):
    """Walk Regionlists from a city article down to leaf district articles.

    Most cities keep districts as subpages ("Chicago/Loop"), and some city
    articles also list surrounding metro regions, so subpage links win when a
    page has any. New York has none at the top level because its boroughs are
    articles of their own, each with district subpages.
    """
    page = fetch_page(city_title)
    links = region_links(page["wikitext"])
    subpages = [(t, d) for t, d in links if t.startswith(page["title"] + "/")]
    links = subpages or links

    leaves = {}
    for title, description in links:
        child = fetch_page(title)
        if region_links(child["wikitext"]) and depth < 1:
            for leaf in districts(title, depth + 1):
                leaves.setdefault(leaf["title"], leaf)
        else:
            child.setdefault("summary", description)
            leaves.setdefault(child["title"], child)
    return list(leaves.values())


def district_records(city):
    """Build the district records for one city from config/cities.yaml."""
    records = []
    for page in districts(city["wikivoyage"]):
        title = page["title"]
        parent, _, name = title.rpartition("/")
        # Label districts below a borough with it, so Brooklyn's "East" and
        # Queens's "East" stay distinguishable.
        if parent and parent != city["wikivoyage"] and parent not in name:
            name = f"{name}, {parent}"
        records.append({
            "city": city["slug"],
            "name": name or title,
            "title": title,
            "summary": page.get("summary", ""),
            "source_url": "https://en.wikivoyage.org/wiki/" + title.replace(" ", "_"),
            "revid": page["revid"],
            "sections": split_sections(page["wikitext"]),
        })
    return records
