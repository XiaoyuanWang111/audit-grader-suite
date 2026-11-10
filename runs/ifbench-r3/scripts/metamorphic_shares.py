"""Post-label: measure the share of panel verdicts that single findings change, by contract-neutral edits.

Each test applies to one check an edit that the contract ignores for that check and that removes
exactly the trigger of one finding (for example, deleting bold markers for F-subbullets-bold). A
grader verdict that changes under the edit is a verdict that the finding decides. The replacement's
flips are printed as a control: a neutral edit should change none of them.
Extraction failures are skipped. Output: printed table and audit/work/metamorphic_shares.json.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/metamorphic_shares.py
"""
import collections
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (os.path.join(W, "audit", "lib"), os.path.join(W, "audit", "replacement")):
    sys.path.insert(0, p)
import ifb  # noqa: E402
import ifbench_contract as rep  # noqa: E402

LETTER = r"[^\W\d_]"


def no_bold(t):
    return t.replace("**", "")


def no_markup_start(t):
    return re.sub(r"^[\s#>*_`]+", "", t.replace("**", "").replace("__", ""))


def collapse_blank_lines(t):
    return re.sub(r"\n[ \t]*\n+", "\n", t)


def straight_quotes(t):
    t = t.replace("“", '"').replace("”", '"')
    t = re.sub(rf"(?<={LETTER})’(?={LETTER})", "\0", t)  # keep apostrophes inside words
    t = t.replace("‘", "'").replace("’", "'")
    return t.replace("\0", "’")


def options_normal(t):
    return re.sub(r"\s+", " ", t).strip()


def lower_no_attached_punct(t):
    return re.sub(r"[^\w\s']", " ", t.lower())


def no_inword_apostrophe(t):
    return re.sub(rf"(?<={LETTER})['’](?={LETTER})", "", t)


def spaced_number_joins(t):
    return re.sub(r"(?<=\d)([-/:–])(?=\d)", r" \1 ", t)


TESTS = [
    ("F-subbullets-bold", "format:sub-bullets", no_bold, "fail_to_pass"),
    ("F-startverb-markup", "words:start_verb", no_markup_start, "fail_to_pass"),
    ("F-nbb-blank-line", "format:no_bullets_bullets", collapse_blank_lines, "fail_to_pass"),
    ("F-quotes-curly", "format:quotes", straight_quotes, "fail_to_pass"),
    ("F-quote-curly", "format:quote_unquote", straight_quotes, "pass_to_fail"),
    ("F-options-whitespace", "format:options", options_normal, "fail_to_pass"),
    ("F-conj-surface-forms", "count:conjunctions", lower_no_attached_punct, "pass_to_fail"),
    ("F-wordcount-contractions", "count:word_count_range", no_inword_apostrophe, "both"),
    ("F-title-contraction", "format:title_case", no_inword_apostrophe, "fail_to_pass"),
    ("F-numbers-joined", "count:numbers", spaced_number_joins, "both"),
]


def main():
    ifb.verify_pins()
    rows = ifb.load_rows()
    by_check = collections.defaultdict(list)
    for t in TESTS:
        by_check[t[1]].append(t)
    res = {t[0]: collections.Counter() for t in TESTS}
    for cfg, run, i, rec in ifb.iter_panel():
        if ifb.extraction_failure(rec):
            continue
        row = rows[i]
        resp = rec["response"]
        for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
            for fid, _, fn, _ in by_check.get(iid, []):
                c = res[fid]
                c["n"] += 1
                new = fn(resp)
                if new == resp:
                    continue
                c["edited"] += 1
                g0, _ = ifb.verdict("grader", iid, kw, row["prompt"], resp)
                g1, _ = ifb.verdict("grader", iid, kw, row["prompt"], new)
                if g0 != g1:
                    c["pass_to_fail" if g0 else "fail_to_pass"] += 1
                if rep.check(iid, kw, row["prompt"], resp) != rep.check(iid, kw, row["prompt"], new):
                    c["replacement_flips"] += 1
    print(f"{'finding':26s} {'check':28s} {'verdicts':>8s} {'edited':>6s} {'p->f':>5s} {'f->p':>5s} {'repl':>5s}  expected")
    for fid, iid, _, exp in TESTS:
        c = res[fid]
        print(f"{fid:26s} {iid:28s} {c['n']:8d} {c['edited']:6d} {c['pass_to_fail']:5d} {c['fail_to_pass']:5d} "
              f"{c['replacement_flips']:5d}  {exp}")
    with open(os.path.join(W, "audit", "work", "metamorphic_shares.json"), "w", encoding="utf-8") as fh:
        json.dump({k: dict(v) for k, v in res.items()}, fh, indent=1)


if __name__ == "__main__":
    main()
