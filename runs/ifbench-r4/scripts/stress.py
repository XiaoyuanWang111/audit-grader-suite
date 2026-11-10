"""Step 4 stress tests: fuzzing, content-free responses, metamorphic edits, loose transform.

Writes audit/frozen/stress.json and prints a summary.
  fuzz: 400 random texts per dataset instruction instance (344 instances, seed 10060),
        exceptions counted per grader and check, with the shortest input per exception type.
  content_free: empty, whitespace, repeated word, repeated sentence, the prompt itself,
        and the instruction-free task text; lists the checks each passes under G strict.
  metamorphic: on fixtures that pass under the contract and under G: LF->CRLF, straight->curly
        apostrophes, append a trailing newline; counts G verdict flips (all edits the contract ignores,
        the last one under D-trim P).
  harness: whether one checker exception stops grader.py's per-prompt loop.
"""
import json
import os
import random
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
import ifbaudit as A  # noqa: E402
import replacement as X  # noqa: E402
from fixtures import FIXTURES, resolve  # noqa: E402

ATOMS = ["word", "Word", "the", "and", "I", "don't", "well-known", "1,000", "3.5", "10-20", "2021", "日本", "猫",
         "😀", "🇯🇵", "❤️", "*", "**", "-", "—", "...", "?!", "‽", ".", ",", ";", ":", "!", "?", "\"", "'", "“", "”",
         "‘", "’", "(", ")", "[", "]", "{", "}", "<i>", "</i>", "<em>", "\t", "\n", "\n\n", "\r\n", " ", "  ",
         "* item", "- sub", "1.", "Question 1:", "A)", "My Answer:", "Zimbabwe", "eagle", "SEPARATOR", "!?!?",
         "​", " ", "é", "Ω", "#", "## Head", "```", "|", "\\", "/", "%", "$", "0", "a"]


def rand_text(rng):
    k = rng.choice([0, 1, 2, 3, 5, 8, 13, 30, 80])
    parts = [rng.choice(ATOMS) for _ in range(k)]
    sep = rng.choice(["", " ", " ", "\n"])
    return sep.join(parts)


def v(fn, *a):
    try:
        return bool(fn(*a))
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__ + ":" + str(e)[:60]


def main():
    rng = random.Random(10060)
    out = {"fuzz": {}, "content_free": {}, "metamorphic": {}, "harness": {}}
    exc = {}
    n_calls = 0
    for row in A.ROWS:
        for j, iid in enumerate(row["instruction_id_list"]):
            kw = A.nonnull(row["kwargs"][j])
            for _ in range(400):
                t = rand_text(rng)
                for name, fn in (("G", A.check_G), ("R", A.check_R), ("X", X.check)):
                    res = v(fn, iid, kw, t, row["prompt"])
                    n_calls += 1
                    if isinstance(res, str):
                        key = f"{name}|{iid}|{res.split(':')[1]}"
                        if key not in exc or len(t) < len(exc[key]["text"]):
                            exc[key] = {"text": t, "row": row["key"], "msg": res, "count": exc.get(key, {}).get("count", 0)}
                        exc[key]["count"] += 1
    out["fuzz"] = {"calls": n_calls, "exceptions": exc}
    # content-free responses
    for name, mk in [("empty", lambda r: ""), ("whitespace", lambda r: "   \n  "),
                     ("repeated word", lambda r: " ".join(["the"] * 200)),
                     ("repeated sentence", lambda r: " ".join(["This is a sentence."] * 40)),
                     ("prompt restated", lambda r: r["prompt"])]:
        passed = {}
        for row in A.ROWS:
            res = A.grade_G(row, mk(row))
            for iid, ok in zip(row["instruction_id_list"], res):
                passed.setdefault(iid, [0, 0])
                passed[iid][0] += ok
                passed[iid][1] += 1
        out["content_free"][name] = {k: f"{a}/{b}" for k, (a, b) in sorted(passed.items()) if a}
    # metamorphic
    flips = {"crlf": [], "curly_apostrophe": [], "trailing_newline": []}
    for f in FIXTURES:
        if not f["label"]:
            continue
        kw, prompt = resolve(f, A.ROWS)
        if A.check_G(f["check"], kw, f["text"], prompt) is not True:
            continue
        edits = {"crlf": f["text"].replace("\n", "\r\n"),
                 "curly_apostrophe": f["text"].replace("'", "’"),
                 "trailing_newline": f["text"] + "\n"}
        for k, t in edits.items():
            if t == f["text"]:
                continue
            g = v(A.check_G, f["check"], kw, t, prompt)
            x = v(X.check, f["check"], kw, t, prompt, X.PROPOSED)
            if g is not True:
                flips[k].append({"fixture": f["id"], "G": g, "X_proposed": x})
    out["metamorphic"] = flips
    # harness: does one exception stop the per-prompt loop?
    row = dict(A.ROWS[275])  # custom:csv_quotes
    bad = '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t"Math"\t"A"\t"Fall"\t'
    out["harness"]["csv_quotes_empty_field"] = v(A.grade_G, row, bad)
    with open(os.path.join(W, "audit", "frozen", "stress.json"), "w", encoding="utf-8", newline="\n") as fo:
        json.dump(out, fo, indent=1, ensure_ascii=False)
    print("fuzz calls", n_calls, "exception keys", len(exc))
    for k, e in sorted(exc.items()):
        print("  ", k, e["count"], repr(e["text"][:80]))
    for k, d in out["content_free"].items():
        print("content-free", k, d)
    for k, l in flips.items():
        print("metamorphic", k, len(l), [x["fixture"] for x in l][:12])
    print("harness", out["harness"])


if __name__ == "__main__":
    main()
