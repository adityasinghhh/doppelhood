import SwiftUI

/// Pick a city you know, then a neighborhood in it.
struct NeighborhoodListView: View {
    @Environment(Store.self) private var store
    @AppStorage("fromCity") private var fromCity = "san-francisco"
    @State private var query = ""
    @State private var showingAbout = false

    private var neighborhoods: [Neighborhood] {
        let all = store.neighborhoods(in: fromCity)
        guard !query.isEmpty else { return all }
        return all.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }

    var body: some View {
        NavigationStack {
            List(neighborhoods) { hood in
                NavigationLink(value: hood) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(hood.name).font(.body.weight(.medium))
                        Text(hood.summary)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                    .padding(.vertical, 2)
                }
            }
            .listStyle(.plain)
            .searchable(text: $query, prompt: "Search neighborhoods")
            .navigationTitle(store.city(fromCity)?.name ?? "Doppelhood")
            .navigationDestination(for: Neighborhood.self) { MatchesView(neighborhood: $0) }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Menu {
                        Picker("City you know", selection: $fromCity) {
                            ForEach(store.cities) { Text($0.label).tag($0.slug) }
                        }
                    } label: {
                        Label("Change city", systemImage: "building.2")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("About", systemImage: "info.circle") { showingAbout = true }
                }
            }
            .sheet(isPresented: $showingAbout) { AboutView() }
        }
    }
}
