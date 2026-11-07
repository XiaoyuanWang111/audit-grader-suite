"""Print the exact response of one review case: python audit/frozen/print_case.py K07 [--code]

--code prints only the code that rule 1 of the grading rule extracts, ready to run with: ... --code > case.py
"""
import json
import os
import re
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_r1_cases.jsonl")
FENCE = re.compile(r"```([A-Za-z0-9_+\-]*)[ \t]*\Z")


def extract(text):
    lines = text.split("\n")
    first = next((i for i, l in enumerate(lines) if FENCE.match(l)), None)
    if first is not None:
        for j in range(first + 1, len(lines)):
            m = FENCE.match(lines[j])
            if m and m.group(1) == "":
                return "\n".join(lines[first + 1:j]) + "\n"
    return text


def main():
    case_id = sys.argv[1]
    with open(PATH, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["case_id"] == case_id:
                text = extract(c["response"]) if "--code" in sys.argv[2:] else c["response"]
                sys.stdout.write(text)
                return
    sys.exit("no such case: " + case_id)


if __name__ == "__main__":
    main()
