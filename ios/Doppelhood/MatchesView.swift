import SwiftUI

/// A neighborhood's closest equivalents in one other city.
struct MatchesView: View {
    @Environment(Store.self) private var store
    let neighborhood: Neighborhood
    @AppStorage("toCity") private var toCity = "new-york"

    private var targets: [City] {
        store.cities.filter { $0.slug != neighborhood.city }
    }

    private var target: String {
        targets.contains { $0.slug == toCity } ? toCity : targets.first?.slug ?? ""
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(neighborhood.summary)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Link("Read on Wikipedia", destination: neighborhood.sourceURL)
                    .font(.subheadline)

                Picker("Compare with", selection: $toCity) {
                    ForEach(targets) { Text($0.label).tag($0.slug) }
                }
                .pickerStyle(.menu)
                .padding(.top, 4)

                ForEach(store.matches(for: neighborhood, in: target), id: \.id) { match in
                    if let hood = store.neighborhood(match.id) {
                        NavigationLink(value: hood) {
                            MatchCard(neighborhood: hood, match: match)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding()
        }
        .navigationTitle(neighborhood.name)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if !targets.contains(where: { $0.slug == toCity }), let first = targets.first {
                toCity = first.slug
            }
        }
    }
}

struct MatchCard: View {
    let neighborhood: Neighborhood
    let match: Match

    private let columns = [GridItem(.adaptive(minimum: 130), spacing: 12)]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                Text(neighborhood.name)
                    .font(.headline)
                Spacer()
                Text("\(match.score)")
                    .font(.title2.bold().monospacedDigit())
                    .foregroundStyle(.orange)
            }
            Text(neighborhood.summary)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .lineLimit(3)
            LazyVGrid(columns: columns, alignment: .leading, spacing: 8) {
                ForEach(partLabels, id: \.key) { part in
                    if let value = match.parts[part.key] {
                        VStack(alignment: .leading, spacing: 3) {
                            HStack {
                                Text(part.label)
                                Spacer()
                                Text("\(value)").monospacedDigit()
                            }
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            ProgressView(value: Double(value), total: 100)
                        }
                    }
                }
            }
        }
        .padding()
        .background(.background.secondary, in: .rect(cornerRadius: 14))
    }
}
