"""Counterexamples cited in audit/AUDIT.md, with the verdicts the report states.

`python audit/scripts/report_cases.py`        prints a markdown table of every case
`python audit/scripts/report_cases.py check`  re-runs every case and fails loudly if a
                                              grader verdict differs from the report
Each fixture case is reproduced by
  .venv/Scripts/python.exe audit/scripts/verdict.py --fixture '<id>'
and each panel case by
  .venv/Scripts/python.exe audit/scripts/verdict.py --panel <folder> <run> <key>
"""
import sys

import common
import ref_runner
import replacement
from tests.fixtures_data import FIX

# finding id -> list of (fixture id, grader verdict the report states, reference verdict the report states)
CASES = {
    "F-CONJ": [("count:conjunctions#85e471f8", True, True)],
    "F-KWM": [("count:keywords_multiple#487922bc", False, True)],
    "F-NUM": [("count:numbers#57019ffa", False, False)],
    "F-CONTRACTION": [("count:word_count_range#7c51fcd2", False, False), ("ratio:stop_words#2cf31b94", False, False)],
    "F-STYPE": [("ratio:sentence_type#3738487b", True, True), ("ratio:sentence_type#389403cd", False, False)],
    "F-SBAL": [("ratio:sentence_balance#b7761e44", False, False)],
    "F-SWORDS": [("ratio:sentence_words#9bf12340", True, False)],
    "F-INDENT": [("format:line_indent#5ca22c1c", False, False), ("format:line_indent#3006987f", False, False)],
    "F-NEWLINE": [("format:newline#e5f78837", True, True), ("format:newline#07733d8b", False, False)],
    "F-LIST": [("format:list#2584034b", True, True), ("format:list#10c5eeb0", True, True)],
    "F-NBB": [("format:no_bullets_bullets#625c6237", False, False), ("format:no_bullets_bullets#d44d9892", False, False),
              ("format:no_bullets_bullets#653b564a", False, False), ("format:no_bullets_bullets#41d069e7", True, True)],
    "F-OPTIONS": [("format:options#927580bf", False, False), ("format:options#bf4d4ea8", False, False)],
    "F-TEMPLATE": [("format:output_template#3880c6d1", True, True), ("format:output_template#e6f2680a", True, True),
                   ("format:output_template#32aa85d6", True, True)],
    "F-PAREN": [("format:parentheses#9fc38630", True, True)],
    "F-QU": [("format:quote_unquote#9f008108", True, True), ("format:quote_unquote#278caa31", True, True)],
    "F-QUOTES": [("format:quotes#60347bc9", False, False)],
    "F-SUBB": [("format:sub-bullets#212d5ee1", True, True), ("format:sub-bullets#da21f6a4", True, True),
               ("format:sub-bullets#35b65fdf", False, False)],
    "F-THESIS": [("format:thesis#844e324a", True, True), ("format:thesis#8b0c3daa", False, False)],
    "F-TITLE": [("format:title_case#95beef7e", False, False), ("format:title_case#26d02f70", False, False)],
    "F-ALLIT": [("sentence:alliteration_increment#1a1b19f2", False, False), ("sentence:alliteration_increment#20fedc4e", True, True)],
    "F-CAPITALS": [("custom:european_capitals_sort#113de779", False, False)],
    "F-AFRICA": [("custom:reverse_newline#1d2258e7", True, True), ("custom:reverse_newline#1a03b821", False, False)],
    "F-ALPHA-SENT": [("custom:sentence_alphabet#cca075f6", False, True)],
    "F-CSVSPECIAL": [("custom:csv_special_character#be0ed161", True, True)],
    "F-EXC": [("custom:csv_quotes#1737bf8c", "IndexError", "IndexError")],
    "F-DATE": [("custom:date_format_list#443b4fe3", True, True)],
    "F-MCQ": [("custom:mcq_count_length#278fd6e3", True, True), ("custom:mcq_count_length#d7804689", False, False)],
    "F-RCHANGE": [("repeat:repeat_change#093afd81", True, True), ("repeat:repeat_change#a49f0741", True, True)],
    "F-RSPAN": [("repeat:repeat_span#88520227", False, True)],
    "F-VERB": [("words:start_verb#45b07647", False, False), ("words:start_verb#b16e7117", False, False)],
    "F-WPOS": [("words:words_position#0b054f68", False, True)],
    "F-MARKUP": [("count:person_names#44a20674", False, False), ("words:no_consecutive#6af2c5f4", False, False)],
}
# panel cases: (folder, run, key, check, grader verdict, replacement verdict)
PANEL = {
    "F-QUOTES": [("Qwen__Qwen3-8B", "sample8", "118", "format:quotes", True, False)],
    "F-SUBB": [("microsoft__phi-4", "sample0", "127", "format:sub-bullets", False, True)],
    "F-NBB": [("marin-community__marin-8b-instruct", "bi_greedy", "97", "format:no_bullets_bullets", False, True)],
    "F-PAREN": [("Qwen__Qwen3-32B", "greedy_shuffled", "110", "format:parentheses", True, False)],
    "F-VERB": [("mistralai__Mistral-Small-24B-Instruct-2501", "sample3", "257", "words:start_verb", False, True)],
}


def run(fn, f):
    kw, prompt = common.kwargs_for(f["key"], f["check"], f["kw"])
    try:
        return fn(f["check"], kw, prompt, f["response"])
    except Exception as e:  # noqa: BLE001
        return type(e).__name__


if __name__ == "__main__":
    fx = {f["id"]: f for f in FIX}
    mode = sys.argv[1] if len(sys.argv) > 1 else "table"
    bad = 0
    for fid, cases in CASES.items():
        for cid, g_exp, r_exp in cases:
            f = fx[cid]
            g, r, p = run(common.grade_grader, f), run(ref_runner.grade_reference, f), run(replacement.grade, f)
            ok = (g == g_exp) and (r == r_exp) and (str(p) == str(f["label"] == "pass"))
            if mode == "check":
                print(("OK  " if ok else "BAD ") + f"{fid:<14} {cid:<44} grader={g} reference={r} replacement={p} label={f['label']}")
                bad += not ok
            else:
                print(f"| {fid} | `{cid}` | `{ascii(f['response'])}` | {f['label']} | {g} | {r} |")
    for fid, cases in PANEL.items():
        for folder, run_, key, check, g_exp, p_exp in cases:
            import json
            rec = json.loads((common.CASE / "panel" / folder / f"{run_}.jsonl").read_text(encoding="utf-8").splitlines()[common.row_list().index(key)])
            kw, prompt = common.kwargs_for(key, check)
            g = common.grade_grader(check, kw, prompt, rec["response"])
            p = replacement.grade(check, kw, prompt, rec["response"])
            ok = g == g_exp and p == p_exp
            if mode == "check":
                print(("OK  " if ok else "BAD ") + f"{fid:<14} panel {folder}/{run_} key {key} {check} grader={g} replacement={p}")
                bad += not ok
    if mode == "check":
        print("mismatches:", bad)
        sys.exit(1 if bad else 0)
