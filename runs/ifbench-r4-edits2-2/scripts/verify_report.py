"""Check that every command in AUDIT.md's "Exact inputs and commands" table prints the
grader verdict the table states, that the reference's status matches the findings table,
and that the panel cases cited in the findings table print what the report says.

Run from W: .venv/Scripts/python.exe audit/scripts/verify_report.py
"""
import os
import re
import shlex
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = [os.path.join(W, ".venv", "Scripts", "python.exe")]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", NLTK_DATA="case/deps/nltk_data", PYTHONIOENCODING="utf-8")
FIXED_UPSTREAM = {"F-05", "F-26", "F-28", "F-32", "F-34"}

text = open(os.path.join(W, "audit", "AUDIT.md"), encoding="utf-8").read()
sec = text[text.index("### Exact inputs and commands"):text.index("## 6. Decision entries")]
rows = [l for l in sec.split("\n") if l.startswith("| F-")]


def run(cmd):
    argv = shlex.split(cmd)
    assert argv[0] == "$PY"
    out = subprocess.run(PY + argv[1:], cwd=W, env=ENV, capture_output=True, text=True, encoding="utf-8")
    return out.stdout + out.stderr


def field(out, name, which=0):
    vals = re.findall(r"^\s*" + re.escape(name) + r"\s*:\s*(.+)$", out, re.M)
    return vals[which].strip() if len(vals) > which else None


ok = bad = 0
for r in rows:
    cells = [c.strip() for c in r.strip("|").split("|")]
    fid, cmd, says = cells[0], cells[1].strip("`"), cells[3]
    out = run(cmd)
    g = field(out, "grader strict")
    exp = says.split()[0]
    good = True
    if exp == "EXCEPTION":
        good = g is not None and g.startswith("EXCEPTION")
    elif says.startswith("strict fail, loose pass"):
        good = g == "fail" and field(out, "grader loose") == "pass"
    else:
        good = g == exp
    m = re.search(r"\((pass|fail)", says)
    contract = m.group(1) if m else None
    rep = field(out, "replacement")
    if contract and rep and not rep.startswith(contract):
        good = False
    ref = field(out, "reference strict")
    if fid in FIXED_UPSTREAM:
        if ref != contract:
            good = False
    elif fid not in {"F-35", "F-36"} and ref != g and not (g or "").startswith("EXCEPTION"):
        good = False
    print(("OK  " if good else "BAD ") + f"{fid}: grader={g} reference={ref} replacement={rep}  table says: {says}")
    ok += good
    bad += not good

# panel cases cited in the findings table: grader fail, replacement pass
for cfg, run_, key, check in [("Qwen__Qwen2.5-7B-Instruct", "sample7", "279", "F-13"),
                              ("microsoft__phi-4", "sample9", "128", "F-23"),
                              ("Qwen__Qwen3-14B", "sample0", "241", "F-30"),
                              ("microsoft__phi-4", "sample1", "257", "F-31")]:
    out = run(f"$PY audit/scripts/repro.py --panel {cfg} {run_} {key}")
    g, rep = field(out, "grader strict"), field(out, "replacement")
    good = g == "fail" and rep == "pass"
    print(("OK  " if good else "BAD ") + f"{check} panel {cfg}/{run_}/{key}: grader={g} replacement={rep}")
    ok += good
    bad += not good
print(f"{ok} OK, {bad} BAD")
sys.exit(1 if bad else 0)
