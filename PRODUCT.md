# Product

This file tracks what Doppelhood is meant to be, what it does today, where its matches are known to go wrong, and what is planned next.

## Vision

Doppelhood is a free iOS app that tells a traveler which neighborhood in a city they are visiting feels like a neighborhood they already know, from any city to any other.

| Decision | Choice | Consequence |
|---|---|---|
| Audience | Travelers | Matches weight food, nightlife, sights, and atmosphere over rent, schools, or commute |
| Granularity | Neighborhoods | Wikivoyage districts are too coarse, so matching moves to Wikipedia neighborhood articles and OpenStreetMap features on Who's On First boundaries |
| Base city | Any city | San Francisco can no longer serve as the only check on quality, so the validation set needs expected matches from several cities |
| Platform | iOS app | The Python pipeline stays as the data builder, and the app ships its output; the web page remains as a preview |
| Pricing | Free | No payments or accounts to build, and pricing can be revisited once people use it |

## Features

- **Current neighborhoods** come from the place labels OpenStreetMap mappers maintain inside each city's boundary, so former names such as the Barbary Coast and single streets such as Belden Place are left out. Historic-district and housing-development labels are excluded, as are labels for areas larger than a neighborhood, such as New York's boroughs.
- **Character matching** embeds each neighborhood's Wikipedia article without its demographics, government, and transport sections, and with the neighborhood's own name removed so matches cannot hinge on words like "Beach."
- **Visitor listings** assign every geolocated Wikivoyage Eat, Drink, See, Do, and Buy listing to its nearest neighborhood and compare those listings section by section.
- **Street life** compares the mix of restaurants, bars, cafes, shops, venues, and parks within 500 meters of each neighborhood, counted from a local OpenStreetMap extract.
- **Any city as the starting point**, with every signal measured against the rest of its own city first, so a match means two neighborhoods play the same role in their cities.
- **Percentile scores** report each match against every cross-city pairing, overall and per signal.
- **iOS app** in `ios/` lists a city's neighborhoods with search, shows the top five matches in another city with a bar per signal, lets a reader tap through to any match's own matches, and credits every source on its About screen.
- **Web preview** at [adityasinghhh.github.io/doppelhood](https://adityasinghhh.github.io/doppelhood/) shows the same data in a browser.

## Coverage

| City | Neighborhoods | Notes |
|---|---|---|
| San Francisco | 61 | |
| New York | 263 | |
| Other eight cities | 0 | Their OpenStreetMap extracts are not downloaded yet |

A neighborhood is included only when it has an English Wikipedia article within 3 kilometers of its label. OpenStreetMap's Wikidata links are checked against that rule too, since some point at a same-named town or a railroad station. Labels with no qualifying article, such as Cow Hollow, Presidio Heights, and Gramercy, drop out for now.

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
| Remaining cities | Downloading the California, Illinois, Texas, Pennsylvania, and Arizona extracts would add the other eight cities |
| Neighborhoods without articles | Labels such as Cow Hollow could be kept with street life and listings alone, with a summary written from those signals |
| Who's On First boundaries | Finer neighborhood shapes to attach Wikipedia and OpenStreetMap data to, and the basis for a map view |
| Extracted tags | Labels such as "gritty," "touristy," or "late-night" pulled from the text would explain a match in words a reader recognizes |
| Adjustable weights | A reader who cares about food and nightlife could weight those sections up and get different matches than a family would |
| International cities | The Wikivoyage format is the same worldwide, so the pipeline should carry over with little change |
| Map view | Showing the matched districts side by side on maps of both cities |
