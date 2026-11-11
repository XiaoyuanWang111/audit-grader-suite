"""Step 4: metamorphic edits, fuzzing, content-free responses. Writes audit/out/step4.json and prints a summary.

1. Metamorphic: each passing fixture (label True) gets every edit that its check's contract ignores; a grader
   whose verdict changes from pass to fail (or whose verdict differs from the replacement) is counted per check
   and edit. The replacement's own verdict on each edited response is also checked (it must stay pass).
2. Fuzz: 1,000 random texts per check (with kwargs from the data), counting raised exceptions per grader.
   NVIDIA's language checks catch langdetect's exception and return True; those silent passes are counted too.
3. Content-free responses on all 11,817 rows: empty text, a repeated sentence, and the prompt itself.
"""
import collections
import json
import os
import random
import re
import sys
from concurrent.futures import ProcessPoolExecutor

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(AUDIT)
sys.path.insert(0, AUDIT)
sys.path.insert(0, os.path.join(AUDIT, "tests"))

# ------------------------------------------------------------------ edits

def _lines(fn):
    def edit(t):
        return "\n".join(fn(i, line) if line.strip() else line for i, line in enumerate(t.split("\n")))
    return edit


def _word(t, which, fmt):
    ms = list(re.finditer(r"[^\W_]+(?:['’\-][^\W_]+)*", t))
    if not ms:
        return None
    m = ms[0] if which == "first" else ms[-1]
    return t[:m.start()] + fmt(m.group(0)) + t[m.end():]


EDITS = {
    "numbered_label": _lines(lambda i, l: f"{i + 1}. {l}"),
    "bullet_dash": _lines(lambda i, l: f"- {l}"),
    "bold_first_word": lambda t: _word(t, "first", lambda w: f"**{w}**"),
    "bold_last_word": lambda t: _word(t, "last", lambda w: f"**{w}**"),
    "italic_first_word": lambda t: _word(t, "first", lambda w: f"*{w}*"),
    "html_first_word": lambda t: _word(t, "first", lambda w: f"<b>{w}</b>"),
    "typo_quotes_first_word": lambda t: _word(t, "first", lambda w: f"“{w}”"),
    "typo_apostrophe": lambda t: t.replace("'", "’") if "'" in t else None,
    "punct_after_first_word": lambda t: _word(t, "first", lambda w: f"{w};"),
    "blank_line_between_lines": lambda t: "\n\n".join(t.split("\n")) if "\n" in t.strip() else None,
    "trailing_newline": lambda t: t + "\n",
}
LINE_EDITS = {"numbered_label", "bullet_dash", "blank_line_between_lines"}
WORD_EDITS = {"bold_first_word", "bold_last_word", "italic_first_word", "html_first_word", "typo_quotes_first_word",
              "punct_after_first_word"}

# edits the contract does NOT ignore, per check
NOT_IGNORED = collections.defaultdict(set)
for c in ("detectable_format:number_bullet_lists",):
    NOT_IGNORED[c] |= {"numbered_label", "bullet_dash"}
for c in ("paragraphs:paragraphs2", "length_constraints:nth_paragraph_first_word"):
    NOT_IGNORED[c] |= {"blank_line_between_lines"}
for c in ("length_constraints:number_paragraphs", "paragraphs:paragraphs", "count:counting_composition",
          "combination:two_responses", "detectable_format:multiple_sections"):
    NOT_IGNORED[c] |= LINE_EDITS  # a prefix on a divider or marker line changes it
for c in ("detectable_format:number_highlighted_sections",):
    NOT_IGNORED[c] |= {"bold_first_word", "bold_last_word", "italic_first_word", "bullet_dash"}
for c in ("detectable_format:json_format", "detectable_format:constrained_response", "startend:quotation",
          "detectable_format:square_brackets", "detectable_format:bigram_wrapping", "count:count_unique"):
    NOT_IGNORED[c] |= LINE_EDITS | WORD_EDITS | {"typo_apostrophe"}
for c in ("punctuation:punctuation_dot",):
    NOT_IGNORED[c] |= {"numbered_label"}
for c in ("punctuation:no_comma", "punctuation:punctuation_dot", "punctuation:punctuation_exclamation"):
    NOT_IGNORED[c] |= set()
for c in ("keywords:start_end", "startend:end_checker", "last_word:last_word_answer"):
    NOT_IGNORED[c] |= {"bold_last_word"} if c == "keywords:start_end" else set()
for c in ("length_constraints:number_words", "keywords:no_adjacent_consecutive", "count:lowercase_counting",
          "keywords:palindrome", "change_case:capital_word_frequency", "keywords:keyword_specific_position",
          "first_word:first_word_sent", "last_word:last_word_sent", "length_constraints:number_sentences",
          "detectable_format:sentence_hyphens"):
    NOT_IGNORED[c] |= {"numbered_label", "bullet_dash"}  # labels add words or sentences
NOT_IGNORED["detectable_format:sentence_hyphens"] |= {"blank_line_between_lines", "punct_after_first_word"}
NOT_IGNORED["length_constraints:number_sentences"] |= {"blank_line_between_lines"}
NOT_IGNORED["first_word:first_word_sent"] |= {"blank_line_between_lines"}
NOT_IGNORED["last_word:last_word_sent"] |= {"blank_line_between_lines"}
NOT_IGNORED["keywords:keyword_specific_position"] |= {"blank_line_between_lines"}
NOT_IGNORED["change_case:english_capital"] |= {"html_first_word"}  # adds lowercase letters
NOT_IGNORED["change_case:capital_word_frequency"] |= {"html_first_word"}
NOT_IGNORED["keywords:letter_frequency"] |= {"html_first_word"}
NOT_IGNORED["letters:letter_counting2"] |= {"html_first_word"}
NOT_IGNORED["letters:letter_counting"] |= LINE_EDITS | WORD_EDITS
NOT_IGNORED["punctuation:no_comma"] |= set()


def metamorphic():
    from fixtures_data import FIXTURES
    from verdicts import GRADERS, verdict

    out = collections.defaultdict(lambda: collections.Counter())
    examples = {}
    for f in FIXTURES:
        if not f["label"]:
            continue
        base = {g: verdict(g, f["check"], f["kwargs"], f["response"]) for g in GRADERS}
        for name, fn in EDITS.items():
            if name in NOT_IGNORED[f["check"]]:
                continue
            edited = fn(f["response"])
            if edited is None or edited == f["response"]:
                continue
            key = f"{f['check']} | {name}"
            out[key]["n"] += 1
            contract = verdict("replacement", f["check"], f["kwargs"], edited)
            if contract is not True:
                # the replacement says the edit changes the verdict: the edit is not ignored for this response
                out[key]["edit_not_ignored"] += 1
                continue
            out[key]["n_ignored"] += 1
            for g in GRADERS:
                v = verdict(g, f["check"], f["kwargs"], edited)
                if v is None:
                    continue
                if v is not True:
                    out[key][g + "_fails_edited_pass"] += 1
                    if base[g] is True:
                        out[key][g + "_flipped"] += 1
                        examples.setdefault(f"{g} | {key}", {"fixture": f["id"], "edited": edited})
    return {k: dict(v) for k, v in out.items()}, examples


# ------------------------------------------------------------------ fuzz

ALPH = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") * 3 + list(
    " \n\n\t.,!?;:-*_#<>[]\"'`()/\\{}|~") * 2 + list("éüßñçøİıЖжд中文日本語한국어ابت’“”…。，\U0001F600")


def fuzz_check(args):
    import harness
    import replacement as R

    harness.setup()
    iid, kwargs_pool, n, seed = args
    rng = random.Random(seed)
    counts = collections.Counter()
    first = {}
    import langdetect
    real_detect = langdetect.detect
    silent = {"n": 0}

    def counting_detect(text):
        try:
            return real_detect(text)
        except langdetect.LangDetectException:
            silent["n"] += 1
            raise
    for _ in range(n):
        kw = rng.choice(kwargs_pool)
        length = rng.choice([0, 1, 2, 5, 20, 80, 200])
        text = "".join(rng.choice(ALPH) for _ in range(length))
        langdetect.detect = counting_detect
        before = silent["n"]
        passed, err = harness.skyrl_constraint(iid, kw, text)
        langdetect.detect = real_detect
        if err:
            counts["nvidia_exception"] += 1
            first.setdefault("nvidia", (text, err))
        if silent["n"] > before and passed:
            counts["nvidia_langdetect_exception_counted_pass"] += 1
        if iid not in harness.SEMANTIC:
            v, detail = harness.verifyit_constraint(iid, kw, text)
            if detail.startswith("EXC"):
                counts["verifyit_exception"] += 1
                first.setdefault("verifyit", (text, detail))
        try:
            R.check(iid, kw, text)
        except Exception as e:  # noqa: BLE001
            counts["replacement_exception"] += 1
            first.setdefault("replacement", (text, repr(e)))
        counts["n"] += 1
    return iid, dict(counts), {k: [v[0][:80], v[1][:120]] for k, v in first.items()}


# ------------------------------------------------------------------ content-free

def content_free_chunk(rows):
    import harness
    import replacement as R

    harness.setup()
    res = []
    for rec in rows:
        texts = {"empty": "", "repeated": "This is my answer. " * 30, "prompt_restated": rec["prompt"]}
        item = {"ids": rec["instruction_id_list"]}
        for name, t in texts.items():
            random.seed(0)
            sky = harness.skyrl_row(t, rec)
            cur = harness.verifyit_row(t, rec)
            repl = [R.check(i, k, R.graded_text(t, False)) for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
            item[name] = {"skyrl_reward": sky["reward"], "skyrl_infra": sky["infra_error"], "nvidia": sky["results"],
                          "verifyit": cur["results"], "gate": cur["gate_pass"], "repl": repl}
        res.append(item)
    return res


def main():
    summary = {}
    meta, examples = metamorphic()
    summary["metamorphic"] = meta
    summary["metamorphic_examples"] = examples

    rows = []
    with open(os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rows.append(json.loads(row["extra_info"]["nemotron_ultra"]["record_json"]))
    pools = collections.defaultdict(list)
    for rec in rows:
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            if len(pools[iid]) < 200:
                pools[iid].append(kw)
    with ProcessPoolExecutor(4) as pool:
        fz = list(pool.map(fuzz_check, [(iid, pools[iid], 1000, k) for k, iid in enumerate(sorted(pools))]))
        summary["fuzz"] = {iid: {"counts": c, "first": f} for iid, c, f in fz}
        chunks = [rows[i:i + 300] for i in range(0, len(rows), 300)]
        cf = [x for part in pool.map(content_free_chunk, chunks) for x in part]
    agg = {}
    for name in ("empty", "repeated", "prompt_restated"):
        a = collections.Counter()
        per = collections.defaultdict(lambda: collections.Counter())
        for item in cf:
            r = item[name]
            a["rows"] += 1
            a["skyrl_reward_1"] += r["skyrl_reward"] == 1.0
            a["skyrl_infra"] += r["skyrl_infra"]
            a["gate_pass"] += r["gate"]
            a["repl_all_pass"] += all(r["repl"])
            for i, iid in enumerate(item["ids"]):
                per[iid]["n"] += 1
                per[iid]["nvidia_pass"] += r["nvidia"][i]
                per[iid]["verifyit_pass"] += bool(r["verifyit"][i])
                per[iid]["repl_pass"] += r["repl"][i]
        agg[name] = {"rows": dict(a), "per_check": {k: dict(v) for k, v in sorted(per.items())}}
    summary["content_free"] = agg
    with open(os.path.join(AUDIT, "out", "step4.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(json.dumps({"content_free_rows": {k: v["rows"] for k, v in agg.items()}}, indent=1))
    print("fuzz exceptions:")
    for iid, v in summary["fuzz"].items():
        c = v["counts"]
        if any(k != "n" for k in c):
            print(" ", iid, c, v["first"])
    print("metamorphic flips:")
    for k, v in sorted(meta.items()):
        flips = {g: v.get(g + "_flipped", 0) for g in ("nvidia", "verifyit", "replacement")}
        if any(flips.values()):
            print(" ", k, v["n"], flips)


if __name__ == "__main__":
    main()
