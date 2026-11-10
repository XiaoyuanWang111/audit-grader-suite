"""Reproduce verdicts for a fixture, or for an inline input.

    .venv/Scripts/python.exe -I -X utf8 audit/repro.py <fixture-id>
    .venv/Scripts/python.exe -I -X utf8 audit/repro.py --check <instruction id> --kw '<json>' --text '<response>'
    .venv/Scripts/python.exe -I -X utf8 audit/repro.py --row <dataset row> --check <id> --text '<response>'

Prints the exact input (repr), the contract label for a fixture, and the strict verdicts
of the grader under audit (G), the reference (R) and the replacement (X, as-is and
proposed switches). NLTK data is pinned to case/deps/nltk_data by audit/lib/ifbaudit.py.
"""
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
import ifbaudit as A  # noqa: E402
import replacement as X  # noqa: E402
from fixtures import BY_ID, resolve  # noqa: E402


def main(argv):
    if argv and not argv[0].startswith("--"):
        f = BY_ID[argv[0]]
        kw, prompt = resolve(f, A.ROWS)
        check, text = f["check"], f["text"]
        print("fixture:", f["id"], "| tag:", f["tag"], "| contract label:", f["label"], "|", f["note"])
    else:
        a = dict(zip(argv[::2], argv[1::2]))
        check, text = a["--check"], a["--text"].encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8") \
            if "--raw" not in a else a["--text"]
        if "--row" in a:
            kw, prompt = A.row_kwargs(int(a["--row"]), check), A.ROWS[int(a["--row"])]["prompt"]
        else:
            kw, prompt = json.loads(a.get("--kw", "{}")), ""
    print("check:", check)
    print("kwargs:", json.dumps(kw, ensure_ascii=False)[:300])
    print("text:", repr(text) if len(text) < 600 else repr(text[:600]) + f" ...[{len(text)} chars]")
    print("G (grader under audit):", A.check_G(check, kw, text, prompt))
    print("R (reference 1c40f0c): ", A.check_R(check, kw, text, prompt))
    print("X (replacement, as-is):", X.check(check, kw, text, prompt))
    print("X (replacement, proposed):", X.check(check, kw, text, prompt, X.PROPOSED))
    names = ["as is", "* removed", "first line removed", "last line removed", "first+last removed",
             "* removed + first line removed", "* removed + last line removed", "* removed + first+last removed"]
    rescued = [n for n, c in zip(names, A.loose_variants(text)) if c.strip() and A.check_G(check, kw, c, prompt)]
    print("G loose:", bool(rescued), ("(first passing variant: " + rescued[0] + ")") if rescued else "")


if __name__ == "__main__":
    main(sys.argv[1:])
