"""Run every fixture against the grader (G), the reference (R) and, if present, the replacement (X).

Prints one line per fixture whose grader verdict does not match the expectation
(tagged fixtures are expected to be wrong in G, untagged ones right), and a summary.
With --all, prints every fixture. With --json PATH, writes the verdict table.
"""
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
import ifbaudit as A  # noqa: E402
from fixtures import FIXTURES, resolve  # noqa: E402

try:
    import replacement as X  # noqa: E402
except ImportError:
    X = None


def verdict(fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # noqa: BLE001
        return f"EXC:{type(e).__name__}"


def main(argv):
    show_all = "--all" in argv
    out = None
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
    checks = sorted({f["check"] for f in FIXTURES})
    table = []
    unexpected = 0
    unexpected_x = 0
    for f in FIXTURES:
        kw, prompt = resolve(f, A.ROWS)
        g = verdict(A.check_G, f["check"], kw, f["text"], prompt)
        r = verdict(A.check_R, f["check"], kw, f["text"], prompt)
        x = verdict(X.check, f["check"], kw, f["text"], prompt) if X else None
        xp = verdict(X.check, f["check"], kw, f["text"], prompt, X.PROPOSED) if X else None
        expect_wrong = f["tag"] is not None
        g_wrong = g != f["label"]
        ok = g_wrong == expect_wrong
        if not ok:
            unexpected += 1
        row = {"id": f["id"], "check": f["check"], "label": f["label"], "tag": f["tag"], "G": g, "R": r, "X": x, "XP": xp}
        table.append(row)
        # X (as-is switches) must match the label on every fixture except decision fixtures;
        # X with the proposed switches must match every label.
        x_bad = X is not None and x != f["label"] and not (f["tag"] or "").startswith("D-")
        xp_bad = X is not None and xp != f["label"]
        if x_bad or xp_bad:
            unexpected_x += 1
        if show_all or not ok or x_bad or xp_bad:
            flag = "" if ok else "  <-- G unexpected"
            flag += "  <-- X wrong" if x_bad else ""
            flag += "  <-- X(proposed) wrong" if xp_bad else ""
            print(f"{f['id']:<48} label={f['label']!s:<5} G={g!s:<5} R={r!s:<5} X={x!s:<5} XP={xp!s:<5} tag={f['tag']}{flag}")
    print(f"fixtures={len(FIXTURES)} checks={len(checks)} unexpected_G={unexpected} unexpected_X={unexpected_x}")
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as fo:
            json.dump(table, fo, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
