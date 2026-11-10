p = "audit/replacement/ifbench_contract.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


# conjunction heuristic: "so" / "yet" directly followed by a clause subject are conjunctions too
Q = chr(92) + '"'  # the two characters backslash, double quote as they appear in the source
rep('            if prev in (",", ";", ".", "!", "?", "(", "and", "' + Q + '") or i == 0:\n                found.add(w)\n        elif w == "for":',
    '            if prev in (",", ";", ".", "!", "?", "(", "and", "' + Q + '") or i == 0 or nxt in SUBJECTS:\n                found.add(w)\n        elif w == "for":')
rep('            if prev in (",", ";", "and", "but", ".", "!", "?", "(") or i == 0:\n                found.add(w)\n    return len(found) >= n',
    '            if prev in (",", ";", "and", "but", ".", "!", "?", "(") or i == 0 or nxt in SUBJECTS:\n                found.add(w)\n    return len(found) >= n')
# a quoted phrase must contain a word ('"' quoted as a character is not a phrase)
rep("        spans.append((m.start(), m.end()))\n    return spans",
    "        if words(m.group(0)[1:-1]):\n            spans.append((m.start(), m.end()))\n    return spans")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
