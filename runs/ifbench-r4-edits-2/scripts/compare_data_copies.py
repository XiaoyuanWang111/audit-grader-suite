"""Compare the three copies of IFBench_test: the HF parquet (as `datasets` loads it, which is
what eval_instruct.py does), reference/IFBench/data/IFBench_test.jsonl and
reference/IFBench/ifbench/data/IFBench_test.jsonl. Prints differing rows with short excerpts."""
import difflib
import json
import sys

from datasets import load_dataset

W = "<W>/case/"
ds = load_dataset("parquet", data_files=W + "data/train-00000-of-00001.parquet", split="train")
hf = [dict(key=r["key"], prompt=r["prompt"], instruction_id_list=list(r["instruction_id_list"]),
           kwargs=[{k: v for k, v in d.items() if v is not None} for d in r["kwargs"]]) for r in ds]


def load(p):
    out = []
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        r["kwargs"] = [{k: v for k, v in d.items() if v is not None} for d in r["kwargs"]]
        out.append(r)
    return out


ref = load(W + "reference/IFBench/data/IFBench_test.jsonl")
ref2 = load(W + "reference/IFBench/ifbench/data/IFBench_test.jsonl")


def excerpt_diff(a, b):
    sm = difflib.SequenceMatcher(None, a, b)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            out.append(f"{tag}: {a[max(0, i1 - 20):i2 + 20]!r} -> {b[max(0, j1 - 20):j2 + 20]!r}")
    return out[:3]


def cmp(name_a, A, name_b, B):
    print(f"== {name_a} vs {name_b}")
    n = 0
    for i, (a, b) in enumerate(zip(A, B)):
        fields = [f for f in ("key", "prompt", "instruction_id_list", "kwargs")
                  if (str(a[f]) if f == "key" else a[f]) != (str(b[f]) if f == "key" else b[f])]
        if fields:
            n += 1
            print(f"row {i} key {a['key']}: differs in {fields}")
            if "prompt" in fields:
                for d in excerpt_diff(a["prompt"], b["prompt"]):
                    print("   ", d)
            if "kwargs" in fields:
                print("    kwargs", a["kwargs"], "->", b["kwargs"])
            if "instruction_id_list" in fields:
                print("    ids", a["instruction_id_list"], "->", b["instruction_id_list"])
    print("rows differing:", n)


types = sorted({(k, type(v).__name__) for r in hf for d in r["kwargs"] for k, v in d.items()})
print("HF kwarg value types:", types)
cmp("hf_parquet", hf, "ref_data_jsonl", ref)
cmp("ref_data_jsonl", ref, "ref_pkg_jsonl", ref2)
