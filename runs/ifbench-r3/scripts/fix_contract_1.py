p = "audit/CONTRACT.md"
s = open(p, encoding="utf-8").read()
rep = [
 ('| D-span | repeat:repeat_span | 0-based indices; only the span. | B: 1-based indices. C: the span may be surrounded by other text. | Prompt 287 (indices 10 to 12): A "a certain point.", B "on a certain". |',
  '| D-span | repeat:repeat_span | 0-based indices; only the span. | B: 1-based indices. C: the span may be surrounded by other text. | Prompt 287 (indices 10 to 12): A "on a certain", B "lands on a". |'),
 ('| D-custom-extra-text | custom:multiples, custom:date_format_list, custom:reverse_newline, custom:european_capitals_sort | No text other than the requested items (multiples: no other number; list numbering allowed for reverse_newline). | Lead-in or closing text is allowed. | "Here are the multiples: 14, 21, ...": multiples A pass (no other number), date list A fail. |',
  '| D-custom-extra-text | custom:multiples, custom:date_format_list, custom:reverse_newline, custom:european_capitals_sort | The date, capitals and countries responses contain only the requested items (list numbering allowed for reverse_newline); the multiples response may contain words but no number other than the multiples. | B: lead-in or closing text is allowed in all four. C: the multiples response contains nothing but the multiples. | "Here are the multiples: 14, 21, 28, 35, 42, 49": A pass, C fail. "Dates: 1796-04-12, 1805-12-02": A fail, B pass. |'),
 ('exclamation mark, colon, semicolon, apostrophe, quotation mark, hyphen, dash (en or em dash, or\n"--"), parentheses, square brackets, braces, ellipsis ("..." or "…"), slash; and an interrobang\nwritten "?!", "!?" or "‽".',
  'exclamation mark, colon, semicolon, apostrophe, quotation mark, hyphen, dash (en or em dash, or\n"--"), parentheses, square brackets, braces, ellipsis ("..." or "…"); and an interrobang written\n"?!", "!?" or "‽".'),
 ('| D-punct-set | count:punctuation | The 15 marks listed in the contract plus the interrobang. | B: the core marks only (. , ? ! ; : \' " - ( )) plus the interrobang; brackets, braces, dashes, ellipsis and slash optional. |',
  '| D-punct-set | count:punctuation | The 14 marks listed in the contract plus the interrobang. | B: the core marks only (. , ? ! ; : \' " - ( )) plus the interrobang; brackets, braces, dashes and ellipsis optional. |'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
