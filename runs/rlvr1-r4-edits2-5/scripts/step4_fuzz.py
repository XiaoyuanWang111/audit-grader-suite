"""Step 4 fuzzing: random responses against every check of both graders and the replacement.

Counts exceptions per grader and check, and verdict disagreements with the replacement (contract,
proposed readings), each classified as a decision or a finding by fixture_lib.explain. Keeps the
smallest reproducing response of each (grader, check, class, readings) group after greedy
shrinking. Writes audit/work/fuzz_summary.json and audit/work/fuzz_candidates.jsonl.

Usage: python step4_fuzz.py [per_check] [seed]
"""
from __future__ import annotations

import collections
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402
from verifyit.modes.ifeval import CONSTRAINTS  # noqa: E402

DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
OUT_SUMMARY = W / "audit" / "work" / "fuzz_summary.json"
OUT_CAND = W / "audit" / "work" / "fuzz_candidates.jsonl"

BASE_TOKENS = [
    "the", "The", "cat", "dog", "and", "I", "a", "A", "NASA", "is", "was", "level", "noon", "b", "c", "d",
    "don't", "well-known", "café", "Привет", "中文", "2002", "3.5", "1.", "2.",
    ",", ".", "!", "?", ";", ":", "-", "—", "'", '"', "“", "”", "’", "(", ")",
    "*", "**", "***", "* * *", "#", "##", ">", "`", "```", "[", "]", "[name]", "<<", ">>", "<<a b>>",
    "******", "P.S.", "P.P.S", "SECTION 1", "Section 2", "\n", "\n", "\n\n", "\n\n", "\n***\n", "\n- ", "\n* ",
    "My answer is yes.", "{", "}", '{"a": 1}', "<b>", "</b>", "。", "，",
]


def kwargs_by_id():
    found = {}
    for line in DATA.open(encoding="utf-8"):
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            found.setdefault(iid, kw)
    return found


def kw_tokens(kw):
    out = []
    for v in (kw or {}).values():
        if isinstance(v, str):
            out += [v, v.capitalize(), v.upper()] + v.split()
        elif isinstance(v, list):
            out += [x for x in v if isinstance(x, str)]
    return out


def random_response(rng, pool):
    n = rng.randint(0, 25)
    parts = []
    for _ in range(n):
        parts.append(rng.choice(pool))
        parts.append(rng.choice([" ", " ", " ", "", "\n"]))
    return "".join(parts)


def verdicts(iid, kw, resp):
    out = {}
    try:
        out["skyrl"] = fl.verdict_skyrl(iid, kw, resp)
    except Exception as e:  # adapter-level failure
        out["skyrl"] = (None, f"{type(e).__name__}: {e}")
    out["curation"] = fl.verdict_curation(iid, kw, resp)
    return out


def group_key(grader, iid, kw, resp, observed):
    rep = fl.verdict_replacement(iid, kw, resp)
    if observed == rep:
        return None
    readings = fl.explain(iid, kw, resp, observed)
    cls = "decision" if readings else "finding"
    return (grader, iid, cls, ",".join(readings or []))


def shrink(grader, iid, kw, resp, key):
    tokens = resp.split(" ")
    changed = True
    while changed and len(tokens) > 1:
        changed = False
        for i in range(len(tokens)):
            cand = " ".join(tokens[:i] + tokens[i + 1:])
            v, e = verdicts(iid, kw, cand)[grader]
            if e is None and v is not None and group_key(grader, iid, kw, cand, v) == key:
                tokens = tokens[:i] + tokens[i + 1:]
                changed = True
                break
    return " ".join(tokens)


def main():
    per_check = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261112
    rng = random.Random(seed)
    kws = kwargs_by_id()
    exceptions = collections.Counter()
    exception_examples = {}
    disagreements = collections.Counter()
    smallest = {}
    for iid in sorted(kws):
        kw = kws[iid]
        pool = BASE_TOKENS + kw_tokens(kw) * 3
        for _ in range(per_check):
            resp = random_response(rng, pool)
            for grader, (v, e) in verdicts(iid, kw, resp).items():
                if e is not None:
                    exceptions[(grader, iid, e.split(":")[0])] += 1
                    k = (grader, iid, e.split(":")[0])
                    if k not in exception_examples or len(resp) < len(exception_examples[k]):
                        exception_examples[k] = resp
                    continue
                if v is None:
                    continue
                key = group_key(grader, iid, kw, resp, v)
                if key is None:
                    continue
                disagreements[key] += 1
                if key not in smallest or len(resp) < len(smallest[key][0]):
                    smallest[key] = (resp, v)
    summary = {
        "per_check": per_check, "seed": seed,
        "exceptions": [{"grader": g, "check": i, "type": t, "count": c, "example": exception_examples[(g, i, t)]}
                       for (g, i, t), c in sorted(exceptions.items())],
        "disagreements": [{"grader": g, "check": i, "class": c, "readings": r, "count": n}
                          for (g, i, c, r), n in sorted(disagreements.items())],
        "unknown_to_verifyit": sorted(set(kws) - set(CONSTRAINTS)),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    with OUT_CAND.open("w", encoding="utf-8", newline="\n") as f:
        for key, (resp, v) in sorted(smallest.items()):
            grader, iid, cls, readings = key
            small = shrink(grader, iid, kws[iid], resp, key)
            rep = fl.verdict_replacement(iid, kws[iid], small)
            f.write(json.dumps({"source": "fuzz", "instruction_id": iid, "kwargs": kws[iid], "response": small,
                                "label": "pass" if rep else "fail", "note": f"fuzz {grader} {cls} {readings}",
                                "reasoning_model": False, "fuzz_seed": seed}, ensure_ascii=False) + "\n")
    print("exceptions:", sum(exceptions.values()), dict(exceptions))
    print("disagreement groups:", len(disagreements), "total:", sum(disagreements.values()))
    print("unknown_to_verifyit:", summary["unknown_to_verifyit"])


if __name__ == "__main__":
    main()
