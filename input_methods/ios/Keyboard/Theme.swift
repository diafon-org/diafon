// The keyboard's colours and type: the site's palette, light and dark (the
// dark one is the icon's), the operators tinted so the eye learns the split,
// and Diafon Serif for anything that shows a spelling.
import CoreText
import UIKit

enum Theme {
    private static func dyn(_ light: UInt32, _ dark: UInt32) -> UIColor {
        UIColor { $0.userInterfaceStyle == .dark ? rgb(dark) : rgb(light) }
    }
    static func rgb(_ v: UInt32) -> UIColor {
        UIColor(red: CGFloat(v >> 16 & 0xFF) / 255, green: CGFloat(v >> 8 & 0xFF) / 255, blue: CGFloat(v & 0xFF) / 255, alpha: 1)
    }

    static let board = dyn(0xD9DCE1, 0x1B1E25)
    static let key = dyn(0xFFFFFF, 0x3A3F4A)
    static let functional = dyn(0xB4B9C2, 0x2A2E37)
    static let pressed = dyn(0x9CA3AE, 0x5B6472)
    static let shadow = dyn(0x8A909A, 0x0B0D11)
    static let ink = dyn(0x1A1D24, 0xF3F4F6)
    static let muted = dyn(0x5B6472, 0xA3AAB5)
    static let accent = dyn(0x0E7C86, 0x3FC9D1)
    static let onAccent = dyn(0xFFFFFF, 0x1B1E25)
    static let warn = dyn(0xB03F3F, 0xE07A7A)

    /// The operator letters, in the Android keyboard's and the site's colours.
    static let operators: [Character: UIColor] = [
        "c": dyn(0xB06F14, 0xE0A04A), "j": dyn(0x2F6FB0, 0x6FA8E0), "q": dyn(0x7A4FB0, 0xAE8BE0),
        "x": dyn(0x2F8F66, 0x5FC79A), "y": dyn(0xB03F7A, 0xE07AB0), "w": dyn(0x5B6472, 0xA3AAB5)]

    private static var registered = false
    /// Diafon Serif from the bundle, registered once; the system serif if it is missing.
    static func serif(_ size: CGFloat) -> UIFont {
        if !registered {
            registered = true
            if let url = Bundle.main.url(forResource: "DiafonSerif-Regular", withExtension: "ttf") {
                CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
            }
        }
        if let f = UIFont(name: "DiafonSerif-Regular", size: size) { return f }
        let d = UIFont.systemFont(ofSize: size).fontDescriptor.withDesign(.serif)
        return d.map { UIFont(descriptor: $0, size: size) } ?? .systemFont(ofSize: size)
    }
}
