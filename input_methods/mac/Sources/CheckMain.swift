// Validation entry point (built WITHOUT the IMK app sources): reads tab-separated cases on stdin —
//   <mode batch|stream> \t <target> \t <level 0|1> \t <text>
// level: languages = loose input on/off · universal targets = tone signs on/off (uni only).
// Prints one conversion per line; scripts/check_swift.py drives it against the Python CLI.
import Foundation

@main
struct Check {
    static func main() throws {
        let eng = try Engine.load(url: URL(fileURLWithPath: CommandLine.arguments[1]))
        while let line = readLine() {
            let p = line.components(separatedBy: "\t")
            guard p.count == 4 else { print(""); continue }
            let level = Int(p[2]) ?? 0
            let (mode, target, text) = (p[0], p[1], p[3])
            let isUniversal = eng.maps[target] != nil
            let (loose, tones) = (level >= 1, level >= 1 && isUniversal)
            if mode == "batch" {
                print(isUniversal ? renderUniversal(text, target: target, eng: eng, tones: tones)
                                  : decodeText(text, lang: target, loose: loose, eng: eng))
            } else {
                let s = makeStreamer(target: target, loose: loose, tones: tones, eng: eng)
                print(text.reduce("") { $0 + s.feed($1) } + s.flush())
            }
        }
    }
}
