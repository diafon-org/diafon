// Validation entry point (built WITHOUT the IMK app sources): reads tab-separated cases on stdin —
//   <mode batch|stream> \t <target> \t <loose 0|1> \t <text>
// and prints one conversion per line. scripts/check_swift.py drives it against the Python CLI.
import Foundation

@main
struct Check {
    static func main() throws {
        let eng = try Engine.load(url: URL(fileURLWithPath: CommandLine.arguments[1]))
        while let line = readLine() {
            let p = line.components(separatedBy: "\t")
            guard p.count == 4 else { print(""); continue }
            let level = Int(p[2]) ?? 0                    // 0 strict · 1 loose input · 2 +dictionary
            let (mode, target, text) = (p[0], p[1], p[3])
            let (loose, dict) = (level >= 1, level == 2)
            let isUniversal = eng.maps[target] != nil
            if mode == "batch" {
                print(isUniversal ? renderUniversal(text, target: target, eng: eng)
                                  : decodeText(text, lang: target, loose: loose, endict: dict, eng: eng))
            } else {
                let s = makeStreamer(target: target, loose: loose, dict: dict, eng: eng)
                print(text.reduce("") { $0 + s.feed($1) } + s.flush())
            }
        }
    }
}
