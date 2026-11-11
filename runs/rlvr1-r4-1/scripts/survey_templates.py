"""Templatize the requirement text per instruction id, from the data alone.

For rows whose prompt ends in a numbered requirement list with one item per
constraint, replace each kwarg value in the item with {key} and count the
distinct templates per id. For the other rows, check which templates occur in
the prompt (after substitution) to estimate coverage.

Writes audit/out/templates.json and prints a summary per id.
"""
import collections
import json
import pathlib
import re

W = pathlib.Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"


def subst(text, kw):
    # longest values first
    items = sorted(kw.items(), key=lambda kv: -len(str(kv[1])))
    for k, v in items:
        if isinstance(v, list):
            reps = [repr(v), str(v), ", ".join(map(str, v))]
        else:
            reps = [str(v)]
        for r in reps:
            if r and r in text:
                text = text.replace(r, "{" + k + "}")
                break
    return text


def main():
    rows = [json.loads(l) for l in DATA.open(encoding="utf-8")]
    templ = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(dict)
    nconstraints = collections.Counter()
    keysets = collections.defaultdict(collections.Counter)
    numbered_rows = 0
    for row in rows:
        text = row["prompt"][0]["content"]
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        ids = rec["instruction_id_list"]
        kws = [{k: v for k, v in (kw or {}).items() if v is not None} for kw in rec["kwargs"]]
        for iid, kw in zip(ids, kws):
            nconstraints[iid] += 1
            keysets[iid][tuple(sorted(kw))] += 1
        lines = text.split("\n")
        idx = [i for i, l in enumerate(lines) if re.match(r"^\d+\. ", l)]
        if not idx:
            continue
        j = len(idx) - 1
        while j > 0 and idx[j - 1] == idx[j] - 1:
            j -= 1
        items = [re.sub(r"^\d+\. ", "", lines[k]) for k in idx[j:]]
        if len(items) != len(ids):
            continue
        numbered_rows += 1
        for iid, kw, item in zip(ids, kws, items):
            t = subst(item, kw)
            templ[iid][t] += 1
            examples[iid].setdefault(t, {"item": item, "kwargs": kw, "uuid": rec["uuid"]})
    out = {}
    for iid in sorted(nconstraints):
        out[iid] = {
            "n": nconstraints[iid],
            "keysets": [[list(k), c] for k, c in keysets[iid].most_common()],
            "templates": [[t, c, examples[iid][t]] for t, c in templ[iid].most_common()],
        }
    (W / "audit" / "out" / "templates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("numbered rows used", numbered_rows)
    for iid, d in out.items():
        print(f"\n## {iid}  n={d['n']}  keysets={d['keysets']}")
        for t, c, ex in d["templates"][:4]:
            print(f"   [{c}] {t[:260]}")
        if len(d["templates"]) > 4:
            print(f"   ... {len(d['templates'])} templates")


if __name__ == "__main__":
    main()
