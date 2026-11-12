"""Run every hand-written fixture against the graders; print disagreements with the label.

Writes audit/work/fixture_verdicts.json (one record per fixture).
"""
import json
import sys
from pathlib import Path

A = Path("<W>/audit")
sys.path.insert(0, str(A / "lib"))

from fixtures_src import FIXTURES  # noqa: E402
from verdicts import fixture_id, replacement_with, verdicts  # noqa: E402
from contract_grader import DEFAULT_READINGS  # noqa: E402

out = []
for iid, kwargs, response, label, note in FIXTURES:
    thinking = note.startswith("thinking:")
    v = verdicts(iid, kwargs, response, thinking)
    alt = {}
    for entry in DEFAULT_READINGS:
        if entry in note:
            other = "B" if DEFAULT_READINGS[entry] == "A" else "A"
            alt[entry] = replacement_with(iid, kwargs, response, {entry: other}, thinking)
    rec = {
        "id": fixture_id(iid, kwargs, response, thinking),
        "instruction_id": iid,
        "kwargs": kwargs,
        "response": response,
        "thinking": thinking,
        "label": label,
        "note": note,
        **v,
        "replacement_alt": alt,
    }
    out.append(rec)
    flags = []
    for g in ("skyrl", "gate", "replacement"):
        if rec[g] is not None and rec[g] != label:
            flags.append(g)
    if rec["skyrl_error"]:
        flags.append("skyrl_error")
    if flags:
        print(f"{rec['id']:<62} label={label:<4} wrong={','.join(flags):<26} {note} | alt={alt} | err={rec['skyrl_error']}")
(A / "work" / "fixture_verdicts.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("fixtures:", len(out))
