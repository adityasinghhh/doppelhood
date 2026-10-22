# Doppelhood

Doppelhood compares neighborhoods across two cities and finds each one's closest equivalent, such as the New York neighborhood that plays the role the Mission plays in San Francisco. Matches are directional rather than exact, so each one carries a similarity score and a breakdown of where the two neighborhoods agree and where they differ.

## Approach

Similarity is measured on what a visitor experiences rather than on demographics. The Mission and parts of the Bronx look alike in census data, but someone who likes the Mission for its taquerias, murals, and bars will find a closer match in Williamsburg or the East Village.

Each neighborhood is normalized within its own city, so a match means the two neighborhoods play the same role locally even when one city is denser or more expensive than the other.

## Data Sources

| Source | Signal | Limitation |
|---|---|---|
| OpenStreetMap | Current neighborhood names and locations, and the density and mix of restaurants, bars, cafes, shops, venues, and parks | Neighborhood boundaries are not mapped consistently, so each neighborhood is the area within 500 meters of its label |
| Wikidata | Links from each OpenStreetMap label to its Wikipedia article, and neighborhoods that OpenStreetMap does not label | Some links are wrong and are checked by distance |
| Wikipedia | Each neighborhood's character, from its article minus demographics, government, and transport | Coverage of small neighborhoods is uneven |
| Wikivoyage | Eat, Drink, See, Do, and Buy listings with coordinates, assigned to the nearest neighborhood | Only neighborhoods visitors frequent have listings, so elsewhere each section is scored from OpenStreetMap counts of the matching features |

## Scoring

Each signal is centered within its city before comparing, so two neighborhoods match when they differ from the rest of their own cities in the same way. Text is embedded with [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2), and street life is compared as within-city z-scores of log counts. A food, nightlife, sights, activities, or shopping score uses Wikivoyage listings when both neighborhoods have them, and otherwise the distance between their z-scores for the features that section covers, such as restaurants, fast food, and cafes for food.

Every signal's similarity is converted to a percentile over all cross-city pairs, and the percentiles are blended (character 40%, listings 30%, street life 30%). Nearly every best match lands near the top of that scale, so the scores shown rank each pair against every neighborhood's best match in each other city instead. A score of 50 means the pair is as close as a typical best match, and a low score means even the closest neighborhood in that city is a stretch.

## Status

All 21 cities in [config/cities.yaml](config/cities.yaml) are built, with 2,188 neighborhoods between them. [PRODUCT.md](PRODUCT.md) holds the product vision, coverage, known misses, and wishlist.

## Running Locally

```sh
brew install osmium-tool xcodegen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m doppelhood.match san-francisco new-york
.venv/bin/python -m doppelhood.validate
```

The matcher fetches each city's boundary, neighborhood labels, and points of interest from the Overpass API on first use, or cuts them from a Geofabrik extract when one is already in `data/raw/pbf/`. It caches every source under `data/raw/` and writes `web/data/matches.json`. The validator scores the same cities and reports where each comparison in [config/validation.yaml](config/validation.yaml) ranks, so a change to matching can be checked against it.

The iOS app bundles that file. Generate the Xcode project with `cd ios && xcodegen`, then open `Doppelhood.xcodeproj` and run it on a simulator. The web preview reads the same file: `cd web && python3 -m http.server 8765`.

## Licensing

The code is MIT licensed. Data from each source keeps that source's license, and [ATTRIBUTION.md](ATTRIBUTION.md) lists every source, its license, and the credit it requires.
