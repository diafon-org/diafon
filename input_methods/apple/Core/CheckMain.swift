// The vector check, driven by tests/test_swift.py: one request per stdin
// line, "mode<TAB>input", one result per stdout line (the protocol of the
// Kotlin check, so one test shape holds every port).
//   render        strict script form, or "!ERR" when the input is rejected
//   lenient       lenient script form
//   stream        the keystroke trace: buffer, committed, pending joined by
//                 U+001E, steps joined by U+001F
//   stage:<code>  the stage's spelling
//   parse:<src>   the text in that source read back as transport
//   convert:<src>|<target>   converted between sources
//   detect        the source detected
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
            else if mode.hasPrefix("parse:") { result = Stages.parse(input, String(mode.dropFirst(6))) }
            else if mode.hasPrefix("convert:") {
                let parts = mode.dropFirst(8).split(separator: "|").map(String.init)
                result = parts.count == 2 ? Stages.convert(input, parts[0], parts[1]) : "!MODE"
            }
            else if mode == "detect" { result = Stages.detect(input).first?.0 ?? "" }
            else if mode.hasPrefix("lexread:") { result = Lexicon.get(String(mode.dropFirst(8)))?.readWord(input) ?? "!NONE" }
            else if mode.hasPrefix("lexwrite:") {
                switch Lexicon.get(String(mode.dropFirst(9)))?.writeWord(input) {
                case .none: result = "!NONE"
                case .some(.word(let w)): result = w
                case .some(.stem(let a, let b)): result = a + FIELD + b
                }
            }
            else if mode.hasPrefix("loan:") { result = Lexicon.get(String(mode.dropFirst(5)))?.loan(input)?.0 ?? "!NONE" }
            else if mode == "choices" { result = (Lexicon.get("zh")?.choose(input) ?? []).prefix(6).joined(separator: FIELD) }
            else { result = "!MODE" }
            out += result + "\n"
        }
        print(out, terminator: "")
    }
}
