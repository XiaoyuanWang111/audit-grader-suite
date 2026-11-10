p = "audit/replacement/ifbench_contract.py"
s = open(p, encoding="utf-8").read()
old = """        inline_ok = len([p for p in parts if p.strip()]) >= 2 and t.count(sep) >= 1 and \\
            any(parts[i].strip() and parts[i + 1].strip() for i in range(len(parts) - 1))"""
new = """        # inline form: at least two separators with text between them (a lone separator in prose is not a list)
        inline_ok = t.count(sep) >= 2 and len([p for p in inner if p.strip()]) >= 1 and \\
            len([p for p in parts if p.strip()]) >= 3"""
assert s.count(old) == 1, "anchor"
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
