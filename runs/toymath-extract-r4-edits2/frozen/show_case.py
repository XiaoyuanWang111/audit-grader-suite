"""Reviewer helper: print the exact response of one case.

    python -I audit/frozen/show_case.py C07

Prints the response's length, its line count under str.splitlines(), and the
response twice: as Python repr (every character visible, escapes for line
breaks and unusual spaces) and as raw text between markers.
"""
import json
import pathlib
import sys

CASES = pathlib.Path(__file__).resolve().parent / "round1_cases.jsonl"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    want = sys.argv[1]
    for line in CASES.read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        if c["case_id"] == want:
            r = c["response"]
            print(f"case {want}: {len(r)} characters, {len(r.splitlines())} lines (str.splitlines)")
            print("repr:", ascii(r))
            print("<<<RESPONSE BEGIN>>>", flush=True)
            sys.stdout.buffer.write(r.encode("utf-8"))
            sys.stdout.buffer.flush()
            print("\n<<<RESPONSE END>>>", flush=True)
            return
    sys.exit(f"no case {want}")


if __name__ == "__main__":
    main()
