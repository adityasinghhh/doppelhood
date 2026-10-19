"""Count OpenStreetMap points of interest around each neighborhood.

Neighborhood boundaries are not yet available, so each neighborhood is
represented by the area within RADIUS_M of its Wikidata coordinate. Every
neighborhood therefore covers the same area and the counts read as densities.
"""

import json
import time
from pathlib import Path

import numpy as np
import requests

from doppelhood.wikivoyage import USER_AGENT

ENDPOINT = "https://overpass-api.de/api/interpreter"
RAW_DIR = Path("data/raw/osm")
RADIUS_M = 500
TILE_DEGREES = 0.1

QUERY = """
[out:json][timeout:600];
(
  nwr["amenity"~"^(restaurant|fast_food|food_court|cafe|ice_cream|bar|pub|biergarten|nightclub|theatre|cinema|arts_centre|music_venue)$"]({bbox});
  nwr["shop"]({bbox});
  nwr["tourism"~"^(museum|gallery|attraction|viewpoint|hotel|hostel|guest_house)$"]({bbox});
  nwr["leisure"~"^(park|garden)$"]({bbox});
);
out center tags;
"""

CATEGORIES = {
    "restaurant": {"amenity": {"restaurant"}},
    "fast_food": {"amenity": {"fast_food", "food_court"}},
    "cafe": {"amenity": {"cafe", "ice_cream"}},
    "bar": {"amenity": {"bar", "pub", "biergarten"}},
    "nightlife": {"amenity": {"nightclub", "music_venue"}},
    "culture": {"amenity": {"theatre", "cinema", "arts_centre"}, "tourism": {"museum", "gallery"}},
    "attraction": {"tourism": {"attraction", "viewpoint"}},
    "lodging": {"tourism": {"hotel", "hostel", "guest_house"}},
    "park": {"leisure": {"park", "garden"}},
    "fashion": {"shop": {"clothes", "boutique", "shoes", "jewelry", "second_hand", "vintage", "fashion_accessories"}},
    "grocery": {"shop": {"bakery", "deli", "greengrocer", "butcher", "convenience", "supermarket", "alcohol"}},
}
FEATURES = list(CATEGORIES) + ["other_shop"]


def category(tags):
    for name, rules in CATEGORIES.items():
        if any(tags.get(key) in values for key, values in rules.items()):
            return name
    return "other_shop" if "shop" in tags else None


def overpass(bbox, attempts=4):
    for attempt in range(attempts):
        response = requests.post(ENDPOINT, data={"data": QUERY.format(bbox=bbox)},
                                 headers={"User-Agent": USER_AGENT}, timeout=900)
        if response.status_code in (429, 502, 503, 504) and attempt < attempts - 1:
            time.sleep(30 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()["elements"]


def fetch_points(city_slug, neighborhoods, margin=0.01, tile=TILE_DEGREES):
    """Return an array of (lat, lon) and a parallel list of categories for the city.

    Large cities are queried in tiles, since one query over all of New York
    exceeds what the public Overpass server will return.
    """
    cache = RAW_DIR / f"{city_slug}.json"
    if not cache.exists():
        lats = [n["lat"] for n in neighborhoods]
        lons = [n["lon"] for n in neighborhoods]
        south, west = min(lats) - margin, min(lons) - margin
        north, east = max(lats) + margin, max(lons) + margin

        seen, points = set(), []
        for lat in np.arange(south, north, tile):
            for lon in np.arange(west, east, tile):
                bbox = f"{lat},{lon},{min(lat + tile, north)},{min(lon + tile, east)}"
                for element in overpass(bbox):
                    key = (element["type"], element["id"])
                    where = element.get("center", element)
                    kind = category(element.get("tags", {}))
                    if key not in seen and kind and "lat" in where:
                        seen.add(key)
                        points.append([where["lat"], where["lon"], kind])
                time.sleep(2)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(points))
    points = json.loads(cache.read_text())
    coords = np.array([[p[0], p[1]] for p in points])
    return coords, [p[2] for p in points]


def distances_m(lat, lon, coords):
    """Equirectangular distance in meters, accurate at neighborhood scale."""
    dy = (coords[:, 0] - lat) * 110_540
    dx = (coords[:, 1] - lon) * 111_320 * np.cos(np.radians(lat))
    return np.hypot(dx, dy)


def attach_features(city_slug, neighborhoods):
    """Attach a count per feature within RADIUS_M to every neighborhood."""
    coords, kinds = fetch_points(city_slug, neighborhoods)
    kinds = np.array(kinds)
    for n in neighborhoods:
        near = kinds[distances_m(n["lat"], n["lon"], coords) <= RADIUS_M]
        n["osm"] = {f: int((near == f).sum()) for f in FEATURES}
