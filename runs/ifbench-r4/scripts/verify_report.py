"""Check that audit/AUDIT.md matches what the code prints.

1. Every fixture id the report names exists.
2. In the checker findings table, each "x / y / z" triple (G / R / label) matches the
   fixture's current verdicts, in the order the ids appear in the row.
3. In the decision table, each named fixture exists and the grader's verdict differs from its label.
4. The three example commands print what the report says.
Prints mismatches and a final OK/FAIL line.
"""
import os
import re
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
import ifbaudit as A  # noqa: E402
from fixtures import BY_ID, resolve  # noqa: E402

PY = os.path.join(W, ".venv", "Scripts", "python.exe")
ID_RE = re.compile(r"`((?:count|custom|format|ratio|repeat|sentence|words):[a-z_\-]+-[0-9a-f]{8})`|`(-[0-9a-f]{8})`")
TRIPLE_RE = re.compile(r"(pass|fail|\*\*pass\*\*|\*\*fail\*\*) / (pass|fail|\*\*pass\*\*|\*\*fail\*\*) / (pass|fail)")


def word(v):
    return "pass" if v is True else ("fail" if v is False else str(v))


def main():
    text = open(os.path.join(W, "audit", "AUDIT.md"), encoding="utf-8").read()
    bad = 0
    section = None
    n_trip = n_dec = n_ids = 0
    for line in text.splitlines():
        if line.startswith("### Checkers"):
            section = "checkers"
        elif line.startswith("## Decision entries"):
            section = "decisions"
        elif line.startswith("## Steps"):
            section = None
        if not line.startswith("|"):
            continue
        ids, last = [], None
        for m in ID_RE.finditer(line):
            if m.group(1):
                last = m.group(1)
                ids.append(last)
            elif last:
                ids.append(last.rsplit("-", 1)[0] + m.group(2))
        for i in ids:
            if i not in BY_ID:
                print("MISSING fixture", i)
                bad += 1
        ids = [i for i in ids if i in BY_ID]
        n_ids += len(ids)
        if section == "checkers" and ids:
            triples = TRIPLE_RE.findall(line)
            for k, i in enumerate(ids):
                f = BY_ID[i]
                kw, prompt = resolve(f, A.ROWS)
                try:
                    g = word(A.check_G(f["check"], kw, f["text"], prompt))
                except Exception as e:  # noqa: BLE001
                    g = "EXC"
                r = word(A.check_R(f["check"], kw, f["text"], prompt)) if g != "EXC" else "EXC"
                t = triples[k] if k < len(triples) else (triples[-1] if triples else None)
                if t is None:
                    continue
                t = tuple(x.strip("*") for x in t)
                n_trip += 1
                if (g, r, word(f["label"])) != t:
                    print("TRIPLE MISMATCH", i, "report", t, "actual", (g, r, word(f["label"])))
                    bad += 1
        if section == "decisions":
            for i in ids:
                f = BY_ID[i]
                n_dec += 1
                kw, prompt = resolve(f, A.ROWS)
                if A.check_G(f["check"], kw, f["text"], prompt) == f["label"]:
                    print("DECISION fixture where G agrees with the label:", i)
                    bad += 1
    cmds = [
        (["audit/repro.py", "format:sub-bullets-0dc9fe92"], ["G (grader under audit): True", "contract label: False"]),
        (["audit/repro.py", "--check", "count:word_count_range", "--kw", '{"min_words": 5, "max_words": 5}', "--text",
          "one two three four five\\nsix seven eight"],
         ["G (grader under audit): False", "G loose: True (first passing variant: last line removed)"]),
        (["audit/repro.py", "--check", "format:newline", "--text", "Hello\\r\\n\\r\\nworld."], ["G (grader under audit): False"]),
    ]
    for args, expects in cmds:
        out = subprocess.run([PY, "-I", "-X", "utf8"] + args, cwd=W, capture_output=True, text=True, encoding="utf-8").stdout
        for e in expects:
            if e not in out:
                print("COMMAND OUTPUT MISMATCH", args[:2], "missing:", e)
                bad += 1
    print(f"fixture ids named={n_ids} triples compared={n_trip} decision fixtures checked={n_dec} commands={len(cmds)}")
    print("OK" if bad == 0 else f"FAIL ({bad})")


if __name__ == "__main__":
    main()
