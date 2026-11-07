"""Print one review case's exact response and its reference.

    python -I audit/frozen/review_r1_show.py C123

Reads only audit/frozen/review_r1_material.jsonl. The response is printed twice: as a Python
string literal (every tab, carriage return and non-ASCII character escaped), and raw between
begin and end markers. Also prints the response's length and its line count.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -I review_r1_show.py <case id>")
    for line in open(HERE / "review_r1_material.jsonl", encoding="utf-8"):
        row = json.loads(line)
        if row["case_id"] == sys.argv[1]:
            text = row["response"]
            print("REFERENCE:", row["reference"])
            print("RESPONSE as a string literal:", ascii(text))
            print("RESPONSE length: %d characters, %d lines" % (len(text), text.count("\n") + 1))
            print("<<<RESPONSE BEGIN>>>")
            print(text)
            print("<<<RESPONSE END>>>")
            return
    raise SystemExit("no case %s" % sys.argv[1])


if __name__ == "__main__":
    main()
