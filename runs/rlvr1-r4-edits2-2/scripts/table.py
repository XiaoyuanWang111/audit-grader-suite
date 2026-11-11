"""Print the per-check table from audit/out/panel_summary.json."""
import json, os, sys
AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(AUDIT, "out", "panel_summary.json"), encoding="utf-8"))
print(f"{'check':45s} {'n':>5s} {'repl%':>6s} {'nv%':>5s} {'vi%':>5s} | {'nvDef':>5s} {'fp':>4s} {'ff':>4s} {'nvDec':>5s} | {'viDef':>5s} {'fp':>4s} {'ff':>4s} {'viDec':>5s} {'err':>3s}")
for k, c in s["checks"].items():
    g = lambda x: c.get(x, 0)
    vi = g("verifyit_pass_n") / g("verifyit_graded") * 100 if g("verifyit_graded") else float("nan")
    print(f"{k:45s} {g('n'):5d} {g('repl_pass')/g('n')*100:6.1f} {g('nvidia_pass')/g('n')*100:5.1f} {vi:5.1f} | {g('nvidia_defect'):5d} {g('nvidia_defect_false_pass'):4d} {g('nvidia_defect_false_fail'):4d} {g('nvidia_decision'):5d} | {g('verifyit_defect'):5d} {g('verifyit_defect_false_pass'):4d} {g('verifyit_defect_false_fail'):4d} {g('verifyit_decision'):5d} {g('nvidia_error'):3d}")
