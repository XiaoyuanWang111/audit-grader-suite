"""Survey the data: instruction ids, kwargs, and the requirement text each id shows the model.

Reads only case/data. Writes audit/work/survey.json and prints a summary.
"""
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
OUT = W / "audit" / "work"
OUT.mkdir(parents=True, exist_ok=True)

ITEM = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+")


def split_requirements(prompt, n):
    """Return the n items of the last list block of exactly n items, or None."""
    lines = prompt.split(chr(10))
    blocks = []
    cur = []
    for ln in lines:
        if ITEM.match(ln):
            cur.append(ln)
        elif ln.strip() == "":
            if cur:
                blocks.append(cur)
            cur = []
        else:
            if cur:
                cur[-1] = cur[-1] + chr(10) + ln
    if cur:
        blocks.append(cur)
    for b in reversed(blocks):
        if len(b) == n:
            return [ITEM.sub("", it, count=1) for it in b]
    return None


def templ(text, kw):
    t = text
    for k, v in sorted((kw or {}).items(), key=lambda kv: -len(str(kv[1]))):
        if v is None:
            continue
        sv = str(v)
        if sv and sv in t:
            t = t.replace(sv, "{" + k + "}")
    t = re.sub(r"\d+", "#", t)
    return t


def main():
    rows = 0
    ids = collections.Counter()
    per_id_rows = collections.Counter()
    kw_keys = collections.defaultdict(collections.Counter)
    kw_vals = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    templates = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    unmatched = 0
    n_instr = collections.Counter()
    headers = collections.Counter()
    row_hashes = []
    grading_modes = collections.Counter()
    for line in DATA.open(encoding="utf-8"):
        row = json.loads(line)
        rows += 1
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        grading_modes[rec.get("grading_mode")] += 1
        il, kws = rec["instruction_id_list"], rec["kwargs"]
        n_instr[len(il)] += 1
        prompt = row["prompt"][0]["content"]
        assert prompt == rec["prompt"], "prompt mismatch"
        h = hashlib.sha256(json.dumps({"uuid": rec["uuid"], "prompt": prompt, "instruction_id_list": il,
                                       "kwargs": kws}, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        row_hashes.append((rec["uuid"], h))
        reqs = split_requirements(prompt, len(il))
        if reqs is None:
            unmatched += 1
        else:
            # header line
            body = prompt
            first = body.rfind(reqs[0])
            pre = body[:first].rstrip().split("\n")[-1] if first > 0 else ""
            headers[pre.strip()[:80]] += 1
        for k, (iid, kw) in enumerate(zip(il, kws)):
            ids[iid] += 1
            for key, v in (kw or {}).items():
                kw_keys[iid][key + ("=None" if v is None else "")] += 1
                if v is not None:
                    kw_vals[iid][key][json.dumps(v, ensure_ascii=False)[:60]] += 1
            if reqs is not None:
                t = templ(reqs[k], kw)
                templates[iid][t] += 1
                if len(examples[iid]) < 4:
                    examples[iid].append({"text": reqs[k], "kwargs": kw})
        for iid in set(il):
            per_id_rows[iid] += 1
    summary = {
        "rows": rows, "constraints": sum(ids.values()), "unmatched_prompts": unmatched,
        "n_instructions_per_row": dict(sorted(n_instr.items())),
        "grading_modes": {str(k): v for k, v in grading_modes.items()},
        "ids": {iid: {"constraints": ids[iid], "rows": per_id_rows[iid],
                      "kwarg_keys": dict(kw_keys[iid]),
                      "kwarg_values_top": {k: dict(c.most_common(12)) for k, c in kw_vals[iid].items()},
                      "kwarg_values_distinct": {k: len(c) for k, c in kw_vals[iid].items()},
                      "templates": dict(templates[iid].most_common(40)),
                      "n_templates": len(templates[iid]),
                      "examples": examples[iid]}
                for iid in sorted(ids)},
        "headers_top": dict(headers.most_common(30)),
    }
    (OUT / "survey.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    with (OUT / "row_hashes.tsv").open("w", encoding="utf-8", newline="\n") as f:
        for u, h in row_hashes:
            f.write(f"{u}\t{h}\n")
    print("rows", rows, "constraints", summary["constraints"], "ids", len(ids), "unmatched", unmatched)
    print("n_instr", summary["n_instructions_per_row"], "grading_modes", summary["grading_modes"])
    for iid in sorted(ids):
        print(f"{iid}\t{ids[iid]}\t{per_id_rows[iid]}\ttemplates={len(templates[iid])}\tkeys={dict(kw_keys[iid])}")


if __name__ == "__main__":
    main()
