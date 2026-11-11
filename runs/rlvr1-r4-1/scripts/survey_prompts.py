"""Survey the instruction text the model sees, per instruction id, from the data
alone (no grader code). Writes audit/out/instruction_texts.json: for each id,
the count of constraints, the distinct kwargs keys, and up to 12 example
requirement lines with their kwargs.

Also checks that record_json's prompt equals the user message and that the
number of numbered requirement lines equals the number of constraints.
"""
import collections
import json
import pathlib
import re

W = pathlib.Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"


def main():
    rows = [json.loads(l) for l in DATA.open(encoding="utf-8")]
    headers = collections.Counter()
    per_id = collections.defaultdict(lambda: {"n": 0, "keys": collections.Counter(), "examples": []})
    mismatch_prompt = 0
    mismatch_count = 0
    n_sys = 0
    for row in rows:
        msgs = row["prompt"]
        if any(m["role"] == "system" for m in msgs):
            n_sys += 1
        user = [m for m in msgs if m["role"] == "user"]
        text = user[0]["content"]
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        if rec["prompt"] != text:
            mismatch_prompt += 1
        ids = rec["instruction_id_list"]
        kws = rec["kwargs"]
        # find the last block of numbered lines
        lines = text.split("\n")
        # header: the line before the first numbered line of the final block
        idx = [i for i, l in enumerate(lines) if re.match(r"^\d+\. ", l)]
        items = []
        if idx:
            # take trailing consecutive numbered block
            start = idx[-1]
            j = len(idx) - 1
            while j > 0 and idx[j - 1] == idx[j] - 1:
                j -= 1
            start = idx[j]
            items = [re.sub(r"^\d+\. ", "", lines[k]) for k in idx[j:]]
            headers[lines[start - 1] if start > 0 else "<none>"] += 1
        else:
            headers["<no numbered list>"] += 1
        if len(items) != len(ids):
            mismatch_count += 1
            items = [None] * len(ids)
        for iid, kw, item in zip(ids, kws, items):
            d = per_id[iid]
            d["n"] += 1
            kwc = {k: v for k, v in (kw or {}).items() if v is not None}
            d["keys"][tuple(sorted(kwc))] += 1
            if len(d["examples"]) < 12:
                d["examples"].append({"text": item, "kwargs": kwc})
    out = {
        "rows": len(rows),
        "rows_with_system": n_sys,
        "record_prompt_differs": mismatch_prompt,
        "item_count_differs": mismatch_count,
        "headers": headers.most_common(30),
        "ids": {k: {"n": v["n"], "keys": [[list(a), b] for a, b in v["keys"].items()], "examples": v["examples"]}
                for k, v in sorted(per_id.items())},
    }
    (W / "audit" / "out").mkdir(parents=True, exist_ok=True)
    (W / "audit" / "out" / "instruction_texts.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rows", len(rows), "system", n_sys, "record prompt differs", mismatch_prompt, "item count differs", mismatch_count)
    print("ids", len(per_id), "constraints", sum(v["n"] for v in per_id.values()))
    for h, c in headers.most_common(15):
        print(c, repr(h[:100]))


if __name__ == "__main__":
    main()
