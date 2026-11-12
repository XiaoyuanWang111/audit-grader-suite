"""Build audit/fixtures.jsonl and audit/tests/expectations.json from every fixture source.

Sources: fixtures_hand.HAND and PIPELINE (hand-written), and the generated sets written by
stress_tests.py to audit/fixtures_generated/*.jsonl (property, metamorphic, content-free, fuzz).
For each fixture: the label (from the contract), each grader's verdict, and for a wrong verdict
its class: a finding, or the decision entries whose non-proposed readings give that verdict.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_lib as F  # noqa: E402
from fixtures_hand import HAND, PIPELINE  # noqa: E402

AUDIT = os.path.dirname(os.path.abspath(__file__))


def records():
    for iid, kw, resp, label, note in HAND:
        yield {"kind": "hand", "instruction_id": iid, "kwargs": kw, "response": resp, "label": label,
               "note": note}
    for iid, kw, raw, thinking, label, note in PIPELINE:
        yield {"kind": "pipeline", "instruction_id": iid, "kwargs": kw, "response": raw, "label": label,
               "thinking": thinking, "note": note}
    for path in sorted(glob.glob(os.path.join(AUDIT, "fixtures_generated", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)


def main():
    out, expect = [], {}
    seen = set()
    counts = {}
    for rec in records():
        thinking = rec.get("thinking")
        fid = F.fixture_id(rec["instruction_id"], rec["kwargs"], rec["response"], thinking)
        if fid in seen:
            continue
        seen.add(fid)
        rec = {"id": fid, **rec}
        res = F.grade_all(rec["instruction_id"], rec["kwargs"], rec["response"], thinking)
        label = F.label_bool(rec["label"])
        e = {"label": rec["label"], "R": res["R"], "A": res["A"], "B": res["B"],
             "A_error": res["A_error"], "kind": rec["kind"]}
        for g in ("A", "B"):
            v = res[g]
            if v is None or v == label:
                e[g + "_class"] = None if v is None else "ok"
            else:
                e[g + "_class"] = F.classify(rec["instruction_id"], rec["kwargs"], rec["response"], thinking, v)
            key = (rec["kind"], g, (e[g + "_class"] or "n/a").split(":")[0])
            counts[key] = counts.get(key, 0) + 1
        e["R_class"] = "ok" if res["R"] == label else "replacement-wrong"
        counts[(rec["kind"], "R", e["R_class"])] = counts.get((rec["kind"], "R", e["R_class"]), 0) + 1
        out.append(rec)
        expect[fid] = e
    with open(os.path.join(AUDIT, "fixtures.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.makedirs(os.path.join(AUDIT, "tests"), exist_ok=True)
    with open(os.path.join(AUDIT, "tests", "expectations.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(expect, f, ensure_ascii=False, indent=0, sort_keys=True)
    print("fixtures", len(out))
    for k in sorted(counts):
        print(k, counts[k])


if __name__ == "__main__":
    main()
