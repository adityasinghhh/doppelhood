import SwiftUI

/// Colors taken from the app icon.
extension Color {
    static let coral = Color(red: 1.0, green: 0.42, blue: 0.36)
    static let gold = Color(red: 1.0, green: 0.79, blue: 0.29)
    static let navy = Color(red: 0.09, green: 0.17, blue: 0.28)
}

extension ShapeStyle where Self == LinearGradient {
    static var brand: LinearGradient {
        LinearGradient(colors: [.coral, .gold], startPoint: .leading, endPoint: .trailing)
    }
}

/// A match score as a ring filled to the percentile.
struct ScoreRing: View {
    let score: Int
    var size: CGFloat = 44
    var lineWidth: CGFloat = 5
    var onDark = false

    var body: some View {
        ZStack {
            Circle().stroke(onDark ? Color.white.opacity(0.15) : Color.secondary.opacity(0.15), lineWidth: lineWidth)
            Circle()
                .trim(from: 0, to: CGFloat(score) / 100)
                .stroke(AngularGradient(colors: [.coral, .gold, .coral], center: .center),
                        style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
            Text("\(score)")
                .font(.system(size: size * 0.36, weight: .bold, design: .rounded).monospacedDigit())
                .foregroundStyle(onDark ? .white : .primary)
        }
        .frame(width: size, height: size)
    }
}

/// A horizontally scrolling row of city choices.
struct CityChips: View {
    let cities: [City]
    @Binding var selection: String

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(cities) { city in
                        let selected = city.slug == selection
                        Button {
                            withAnimation(.snappy) { selection = city.slug }
                        } label: {
                            Label {
                                Text(city.name)
                            } icon: {
                                city.icon.resizable().scaledToFit().frame(width: 18, height: 18)
                            }
                            .font(.subheadline.weight(.semibold))
                            .padding(.horizontal, 14)
                            .padding(.vertical, 8)
                            .foregroundStyle(selected ? Color.white : Color.primary)
                            .background(selected ? AnyShapeStyle(Color.coral) : AnyShapeStyle(.fill.tertiary),
                                        in: .capsule)
                        }
                        .buttonStyle(.plain)
                        .id(city.slug)
                    }
                }
                .padding(.horizontal)
            }
            .onAppear { proxy.scrollTo(selection, anchor: .center) }
        }
    }
}

/// One signal's label and value, shown as a small tag.
struct PartTag: View {
    let part: Part
    let value: Int
    var onDark = false

    var body: some View {
        Label("\(part.label) \(value)", systemImage: part.symbol)
            .font(.caption.weight(.medium))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .foregroundStyle(onDark ? .white : .secondary)
            .background(onDark ? AnyShapeStyle(Color.white.opacity(0.12)) : AnyShapeStyle(.fill.quaternary),
                        in: .capsule)
    }
}

/// A neighborhood's standout feature as a symbol in a tinted circle.
struct StandoutBadge: View {
    let neighborhood: Neighborhood
    var size: CGFloat = 36

    var body: some View {
        Image(systemName: neighborhood.standoutStyle?.symbol ?? "mappin")
            .font(.system(size: size * 0.42, weight: .semibold))
            .foregroundStyle(Color.coral)
            .frame(width: size, height: size)
            .background(Color.coral.opacity(0.14), in: .circle)
    }
}
