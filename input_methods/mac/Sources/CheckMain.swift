// The vector check, driven by tests/test_swift.py: one request per stdin
// line, "mode<TAB>input", one result per stdout line (the protocol of the
// Kotlin check, so one test shape holds every port).
//   render        strict script form, or "!ERR" when the input is rejected
//   lenient       lenient script form
//   stream        the keystroke trace: buffer, committed, pending joined by
//                 U+001E, steps joined by U+001F
//   stage:<code>  the stage's spelling
import Foundation

let FIELD = "\u{1E}"
let STEP = "\u{1F}"

@main
struct Check {
    static func main() {
        var out = ""
        while let line = readLine() {
            guard let tab = line.firstIndex(of: "\t") else { out += "!MODE\n"; continue }
            let mode = String(line[..<tab])
            let input = String(line[line.index(after: tab)...])
            var result: String
            if mode == "render" { result = (try? Engine.render(input)) ?? "!ERR" }
            else if mode == "lenient" { result = Engine.lenient(input) }
            else if mode == "stream" {
                var buf = ""
                var steps: [String] = []
                for ch in input.unicodeScalars {
                    buf += String(ch)
                    let (c, p) = Engine.stream(buf)
                    steps.append(buf + FIELD + c + FIELD + p)
                    buf = p
                }
                result = steps.joined(separator: STEP)
            }
            else if mode.hasPrefix("stage:"), let st = SpecData.stages[String(mode.dropFirst(6))] { result = Stages.render(input, st) }
            else { result = "!MODE" }
            out += result + "\n"
        }
        print(out, terminator: "")
    }
}
