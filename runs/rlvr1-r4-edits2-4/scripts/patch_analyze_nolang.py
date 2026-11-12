from pathlib import Path
p = Path("<W>/audit/scripts/analyze_panel.py")
s = p.read_text(encoding="utf-8")
a = '''        scores["/".join(key)] = {'''
b = '''        LANG = {"language:response_language", "change_case:english_capital", "change_case:english_lowercase"}
        repl_nolang = [float(all((bool(sv) if iid in LANG else rv) for iid, sv, rv in zip(r["ids"], r["skyrl"], r["repl"]))) for r in rs]
        d_nolang = [b_ - a_ for a_, b_ in zip(sky, repl_nolang)]
        scores["/".join(key) + "#nolang"] = {
            "replacement_nolang": sum(repl_nolang) / len(rs), "delta": sum(d_nolang) / len(rs), "ci": boot_ci(d_nolang),
            "false_rewards_nolang": sum(1 for r, rn in zip(rs, repl_nolang) if r["skyrl_reward"] == 1.0 and not rn),
        }
        scores["/".join(key)] = {'''
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
