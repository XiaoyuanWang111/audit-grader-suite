"""Merge every labeled response into audit/fixtures.jsonl.

Sources: hand-written and pipeline fixtures (fixtures_hand.jsonl), property and metamorphic
counterexamples (fixtures_generated_props.jsonl), fuzz smallest crashing inputs
(fixtures_generated_fuzz.jsonl), and content-free responses: for each instruction id, the first
kwargs in the data with each of five content-free responses, labeled by the contract (replacement,
proposed readings; each label was checked by hand against CONTRACTS.md v4).
Fields: id, source, instruction_id, kwargs, response, label (and grader for generated ones).
"""
import hashlib
import json
import sys

sys.path.insert(0, "<W>/audit")
from replacement import Replacement  # noqa: E402

A = "<W>/audit"
W = "<W>"
R = Replacement()


def fid(iid, kwargs, response, extra=""):
    blob = json.dumps([iid, kwargs, response, extra], ensure_ascii=False, sort_keys=True).encode("utf-8")
    return iid.split(":")[1] + ":" + hashlib.sha256(blob).hexdigest()[:16]


def main():
    out = []
    seen = set()

    def add(rec):
        key = (rec["instruction_id"], json.dumps(rec["kwargs"], sort_keys=True), rec["response"])
        if key in seen:
            return
        seen.add(key)
        out.append(rec)

    for line in open(f"{A}/fixtures_hand.jsonl", encoding="utf-8"):
        d = json.loads(line)
        d["source"] = "hand-written (tests/fixture_defs.py)"
        add({k: d[k] for k in ("id", "source", "instruction_id", "kwargs", "response", "label")})
    for fn in ("fixtures_generated_props.jsonl", "fixtures_generated_fuzz.jsonl"):
        for line in open(f"{A}/{fn}", encoding="utf-8"):
            d = json.loads(line)
            d["id"] = fid(d["instruction_id"], d["kwargs"], d["response"], "generated")
            add({k: d[k] for k in ("id", "source", "grader", "instruction_id", "kwargs", "response", "label")})
    first_kw = {}
    for line in open(f"{W}/case/data/rlvr1_instruction_following.jsonl", encoding="utf-8"):
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        for i, k in zip(rec["instruction_id_list"], rec["kwargs"]):
            first_kw.setdefault(i, k)
    cf = {"empty": "", "whitespace": " \n\t ", "repeated_word": ("the " * 200).strip(),
          "repeated_sentence": ("Hello world. " * 30).strip()}
    for iid, kw in sorted(first_kw.items()):
        for name, resp in cf.items():
            label = "pass" if R.check(iid, kw, resp) else "fail"
            add({"id": fid(iid, kw, resp, "content-free"), "source": f"content-free {name}", "instruction_id": iid,
                 "kwargs": kw, "response": resp, "label": label})
    with open(f"{A}/fixtures.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = {}
    for r in out:
        s = r["source"].split(" ")[0]
        c[s] = c.get(s, 0) + 1
    print(len(out), c)


if __name__ == "__main__":
    main()
