"""Write the small response files that the CLI tests and the report's commands use (audit/tests/data/).

Usage (from W):  python -B audit/tests/make_data.py
"""
import json
import pathlib

D = pathlib.Path(__file__).resolve().parent / "data"
FILES = {
    "empty_in_batch.jsonl": [
        {"id": "e1", "model": "m", "question_id": "q01", "response": "Canberra"},
        {"id": "e2", "model": "m", "question_id": "q10", "response": ""},
        {"id": "e3", "model": "m", "question_id": "q04", "response": "Saturn"},
    ],
    "f1_unclosed_think.jsonl": [
        {"id": "f1", "model": "m", "question_id": "q01", "response": "<think>Australia's capital is"},
    ],
    "f2_second_line.jsonl": [
        {"id": "f2", "model": "m", "question_id": "q01", "response": "Let me answer.\nCanberra"},
    ],
    "unrecorded_prompt.jsonl": [
        {"id": "u1", "model": "m", "question_id": "q01", "response": "Canberra"},
        {"id": "u2", "model": "m", "question_id": "q01", "response": "It is Canberra."},
    ],
}


# Stored responses copied byte for byte from case/responses.jsonl (the panel counterexamples).
STORED = {
    "f1_stored.jsonl": ["a08", "a20", "a40"],
    "f4_stored.jsonl": ["a09", "a16", "a22", "a24", "a32", "a34", "a35"],
    "f4_a24.jsonl": ["a24"],
}


def main():
    D.mkdir(exist_ok=True)
    for name, rows in FILES.items():
        with open(D / name, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("wrote", D / name)
    stored = {}
    for line in (D.parents[2] / "case" / "responses.jsonl").read_bytes().split(b"\n"):
        if line.strip():
            stored[json.loads(line.decode("utf-8"))["id"]] = line
    for name, ids in STORED.items():
        (D / name).write_bytes(b"".join(stored[i] + b"\n" for i in ids))
        print("wrote", D / name)


if __name__ == "__main__":
    main()
