"""Post-label analysis: regrade every grader-replacement disagreement of the panel with all decision readings.

The panel grading (grade_panel.py) computed only a subset of decision switches per check. This
script takes every panel verdict where the grader (strict) and the replacement (proposed readings)
disagree, extraction failures excluded, and grades the stored response again with the replacement
under (1) every single reading of every decision that the check's contract lists, plus D-vacuous
(rule G6 applies to every check), and (2) every pair of such readings from two different
decisions. A disagreement is classed:
  single   one switched reading gives the grader's verdict (a decision, not a finding);
  pair     two switched readings together give it (a decision combination, step 3);
  none     no single reading or pair gives it: a checker finding or a replacement error.
Output: audit/work/regrade_disagreements.jsonl (one line per disagreement) and a printed table of
"none" counts per check and direction, which bounds the checker findings more tightly than
audit/scripts/finding_bounds.py.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/regrade_disagreements.py
"""
import collections
import itertools
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (os.path.join(W, "audit", "lib"), os.path.join(W, "audit", "replacement")):
    sys.path.insert(0, p)
import ifb  # noqa: E402
import ifbench_contract as rep  # noqa: E402

LETTERS = {
    "D-vacuous": "B", "D-word": "BC", "D-word-numbers": "B", "D-sentence": "BC", "D-paragraph": "BC",
    "D-match": "BC", "D-keyword-count": "B", "D-conj": "B", "D-number": "BC", "D-names-case": "B",
    "D-pronoun": "BC", "D-punct-set": "B", "D-unique": "BC", "D-between": "B", "D-japanese": "BC",
    "D-emoji-position": "B", "D-indent": "BC", "D-list": "BCD", "D-options": "BCD", "D-template": "BC",
    "D-paren": "BC", "D-subbullet": "B", "D-section": "B", "D-title": "BC", "D-overlap": "BCDE",
    "D-balance": "BC", "D-char-count": "BC", "D-different-words": "B", "D-stopwords": "B",
    "D-repeat-change": "BC", "D-repeat-simple": "B", "D-span": "BC", "D-alliteration": "BC",
    "D-alphabet-start": "B", "D-y": "B", "D-syllables": "B", "D-palindrome": "BC", "D-prime-length": "B",
    "D-repeat-count": "B", "D-verb": "B", "D-vowel": "BCD", "D-custom-facts": "BC",
    "D-custom-extra-text": "BC", "D-csv": "BCDE", "D-char-reverse": "B", "D-mcq": "BC", "D-trailing-ws": "B",
}


def contract_decisions():
    """Decision ids listed in each check's "Decisions:" line of audit/CONTRACT.md, plus D-vacuous."""
    text = open(os.path.join(W, "audit", "CONTRACT.md"), encoding="utf-8").read()
    out = {}
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        iid = block.split()[0]
        if ":" not in iid:
            continue
        m = re.search(r"Decisions:(.*?)(?:\n\n|\n###|$)", block, flags=re.S)
        ds = re.findall(r"D-[a-z-]+[a-z]", m.group(1)) if m else []
        out[iid] = sorted(set(ds) | {"D-vacuous"})
    return out


def main():
    ifb.verify_pins()
    decs = contract_decisions()
    rows = {r["key"]: r for r in ifb.load_rows()}
    todo = collections.defaultdict(list)
    with open(os.path.join(W, "audit", "work", "panel_verdicts.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            v = json.loads(line)
            if not v["extraction_failure"] and v["g"] != v["p"]:
                todo[(v["cfg"], v["run"])].append(v)
    out, n = [], 0
    for (cfg, run), vs in sorted(todo.items()):
        with open(os.path.join(W, "case", "panel", cfg, run + ".jsonl"), encoding="utf-8") as fh:
            recs = {str(r["key"]): r for r in map(json.loads, fh)}
        for v in vs:
            row = rows[v["key"]]
            kw = row["kwargs"][v["j"]]
            resp = recs[v["key"]]["response"]
            singles = [(d, L) for d in decs[v["iid"]] for L in LETTERS[d]]
            hit1 = [f"{d}:{L}" for d, L in singles if rep.check(v["iid"], kw, row["prompt"], resp, {d: L}) == v["g"]]
            hit2 = []
            if not hit1:
                for (d1, l1), (d2, l2) in itertools.combinations(singles, 2):
                    if d1 != d2 and rep.check(v["iid"], kw, row["prompt"], resp, {d1: l1, d2: l2}) == v["g"]:
                        hit2.append(f"{d1}:{l1}+{d2}:{l2}")
            cls = "single" if hit1 else ("pair" if hit2 else "none")
            out.append({"cfg": cfg, "run": run, "key": v["key"], "j": v["j"], "iid": v["iid"], "heldout": v["heldout"],
                        "g": v["g"], "p": v["p"], "class": cls, "single": hit1, "pair": hit2[:5]})
            n += 1
    with open(os.path.join(W, "audit", "work", "regrade_disagreements.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for o in out:
            fh.write(json.dumps(o) + "\n")
    tot = collections.Counter(o["class"] for o in out)
    print(f"{n} disagreements: single switch {tot['single']}, pair of switches {tot['pair']}, none {tot['none']}")
    per = collections.defaultdict(collections.Counter)
    for o in out:
        per[o["iid"]][o["class"]] += 1
        if o["class"] == "none":
            per[o["iid"]]["none_g1p0" if o["g"] else "none_g0p1"] += 1
    print(f"{'check':34s} {'single':>6s} {'pair':>5s} {'none':>5s} {'none g1p0':>9s} {'none g0p1':>9s}")
    for k, c in sorted(per.items(), key=lambda kv: -kv[1]["none"]):
        print(f"{k:34s} {c['single']:6d} {c['pair']:5d} {c['none']:5d} {c['none_g1p0']:9d} {c['none_g0p1']:9d}")


if __name__ == "__main__":
    main()
