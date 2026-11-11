"""Classify each metamorphic wrong verdict as a decision or a finding.

A grader's pass->fail flip under an edit the contract ignores is a decision if
some single alternative reading (or a pair) of the decision table also makes the
replacement fail the edited response; otherwise it is a finding.
Writes audit/work/metamorphic_classified.json.
"""
import itertools
import json

import common
import replacement as R

ALTS = {"D-word": "whitespace", "D-strip-ends": "keep", "D-word-numbers": "include", "D-sentence": "punct",
        "D-paragraph": "line", "D-keyword-match": "inflect", "D-name-case": "insensitive",
        "D-pronoun-set": "broad", "D-verb-context": "can-be", "D-list-intro": "allow",
        "D-whitespace-set": "ascii", "D-quotes-start": "double", "D-options-text": "exact"}

rows = json.load(open(common.W / "audit" / "work" / "metamorphic.json", encoding="utf-8"))
out = []
seen = {}
for r in rows:
    if r["grader"] == "replacement":
        continue
    key = (r["grader"], r["check"], r["edit"])
    f = next(x for x in __import__("tests.fixtures_data", fromlist=["FIX"]).FIX if x["id"] == r["fixture"])
    kw, prompt = common.kwargs_for(f["key"], f["check"], f["kw"])
    expl = None
    for k in (1, 2):
        for combo in itertools.combinations(ALTS.items(), k):
            o = dict(combo)
            try:
                if R.grade(r["check"], kw, prompt, r["original"], o) and not R.grade(r["check"], kw, prompt, r["edited"], o):
                    expl = [c[0] for c in combo]
                    break
            except Exception:  # noqa: BLE001
                pass
        if expl:
            break
    r2 = dict(r, classification=("decision " + "+".join(expl)) if expl else "finding")
    out.append(r2)
    seen.setdefault(key, set()).add(r2["classification"])
(common.W / "audit" / "work" / "metamorphic_classified.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
for key in sorted(seen):
    print(" | ".join(key), "->", "; ".join(sorted(seen[key])))
