p = "scripts/fuzz.py"
s = open(p, encoding="utf-8").read()
start = s.index("    cur = text\n    changed = True")
end = s.index("    r = H.r_check(iid, kw, cur)")
new = '''    cur = text
    for unit in ("token", "token", "char"):
        if unit == "char" and len(cur) > 60:
            break
        parts = cur.split(" ") if unit == "token" else list(cur)
        joiner = " " if unit == "token" else ""
        i = 0
        while i < len(parts):
            cand = joiner.join(parts[:i] + parts[i + 1:])
            ok, vv = unexplained(g, iid, kw, cand)
            if ok and vv == v:
                parts = parts[:i] + parts[i + 1:]
                cur = cand
            else:
                i += 1
'''
s = s[:start] + new + s[end:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
