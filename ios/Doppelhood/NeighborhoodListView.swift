import SwiftUI

/// Two cities side by side, with each neighborhood in the first beside its best match in the second.
struct NeighborhoodListView: View {
    @Environment(Store.self) private var store
    @AppStorage("fromCity") private var fromCity = "san-francisco"
    @AppStorage("toCity") private var toCity = "new-york"
    @State private var query = ""
    @State private var showingAbout = false
    @State private var path: [Neighborhood] = []

    private var pairs: [(neighborhood: Neighborhood, match: Match, other: Neighborhood)] {
        store.neighborhoods(in: fromCity)
            .filter { query.isEmpty || $0.name.localizedCaseInsensitiveContains(query) }
            .compactMap { hood in
                guard let best = store.matches(for: hood, in: toCity).first,
                      let other = store.neighborhood(best.id) else { return nil }
                return (hood, best, other)
            }
    }

    var body: some View {
        NavigationStack(path: $path) {
            List {
                Section {
                    ForEach(pairs, id: \.neighborhood.id) { pair in
                        NavigationLink(value: pair.neighborhood) {
                            PairRow(neighborhood: pair.neighborhood, match: pair.match, other: pair.other)
                        }
                        .listRowBackground(Color.page)
                    }
                } header: {
                    HStack(spacing: 8) {
                        CityCard(caption: "You know", selection: $fromCity, other: $toCity)
                        Button("Swap cities", systemImage: "arrow.left.arrow.right") {
                            withAnimation(.snappy) { (fromCity, toCity) = (toCity, fromCity) }
                        }
                        .labelStyle(.iconOnly)
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(.white)
                        .frame(width: 36, height: 36)
                        .background(Color.coral, in: .circle)
                        CityCard(caption: "Visiting", selection: $toCity, other: $fromCity)
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 8)
                    .textCase(nil)
                    .listRowInsets(EdgeInsets())
                    .background(Color.page)
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(Color.page)
            .animation(.snappy, value: fromCity + toCity)
            .searchable(text: $query, prompt: "Search neighborhoods")
            .navigationTitle("Doppelhood")
            .navigationDestination(for: Neighborhood.self) { MatchesView(neighborhood: $0) }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("About", systemImage: "info.circle") { showingAbout = true }
                }
            }
            .sheet(isPresented: $showingAbout) { AboutView() }
        }
        #if DEBUG
        // Screenshots: SIMCTL_CHILD_DOPPELHOOD_OPEN=san-francisco:Mission xcrun simctl launch ...
        .onAppear {
            if let id = ProcessInfo.processInfo.environment["DOPPELHOOD_OPEN"], let hood = store.neighborhood(id) {
                path = [hood]
            }
        }
        #endif
    }
}

/// One city's photo and name, opening a menu of cities. Choosing the city on the
/// other side swaps the two, so the cards never show the same city.
struct CityCard: View {
    @Environment(Store.self) private var store
    let caption: String
    @Binding var selection: String
    @Binding var other: String

    var body: some View {
        Menu {
            ForEach(store.cities) { city in
                Button {
                    withAnimation(.snappy) {
                        if city.slug == other { other = selection }
                        selection = city.slug
                    }
                } label: {
                    Label { Text(city.name) } icon: { city.icon }
                }
            }
        } label: {
            if let city = store.city(selection) {
                CityHero(city: city, caption: caption, height: 120)
            }
        }
    }
}

/// A neighborhood beside its best match in the other city.
struct PairRow: View {
    let neighborhood: Neighborhood
    let match: Match
    let other: Neighborhood

    var body: some View {
        HStack(spacing: 10) {
            side(neighborhood)
            Image(systemName: "arrow.right")
                .font(.caption.weight(.bold))
                .foregroundStyle(.tertiary)
            side(other)
            ScoreRing(score: match.score, size: 36, lineWidth: 4)
        }
        .padding(.vertical, 4)
    }

    private func side(_ hood: Neighborhood) -> some View {
        HStack(spacing: 8) {
            StandoutBadge(neighborhood: hood, size: 28)
            Text(hood.name)
                .font(.subheadline.weight(.semibold))
                .lineLimit(2)
                .minimumScaleFactor(0.85)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
