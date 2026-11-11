"""Write one counterexample file per finding, in the grader's own response-file format.

    python -B audit/make_counterexamples.py

Each file audit/counterexamples/<id>.jsonl has rows with id, checkpoint (= the finding id, so the grader's table
prints one line per finding), order_id and response. Reproduce the grader's verdict with its own command line:
    python -B case/reward.py --responses audit/counterexamples/<id>.jsonl
and the contract's label with the replacement:
    python -B audit/replacement_reward.py --responses audit/counterexamples/<id>.jsonl
"""

import json
import os

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(W, "audit", "counterexamples")

V2 = '{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}'


def v2(items='[{"sku": "EF-310", "qty": 3}]', total="29.97", extra=""):
    return ('{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": %s, "total": %s%s}'
            % (items, total, extra))


CASES = {
    "F1": [V2 + "."],
    "F2": [v2(items='[{"sku": "EF-310", "qty": 3}, {"sku": "EF-310", "qty": 3}]')],
    "F3": ["[]"],
    "F4a": [v2(extra=', "n": 1' + "0" * 4300)],
    "F4b": ["[" * 100000 + "]" * 100000],
    "F5": [v2(total="1e999999999")],
    "F6": [v2(total="29.975" + "0" * 27 + "1")],
    "D-qty-decimal": [v2(items='[{"sku": "EF-310", "qty": 3.0}]')],
    "D-crlf": ["```json\r\n" + V2 + "\r\n```"],
    "G3": [V2, "[]", V2],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for cid, responses in CASES.items():
        path = os.path.join(OUT, f"{cid}.jsonl")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for k, resp in enumerate(responses, 1):
                f.write(json.dumps({"id": f"{cid}-{k}", "checkpoint": cid, "order_id": "o02",
                                    "response": resp}) + "\n")
        print(path)


if __name__ == "__main__":
    main()
