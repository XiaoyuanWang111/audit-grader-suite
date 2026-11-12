"""Grade every fixture with both graders and the replacement, classify wrong verdicts, and write
audit/fixtures.jsonl (merged with fixtures from other sources) and audit/tests/known_failures.json.

Usage: python build_fixtures.py [extra.jsonl ...]   (extra files hold generated fixtures with the
same fields: source, instruction_id, kwargs, response, label, note, reasoning_model)
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(W / "audit" / "tests"))
sys.path.insert(0, str(HERE))

import fixture_lib as fl  # noqa: E402
from fixture_defs import EXTRACTION_FIXTURES, FIXTURES  # noqa: E402

OUT = W / "audit" / "fixtures.jsonl"
KNOWN = W / "audit" / "tests" / "known_failures.json"
NONDETERMINISTIC_RUNS = 30


def entries():
    for iid, kw, resp, label, note in FIXTURES:
        yield {"source": "hand", "instruction_id": iid, "kwargs": kw, "response": resp, "label": label,
               "note": note, "reasoning_model": False}
    for iid, kw, resp, reasoning, label, note in EXTRACTION_FIXTURES:
        yield {"source": "extraction", "instruction_id": iid, "kwargs": kw, "response": resp, "label": label,
               "note": note, "reasoning_model": reasoning}
    for path in sys.argv[1:]:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def main():
    rows = []
    seen = set()
    known = {"skyrl": [], "curation": []}
    summary = collections.Counter()
    problems = []
    for e in entries():
        fid = fl.fixture_id(e["instruction_id"], e["kwargs"], e["response"], e.get("reasoning_model", False))
        if fid in seen:
            continue
        seen.add(fid)
        iid, kw, resp, label, rm = e["instruction_id"], e["kwargs"], e["response"], e["label"], e.get("reasoning_model", False)
        rep = fl.verdict_replacement(iid, kw, resp, rm)
        if ("pass" if rep else "fail") != label:
            problems.append(f"replacement disagrees with label: {fid} {e.get('note')}")
        sv, se = fl.verdict_skyrl(iid, kw, resp)
        runs = None
        if iid == "length_constraints:nth_paragraph_first_word" and kw and kw.get("nth_paragraph", 0) > kw.get("num_paragraphs", 99):
            runs = [fl.verdict_skyrl(iid, kw, resp)[0] for _ in range(NONDETERMINISTIC_RUNS)]
            sv = any(runs)  # the verdict that a run can give
        cv, ce = fl.verdict_curation(iid, kw, resp)
        sclass, sdec = fl.classify(iid, kw, resp, label, sv, se, rm)
        cclass, cdec = fl.classify(iid, kw, resp, label, cv, ce, rm)
        if sclass != "ok":
            known["skyrl"].append(fid)
        if cclass not in ("ok", "not_applicable"):
            known["curation"].append(fid)
        summary[("skyrl", sclass)] += 1
        summary[("curation", cclass)] += 1
        row = {"id": fid, "source": e["source"], "instruction_id": iid, "kwargs": kw, "response": resp,
               "label": label, "note": e.get("note", ""), "reasoning_model": rm,
               "skyrl": {"verdict": None if sv is None else ("pass" if sv else "fail"), "error": se,
                         "class": sclass, "decisions": sdec},
               "curation": {"verdict": None if cv is None else ("pass" if cv else "fail"), "error": ce,
                            "class": cclass, "decisions": cdec},
               "replacement": "pass" if rep else "fail"}
        for key in ("base_id", "edit", "fuzz_seed"):
            if key in e:
                row[key] = e[key]
        if runs is not None:
            row["skyrl"]["passes_in_runs"] = f"{sum(runs)}/{len(runs)}"
        rows.append(row)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    KNOWN.write_text(json.dumps(known, indent=1), encoding="utf-8", newline="\n")
    print(f"{len(rows)} fixtures written")
    for k in sorted(summary):
        print(k, summary[k])
    for p in problems:
        print("PROBLEM", p)


if __name__ == "__main__":
    main()
