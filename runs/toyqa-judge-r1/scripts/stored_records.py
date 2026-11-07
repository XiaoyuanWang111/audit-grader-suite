"""Count what the stored run records already show (step 5, before any grading).

Reasoning text is never printed: each reasoning span is shown as its length only.

    python -I audit/scripts/stored_records.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from toyqa_audit_lib import CASE, contract_graded_text, contract_parse, grader_module, load_jsonl  # noqa: E402


def masked(response):
    """The response with every reasoning span replaced by its length."""
    out, rest = [], response
    while True:
        i = rest.find("<think>")
        j = rest.find("</think>")
        if i == -1 and j == -1:
            out.append(rest)
            break
        if j != -1 and (i == -1 or j < i):      # reasoning opened before the response started
            out.append(f"[{j} chars]</think>")
            rest = rest[j + len("</think>"):]
            continue
        k = rest.find("</think>", i)
        out.append(rest[:i])
        if k == -1:
            out.append(f"<think>[{len(rest) - i - len('<think>')} chars, never closed]")
            break
        out.append(f"<think>[{k - i - len('<think>')} chars]</think>")
        rest = rest[k + len("</think>"):]
    return "".join(out)


def main():
    rows = load_jsonl(CASE / "responses.jsonl")
    stats = Counter()
    print("id   model            qid  finish  graded text (contract), reasoning masked")
    for r in rows:
        text = r["response"]
        graded = contract_graded_text(text)
        stats["rows"] += 1
        stats[f"finish_{r['finish_reason']}"] += 1
        stats["has_open"] += "<think>" in text
        stats["has_close"] += "</think>" in text
        stats["close_without_open"] += "</think>" in text and "<think>" not in text
        stats["several_close"] += text.count("</think>") > 1
        if graded is None:
            stats["extraction_failure"] += 1
            stats[f"extraction_failure_finish_{r['finish_reason']}"] += 1
        else:
            stats["empty_graded"] += graded == ""
            stats["multiline_graded"] += len(graded.splitlines()) > 1
            stats["graded_over_300"] += len(graded) > 300
        shown = masked(text) if graded is None else graded
        if graded is not None and ("<think>" in text or "</think>" in text):
            shown = "[after reasoning] " + (masked(graded) if "<think>" in graded else graded)
        print(f"{r['id']:<4} {r['model']:<16} {r['question_id']:<4} {r['finish_reason']:<7} {json.dumps(shown)[:150]}")
    print(json.dumps(dict(sorted(stats.items()))))

    replies = load_jsonl(CASE / "judge_replies.jsonl")
    by_text = Counter((r["call"], r["reply"]) for r in replies)
    print("\ncall  count  contract  grader  reply")
    for (call, reply), n in sorted(by_text.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1])):
        print(f"{call:<5} {n:<6} {str(contract_parse(reply)):<9} {str(grader_module.parse_grade(reply)):<7} "
              f"{json.dumps(reply)}")


if __name__ == "__main__":
    main()
