import MapKit
import SwiftUI

/// A neighborhood's closest equivalents in one other city.
struct MatchesView: View {
    @Environment(Store.self) private var store
    let neighborhood: Neighborhood
    @AppStorage("toCity") private var toCity = "new-york"
    @State private var expanded = false

    private var targets: [City] {
        store.cities.filter { $0.slug != neighborhood.city }
    }

    private var target: String {
        targets.contains { $0.slug == toCity } ? toCity : targets.first?.slug ?? ""
    }

    private var matches: [(match: Match, neighborhood: Neighborhood)] {
        store.matches(for: neighborhood, in: target).compactMap { match in
            store.neighborhood(match.id).map { (match, $0) }
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                VStack(alignment: .leading, spacing: 12) {
                    Text("Feels like")
                        .font(.title2.bold())
                        .padding(.horizontal)
                    CityChips(cities: targets, selection: $toCity)
                }
                VStack(spacing: 12) {
                    if let top = matches.first {
                        NavigationLink(value: top.neighborhood) {
                            TopMatchCard(neighborhood: top.neighborhood, match: top.match)
                        }
                        .buttonStyle(.plain)
                    }
                    ForEach(matches.dropFirst(), id: \.match.id) { item in
                        MatchRow(neighborhood: item.neighborhood, match: item.match)
                    }
                }
                .padding(.horizontal)
                .animation(.snappy, value: target)
            }
            .padding(.bottom, 24)
        }
        .background(Color.page)
        .navigationTitle(neighborhood.name)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if !targets.contains(where: { $0.slug == toCity }), let first = targets.first {
                toCity = first.slug
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 12) {
            MapPreview(neighborhood: neighborhood, height: 180)
            VStack(alignment: .leading, spacing: 4) {
                Text(neighborhood.name)
                    .font(.largeTitle.bold())
                Text(store.city(neighborhood.city)?.label ?? "")
                    .font(.headline)
                    .foregroundStyle(.secondary)
            }
            if let style = neighborhood.standoutStyle {
                Label(style.label == "Residential" ? "Mostly residential" : "Known for \(style.label.lowercased())",
                      systemImage: style.symbol)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.coral)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.coral.opacity(0.14), in: .capsule)
            }
            Text(neighborhood.summary)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .lineLimit(expanded ? nil : 2)
            HStack(spacing: 16) {
                Button(expanded ? "Less" : "More") {
                    withAnimation(.snappy) { expanded.toggle() }
                }
                Link(destination: neighborhood.sourceURL) {
                    Label("Wikipedia", systemImage: "arrow.up.right")
                }
            }
            .font(.subheadline.weight(.semibold))
        }
        .padding(.horizontal)
    }
}

/// A non-interactive map centered on a neighborhood's label.
struct MapPreview: View {
    let neighborhood: Neighborhood
    var height: CGFloat

    var body: some View {
        let center = CLLocationCoordinate2D(latitude: neighborhood.lat, longitude: neighborhood.lon)
        Map(initialPosition: .region(MKCoordinateRegion(center: center, latitudinalMeters: 1800,
                                                        longitudinalMeters: 1800)),
            interactionModes: []) {
            Annotation(neighborhood.name, coordinate: center) {
                Circle()
                    .fill(Color.coral)
                    .stroke(.white, lineWidth: 3)
                    .frame(width: 18, height: 18)
                    .shadow(radius: 3)
            }
            .annotationTitles(.hidden)
        }
        .mapStyle(.standard(pointsOfInterest: .excludingAll))
        .frame(height: height)
        .clipShape(.rect(cornerRadius: 20))
        .id(neighborhood.id)
    }
}

/// The best match, with its map and every signal.
struct TopMatchCard: View {
    @Environment(Store.self) private var store
    let neighborhood: Neighborhood
    let match: Match

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            MapPreview(neighborhood: neighborhood, height: 120)
            HStack(alignment: .center, spacing: 14) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Best match")
                        .font(.caption.weight(.semibold))
                        .textCase(.uppercase)
                        .foregroundStyle(Color.gold)
                    Text(neighborhood.name)
                        .font(.title2.bold())
                        .foregroundStyle(.white)
                }
                Spacer(minLength: 0)
                ScoreRing(score: match.score, size: 64, lineWidth: 7, onDark: true)
            }
            VStack(spacing: 8) {
                ForEach(allParts, id: \.key) { part in
                    PartBar(part: part, value: match.parts[part.key])
                }
            }
        }
        .padding(14)
        .background(Color.navy, in: .rect(cornerRadius: 24))
    }
}

/// One signal's score as a labeled bar, or a note when either neighborhood
/// has no Wikivoyage listings in that section.
struct PartBar: View {
    let part: Part
    let value: Int?
    var onDark = true

    private var muted: AnyShapeStyle {
        onDark ? AnyShapeStyle(.white.opacity(0.4)) : AnyShapeStyle(.tertiary)
    }

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: part.symbol)
                .frame(width: 20)
                .foregroundStyle(value == nil ? muted : AnyShapeStyle(onDark ? Color.gold : Color.coral))
            Text(part.label)
                .frame(width: 84, alignment: .leading)
                .foregroundStyle(value == nil ? muted
                                 : onDark ? AnyShapeStyle(.white.opacity(0.85)) : AnyShapeStyle(.secondary))
            if let value {
                GeometryReader { proxy in
                    ZStack(alignment: .leading) {
                        Capsule().fill(onDark ? AnyShapeStyle(.white.opacity(0.12)) : AnyShapeStyle(.fill.tertiary))
                        Capsule().fill(.brand)
                            .frame(width: proxy.size.width * CGFloat(value) / 100)
                    }
                }
                .frame(height: 6)
                Text("\(value)")
                    .monospacedDigit()
                    .frame(width: 26, alignment: .trailing)
                    .foregroundStyle(onDark ? AnyShapeStyle(.white.opacity(0.85)) : AnyShapeStyle(.secondary))
            } else {
                Text("No listings")
                    .italic()
                    .foregroundStyle(muted)
                Spacer(minLength: 0)
            }
        }
        .font(.caption.weight(.medium))
    }
}

/// A runner-up match with its two strongest signals, expanding to all of them.
struct MatchRow: View {
    let neighborhood: Neighborhood
    let match: Match
    @State private var expanded = false

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 14) {
                ScoreRing(score: match.score)
                StandoutBadge(neighborhood: neighborhood, size: 30)
                VStack(alignment: .leading, spacing: 6) {
                    Text(neighborhood.name)
                        .font(.headline)
                    if !expanded {
                        HStack(spacing: 6) {
                            ForEach(match.strongest(2), id: \.part.key) { PartTag(part: $0.part, value: $0.value) }
                        }
                    }
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.down")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(.tertiary)
                    .rotationEffect(.degrees(expanded ? 180 : 0))
            }
            if expanded {
                VStack(spacing: 8) {
                    ForEach(allParts, id: \.key) { part in
                        PartBar(part: part, value: match.parts[part.key], onDark: false)
                    }
                }
                NavigationLink(value: neighborhood) {
                    Label("Open \(neighborhood.name)", systemImage: "arrow.right")
                        .font(.subheadline.weight(.semibold))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
        .padding(14)
        .background(Color.surface, in: .rect(cornerRadius: 18))
        .contentShape(.rect)
        .onTapGesture { withAnimation(.snappy) { expanded.toggle() } }
    }
}
