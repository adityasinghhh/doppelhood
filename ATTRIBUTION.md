# Attribution and Licensing

Doppelhood's code is released under the MIT License in [LICENSE](LICENSE). The data it collects and the datasets it derives carry the licenses of their sources, which are listed here along with the attribution each one requires.

## Sources

| Source | License | Required attribution |
|---|---|---|
| [Wikivoyage](https://www.wikivoyage.org/) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), also available under the [GFDL](https://www.gnu.org/licenses/fdl-1.3.html) | A link to each article reused, whose history page credits its authors, plus a license notice and a statement of any modifications |
| [Wikipedia](https://www.wikipedia.org/) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), also available under the [GFDL](https://www.gnu.org/licenses/fdl-1.3.html) | A link to each article reused, plus a license notice and a statement of any modifications |
| [OpenStreetMap](https://www.openstreetmap.org/) | [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | "© OpenStreetMap contributors" with a link to [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |
| [Wikidata](https://www.wikidata.org/) | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | None required |
| [Who's On First](https://whosonfirst.org/) | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) for Who's On First's own work, with some underlying sources under CC BY | "Data from Who's On First" with a link to its [license](https://github.com/whosonfirst-data/whosonfirst-data-admin-us/blob/master/LICENSE.md), plus the credit each record's source requires |

Matching uses the [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) embedding model, released under the Apache License 2.0. The model is downloaded at run time and is not redistributed in this repository.

The app icon and the city landmark icons in `ios/icon.svg` and `ios/icons/` were drawn for Doppelhood and fall under the MIT License with the code. Neighborhood symbols are Apple's SF Symbols, used in the app under Apple's license for apps on its platforms. The maps in the iOS app come from Apple's MapKit, which displays its own attribution and legal link on every map.

The Wikimedia terms come from the [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), and the OpenStreetMap terms from its [copyright page](https://www.openstreetmap.org/copyright) and [attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines).

## Share-Alike Obligations

Wikivoyage, Wikipedia, and OpenStreetMap all require derived data to be shared under the same license, so Doppelhood keeps the outputs of each source separate:
- **Text-derived data**, including extracted sections, tags, and embeddings built from Wikivoyage and Wikipedia articles, is published under CC BY-SA 4.0, with the source article URL stored on every record.
- **OpenStreetMap-derived data**, including neighborhood names and locations and point-of-interest counts, is published under the ODbL 1.0.
- **Similarity scores** shown in the app are produced works built from both, and every page that shows them carries the attribution for each source above.

Whether embeddings legally count as adaptations of the text they encode is unsettled, so Doppelhood treats them as adaptations and licenses them accordingly.

## Who's On First Source Credits

Who's On First compiles boundaries from many upstream datasets, and some of those require their own credit. The source of each geometry is recorded in its `src:geom` property, and Doppelhood includes the matching credit for every boundary it uses:

| Upstream source | License | Credit |
|---|---|---|
| GeoNames | CC BY | GeoNames |
| Yahoo GeoPlanet | CC BY 3.0 US | "Yahoo! GeoPlanet" |
| Quattroshapes | CC BY | "Includes data from foursquare quattroshapes" |
| Mesoshapes | CC0 or CC BY, per its `meso:source` property | As the record specifies |
| Ordnance Survey | Crown copyright | A statement that the data is Crown copyright and database right |
| Natural Earth, OurAirports | Public domain | None required |
