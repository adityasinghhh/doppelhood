"""Read current neighborhoods and points of interest from OpenStreetMap.

Each city's boundary, its place=neighbourhood, suburb, and quarter labels,
and its restaurants, bars, shops, venues, and parks are saved under
data/raw/osm/<slug>/. When the city's Geofabrik extract is already in
data/raw/pbf/, osmium cuts them out of it; otherwise they come from the
Overpass API, which returns only the city's area rather than a whole state
or country. Labels
are what mappers maintain today, so the list reflects current neighborhoods
rather than every name the city has ever used.

Neighborhood boundaries are not mapped consistently, so each neighborhood is
represented by the area within RADIUS_M of its label. Every neighborhood
therefore covers the same area and the counts read as densities.
"""

import json
import re
import subprocess
import time
from pathlib import Path

import numpy as np
import requests
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import linemerge, polygonize, unary_union

from doppelhood.wikivoyage import USER_AGENT

GEOFABRIK = "https://download.geofabrik.de/{}-latest.osm.pbf"
# The main Overpass server and two public mirrors of the same data, tried in
# turn when one is busy.
OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
# The public Overpass server rejects heavy queries, so large cities are
# fetched in tiles of about this many degrees, and busy responses are retried.
TILE_DEG = 0.15
OVERPASS_RETRIES = 18
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
    path = extract_path(city)
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


def extract_path(city):
    return PBF_DIR / (city["geofabrik"].rsplit("/", 1)[-1] + "-latest.osm.pbf")


def prepare(city):
    """Save the city's boundary, neighborhood labels, and POIs, from its extract
    when one is on disk and from Overpass otherwise."""
    out = CITY_DIR / city["slug"]
    if (out / "pois.geojsonseq").exists():
        return out
    out.mkdir(parents=True, exist_ok=True)
    if not extract_path(city).exists():
        return prepare_overpass(city, out)
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


def overpass(query):
    for attempt in range(OVERPASS_RETRIES):
        endpoint = OVERPASS[attempt % len(OVERPASS)]
        try:
            response = requests.post(endpoint, data={"data": f"[out:json][timeout:300];{query}"},
                                     headers={"User-Agent": USER_AGENT}, timeout=(20, 360))
        except (requests.ConnectionError, requests.Timeout):
            continue
        if response.status_code not in (429, 502, 503, 504):
            response.raise_for_status()
            return response.json()["elements"]
        if attempt % len(OVERPASS) == len(OVERPASS) - 1:
            # Back off longer after each full cycle, up to five minutes.
            time.sleep(min(300, 30 * (attempt // len(OVERPASS) + 1)))
    raise RuntimeError(f"Every Overpass server was busy after {OVERPASS_RETRIES} attempts")


def tiles(boundary):
    """Split the boundary's bounding box into tiles, keeping those that touch the city."""
    west, south, east, north = boundary.bounds
    rows = max(1, round((north - south) / TILE_DEG))
    cols = max(1, round((east - west) / TILE_DEG))
    dy, dx = (north - south) / rows, (east - west) / cols
    for r in range(rows):
        for c in range(cols):
            tile = box(west + c * dx, south + r * dy, west + (c + 1) * dx, south + (r + 1) * dy)
            if tile.intersects(boundary):
                yield f"({tile.bounds[1]},{tile.bounds[0]},{tile.bounds[3]},{tile.bounds[2]})"


def overpass_tiled(boundary, statements, cache):
    """Run statements, each with a {bbox} placeholder, over every tile, without duplicates.
    Each tile's result is kept in the cache directory, so a failed run resumes where it stopped."""
    cache.mkdir(parents=True, exist_ok=True)
    elements = {}
    for i, bbox in enumerate(tiles(boundary)):
        query = "(" + "".join(s.format(bbox=bbox) for s in statements) + ");out center tags;"
        path = cache / f"{i}.json"
        if path.exists():
            result = json.loads(path.read_text())
        else:
            result = overpass(query)
            path.write_text(json.dumps(result))
        for e in result:
            elements[(e["type"], e["id"])] = e
    return list(elements.values())


def write_seq(path, features):
    with open(path, "w") as f:
        for feature in features:
            f.write(json.dumps(feature) + "\n")


def as_point_feature(element):
    """A node, or a way or relation's center, as a GeoJSON point with its tags."""
    where = element if element["type"] == "node" else element.get("center")
    if not where:
        return None
    return {"type": "Feature", "properties": element.get("tags", {}),
            "geometry": {"type": "Point", "coordinates": [where["lon"], where["lat"]]}}


def boundary_polygon(relation):
    """Assemble a relation's outer and inner member ways into one polygon."""
    rings = {"outer": [], "inner": []}
    for member in relation["members"]:
        if member["type"] == "way" and member.get("geometry"):
            role = "inner" if member.get("role") == "inner" else "outer"
            rings[role].append(LineString([(p["lon"], p["lat"]) for p in member["geometry"]]))
    outer = unary_union(list(polygonize(linemerge(rings["outer"]))))
    if rings["inner"]:
        outer = outer.difference(unary_union(list(polygonize(linemerge(rings["inner"])))))
    return outer


def prepare_overpass(city, out):
    """Fetch each file in turn, keeping those already fetched, since a large city
    can take many minutes on a busy server."""
    if (out / "boundary.geojsonseq").exists():
        boundary = city_boundary(out)
    else:
        boundary = overpass_boundary(city, out)
    if not (out / "places.geojsonseq").exists():
        places = overpass_tiled(boundary, [f'nwr["place"~"^({"|".join(sorted(PLACE_TYPES))})$"]{{bbox}};'],
                                out / "tiles" / "places")
        write_seq(out / "places.geojsonseq", filter(None, map(as_point_feature, places)))

    # Only the tag values the feature categories count, plus every shop.
    statements = ['nwr["shop"]{bbox};']
    for key in sorted({k for rules in CATEGORIES.values() for k in rules if k != "shop"}):
        values = sorted({v for rules in CATEGORIES.values() for v in rules.get(key, ())})
        statements.append(f'nwr["{key}"~"^({"|".join(values)})$"]{{bbox}};')
    pois = overpass_tiled(boundary, statements, out / "tiles" / "pois")
    write_seq(out / "pois.geojsonseq", filter(None, map(as_point_feature, pois)))
    return out


def overpass_boundary(city, out):
    relations = [e for e in overpass(f'rel["wikidata"="{city["wikidata"]}"];out geom;')
                 if e.get("tags", {}).get("type") in ("boundary", "multipolygon")]
    polygons = [boundary_polygon(r) for r in relations]
    boundary = unary_union([p for p in polygons if not p.is_empty])
    if boundary.is_empty:
        raise RuntimeError(f"No boundary relation in OpenStreetMap for {city['wikidata']}")
    write_seq(out / "boundary.geojsonseq",
              [{"type": "Feature", "properties": {}, "geometry": mapping(boundary)}])
    return boundary


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
