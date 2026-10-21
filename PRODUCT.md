# Product

This file tracks what Doppelhood is meant to be, what it does today, where its matches are known to go wrong, and what is planned next.

## Vision

Doppelhood is a free iOS app that tells a traveler which neighborhood in a city they are visiting feels like a neighborhood they already know, from any city to any other.

| Decision | Choice | Consequence |
|---|---|---|
| Audience | Travelers | Matches weight food, nightlife, sights, and atmosphere over rent, schools, or commute |
| Granularity | Neighborhoods | Wikivoyage districts are too coarse, so matching moves to Wikipedia neighborhood articles and the OpenStreetMap features around each neighborhood's label |
| Base city | Any city | San Francisco can no longer serve as the only check on quality, so the validation set needs expected matches from several cities |
| Platform | iOS app | The Python pipeline stays as the data builder, and the app ships its output; the web page remains as a preview |
| Pricing | Free | No payments or accounts to build, and pricing can be revisited once people use it |

## Features

- **Current neighborhoods** come from the place labels OpenStreetMap mappers maintain inside each city's boundary, so former names such as the Barbary Coast and single streets such as Belden Place are left out. Historic-district and housing-development labels are excluded, as are labels for areas larger than a neighborhood, such as New York's boroughs.
- **Character matching** embeds each neighborhood's Wikipedia article without its demographics, government, and transport sections, and with the neighborhood's own name removed so matches cannot hinge on words like "Beach."
- **Visitor listings** assign every geolocated Wikivoyage Eat, Drink, See, Do, and Buy listing to its nearest neighborhood and compare those listings section by section.
- **Street life** compares the mix of restaurants, bars, cafes, shops, venues, and parks within 500 meters of each neighborhood, counted from OpenStreetMap.
- **Standouts** name the feature each neighborhood has most of relative to the rest of its city, such as nightlife in the Mission or hotels in the Tenderloin, or mark it as mostly residential.
- **Any city as the starting point**, with every signal measured against the rest of its own city first, so a match means two neighborhoods play the same role in their cities.
- **Scores** rank each match against every neighborhood's best match in another city, overall and per signal, so a weak best match reads as weak.
- **iOS app** in `ios/` opens on a photo of the chosen city and lists its neighborhoods with each one's standout and closest match elsewhere. A neighborhood's page shows it on a map, then its top five matches in another city: the best with its own map and a bar per signal, the rest with their two strongest signals and a tap to see all seven. Signals a pair cannot be scored on, for lack of Wikivoyage listings, are marked rather than hidden. The About screen credits every source and photo.
- **Web preview** at [adityasinghhh.github.io/doppelhood](https://adityasinghhh.github.io/doppelhood/) shows the same data in a browser.

## Coverage

| City | Neighborhoods | Notes |
|---|---|---|
| San Francisco | 61 | |
| New York | 265 | |
| Mexico City | 58 | OpenStreetMap labels about 2,000 colonias, but only the better-known ones have English Wikipedia articles |
| Boston | 44 | |
| New Orleans | 26 | OpenStreetMap labels fewer New Orleans neighborhoods than the city's official list |
| Other nine cities | 0 | Their OpenStreetMap extracts are not downloaded yet |

A neighborhood is included only when it has an English Wikipedia article within 3 kilometers of its label, and only when that article describes a place that exists and that people live in. An article whose first sentence is in the past tense ("Tlatelolco was a pre-Columbian altepetl") or that describes an uninhabited island is dropped. OpenStreetMap's Wikidata links are checked against that rule too, since some point at a same-named town or a railroad station. Labels with no qualifying article, such as Cow Hollow, Presidio Heights, and Gramercy, drop out for now.

## Known Misses

These come from checking matches against first-hand knowledge of San Francisco, and they are the test cases for any change to the scoring:
- Pacific Heights matches Tremont and Kensington rather than the Upper East Side.
- The Castro matches Civic Center and Harlem rather than Chelsea or the West Village.
- The Haight matches the Garment District, and Noe Valley matches Cambria Heights.
- The Mission's top New York match is Fresh Pond, ahead of Williamsburg and the East Village, which follow closely.

## Wishlist

| Item | Why |
|---|---|
| Labeled validation set | A list of expected matches from people who know both cities would turn the known misses into a score that every model change can be measured against |
| Signals for every neighborhood | Food, nightlife, sights, activities, and shopping need Wikivoyage listings in both neighborhoods, which two thirds of pairs lack; OpenStreetMap counts could fill them in |
| Areas outside city limits | The Las Vegas Strip and Miami Beach sit outside the cities they are known by, so city boundaries alone leave them out |
| Traveler signals | Walkability, transit, late-night activity, green space, and how touristy a neighborhood is, all measurable from OpenStreetMap |
| Safety | Reported-crime data from each city's open-data portal, shown relative to the rest of the city and kept out of the match score |
| Neighborhoods without articles | Labels such as Cow Hollow could be kept with street life and listings alone, with a summary written from those signals |
| Spanish Wikipedia for Mexico City | Most colonias have Spanish articles only, which a multilingual embedding model could compare against English ones |
| Who's On First boundaries | Finer neighborhood shapes to attach Wikipedia and OpenStreetMap data to, and the basis for a map view |
| Extracted tags | Labels such as "gritty," "touristy," or "late-night" pulled from the text would explain a match in words a reader recognizes |
| Adjustable weights | A reader who cares about food and nightlife could weight those sections up and get different matches than a family would |
| Map view | Showing the matched districts side by side on maps of both cities |
