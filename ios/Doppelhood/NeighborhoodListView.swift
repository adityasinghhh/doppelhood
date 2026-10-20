import SwiftUI

/// Pick a city you know, then a neighborhood in it.
struct NeighborhoodListView: View {
    @Environment(Store.self) private var store
    @AppStorage("fromCity") private var fromCity = "san-francisco"
    @State private var query = ""
    @State private var showingAbout = false
    @State private var path: [Neighborhood] = []

    private var neighborhoods: [Neighborhood] {
        let all = store.neighborhoods(in: fromCity)
        guard !query.isEmpty else { return all }
        return all.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }

    var body: some View {
        NavigationStack(path: $path) {
            List {
                if query.isEmpty, let city = store.city(fromCity) {
                    CityHero(city: city)
                        .animation(.easeInOut(duration: 0.35), value: fromCity)
                        .listRowInsets(EdgeInsets(top: 0, leading: 16, bottom: 8, trailing: 16))
                        .listRowSeparator(.hidden)
                        .listRowBackground(Color.page)
                }
                Section {
                    ForEach(neighborhoods) { hood in
                        NavigationLink(value: hood) { NeighborhoodRow(neighborhood: hood) }
                            .listRowBackground(Color.page)
                    }
                } header: {
                    VStack(alignment: .leading, spacing: 10) {
                        CityChips(cities: store.cities, selection: $fromCity)
                    }
                    .textCase(nil)
                    .padding(.bottom, 6)
                    .listRowInsets(EdgeInsets())
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(Color.page)
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

/// A neighborhood's name and the place it most resembles elsewhere.
struct NeighborhoodRow: View {
    @Environment(Store.self) private var store
    let neighborhood: Neighborhood

    var body: some View {
        HStack(spacing: 14) {
            StandoutBadge(neighborhood: neighborhood)
            VStack(alignment: .leading, spacing: 3) {
                Text(neighborhood.name)
                    .font(.headline)
                if let best = store.bestMatch(for: neighborhood) {
                    Text("Like \(best.neighborhood.name), \(store.city(best.neighborhood.city)?.name ?? "")")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }
            Spacer(minLength: 0)
            if let best = store.bestMatch(for: neighborhood) {
                ScoreRing(score: best.match.score, size: 36, lineWidth: 4)
            }
        }
        .padding(.vertical, 4)
    }
}
