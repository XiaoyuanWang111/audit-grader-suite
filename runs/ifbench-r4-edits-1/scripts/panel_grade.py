"""Step 5: grade every stored panel response with every grader.

For each run file, writes audit/work/panel/<folder>__<run>.jsonl with one line
per response: per-instruction verdicts of grader strict/loose (grader.py
harness functions), reference strict/loose (evaluation_lib functions, strict
then loose on the same input object, as run_eval does), and the replacement
under the proposed readings plus each measured alternative reading (stored
only where it differs). Exceptions are recorded, not raised (in a real run one
exception stops the run; see AUDIT.md). Resumable: existing outputs are kept.

Graded text: the panel `response` (text after the last </think>, leading
whitespace removed). For a thinking-on completion with no </think> the
contract has no answer (extraction failure): the replacement fails every
check; the grader and reference are given `response` as Evalchemy would
receive it if it used the panel's rule (the whole completion).

Usage: python audit/scripts/panel_grade.py [workers]
"""
import json
import multiprocessing as mp
import sys
import traceback

import common

OUT = common.W / "audit" / "work" / "panel"

ALL = None  # all checks
WORDISH = {"count:conjunctions", "count:keywords_multiple", "count:person_names", "count:pronouns", "count:unique_word_count",
           "count:word_count_range", "count:words_japanese", "format:newline", "format:title_case", "ratio:stop_words",
           "ratio:sentence_words", "repeat:repeat_change", "sentence:increment", "sentence:alliteration_increment",
           "words:alphabet", "words:consonants", "words:keywords_specific_position", "words:last_first",
           "words:no_consecutive", "words:odd_even_syllables", "words:palindrome", "words:paragraph_last_first",
           "words:prime_lengths", "words:repeats", "words:vowel", "words:words_position", "custom:word_reverse",
           "custom:sentence_alphabet"}
SENT = {"custom:sentence_alphabet", "format:emoji", "ratio:sentence_balance", "ratio:sentence_type", "ratio:sentence_words",
        "sentence:alliteration_increment", "sentence:increment", "sentence:keyword", "words:keywords_specific_position",
        "words:last_first", "format:no_bullets_bullets", "custom:character_reverse"}
LETTER = {"words:alphabet", "words:consonants", "words:no_consecutive", "words:odd_even_syllables", "words:palindrome",
          "words:prime_lengths", "words:vowel", "format:title_case", "custom:sentence_alphabet",
          "sentence:alliteration_increment", "count:words_japanese"}
ALTS = [
    ("D-strip-ends", "keep", ALL), ("D-word", "whitespace", WORDISH), ("D-word-numbers", "include", LETTER),
    ("D-sentence", "punct", SENT), ("D-paragraph", "line", {"words:vowel", "format:thesis"}),
    ("D-keyword-match", "inflect", {"count:keywords_multiple", "sentence:keyword"}),
    ("D-count-exact", "atleast", {"count:keywords_multiple"}), ("D-number", "digits+words", {"count:numbers"}),
    ("D-name-case", "insensitive", {"count:person_names"}), ("D-pronoun-set", "broad", {"count:pronouns"}),
    ("D-punct-set", "short", {"count:punctuation"}), ("D-punct-set", "long", {"count:punctuation"}),
    ("D-unique-case", "sensitive", {"count:unique_word_count"}), ("D-between", "exclusive", {"count:word_count_range"}),
    ("D-reverse-extra", "allow", {"custom:character_reverse", "custom:word_reverse"}),
    ("D-csv-rows", "lines", {"custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"}),
    ("D-csv-wrapper", "only", {"custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"}),
    ("D-csv-header-quoted", "data", {"custom:csv_quotes"}), ("D-special-char", "any", {"custom:csv_special_character"}),
    ("D-csv-one-field", "exactly", {"custom:csv_special_character"}), ("D-date-extra", "allow", {"custom:date_format_list"}),
    ("D-capitals-set", "astana", {"custom:european_capitals_sort"}), ("D-capitals-set", "nomoscow", {"custom:european_capitals_sort"}),
    ("D-capitals-complete", "order", {"custom:european_capitals_sort"}), ("D-mcq-length", "words", {"custom:mcq_count_length"}),
    ("D-multiples-extra", "numbers-only", {"custom:multiples"}), ("D-africa-complete", "order", {"custom:reverse_newline"}),
    ("D-list-intro", "allow", {"custom:reverse_newline"}), ("D-emoji-position", "last", {"format:emoji"}),
    ("D-indent-step", "constant", {"format:line_indent"}), ("D-indent-min", "one", {"format:line_indent"}),
    ("D-list-sep", "prefix", {"format:list"}), ("D-list-intro-sep", "none", {"format:list"}),
    ("D-whitespace-set", "ascii", {"format:no_whitespace"}), ("D-options-text", "label", {"format:options"}),
    ("D-options-text", "exact", {"format:options"}), ("D-punct-set", "grader6", {"count:punctuation"}),
    ("D-template-markup", "plain", {"format:output_template"}), ("D-paren-types", "all3", {"format:parentheses"}),
    ("D-quotes-start", "double", {"format:quotes"}), ("D-subbullet-indent", "yes", {"format:sub-bullets"}),
    ("D-plural", "two", {"format:sub-bullets"}), ("D-italic-tag", "i", {"format:thesis"}), ("D-section", "whole", {"format:thesis"}),
    ("D-title-minor", "lower", {"format:title_case"}), ("D-overlap-def", "reference", {"ratio:overlap"}),
    ("D-overlap-def", "jaccard", {"ratio:overlap"}), ("D-overlap-def", "char", {"ratio:overlap"}),
    ("D-overlap-tol", "relative", {"ratio:overlap"}), ("D-balanced", "equal", {"ratio:sentence_balance"}),
    ("D-sentence-type", "exclude", {"ratio:sentence_balance", "ratio:sentence_type"}),
    ("D-char-count", "letters", {"ratio:sentence_words"}), ("D-different-words", "across", {"ratio:sentence_words"}),
    ("D-repeat-format", "loose", {"repeat:repeat_simple"}), ("D-span-base", "1", {"repeat:repeat_span"}),
    ("D-alphabet-start", "a", {"words:alphabet"}), ("D-consonant-y", "vowel", {"words:consonants"}),
    ("D-palindrome-distinct", "occurrences", {"words:palindrome"}), ("D-paragraph-newline", "blank", {"words:paragraph_last_first"}),
    ("D-repeats-count", "repeats", {"words:repeats"}), ("D-verb-context", "can-be", {"words:start_verb"}),
    ("D-vowel-scope", "word", {"words:vowel"}), ("D-vowel-paragraph", "many", {"words:vowel"}),
]
HELD_OUT = {"sample7", "greedy_repeat__thinking"}


def held_out(folder, run):
    return run == "sample7" or (folder.endswith("__thinking") and run == "greedy_repeat")


def work(path):
    import copy
    import evaluation_lib as EL
    import replacement as R
    from IFBench import grader as G
    path = common.pathlib.Path(path)
    folder, run = path.parent.name, path.stem
    out = OUT / f"{folder}__{run}.jsonl"
    if out.exists():
        return str(out), "kept"
    rows = common.rows()
    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    res = []
    for rec in lines:
        r = rows[str(rec["key"])]
        resp = rec["response"]
        xfail = folder.endswith("__thinking") and "</think>" not in rec["raw_response"]
        p2r = {r["prompt"]: resp}
        ent = dict(key=r["key"], truncated=rec["finish_reason"] == "length", extraction_failure=xfail, checks=[])
        gs = gl = rs = rl = None
        err = {}
        inp = G.InputExample(key=int(r["key"]), instruction_id_list=r["instruction_id_list"], prompt=r["prompt"], kwargs=copy.deepcopy(r["kwargs"]))
        try:
            gs = G.test_instruction_following_strict(inp, p2r).follow_instruction_list
        except Exception as e:  # noqa: BLE001
            err["grader_strict"] = type(e).__name__ + ": " + str(e)[:80]
        try:
            gl = G.test_instruction_following_loose(inp, p2r).follow_instruction_list
        except Exception as e:  # noqa: BLE001
            err["grader_loose"] = type(e).__name__ + ": " + str(e)[:80]
        einp = EL.InputExample(key=r["key"], instruction_id_list=list(r["instruction_id_list"]), prompt=r["prompt"], kwargs=copy.deepcopy(r["kwargs"]))
        try:
            rs = EL.test_instruction_following_strict(einp, p2r).follow_instruction_list
        except Exception as e:  # noqa: BLE001
            err["reference_strict"] = type(e).__name__ + ": " + str(e)[:80]
            einp.kwargs = [{k: v for k, v in kw.items() if v is not None} for kw in einp.kwargs]
        try:
            rl = EL.test_instruction_following_loose(einp, p2r).follow_instruction_list
        except Exception as e:  # noqa: BLE001
            err["reference_loose"] = type(e).__name__ + ": " + str(e)[:80]
        for i, (check, kw) in enumerate(zip(r["instruction_id_list"], r["kwargs"])):
            c = dict(check=check, gs=None if gs is None else gs[i], gl=None if gl is None else gl[i],
                     rs=None if rs is None else rs[i], rl=None if rl is None else rl[i])
            if xfail:
                c["rep"] = False
            else:
                try:
                    c["rep"] = R.grade(check, kw, r["prompt"], resp)
                except Exception as e:  # noqa: BLE001
                    c["rep"] = None
                    err["replacement"] = type(e).__name__ + ": " + str(e)[:80]
                alts = {}
                for entry, val, checks in ALTS:
                    if checks is not None and check not in checks:
                        continue
                    try:
                        v = R.grade(check, kw, r["prompt"], resp, {entry: val})
                    except Exception:  # noqa: BLE001
                        v = None
                    if v != c["rep"]:
                        alts[f"{entry}={val}"] = v
                if alts:
                    c["alts"] = alts
            ent["checks"].append(c)
        if err:
            ent["errors"] = err
        res.append(ent)
    tmp = out.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in res) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(out)
    return str(out), "done"


def safe(path):
    try:
        return work(path)
    except Exception:  # noqa: BLE001
        return str(path), "FAILED " + traceback.format_exc()[-400:]


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(str(p) for p in (common.CASE / "panel").glob("*/*.jsonl"))
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    with mp.Pool(n) as pool:
        for i, (p, status) in enumerate(pool.imap_unordered(safe, files), 1):
            print(f"{i}/{len(files)} {status[:300]} {p}", flush=True)
