# Doppelhood

Doppelhood compares neighborhoods across two cities and finds each one's closest equivalent, such as the New York neighborhood that plays the role the Mission plays in San Francisco. Matches are directional rather than exact, so each one carries a similarity score and a breakdown of where the two neighborhoods agree and where they differ.

## Approach

Similarity is measured on what a visitor experiences rather than on demographics. The Mission and parts of the Bronx look alike in census data, but someone who likes the Mission for its taquerias, murals, and bars will find a closer match in Williamsburg or the East Village.

Each neighborhood is normalized within its own city, so a match means the two neighborhoods play the same role locally even when one city is denser or more expensive than the other.

## Data Sources

| Source | Signal | Limitation |
|---|---|---|
| Wikivoyage | Visitor experience, split into sections such as See, Do, Eat, and Drink | Districts are coarser than neighborhoods |
| Wikipedia | History, character, and reputation of individual neighborhoods | Skews toward demographic description |
| OpenStreetMap | Density and mix of bars, cafes, restaurants, parks, and venues | Says nothing about atmosphere |
| Who's On First | Neighborhood boundaries | Boundary quality varies by city |

## Scoring

Each district's Understand, See, Do, Buy, Eat, and Drink sections are embedded separately with [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2), so two districts are compared Eat to Eat and Drink to Drink. Before comparing, each city's average vector is subtracted from its districts' vectors, which removes what every district in the city shares and leaves how each one differs from the rest of its own city.

Scores are percentiles. A score of 90 means the pairing is more similar than 90% of all pairings between a San Francisco district and a district in another city, and the same holds for each section's score. OpenStreetMap features are not yet blended in.

## Status

The current release compares San Francisco against the ten largest US cities by the Census Bureau's Vintage 2025 population estimates, which are listed in [config/cities.yaml](config/cities.yaml). Phoenix, San Antonio, and Fort Worth have no Wikivoyage district articles and are not yet matched. [PRODUCT.md](PRODUCT.md) lists coverage per city, the known misses, and the wishlist.

The app is live at [adityasinghhh.github.io/doppelhood](https://adityasinghhh.github.io/doppelhood/).

## Running Locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m doppelhood.match
cd web && python3 -m http.server 8765
```

The matcher caches Wikivoyage responses under `data/raw/` and writes `web/data/matches.json`, which the page at http://localhost:8765 reads.

## Licensing

The code is MIT licensed. Data from each source keeps that source's license, and [ATTRIBUTION.md](ATTRIBUTION.md) lists every source, its license, and the credit it requires.
