# Doppelhood

Doppelhood compares neighborhoods across two cities and finds each one's closest equivalent, such as the New York neighborhood that plays the role the Mission plays in San Francisco. Matches are directional rather than exact, so each one carries a similarity score and a breakdown of where the two neighborhoods agree and where they differ.

## Approach

Similarity is measured on what a visitor experiences rather than on demographics. The Mission and parts of the Bronx look alike in census data, but someone who likes the Mission for its taquerias, murals, and bars will find a closer match in Williamsburg or the East Village.

Each neighborhood is normalized within its own city, so a match means the two neighborhoods play the same role locally even when one city is denser or more expensive than the other.

## Data Sources

| Source | Signal | Limitation |
|---|---|---|
| OpenStreetMap | Current neighborhood names and locations, and the density and mix of restaurants, bars, cafes, shops, venues, and parks | Neighborhood boundaries are not mapped consistently, so each neighborhood is the area within 500 meters of its label |
| Wikidata | Links from each OpenStreetMap label to its Wikipedia article | Some links are wrong and are checked by distance |
| Wikipedia | Each neighborhood's character, from its article minus demographics, government, and transport | Coverage of small neighborhoods is uneven |
| Wikivoyage | Eat, Drink, See, Do, and Buy listings with coordinates, assigned to the nearest neighborhood | Only neighborhoods visitors frequent have listings |

## Scoring

Each signal is centered within its city before comparing, so two neighborhoods match when they differ from the rest of their own cities in the same way. Text is embedded with [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2), and street life is compared as within-city z-scores of log counts.

Every signal's similarity is converted to a percentile over all cross-city pairs, the percentiles are blended (character 40%, listings 30%, street life 30%), and the blend is converted to a percentile again. A score of 90 means the pairing is more similar than 90% of all pairings between neighborhoods in different cities.

## Status

San Francisco, New York, Mexico City, Boston, and New Orleans are built, with 454 neighborhoods between them. [config/cities.yaml](config/cities.yaml) lists every city, including those not yet built. [PRODUCT.md](PRODUCT.md) holds the product vision, coverage, known misses, and wishlist.

## Running Locally

```sh
brew install osmium-tool xcodegen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m doppelhood.match san-francisco new-york
```

The matcher downloads each city's OpenStreetMap extract from Geofabrik on first use (several hundred megabytes per state), caches every source under `data/raw/`, and writes `web/data/matches.json`.

The iOS app bundles that file. Generate the Xcode project with `cd ios && xcodegen`, then open `Doppelhood.xcodeproj` and run it on a simulator. The web preview reads the same file: `cd web && python3 -m http.server 8765`.

## Licensing

The code is MIT licensed. Data from each source keeps that source's license, and [ATTRIBUTION.md](ATTRIBUTION.md) lists every source, its license, and the credit it requires.
