# Doppelhood

Doppelhood compares neighborhoods across two cities and finds each one's closest equivalent, such as the New York neighborhood that plays the role the Mission plays in San Francisco. Matches are directional rather than exact, so each one carries a similarity score and a breakdown of where the two neighborhoods agree and where they differ.

## Approach

Similarity is measured on what a visitor experiences rather than on demographics. The Mission and parts of the Bronx look alike in census data, but someone who likes the Mission for its taquerias, murals, and bars will find a closer match in Williamsburg or the East Village.

Each neighborhood is normalized within its own city, so a match means the two neighborhoods play the same role locally even when one city is denser or more expensive than the other.

## Data Sources

| Source | Signal | Limitation |
|---|---|---|
| Wikivoyage | Visitor experience, split into See, Do, Eat, Drink, and Sleep sections | Districts are coarser than neighborhoods |
| Wikipedia | History, character, and reputation of individual neighborhoods | Skews toward demographic description |
| OpenStreetMap | Density and mix of bars, cafes, restaurants, parks, and venues | Says nothing about atmosphere |
| Who's On First | Neighborhood boundaries | Boundary quality varies by city |

## Scoring

Each Wikivoyage section is embedded separately, so two districts are compared Eat to Eat and Drink to Drink, which produces the per-dimension breakdown directly. Structured features from OpenStreetMap are blended with the text similarity to produce the final score.

## Status

The first release compares San Francisco against the ten largest US cities by the Census Bureau's Vintage 2025 population estimates, which are listed in [config/cities.yaml](config/cities.yaml). San Francisco is the validation set because its neighborhoods are the ones the matches can be checked against from experience. San Antonio and Fort Worth have no Wikivoyage district articles, so their matches rest on Wikipedia and OpenStreetMap alone and carry less visitor-experience signal.

## Licensing

The code is MIT licensed. Data from each source keeps that source's license, and [ATTRIBUTION.md](ATTRIBUTION.md) lists every source, its license, and the credit it requires.
