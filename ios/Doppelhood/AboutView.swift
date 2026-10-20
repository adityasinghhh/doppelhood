import SwiftUI

struct AboutView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section("How Matching Works") {
                    Text("Scores are percentiles. A score of 90 means the pairing is more similar than 90% of all pairings between neighborhoods in different cities.")
                    Text("Each neighborhood is compared on its Wikipedia article (character), the Wikivoyage listings located in it (food, nightlife, sights, activities, shopping), and the restaurants, bars, shops, and parks mapped in OpenStreetMap within 500 meters (street life). Every signal is measured against the rest of its own city first, so a match means two neighborhoods play the same role in their cities.")
                }
                .listRowBackground(Color.surface)
                Section("Sources and Licenses") {
                    Link("Wikipedia and Wikivoyage text, CC BY-SA 4.0",
                         destination: URL(string: "https://creativecommons.org/licenses/by-sa/4.0/")!)
                    Link("Map data © OpenStreetMap contributors, ODbL",
                         destination: URL(string: "https://www.openstreetmap.org/copyright")!)
                    Link("Neighborhood lists and locations from Wikidata, CC0",
                         destination: URL(string: "https://www.wikidata.org/")!)
                    Text("Each neighborhood links to its Wikipedia article, whose history page credits its authors.")
                        .foregroundStyle(.secondary)
                }
                .listRowBackground(Color.surface)
                Section("City Photos") {
                    ForEach(photoCredits, id: \.city) { credit in
                        Link(destination: credit.page) {
                            Text("\(credit.author), \(credit.license)")
                        }
                    }
                    Text("Photos from Wikimedia Commons, cropped and resized for the app. Each links to its original page and license.")
                        .foregroundStyle(.secondary)
                }
                .listRowBackground(Color.surface)
                Section {
                    Link("Source code on GitHub",
                         destination: URL(string: "https://github.com/adityasinghhh/doppelhood")!)
                }
                .listRowBackground(Color.surface)
            }
            .scrollContentBackground(.hidden)
            .background(Color.page)
            .navigationTitle("About")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
