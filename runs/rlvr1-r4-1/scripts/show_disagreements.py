"""Print short excerpts of the graded text for panel disagreements of one check (development half only).

Usage: python audit/scripts/show_disagreements.py <check id> <skyrl|gate> <false_pass|false_fail> [k] [--heldout]
Prints at most k cases (default 5): the run, uuid, kwargs and the first/last 160 characters of the
graded text (never thinking text: the graded text is what the graders score).
"""
import json
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
import harness  # noqa: E402
import replacement as rp  # noqa: E402


def main():
    check, grader, direction = sys.argv[1], sys.argv[2], sys.argv[3]
    k = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 5
    heldout = "--heldout" in sys.argv
    want_pass = direction == "false_pass"
    shown = 0
    raws = {}
    for line in (W / "audit" / "out" / "panel_verdicts.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        if rec["heldout"] != heldout or check not in rec["ids"]:
            continue
        i = rec["ids"].index(check)
        gv = rec["skyrl"][i] if grader == "skyrl" else rec["gate"][i]
        if gv is None or gv != want_pass or rec["repl"][i] == gv:
            continue
        key = (rec["folder"], rec["run"])
        if key not in raws:
            raws[key] = {json.loads(l)["uuid"]: json.loads(l)["raw_response"]
                         for l in (W / "case" / "panel" / rec["folder"] / f"{rec['run']}.jsonl").open(encoding="utf-8")}
        raw = raws[key][rec["uuid"]]
        text = harness.final_answer_text(raw)
        print("=" * 80)
        print(rec["folder"], rec["run"], rec["uuid"], "kwargs:", json.dumps(rec["kwargs"][i], ensure_ascii=False))
        print("HEAD:", repr(text[:160]))
        print("TAIL:", repr(text[-160:]))
        shown += 1
        if shown >= k:
            break


if __name__ == "__main__":
    main()
