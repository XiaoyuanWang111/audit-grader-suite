"""Compare the agent's answer file with the expected count.

Usage: python3 check_answer.py ANSWER_FILE EXPECTED_JSON
Exit status 0 when the answer is the expected count, 1 otherwise.
"""

import json
import re
import sys


def main(argv):
    answer_path, expected_path = argv[1], argv[2]
    with open(expected_path, encoding="utf-8") as f:
        expected = json.load(f)["server_error_count"]
    with open(answer_path, encoding="utf-8", errors="replace") as f:
        text = f.read().strip()
    if not re.fullmatch(r"[0-9]+", text):
        print("answer is not a decimal integer")
        return 1
    if int(text) != expected:
        print(f"wrong count: {int(text)}")
        return 1
    print("correct")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
