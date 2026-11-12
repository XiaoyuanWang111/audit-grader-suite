"""Step 4: property tests (hypothesis.find for the smallest counterexample per property and grader),
and the whitespace metamorphic test (P2) over the hand fixtures.

Writes audit/out/properties.json and audit/fixtures_generated_props.jsonl.
"""
import json
import random
import sys

from hypothesis import HealthCheck, find, settings
from hypothesis.errors import NoSuchExample

sys.path.insert(0, "<W>/audit")
sys.path.insert(0, "<W>/audit/tests")
import harness as h  # noqa: E402
import props  # noqa: E402
from fixture_defs import FIXTURES  # noqa: E402

A = "<W>/audit"
SEED = 20261112
GRADERS = ("NV", "VS", "VG", "R")


def verdict(g, iid, kw, resp):
    random.seed(SEED)
    if g == "NV":
        return h.nv_check(iid, kw, resp)[0]
    if g == "VS":
        return h.vs_check(iid, kw, resp)[0]
    if g == "VG":
        return h.vg_check(iid, kw, resp)[0]
    return h.R.check(iid, kw, resp)


def main():
    results = {}
    generated = []
    cfg = settings(max_examples=400, database=None, derandomize=True, deadline=None,
                   suppress_health_check=list(HealthCheck))
    for name, strat in props.PROPERTIES.items():
        results[name] = {}
        for g in GRADERS:
            def wrong(x, g=g):
                iid, kw, resp, label = x
                v = verdict(g, iid, kw, resp)
                return v is not None and bool(v) != label
            try:
                ex = find(strat(), wrong, settings=cfg)
                iid, kw, resp, label = ex
                results[name][g] = {"counterexample": {"instruction_id": iid, "kwargs": kw, "response": resp,
                                                      "label": "pass" if label else "fail"}}
                generated.append({"source": f"property {name}", "grader": g, "instruction_id": iid, "kwargs": kw,
                                  "response": resp, "label": "pass" if label else "fail"})
            except NoSuchExample:
                results[name][g] = {"counterexample": None}
            print(name, g, "FAIL" if results[name][g]["counterexample"] else "ok", flush=True)

    # P2: leading/trailing whitespace is ignored by the contract (G2)
    meta = {g: [] for g in GRADERS}
    lead, trail = props.PAD
    for iid, kw, resp, label, deps, note in FIXTURES:
        for g in GRADERS:
            v0 = verdict(g, iid, kw, resp)
            if v0 is None:
                continue
            padded = lead + resp + trail
            v1 = verdict(g, iid, kw, padded)
            if bool(v1) != bool(v0) and bool(v0) == (label == "pass"):
                meta[g].append({"instruction_id": iid, "kwargs": kw, "response": padded, "label": label,
                                "original": resp})
    for g in GRADERS:
        for m in meta[g]:
            generated.append({"source": "metamorphic P2 (leading/trailing whitespace)", "grader": g,
                              "instruction_id": m["instruction_id"], "kwargs": m["kwargs"],
                              "response": m["response"], "label": m["label"]})
    results["P2-whitespace"] = {g: meta[g] for g in GRADERS}
    print("P2", {g: len(meta[g]) for g in GRADERS})
    json.dump(results, open(f"{A}/out/properties.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(f"{A}/fixtures_generated_props.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in generated:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
