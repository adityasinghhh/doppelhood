import SwiftUI

/// Colors taken from the app icon.
extension Color {
    static let coral = Color(red: 1.0, green: 0.42, blue: 0.36)
    static let gold = Color(red: 1.0, green: 0.79, blue: 0.29)
    /// The best-match card, lifted off the page in dark mode.
    static let navy = Color(light: 0x172B47, dark: 0x1F3350)
    /// Screen background: the icon's cream in light mode, its navy in dark mode.
    static let page = Color(light: 0xFBF7F2, dark: 0x0E1A2B)
    /// Rows and unselected chips on the page.
    static let surface = Color(light: 0xFFFFFF, dark: 0x17263B)

    init(light: UInt32, dark: UInt32) {
        func rgb(_ hex: UInt32) -> UIColor {
            UIColor(red: CGFloat(hex >> 16 & 0xFF) / 255, green: CGFloat(hex >> 8 & 0xFF) / 255,
                    blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
        }
        self.init(uiColor: UIColor { $0.userInterfaceStyle == .dark ? rgb(dark) : rgb(light) })
    }
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
                            .background(selected ? AnyShapeStyle(Color.coral) : AnyShapeStyle(Color.surface),
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
