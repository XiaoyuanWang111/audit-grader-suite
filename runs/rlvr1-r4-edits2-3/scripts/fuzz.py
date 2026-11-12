"""Step 4: fuzz both graders with random responses on random rows (counts, not rates).

Each sample picks a row (seeded) and builds a random response from words (including the
row's keywords), punctuation of several scripts, markdown, brackets, quotes, list labels,
dividers, line breaks and reasoning markers. For every constraint of the row it records:
- an exception in a SkyRL checker (grade_instruction_following's instruction_errors) or in a
  task-curation check (counted as failed by the gate);
- a verdict that differs from the replacement (the contract implementation).
For each (grader, check, kind) the smallest reproducing response is kept (greedy token
deletion). Writes audit/fuzz_results.json. The minimal disagreement cases are written to
audit/fuzz_minimal.jsonl for review before any of them becomes a fixture.
"""

import collections
import json
import logging
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)
logging.disable(logging.ERROR)

import harness as h  # noqa: E402

SEED = 20261112
N = int(os.environ.get("FUZZ_N", "30000"))
BASE_WORDS = ["the", "a", "I", "we", "data", "answer", "is", "and", "level", "noon", "apple", "banana", "cat",
              "dog", "NASA", "OK", "yes", "no", "Section", "SECTION", "P.S.", "P.P.S", "p.s.", "My", "answer",
              "maybe.", "think", "3.14", "2024", "don't", "it's", "well-known", "café", "数据", "答案", "Привет",
              "x", "Live", "each", "day", "to", "fullest", "Any", "other", "questions?"]
PUNCT = [".", ",", "!", "?", ";", ":", "-", "—", "…", "，", "。", "！", "、", "'", '"', "“", "”", "’", "(", ")"]
MARKUP = ["**", "*", "_", "#", "##", ">", "`", "```", "[", "]", "<<", ">>", "<b>", "</b>", "[x]", "<<title>>"]
STRUCT = ["\n", "\n\n", "\n\n\n", "\n***\n", "\n* * *\n", "\n******\n", "\n- ", "\n* ", "\n1. ", "\n2. ",
          "<think>", "</think>", "<<think>>", " ", "  ", "\t", "\n---\n", "\n+ "]


NO_MARKERS = bool(os.environ.get("FUZZ_NO_MARKERS"))
SUFFIX = "_no_markers" if NO_MARKERS else ""
if NO_MARKERS:
    STRUCT = [s for s in STRUCT if "think" not in s]
    BASE_WORDS = [w for w in BASE_WORDS if w != "think"]


def row_words(row):
    out = []
    for kw in row["kwargs"]:
        for k, v in (kw or {}).items():
            if isinstance(v, str):
                out.extend(v.split())
            elif isinstance(v, list):
                out.extend(x for x in v if isinstance(x, str))
    return out


def make(rng, row):
    vocab = BASE_WORDS + row_words(row) * 3
    toks = []
    for _ in range(rng.randint(0, 60)):
        r = rng.random()
        if r < 0.55:
            w = rng.choice(vocab)
            toks.append(w.upper() if rng.random() < 0.08 else (w.capitalize() if rng.random() < 0.15 else w))
            toks.append(" ")
        elif r < 0.75:
            toks.append(rng.choice(PUNCT))
            if rng.random() < 0.5:
                toks.append(" ")
        elif r < 0.88:
            toks.append(rng.choice(MARKUP))
        else:
            toks.append(rng.choice(STRUCT))
    return toks


def verdicts(text, iid, kw, prompt):
    sky_v, sky_e = h.skyrl_check(h.final_answer_text(text), iid, kw)
    tc_v, tc_d = h.tc_check(h.tc_answer_text(text), iid, kw)
    rep = h.contract_grade(text, [iid], [kw], prompt, False)["results"][0]
    return {
        "skyrl": None if sky_e else bool(sky_v),
        "skyrl_exc": sky_e.split(":")[0] if sky_e else None,
        "tc": tc_v,
        "tc_exc": tc_d.split(":")[0] if isinstance(tc_d, str) and tc_d.startswith("exception") else None,
        "rep": rep,
    }


def kinds(v):
    out = []
    if v["skyrl_exc"]:
        out.append(("skyrl", "exception " + v["skyrl_exc"]))
    elif v["skyrl"] != v["rep"]:
        out.append(("skyrl", "false pass" if v["skyrl"] else "false fail"))
    if v["tc_exc"]:
        out.append(("tc", "exception " + v["tc_exc"]))
    elif v["tc"] is not None and v["tc"] != v["rep"]:
        out.append(("tc", "false pass" if v["tc"] else "false fail"))
    return out


def shrink(toks, iid, kw, prompt, key):
    """Greedy deletion while (grader, kind) still reproduces."""
    def holds(ts):
        return key in kinds(verdicts("".join(ts), iid, kw, prompt))
    changed = True
    while changed:
        changed = False
        for i in range(len(toks)):
            cand = toks[:i] + toks[i + 1:]
            if holds(cand):
                toks = cand
                changed = True
                break
    return "".join(toks)


def main():
    rng = random.Random(SEED)
    rows = h.load_rows()
    counts = collections.Counter()
    totals = collections.Counter()
    minimal = {}
    for _ in range(N):
        row = rng.choice(rows)
        toks = make(rng, row)
        text = "".join(toks)
        for iid, kw in zip(row["ids"], row["kwargs"]):
            totals[iid] += 1
            v = verdicts(text, iid, kw, row["prompt"])
            for grader, kind in kinds(v):
                counts[(grader, iid, kind)] += 1
                key = (grader, iid, kind)
                if key not in minimal and len(minimal) < 400:
                    small = shrink(list(toks), iid, kw, row["prompt"], (grader, kind))
                    minimal[key] = {"grader": grader, "instruction_id": iid, "kwargs": kw, "kind": kind,
                                    "response": small, "row": row["index"], "prompt": row["prompt"]}
    res = {
        "seed": SEED,
        "reasoning_markers": not NO_MARKERS,
        "samples": N,
        "constraints_per_check": dict(sorted(totals.items())),
        "counts": {" | ".join(k): v for k, v in sorted(counts.items())},
    }
    with open(os.path.join(AUDIT, "fuzz_results" + SUFFIX + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    with open(os.path.join(AUDIT, "fuzz_minimal" + SUFFIX + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for key in sorted(minimal):
            m = dict(minimal[key])
            m.pop("prompt")
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    for k, v in sorted(counts.items()):
        if k[2].startswith("exception"):
            print("EXCEPTION", k, v)
    by = collections.Counter()
    for k, v in counts.items():
        by[(k[0], k[2])] += v
    print(dict(by))


if __name__ == "__main__":
    main()
