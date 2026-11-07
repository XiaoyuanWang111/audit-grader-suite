"""Score effect of each decision entry's readings on the stored run, from the contract pipeline's labels.

The stored cases under each entry were classified from their graded text (listed below); a reading sets the label of
those cases, and every other label stays as the replacement gave it with the recorded judge. This measures the
stakes of each decision; it does not decide it.

    python -I audit/scripts/decision_effects.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from toyqa_audit_lib import CASE, WORK, contract_scores, load_jsonl  # noqa: E402

MODELS = ["orca-7b", "puffin-13b", "heron-32b-think", "ibis-8b-think"]
ENTRIES = {
    # entry: (cases, {reading name: label})
    "D-multiple-candidates": (["a06", "a36", "a41"], {"reading 1 (A)": "correct", "reading 2 (B, proposed)": "incorrect"}),
    "D-cut-off-answer": (["a47"], {"reading 1 (C, proposed)": "not_attempted", "reading 2 (B)": "incorrect"}),
}


def table(labels, rows):
    out = {}
    for m in MODELS:
        s = contract_scores([labels[r["id"]] for r in rows if r["model"] == m])
        out[m] = {k: round(100 * s[k], 1) for k in ("accuracy", "cga", "f_score", "not_attempted_rate")}
    return out


def main():
    rows = load_jsonl(CASE / "responses.jsonl")
    base = {d["id"]: d["label"] for d in load_jsonl(WORK / "panel" / "replacement.labels.jsonl")}
    per_row = {d["id"]: d for d in load_jsonl(WORK / "panel" / "per_row.jsonl")}
    base_t = table(base, rows)
    for entry, (cases, readings) in ENTRIES.items():
        print(f"== {entry}: cases {cases}")
        for c in cases:
            d = per_row[c]
            print(f"   {c} {d['model']:<16} judge call 1 {d['reply_call1']!r}, call 2 {d['reply_call2']!r}, "
                  f"label as judged {base[c]}")
        for name, label in readings.items():
            labels = dict(base, **{c: label for c in cases})
            t = table(labels, rows)
            changed = {m: {k: round(t[m][k] - base_t[m][k], 1) for k in t[m] if t[m][k] != base_t[m][k]}
                       for m in MODELS}
            print(f"   {name}: change from the labels as judged: "
                  + "; ".join(f"{m} {v}" for m, v in changed.items() if v) if any(changed.values()) else
                  f"   {name}: no change from the labels as judged")


if __name__ == "__main__":
    main()
