"""Rerun the IFBench audit's labeled fixtures on the grader, the reference and the replacement.

Groups the results by the finding or decision id that the audit recorded for each fixture, and writes
`fixture_repro.json` (every fixture with its verdicts, including the full response) and `fixture_repro.txt` (the
summary) into the output folder.

The workspace is a folder that holds `case/` (the IFBench case, rebuilt as `cases/ifbench/SOURCES.md` describes) and
`audit/` (a copy of `runs/ifbench-r3/`). The script imports the audit's `audit/lib/ifb.py`,
`audit/tests/fixtures_data.py` and `audit/replacement/ifbench_contract.py`, and changes into the workspace, as the
audit's own scripts do. It writes no
file into the workspace: bytecode is off, and `ifb.py` points NLTK at `case/deps/nltk_data`. Run it with the case's
Python environment (`cases/ifbench/deps/requirements.lock.txt`).

Usage: <python> -B -X utf8 keys/tools/ifbench/fixture_repro.py <workspace> <output folder>
"""

import sys

sys.dont_write_bytecode = True
import collections
import hashlib
import json
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 3:
    sys.exit(__doc__)
W, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
for sub in ("audit/tests", "audit/lib", "audit/replacement"):
    sys.path.insert(0, str(W / sub))
os.chdir(W)

import ifb

ifb.verify_pins()
import ifbench_contract as rep
from fixtures_data import FIXTURES


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


rows = []
for f in FIXTURES:
    want = f.label == "pass"
    g, g_err = ifb.verdict("grader", f.check, f.kwargs, f.prompt, f.response)
    g_loose, _ = ifb.verdict("grader", f.check, f.kwargs, f.prompt, f.response, mode="loose")
    r, r_err = ifb.verdict("reference", f.check, f.kwargs, f.prompt, f.response)
    try:
        p, p_err = bool(rep.check(f.check, f.kwargs, f.prompt, f.response)), None
    except Exception as exc:
        p, p_err = None, f"{type(exc).__name__}: {exc}"
    rows.append(
        {
            "id": f.id,
            "check": f.check,
            "label": f.label,
            "kind": f.kind,
            "key": f.key,
            "note": f.note,
            "decisions": list(f.decisions),
            "recorded_grader": f.grader,
            "recorded_reference": f.reference,
            "grader_strict": g,
            "grader_error": g_err,
            "grader_loose": g_loose,
            "reference_strict": r,
            "reference_error": r_err,
            "replacement": p,
            "replacement_error": p_err,
            "grader_wrong": g != want,
            "reference_wrong": r != want,
            "replacement_wrong": p != want,
            "response_chars": len(f.response),
            "response": f.response,
            "kwargs": f.kwargs,
            "prompt_head": f.prompt[:400],
        }
    )

OUT.mkdir(parents=True, exist_ok=True)
meta = {
    "fixtures": len(rows),
    "fixtures_data_sha256": sha(W / "audit/tests/fixtures_data.py"),
    "replacement_sha256": sha(W / "audit/replacement/ifbench_contract.py"),
    "grader_wrong": sum(r["grader_wrong"] for r in rows),
    "reference_wrong": sum(r["reference_wrong"] for r in rows),
    "replacement_wrong": sum(r["replacement_wrong"] for r in rows),
    "grader_exceptions": sum(r["grader_strict"] is None for r in rows),
    "recorded_grader_nonempty": sum(bool(r["recorded_grader"]) for r in rows),
    "recorded_vs_observed_grader_mismatch": [r["id"] for r in rows if bool(r["recorded_grader"]) != r["grader_wrong"]],
    "recorded_vs_observed_reference_mismatch": [
        r["id"] for r in rows if bool(r["recorded_reference"]) != r["reference_wrong"]
    ],
}
(OUT / "fixture_repro.json").write_text(
    json.dumps({"meta": meta, "rows": rows}, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n"
)

lines = [json.dumps(meta, indent=1)]
by_reason = collections.defaultdict(list)
for r in rows:
    if r["recorded_grader"]:
        by_reason[r["recorded_grader"]].append(r)
lines.append("")
lines.append("Fixtures the audit records as wrong on the grader, by recorded reason (finding id, or decision ids):")
lines.append(f"{'reason':44s} {'n':>3s} {'repro':>5s} {'ref wrong':>9s} {'loose pass':>10s}  checks")
for reason in sorted(by_reason, key=lambda s: (not s.startswith("F-"), s)):
    group = by_reason[reason]
    checks = sorted({r["check"] for r in group})
    lines.append(
        f"{reason[:44]:44s} {len(group):3d} {sum(r['grader_wrong'] for r in group):5d} "
        f"{sum(r['reference_wrong'] for r in group):9d} {sum(bool(r['grader_loose']) for r in group):10d}  "
        f"{', '.join(checks)}"
    )
lines.append("")
lines.append("Per fixture (grader wrong only):")
for r in rows:
    if r["grader_wrong"] or r["recorded_grader"]:
        g = "EXC" if r["grader_strict"] is None else ("pass" if r["grader_strict"] else "fail")
        ref = "EXC" if r["reference_strict"] is None else ("pass" if r["reference_strict"] else "fail")
        lines.append(
            f"{r['id']:52s} label={r['label']:4s} grader={g:4s} ref={ref:4s} kind={r['kind']:10s} "
            f"[{r['recorded_grader']}] "
            f"dec={','.join(r['decisions'])} | {r['note'][:90]}"
        )
        if r["grader_error"]:
            lines.append(f"{'':52s} grader error: {r['grader_error'][:120]}")
lines.append("")
per_check = collections.Counter(r["check"] for r in rows)
lines.append(
    f"checks with fixtures: {len(per_check)}; fewest fixtures: {sorted(per_check.items(), key=lambda kv: kv[1])[:8]}"
)
kinds = collections.Counter(r["kind"] for r in rows)
lines.append(f"kinds: {dict(kinds)}")
(OUT / "fixture_repro.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines[:1]))
print(
    f"wrote {OUT / 'fixture_repro.json'} and .txt; reasons {len(by_reason)}; "
    f"F- reasons {sum(1 for k in by_reason if k.startswith('F-'))}"
)
