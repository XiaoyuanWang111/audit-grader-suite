"""Post-label metamorphic tests on the stored panel for two defects found while explaining review cases.

1. HTML tags (contract G5: HTML tags are formatting; they are not words and do not create or
   join sentences). For every stored response that contains an HTML tag, remove every tag and
   grade again, for every check except format:thesis (which asks for HTML) and the
   character-level checks. A verdict that changes is a G5 violation of that grader.
2. Flag emoji (format:emoji: "a Unicode emoji character or sequence"). For every stored response
   that contains a flag (two regional-indicator characters), replace each flag with U+1F389
   (party popper) and grade format:emoji again. A verdict that changes means the grader does not
   take a flag as an emoji.
Extraction failures are skipped. Grader = strict function of the grader under audit; replacement =
proposed readings.
Output: printed counts per check and audit/work/metamorphic_post.json.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/metamorphic_post.py
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

TAG = re.compile(r"</?[A-Za-z][^>]*>")
FLAG = re.compile("[\U0001F1E6-\U0001F1FF]{2}")
SKIP_HTML = {"format:thesis", "format:no_whitespace", "ratio:sentence_words", "custom:csv_city", "custom:csv_quotes",
             "custom:csv_special_character", "repeat:repeat_change", "repeat:repeat_simple", "repeat:repeat_span"}


def main():
    ifb.verify_pins()
    rows = ifb.load_rows()
    res = {"html": collections.defaultdict(collections.Counter), "flag": collections.defaultdict(collections.Counter)}
    examples = {"html": {}, "flag": {}}
    for cfg, run, i, rec in ifb.iter_panel():
        if ifb.extraction_failure(rec):
            continue
        resp = rec["response"]
        has_tag, has_flag = bool(TAG.search(resp)), bool(FLAG.search(resp))
        if not (has_tag or has_flag):
            continue
        row = rows[i]
        for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
            tests = []
            if has_tag and iid not in SKIP_HTML:
                tests.append(("html", TAG.sub("", resp)))
            if has_flag and iid == "format:emoji":
                tests.append(("flag", FLAG.sub("\U0001F389", resp)))
            for name, new in tests:
                c = res[name][iid]
                g0, _ = ifb.verdict("grader", iid, kw, row["prompt"], resp)
                g1, _ = ifb.verdict("grader", iid, kw, row["prompt"], new)
                p0 = rep.check(iid, kw, row["prompt"], resp)
                p1 = rep.check(iid, kw, row["prompt"], new)
                c["n"] += 1
                if g0 != g1:
                    c["grader_flips"] += 1
                    c["grader_" + ("pass_to_fail" if g0 else "fail_to_pass")] += 1
                    examples[name].setdefault(iid, f"{cfg}/{run} key {row['key']}")
                if p0 != p1:
                    c["replacement_flips"] += 1
    out = {k: {i: dict(c) for i, c in v.items()} for k, v in res.items()}
    out["examples"] = examples
    for name in ("html", "flag"):
        tot = collections.Counter()
        print(f"\n{name}: verdicts tested, grader flips (pass to fail / fail to pass), replacement flips")
        for iid, c in sorted(res[name].items(), key=lambda kv: -kv[1]["grader_flips"]):
            tot.update(c)
            if c["grader_flips"] or c["replacement_flips"]:
                print(f"  {iid:34s} n={c['n']:5d} grader {c['grader_flips']:4d} ({c['grader_pass_to_fail']}/{c['grader_fail_to_pass']}) "
                      f"replacement {c['replacement_flips']:4d}   e.g. {examples[name].get(iid, '')}")
        print(f"  total n={tot['n']} grader flips {tot['grader_flips']} replacement flips {tot['replacement_flips']}")
    with open(os.path.join(W, "audit", "work", "metamorphic_post.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
