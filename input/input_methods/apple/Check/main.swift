// The check of the shared core (tests/test_apple.py): one request per stdin
// line, "mode<TAB>input", one result per stdout line.
//   render          what was typed, in the script
//   joined          the same, long consonants joined
//   stream          the keystroke trace: buffer, committed, pending joined by
//                   U+001E, steps joined by U+001F
//   out:<output>    what was typed, in an output
//   convert:<src>|<target>   a text converted
//   keys            the keys that type a Diafon text; rekey: typed, written, keyed and written again
//   detect          the source detected
//   info            the alphabet's version, the typing, the stages
import Foundation

let FIELD = "\u{1E}", STEP = "\u{1F}"
let d = Diafon.shared
if let f = d.failure { FileHandle.standardError.write("Diafon: \(f)\n".data(using: .utf8)!); exit(2) }
var out = ""
while let line = readLine() {
    guard let tab = line.firstIndex(of: "\t") else { out += "!MODE\n"; continue }
    let mode = String(line[..<tab]), input = String(line[line.index(after: tab)...])
    var result: String
    if mode == "render" { result = d.render(input) }
    else if mode == "joined" { result = d.render(input, join: true) }
    else if mode == "stream" {
        var buf = "", steps: [String] = []
        for ch in input.unicodeScalars {
            buf += String(ch)
            let (c, p) = d.stream(buf)
            steps.append(buf + FIELD + c + FIELD + p)
            buf = p
        }
        result = steps.joined(separator: STEP)
    }
    else if mode.hasPrefix("out:") { result = d.render(input, output: String(mode.dropFirst(4))) }
    else if mode.hasPrefix("convert:") {
        let parts = mode.dropFirst(8).split(separator: "|").map(String.init)
        result = parts.count == 2 ? d.convert(input, parts[0], parts[1]) : "!MODE"
    }
    else if mode == "keys" { result = d.keys(for: input) }
    else if mode == "rekey" { result = d.render(d.keys(for: d.render(input))) }      // typed -> script -> keys -> script
    else if mode == "detect" { result = d.detect(input).first?.0 ?? "" }
    else if mode == "info" { result = "\(d.version) \(d.typing) " + d.stageOrder.joined(separator: ",") }
    else { result = "!MODE" }
    out += result.replacingOccurrences(of: "\n", with: "\u{1D}") + "\n"
}
print(out, terminator: "")
