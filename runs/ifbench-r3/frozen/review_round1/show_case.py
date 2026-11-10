"""Print the exact response of a review case.

Usage (from any folder):
  python show_case.py CASE_ID          the response exactly as graded, nothing added
  python show_case.py CASE_ID --repr   the response as a Python string literal (shows spaces, tabs, newlines)
  python show_case.py CASE_ID --json   one JSON object with case_id, check, requirement, prompt, response
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cid = sys.argv[1]
    with open(os.path.join(HERE, "review_cases.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            c = json.loads(line)
            if c["case_id"] == cid:
                break
        else:
            sys.exit(f"unknown case id {cid}")
    out = sys.stdout
    if hasattr(out, "reconfigure"):
        out.reconfigure(encoding="utf-8", newline="")
    if "--json" in sys.argv:
        out.write(json.dumps(c, ensure_ascii=False))
    elif "--repr" in sys.argv:
        out.write(repr(c["response"]) + "\n")
    else:
        out.write(c["response"])


if __name__ == "__main__":
    main()
