import Foundation
import Observation

struct City: Decodable, Hashable, Identifiable {
    let slug: String
    let name: String
    let state: String

    var id: String { slug }
    var label: String { "\(name), \(state)" }
}

struct Neighborhood: Decodable, Hashable, Identifiable {
    let id: String
    let city: String
    let name: String
    let summary: String
    let sourceURL: URL
    let lat: Double
    let lon: Double

    enum CodingKeys: String, CodingKey {
        case id, city, name, summary, lat, lon
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
}

/// Display names for the per-signal scores, in the order they are shown.
let partLabels: [(key: String, label: String)] = [
    ("character", "Character"),
    ("street", "Street life"),
    ("eat", "Food"),
    ("drink", "Nightlife"),
    ("see", "Sights"),
    ("do", "Activities"),
    ("buy", "Shopping"),
]
