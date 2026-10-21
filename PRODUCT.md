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
- **Visitor listings** assign every geolocated Wikivoyage Eat, Drink, See, Do, and Buy listing to its nearest neighborhood and compare those listings section by section. Where either neighborhood has no listings in a section, the section is scored from OpenStreetMap counts of its features instead, so every pair gets all seven signals.
- **Street life** compares the mix of restaurants, bars, cafes, shops, venues, and parks within 500 meters of each neighborhood, counted from OpenStreetMap.
- **Standouts** name the feature each neighborhood has most of relative to the rest of its city, such as nightlife in the Mission or hotels in the Tenderloin, or mark it as mostly residential.
- **Any city as the starting point**, with every signal measured against the rest of its own city first, so a match means two neighborhoods play the same role in their cities.
- **Scores** rank each match against every neighborhood's best match in another city, overall and per signal, so a weak best match reads as weak.
- **Validation** in `config/validation.yaml` lists comparisons travel writing commonly makes, such as the Mission and Williamsburg, and `doppelhood.validate` reports where each ranks, so a change to matching is kept only when it moves those pairs up.
- **iOS app** in `ios/` opens on two cities side by side, the one you know and the one you are visiting, with each neighborhood in the first beside its best match in the second. A neighborhood's page shows it on a map, then its top five matches in another city: the best with its own map and a bar per signal, the rest with their two strongest signals and a tap to see all seven. The About screen credits every source and photo.
- **Web preview** at [adityasinghhh.github.io/doppelhood](https://adityasinghhh.github.io/doppelhood/) shows the same data in a browser.

## Coverage

| City | Neighborhoods | Notes |
|---|---|---|
| San Francisco | 61 | |
| New York | 265 | |
| Los Angeles | 152 | |
| Chicago | 158 | |
| Boston | 44 | |
| New Orleans | 28 | OpenStreetMap labels fewer New Orleans neighborhoods than the city's official list |
| San Diego | 102 | |
| Denver | 34 | |
| Philadelphia | 102 | |
| Mexico City | 61 | OpenStreetMap labels about 2,000 colonias, but only the better-known ones have English Wikipedia articles |
| Seattle | 76 | |
| Miami | 13 | Miami Beach is a separate city, so it falls outside the boundary |
| Las Vegas | 9 | The Strip lies in unincorporated Paradise, outside the city boundary |
| Washington | 109 | |
| Honolulu | 15 | |
| Nashville | 7 | Most OpenStreetMap labels in Nashville are subdivisions and apartment complexes |
| Austin | 27 | |
| London | 495 | |
| Paris | 52 | |
| Berlin | 117 | |
| Amsterdam | 44 | |

A neighborhood is included only when it has an English Wikipedia article within 3 kilometers of its label, and only when that article describes a place that exists today. An article about a former neighborhood, village, or parish ("Sloterdijk was a village in the Dutch province of North Holland") or about an uninhabited island is dropped. An article in the past tense about something else, such as the Bastille fortress or Fort Logan, keeps its neighborhood, which is then matched without character. OpenStreetMap's Wikidata links are checked against the same rule, since some point at a same-named town or a railroad station. Labels with no qualifying article, such as Cow Hollow, Presidio Heights, and Gramercy, drop out for now.

## Known Misses

[config/validation.yaml](config/validation.yaml) lists 48 comparisons that travel writing and locals commonly make, and `doppelhood.validate` reports where each one ranks. The expected match ranks first in 14 of them and in the top five in 25. The worst misses are these:

| Neighborhood | Expected match | Rank | Top match |
|---|---|---|---|
| Fishtown | Williamsburg | 223 | Clinton Hill |
| Pacific Heights | Upper East Side | 130 | Fordham |
| Pacific Heights | Gold Coast or Lincoln Park | 98 | Kenwood |
| Dogpatch | Red Hook or Dumbo | 83 | Arrochar |
| Williamsburg | Silver Lake or Echo Park | 77 | South Park |
| Noe Valley | Andersonville or Lincoln Square | 73 | Buena Park |
| Noe Valley | Park Slope | 63 | Fordham |

In each of these, the street counts are close but the character scores from the Wikipedia articles treat the two neighborhoods as opposites. Trying other parts of the article as input made matching worse, so a better text model is the likeliest fix.

## Wishlist

| Item | Why |
|---|---|
| Validation from locals | The validation set is editorial, and expected matches from people who know both cities would make it a firmer benchmark |
| Areas outside city limits | The Las Vegas Strip and Miami Beach sit outside the cities they are known by, so city boundaries alone leave them out |
| Traveler signals | Walkability, transit, late-night activity, green space, and how touristy a neighborhood is, all measurable from OpenStreetMap |
| Safety | Reported-crime data from each city's open-data portal, shown relative to the rest of the city and kept out of the match score |
| Neighborhoods without articles | Labels such as Cow Hollow could be kept with street life and listings alone, with a summary written from those signals |
| Spanish Wikipedia for Mexico City | Most colonias have Spanish articles only, which a multilingual embedding model could compare against English ones |
| Who's On First boundaries | Finer neighborhood shapes to attach Wikipedia and OpenStreetMap data to, and the basis for a map view |
| Extracted tags | Labels such as "gritty," "touristy," or "late-night" pulled from the text would explain a match in words a reader recognizes |
| Adjustable weights | A reader who cares about food and nightlife could weight those sections up and get different matches than a family would |
| Map view | Showing the matched districts side by side on maps of both cities |
