import SwiftUI

@main
struct DoppelhoodApp: App {
    @State private var store = Store()

    var body: some Scene {
        WindowGroup {
            NeighborhoodListView()
                .environment(store)
                .tint(.orange)
        }
    }
}
