"""Replacement with the official reading (the one NVIDIA's checker follows) of every decision entry:
"fixes only". Its difference from the SkyRL reward is the effect of defects alone.
Writes audit/work/fixes_only.json."""
import json
import random
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

A = Path("<W>/audit")
CASE = A.parent / "case"
OFFICIAL = {
    "D-empty-response": "B", "D-word-units": "B", "D-word-cjk": "B", "D-word-case": "A", "D-keyword-inflection": "B",
    "D-sentence-split": "B", "D-capital-word": "A", "D-language-mixed": "A", "D-two-different": "A",
    "D-repeat-center": "B", "D-repeat-original": "A", "D-lowercase-count": "A", "D-lowercase-scope": "B",
    "D-placeholder": "A", "D-postscript-case": "B", "D-postscript-position": "B", "D-bigram-odd": "A",
    "D-constrained-extra": "A", "D-json-value": "B", "D-section-case": "B", "D-section-label": "B",
    "D-sections-preamble": "B", "D-bullet-markers": "B", "D-highlight-bold": "A", "D-hyphens-single": "B",
    "D-hyphens-spaces": "A", "D-brackets-each": "A", "D-title-position": "A", "D-consecutive-order": "B",
    "D-consecutive-script": "B", "D-palindrome-unit": "A", "D-palindrome-length": "B", "D-word-count-exact": "B",
    "D-paragraph-blank-lines": "B", "D-divider-form": "A", "D-divider-edges": "B", "D-divider-blank-lines": "A",
    "D-letter-case": "A", "D-letter-script": "B", "D-comma-chars": "B", "D-dot-chars": "B",
    "D-exclamation-chars": "B", "D-end-markup": "B", "D-end-case": "B", "D-quote-chars": "B",
    "D-start-end-single": "B",
}


def init():
    sys.path.insert(0, str(A / "lib"))
    global cg, rows
    import harness as h
    from contract_grader import ContractGrader

    cg = ContractGrader(OFFICIAL)
    rows = h.load_rows()


def grade(args):
    folder, run, i, line = args
    obj = json.loads(line)
    rec = rows[obj["uuid"]]
    text = cg.extract(obj["raw_response"], folder.endswith("__thinking"))
    return folder, run, i, [cg.check(a, k, text) for a, k in zip(rec["instruction_id_list"], rec["kwargs"])]


def tasks():
    for path in sorted((CASE / "panel").glob("*/*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                yield path.parent.name, path.stem, i, line


if __name__ == "__main__":
    sys.path.insert(0, str(A / "lib"))
    from contract_grader import DEFAULT_READINGS

    assert set(OFFICIAL) == set(DEFAULT_READINGS), set(DEFAULT_READINGS) ^ set(OFFICIAL)
    with Pool(8, initializer=init) as pool:
        official = {(f, r, i): v for f, r, i, v in pool.imap(grade, tasks(), chunksize=32)}
    import numpy as np

    runs = defaultdict(list)
    for line in open(A / "work" / "panel_verdicts.jsonl", encoding="utf-8"):
        rec = json.loads(line)
        runs[f"{rec['folder']}/{rec['run']}"].append((rec, official[(rec["folder"], rec["run"], rec["i"])]))
    out = {}
    rng = np.random.default_rng(0)
    for key, items in sorted(runs.items()):
        sky = np.array([r["skyrl_reward"] for r, _ in items])
        fix = np.array([float(all(v)) for _, v in items])
        prop = np.array([float(all(r["repl"])) for r, _ in items])
        d = fix - sky
        boots = d[rng.integers(0, len(d), size=(2000, len(d)))].mean(axis=1)
        out[key] = {
            "n": len(items), "skyrl": sky.mean(), "fixes_only": fix.mean(), "proposed": prop.mean(),
            "delta_fixes_minus_skyrl": d.mean(), "ci": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "rows_gained": int((d > 0).sum()), "rows_lost": int((d < 0).sum()),
            "skyrl_rewards": int((sky == 1).sum()), "false_rewards_fixes_only": int(((sky == 1) & (fix == 0)).sum()),
        }
        print(key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out[key].items()})
    (A / "work" / "fixes_only.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
