"""Print every fixture with its label and each grader's verdict, and export the fixtures.

    python -I -B audit/scripts/fixture_table.py

Writes audit/runs/fixture_table.md (one row per fixture) and audit/frozen/fixtures.jsonl
(the fixtures with their labels and the grader's verdict), and prints a count per mark.
"""
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "audit" / "tests"))
sys.dont_write_bytecode = True

from fixtures import FIXTURES  # noqa: E402
from support import REFS, grader, replacement, run, verdict_ok  # noqa: E402


def show(outcome):
    status, value = outcome
    return ("%.4f" % value) if status == "ok" else "raises " + value


def snippet(text, n=60):
    t = text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").replace("|", "\\|")
    return t if len(t) <= n else t[:n - 15] + " ... " + t[-10:] + " (%d chars)" % len(text)


def main():
    rows, export = [], []
    counts = collections.Counter()
    for f in FIXTURES:
        ref = REFS[f["order_id"]]
        g = run(grader.reward, f["response"], ref)
        p = run(replacement.reward, f["response"], ref)
        o = run(replacement.reward, f["response"], ref, **replacement.OFFICIAL)
        agrees = verdict_ok(g, f["expected"])
        mark = f["grader"] or ""
        if bool(mark) == agrees:
            raise SystemExit("mark mismatch for %s: grader %r, mark %r" % (f["id"], g, mark))
        counts[mark or "agrees"] += 1
        rows.append("| `%s` | %s | %s | `%s` | %.4f | %s | %s | %s | %s |" % (
            f["id"], f["kind"], f["order_id"], snippet(f["response"]), f["expected"], show(g), show(p), show(o), mark))
        export.append({"id": f["id"], "check": f["check"], "kind": f["kind"], "order_id": f["order_id"],
                       "response": f["response"], "expected": f["expected"], "readings": f["readings"],
                       "mark": f["grader"], "grader_verdict": show(g), "note": f["note"]})
    head = ["| Fixture | Kind | Order | Response | Contract | Grader | Replacement, proposed | Replacement, official | Mark |",
            "|---|---|---|---|---|---|---|---|---|"]
    (ROOT / "audit" / "runs" / "fixture_table.md").write_text("\n".join(head + rows) + "\n", encoding="utf-8", newline="\n")
    with open(ROOT / "audit" / "frozen" / "fixtures.jsonl", "w", encoding="utf-8", newline="\n") as out:
        for row in export:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("fixtures:", len(FIXTURES))
    for mark, n in sorted(counts.items()):
        print("  %-18s %d" % (mark, n))
    by_check = collections.Counter(f["check"] for f in FIXTURES)
    by_kind = collections.Counter(f["kind"] for f in FIXTURES)
    print("by check:", dict(by_check))
    print("by kind:", dict(by_kind))


if __name__ == "__main__":
    main()
