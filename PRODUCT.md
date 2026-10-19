# Product

This file tracks what Doppelhood does today, where its matches are known to go wrong, and what is planned next.

## Features

- **District matching** ranks the five closest districts in each comparison city for every San Francisco district, using the Wikivoyage articles for 104 districts across eight cities.
- **Section breakdown** scores each match separately on Character, Sights, Activities, Shopping, Food, and Nightlife, so a reader can see which parts of the experience line up.
- **City-relative scoring** removes what all of a city's districts share before comparing, so a match means two districts play the same role in their own cities.
- **Percentile scores** report each match against every other cross-city pairing, which keeps the numbers readable and comparable.
- **Web app** at [adityasinghhh.github.io/doppelhood](https://adityasinghhh.github.io/doppelhood/) lets a reader pick a San Francisco district and a city, and links every district to its Wikivoyage source.

## Coverage

| City | Districts | Notes |
|---|---|---|
| San Francisco | 15 | Base city |
| New York | 31 | Districts across Manhattan, Brooklyn, and Queens, plus the Bronx and Staten Island as single districts |
| Chicago | 21 | |
| Houston | 10 | |
| San Diego | 9 | |
| Philadelphia | 8 | |
| Los Angeles | 7 | The Westside and San Fernando Valley are missing because Wikivoyage files them as county regions rather than city districts |
| Dallas | 3 | Too coarse for useful matches |
| Phoenix, San Antonio, Fort Worth | 0 | Wikivoyage has no district articles for them |

## Known Misses

These come from checking matches against first-hand knowledge of San Francisco, and they are the test cases for any change to the scoring:
- The Castro does not match Lakeview (Boystown) in Chicago or Chelsea in New York. Its Wikivoyage article is shared with Noe Valley and says little about LGBTQ nightlife.
- The Mission's top New York match is Harlem and Upper Manhattan, ahead of the East Village. It does match Pilsen and Logan Square in Chicago, which is closer to expectations.
- SoMa matches Bedford-Stuyvesant in New York, which has no clear basis.

## Wishlist

| Item | Why |
|---|---|
| Labeled validation set | A list of expected matches from people who know both cities would turn the known misses into a score that every model change can be measured against |
| OpenStreetMap features | Density and the mix of bars, cafes, restaurants, and parks would add a signal that does not depend on how well a Wikivoyage article is written |
| Wikipedia neighborhood articles | Would cover Phoenix, San Antonio, and Fort Worth, and split coarse districts such as Castro-Noe Valley into real neighborhoods |
| Who's On First boundaries | Finer neighborhood shapes to attach Wikipedia and OpenStreetMap data to, and the basis for a map view |
| Extracted tags | Labels such as "gritty," "touristy," or "late-night" pulled from the text would explain a match in words a reader recognizes |
| Adjustable weights | A reader who cares about food and nightlife could weight those sections up and get different matches than a family would |
| Any city as the base | Comparing from New York to Chicago, not only from San Francisco |
| International cities | The Wikivoyage format is the same worldwide, so the pipeline should carry over with little change |
| Map view | Showing the matched districts side by side on maps of both cities |
