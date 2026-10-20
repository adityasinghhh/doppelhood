import Foundation
import SwiftUI
import Observation

struct City: Decodable, Hashable, Identifiable {
    let slug: String
    let name: String
    let state: String

    var id: String { slug }
    var label: String { "\(name), \(state)" }
    /// A landmark drawn for the app, in the asset catalog as city-<slug>.
    var icon: Image {
        UIImage(named: "city-\(slug)") != nil ? Image("city-\(slug)") : Image(systemName: "building.2")
    }
}

struct Neighborhood: Decodable, Hashable, Identifiable {
    let id: String
    let city: String
    let name: String
    let summary: String
    let sourceURL: URL
    let lat: Double
    let lon: Double
    /// The street feature it has most of relative to its city, or "residential".
    let standout: String?

    enum CodingKeys: String, CodingKey {
        case id, city, name, summary, lat, lon, standout
        case sourceURL = "source_url"
    }
}

struct Match: Decodable, Hashable {
    let id: String
    let score: Int
    let parts: [String: Int]
}

/// The pipeline's output, web/data/matches.json, bundled with the app.
struct Dataset: Decodable {
    let cities: [City]
    let neighborhoods: [Neighborhood]
    let matches: [String: [String: [Match]]]
}

@Observable
final class Store {
    let cities: [City]
    private let neighborhoods: [Neighborhood]
    private let byID: [String: Neighborhood]
    private let matches: [String: [String: [Match]]]

    init() {
        let url = Bundle.main.url(forResource: "matches", withExtension: "json")!
        let dataset = try! JSONDecoder().decode(Dataset.self, from: Data(contentsOf: url))
        cities = dataset.cities
        neighborhoods = dataset.neighborhoods
        byID = Dictionary(uniqueKeysWithValues: dataset.neighborhoods.map { ($0.id, $0) })
        matches = dataset.matches
    }

    func city(_ slug: String) -> City? {
        cities.first { $0.slug == slug }
    }

    func neighborhood(_ id: String) -> Neighborhood? {
        byID[id]
    }

    func neighborhoods(in city: String) -> [Neighborhood] {
        neighborhoods
            .filter { $0.city == city }
            .sorted { $0.name.localizedStandardCompare($1.name) == .orderedAscending }
    }

    func matches(for neighborhood: Neighborhood, in city: String) -> [Match] {
        matches[neighborhood.id]?[city] ?? []
    }

    /// The highest-scoring match in any other city.
    func bestMatch(for neighborhood: Neighborhood) -> (match: Match, neighborhood: Neighborhood)? {
        let best = matches[neighborhood.id]?.values.compactMap(\.first).max { $0.score < $1.score }
        guard let best, let hood = byID[best.id] else { return nil }
        return (best, hood)
    }
}

/// A per-signal score's display name and symbol, in the order they are shown.
struct Part {
    let key: String
    let label: String
    let symbol: String
}

let allParts: [Part] = [
    Part(key: "character", label: "Character", symbol: "text.book.closed"),
    Part(key: "street", label: "Street life", symbol: "storefront"),
    Part(key: "eat", label: "Food", symbol: "fork.knife"),
    Part(key: "drink", label: "Nightlife", symbol: "wineglass"),
    Part(key: "see", label: "Sights", symbol: "camera"),
    Part(key: "do", label: "Activities", symbol: "figure.walk"),
    Part(key: "buy", label: "Shopping", symbol: "bag"),
]

extension Match {
    /// The signals this match scores highest on.
    func strongest(_ count: Int) -> [(part: Part, value: Int)] {
        allParts.compactMap { part in self.parts[part.key].map { (part: part, value: $0) } }
            .sorted { $0.value > $1.value }
            .prefix(count)
            .map { $0 }
    }
}

/// What a neighborhood's standout street feature is called and drawn as.
let standouts: [String: (label: String, symbol: String)] = [
    "restaurant": ("Restaurants", "fork.knife"),
    "fast_food": ("Quick bites", "takeoutbag.and.cup.and.straw"),
    "cafe": ("Cafes", "cup.and.saucer"),
    "bar": ("Bars", "wineglass"),
    "nightlife": ("Nightlife", "music.note"),
    "culture": ("Arts and culture", "theatermasks"),
    "attraction": ("Sights", "binoculars"),
    "lodging": ("Hotels", "bed.double"),
    "park": ("Parks", "tree"),
    "fashion": ("Fashion", "tshirt"),
    "grocery": ("Markets", "basket"),
    "other_shop": ("Shops", "bag"),
    "residential": ("Residential", "house"),
]

extension Neighborhood {
    var standoutStyle: (label: String, symbol: String)? {
        standout.flatMap { standouts[$0] }
    }
}
