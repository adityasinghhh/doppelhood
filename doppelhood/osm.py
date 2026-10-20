"""Read current neighborhoods and points of interest from a local OpenStreetMap extract.

Each city's Geofabrik extract is downloaded once into data/raw/pbf/ and cut
down with osmium to the city's boundary, its place=neighbourhood, suburb, and
quarter labels, and its restaurants, bars, shops, venues, and parks. Labels
are what mappers maintain today, so the list reflects current neighborhoods
rather than every name the city has ever used.

Neighborhood boundaries are not mapped consistently, so each neighborhood is
represented by the area within RADIUS_M of its label. Every neighborhood
therefore covers the same area and the counts read as densities.
"""

import json
import re
import subprocess
from pathlib import Path

import numpy as np
import requests
from shapely.geometry import Point, shape
from shapely.ops import unary_union

from doppelhood.wikivoyage import USER_AGENT

GEOFABRIK = "https://download.geofabrik.de/{}-latest.osm.pbf"
PBF_DIR = Path("data/raw/pbf")
CITY_DIR = Path("data/raw/osm")
RADIUS_M = 500

PLACE_TYPES = {"neighbourhood", "suburb", "quarter"}
# Some place labels name a historic district or a housing development rather
# than a neighborhood people would recognize.
NOT_NEIGHBORHOOD = re.compile(r"historic district|\bhouses$", re.IGNORECASE)

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


def osmium(*args):
    subprocess.run(["osmium", *args, "--overwrite", "--no-progress"], check=True)


def extract(city):
    """Return the path of the city's Geofabrik extract, downloading it if missing."""
    path = PBF_DIR / (city["geofabrik"].rsplit("/", 1)[-1] + "-latest.osm.pbf")
    if not path.exists():
        PBF_DIR.mkdir(parents=True, exist_ok=True)
        # Download beside the target and rename at the end, so an interrupted
        # download is never mistaken for a complete extract.
        partial = path.with_suffix(".part")
        with requests.get(GEOFABRIK.format(city["geofabrik"]), stream=True,
                          headers={"User-Agent": USER_AGENT}, timeout=60) as response:
            response.raise_for_status()
            with open(partial, "wb") as f:
                for chunk in response.iter_content(1 << 20):
                    f.write(chunk)
        partial.rename(path)
    return path


def features(path):
    """Read a GeoJSON sequence written by osmium export."""
    with open(path) as f:
        return [json.loads(line.lstrip("\x1e")) for line in f if line.strip()]


def prepare(city):
    """Cut the city's boundary, neighborhood labels, and POIs out of its extract."""
    out = CITY_DIR / city["slug"]
    if (out / "pois.geojsonseq").exists():
        return out
    out.mkdir(parents=True, exist_ok=True)
    source = str(extract(city))

    osmium("tags-filter", source, f"r/wikidata={city['wikidata']}", "-o", str(out / "boundary.pbf"))
    osmium("export", str(out / "boundary.pbf"), "-f", "geojsonseq", "-o", str(out / "boundary.geojsonseq"))
    boundary = city_boundary(out)
    west, south, east, north = boundary.bounds

    osmium("extract", "-b", f"{west},{south},{east},{north}", source, "-o", str(out / "city.pbf"))
    osmium("tags-filter", str(out / "city.pbf"), "nwr/place=" + ",".join(sorted(PLACE_TYPES)),
           "-o", str(out / "places.pbf"))
    osmium("export", str(out / "places.pbf"), "-f", "geojsonseq", "-o", str(out / "places.geojsonseq"))
    osmium("tags-filter", str(out / "city.pbf"), "nwr/amenity", "nwr/shop", "nwr/tourism", "nwr/leisure",
           "-o", str(out / "pois.pbf"))
    osmium("export", str(out / "pois.pbf"), "-f", "geojsonseq", "-o", str(out / "pois.geojsonseq"))
    return out


def city_boundary(out):
    polygons = [shape(f["geometry"]) for f in features(out / "boundary.geojsonseq")
                if f["geometry"]["type"] in ("Polygon", "MultiPolygon")]
    return unary_union(polygons)


def neighborhoods(city):
    """Return the current neighborhood labels inside the city boundary.

    Labels that are also administrative boundaries are skipped, since those
    are boroughs or the city itself rather than neighborhoods.
    """
    out = prepare(city)
    boundary = city_boundary(out)
    results, seen = [], set()
    for f in features(out / "places.geojsonseq"):
        props = f["properties"]
        if props.get("place") not in PLACE_TYPES or "name" not in props:
            continue
        if props.get("boundary") == "administrative" or props.get("wikidata") == city["wikidata"]:
            continue
        if NOT_NEIGHBORHOOD.search(props["name"]) or props["name"] in city.get("exclude_labels", []):
            continue
        point = shape(f["geometry"]).representative_point()
        if not boundary.contains(point) or props["name"] in seen:
            continue
        seen.add(props["name"])
        results.append({
            "name": props["name"],
            "lat": point.y,
            "lon": point.x,
            "wikidata": props.get("wikidata"),
            "wikipedia": props.get("wikipedia"),
        })
    return results


def distances_m(lat, lon, coords):
    """Equirectangular distance in meters, accurate at neighborhood scale."""
    dy = (coords[:, 0] - lat) * 110_540
    dx = (coords[:, 1] - lon) * 111_320 * np.cos(np.radians(lat))
    return np.hypot(dx, dy)


def attach_features(city, hoods):
    """Attach a count per feature within RADIUS_M to every neighborhood."""
    coords, kinds = [], []
    for f in features(prepare(city) / "pois.geojsonseq"):
        kind = category(f["properties"])
        if kind:
            point = shape(f["geometry"]).representative_point()
            coords.append([point.y, point.x])
            kinds.append(kind)
    coords, kinds = np.array(coords), np.array(kinds)
    for n in hoods:
        near = kinds[distances_m(n["lat"], n["lon"], coords) <= RADIUS_M]
        n["osm"] = {f: int((near == f).sum()) for f in FEATURES}
