p = "<W>/audit/CONTRACTS.md"
s = open(p, encoding="utf-8").read()
a = """letters ignoring case. Fail iff some pair's first letters are consecutive in a-z, in either order
(`a b` and `b a`, D-consecutive-order). Words that start with a digit or a non-Latin letter take
part in no pair."""
b = """letters ignoring case. Fail iff some pair's first letters are consecutive in their alphabet, in
either order (`a b` and `b a`, D-consecutive-order). [v4] The alphabet is the letters' own: Latin
a-z, Cyrillic а-я, Greek α-ω; two letters of different alphabets are not consecutive
(D-consecutive-script [v4]). Words that start with a digit or another character take part in no
pair."""
assert s.count(a) == 1
s = s.replace(a, b)
a = "| D-start-end-single [v2] | **a one-word response passes keywords:start_end** | two words needed | `Hello` |"
b = a + """
| D-two-sep-edge [v4] | **a separator before the first or after the second response is an extra separator (fail)** | separators at the ends are ignored | `A\n******\nB\n******` |
| D-postscript-line [v4] | **the marker begins a line** | the marker may follow other text in the last block | `… main text - P.P.S extra` |
| D-hyphen-dash [v4] | **an en or em dash is not a hyphen** | any dash counts as a hyphen | `First.—Second.` |
| D-consecutive-script [v4] | **consecutive in the letters' own alphabet (Latin, Cyrillic, Greek)** | Latin a-z only | `потом раз` (п, р) |"""
assert s.count(a) == 1
s = s.replace(a, b)
s = s.replace("Version 3 (changes marked [v2] and [v3]; reasons in audit/ISSUE.md, step 3 entries).",
              "Version 4 (changes marked [v2], [v3] and [v4]; reasons in audit/ISSUE.md, step 3 and step 5 entries).")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
