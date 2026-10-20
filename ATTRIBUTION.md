# Attribution and Licensing

Doppelhood's code is released under the MIT License in [LICENSE](LICENSE). The data it collects and the datasets it derives carry the licenses of their sources, which are listed here along with the attribution each one requires.

## Sources

| Source | License | Required attribution |
|---|---|---|
| [Wikivoyage](https://www.wikivoyage.org/) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), also available under the [GFDL](https://www.gnu.org/licenses/fdl-1.3.html) | A link to each article reused, whose history page credits its authors, plus a license notice and a statement of any modifications |
| [Wikipedia](https://www.wikipedia.org/) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), also available under the [GFDL](https://www.gnu.org/licenses/fdl-1.3.html) | A link to each article reused, plus a license notice and a statement of any modifications |
| [OpenStreetMap](https://www.openstreetmap.org/) | [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | "© OpenStreetMap contributors" with a link to [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |
| [Wikidata](https://www.wikidata.org/) | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | None required |

Matching uses the [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) embedding model, released under the Apache License 2.0. The model is downloaded at run time and is not redistributed in this repository.

The app icon and the city landmark icons in `ios/icon.svg` and `ios/icons/` were drawn for Doppelhood and fall under the MIT License with the code. Neighborhood symbols are Apple's SF Symbols, used in the app under Apple's license for apps on its platforms. The maps in the iOS app come from Apple's MapKit, which displays its own attribution and legal link on every map.

The iOS app's city header photos come from Wikimedia Commons. Each is cropped to 2:1 and resized to 1200 by 600 pixels, and the modified versions in `ios/Doppelhood/Assets.xcassets/photo-*.imageset/` are shared under the same license as the original (the public-domain Denver photo, a U.S. federal work, carries no conditions):

| City | Photo | Photographer | License |
|---|---|---|---|
| San Francisco | [Golden Gate Bridge, 2022](https://commons.wikimedia.org/wiki/File:San_Francisco_(CA,_USA),_Golden_Gate_Bridge_--_2022_--_3015.jpg) | Dietmar Rabich | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| New York | [Midtown Manhattan from Weehawken](https://commons.wikimedia.org/wiki/File:Midtown_Manhattan_from_Weehawken_September_2021_HDR.jpg) | King of Hearts | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Mexico City | [Ángel de la Independencia](https://commons.wikimedia.org/wiki/File:Angel_de_la_independencia170409.jpg) | Carlos Valenzuela | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| New Orleans | [Jackson Square](https://commons.wikimedia.org/wiki/File:Jackson_Square.jpg) | Daniel Schwen | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Boston | [Boston skyline from Longfellow Bridge](https://commons.wikimedia.org/wiki/File:Boston_skyline_from_Longfellow_Bridge_September_2017_panorama_2.jpg) | King of Hearts | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Los Angeles | [Hollywood Sign](https://commons.wikimedia.org/wiki/File:Hollywood_Sign_(Zuschnitt).jpg) | Thomas Wolf | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Chicago | [Chicago skyline at sunrise](https://commons.wikimedia.org/wiki/File:Chicago_Skyline_Sunrise_March_15_2026_-_02.jpg) | NorbertNagel | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Philadelphia | [Philadelphia from South Street Bridge](https://commons.wikimedia.org/wiki/File:Philadelphia_from_South_Street_Bridge_July_2016_panorama_1.jpg) | King of Hearts | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| San Diego | [San Diego skyline](https://commons.wikimedia.org/wiki/File:Wedding_Skyline_San_Diego_2013.jpg) | Tuxyso | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Denver | [Denver skyline](https://commons.wikimedia.org/wiki/File:Denver_Skyline_(15242286069).jpg) | U.S. Fish and Wildlife Service | [Public domain](https://creativecommons.org/publicdomain/mark/1.0/) |

The Wikimedia terms come from the [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), and the OpenStreetMap terms from its [copyright page](https://www.openstreetmap.org/copyright) and [attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines).

## Share-Alike Obligations

Wikivoyage, Wikipedia, and OpenStreetMap all require derived data to be shared under the same license, so Doppelhood keeps the outputs of each source separate:
- **Text-derived data**, including extracted sections, tags, and embeddings built from Wikivoyage and Wikipedia articles, is published under CC BY-SA 4.0, with the source article URL stored on every record.
- **OpenStreetMap-derived data**, including neighborhood names and locations and point-of-interest counts, is published under the ODbL 1.0.
- **Similarity scores** shown in the app are produced works built from both, and every page that shows them carries the attribution for each source above.

Whether embeddings legally count as adaptations of the text they encode is unsettled, so Doppelhood treats them as adaptations and licenses them accordingly.
