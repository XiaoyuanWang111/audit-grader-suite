"""Step 4 stress tests: metamorphic edits, fuzzing, content-free responses, loose-transform probes.

Writes audit/frozen/stress_results.json and prints summary tables.
"""
import json
import random
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parent))
import harness as H  # noqa: E402
from replacement import contract_grader as R  # noqa: E402

rows = H.load_rows()
inst = []  # (row, idx, iid, kwargs)
for r in rows:
    for i, (iid, kw) in enumerate(zip(r["instruction_id_list"], r["kwargs"])):
        inst.append((r, i, iid, kw))


def g(iid, kw, resp, prompt):
    try:
        return "1" if H.check_grader(iid, kw, resp, prompt) else "0"
    except Exception as e:  # noqa: BLE001
        return "E:" + type(e).__name__


def rp(iid, kw, resp, prompt):
    try:
        return "1" if R.check(iid, kw, resp, prompt) else "0"
    except Exception as e:  # noqa: BLE001
        return "E:" + type(e).__name__


# ------------------------------------------------------------------ metamorphic edits
import re


def _first_word_span(line):
    """Span of the first word outside HTML tags."""
    masked = re.sub(r"</?[A-Za-z][^<>]{0,40}>", lambda m: " " * len(m.group(0)), line)
    m = re.search(r"(?<![A-Za-z'])[A-Za-z][A-Za-z']*", masked)
    return m.span() if m else None


def e_bullets(t):
    return "\n".join(("- " + ln) if ln.strip() else ln for ln in t.split("\n"))


def e_numbers(t):
    k = 0
    out = []
    for ln in t.split("\n"):
        if ln.strip():
            k += 1
            out.append(f"{k}. {ln}")
        else:
            out.append(ln)
    return "\n".join(out)


def _wrap_first_word(t, left, right):
    sp = _first_word_span(t)
    if not sp:
        return t
    a, b = sp
    return t[:a] + left + t[a:b] + right + t[b:]


def e_bold(t):
    return _wrap_first_word(t, "**", "**")


def e_italic_html(t):
    return _wrap_first_word(t, "<b>", "</b>")


def e_typo_quotes(t):
    return _wrap_first_word(t, "“", "”")


def e_typo_apostrophe(t):
    return re.sub(r"(?<=[A-Za-z])'(?=[A-Za-z])", "’", t)


def e_comma_after_first(t):
    sp = _first_word_span(t)
    if not sp:
        return t
    return t[:sp[1]] + "," + t[sp[1]:]


def e_blank_lines(t):
    return re.sub(r"\n(?!\n)", "\n\n", t)


def e_trailing_newline(t):
    return t + "\n"


EDITS = {
    "bullet": e_bullets, "numbered": e_numbers, "bold": e_bold, "html_b": e_italic_html,
    "typo_quotes": e_typo_quotes, "typo_apostrophe": e_typo_apostrophe, "comma_after_word": e_comma_after_first,
    "blank_line": e_blank_lines, "trailing_newline": e_trailing_newline,
}
# checks whose contract does NOT ignore the edit (excluded from that edit)
LINE_CHECKS = {"format:line_indent", "format:newline", "format:sub-bullets", "format:no_bullets_bullets", "format:list",
               "format:thesis", "custom:csv_city", "custom:csv_quotes", "custom:csv_special_character",
               "custom:reverse_newline", "custom:mcq_count_length", "words:paragraph_last_first", "words:vowel",
               "format:output_template", "format:no_whitespace"}
EXACT = {"repeat:repeat_change", "repeat:repeat_simple", "repeat:repeat_span", "custom:character_reverse",
         "custom:word_reverse", "custom:multiples", "custom:date_format_list", "custom:european_capitals_sort",
         "format:options", "ratio:overlap", "ratio:sentence_words"}
EXCLUDE = {
    "bullet": LINE_CHECKS | EXACT | {"count:punctuation"},
    "numbered": LINE_CHECKS | EXACT | {"count:numbers", "count:punctuation"},
    "bold": EXACT | {"format:sub-bullets", "format:no_bullets_bullets", "format:list", "format:thesis", "custom:csv_city",
                     "custom:csv_quotes", "custom:csv_special_character", "custom:reverse_newline",
                     "custom:mcq_count_length", "count:punctuation"},
    "html_b": EXACT | {"format:thesis", "custom:csv_city", "custom:csv_quotes", "custom:csv_special_character",
                       "custom:reverse_newline", "custom:mcq_count_length", "count:punctuation", "format:parentheses"},
    "typo_quotes": EXACT | {"format:quotes", "format:quote_unquote", "count:punctuation", "custom:csv_city",
                            "custom:csv_quotes", "custom:csv_special_character", "custom:reverse_newline",
                            "custom:mcq_count_length", "format:output_template"},
    "typo_apostrophe": EXACT | {"format:quotes", "format:quote_unquote", "custom:csv_city", "custom:csv_quotes",
                                "custom:csv_special_character"},
    "comma_after_word": EXACT | {"count:punctuation", "custom:csv_city", "custom:csv_quotes", "custom:csv_special_character",
                                 "custom:reverse_newline", "custom:mcq_count_length", "format:output_template",
                                 "format:options"},
    "blank_line": EXACT | {"format:no_whitespace", "format:thesis", "words:vowel", "custom:csv_city", "custom:csv_quotes",
                           "custom:csv_special_character", "custom:mcq_count_length", "format:newline",
                           "format:no_bullets_bullets", "format:line_indent"},
    "trailing_newline": set(),
}


def load_panel_passes(per_check=12, seed=0):
    """Panel responses that both the grader and the replacement pass, per check (non-held-out files)."""
    import csv
    import gzip

    THINK = ("Qwen__Qwen3-8B__thinking", "Qwen__Qwen3-14B__thinking")
    cand = defaultdict(list)
    for r in csv.DictReader(gzip.open(H.W / "audit/frozen/panel_verdicts.tsv.gz", "rt", encoding="utf-8"), delimiter="\t"):
        if r["g_strict"] == "1" and r["rep"] == "1" and r["unclosed"] == "0" and \
                r["run"] != ("greedy_repeat" if r["config"] in THINK else "sample0"):
            cand[r["iid"]].append(r)
    rnd = random.Random(seed)
    out = {}
    cache = {}
    for iid, lst in cand.items():
        rnd.shuffle(lst)
        picked = []
        seen = set()
        for r in lst:
            if (r["key"], r["config"]) in seen:
                continue
            seen.add((r["key"], r["config"]))
            f = H.CASE / "panel" / r["config"] / f"{r['run']}.jsonl"
            if f not in cache:
                cache[f] = {json.loads(l)["key"]: json.loads(l)["response"] for l in f.read_text(encoding="utf-8").splitlines()}
            picked.append((r["key"], int(r["idx"]), cache[f][r["key"]]))
            if len(picked) >= per_check:
                break
        out[iid] = picked
    return out


def metamorphic():
    passes = load_panel_passes()
    by_key = {str(r["key"]): r for r in rows}
    table = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))  # edit -> check -> [n, grader flips, replacement flips]
    examples = defaultdict(list)
    for iid, items in passes.items():
        for key, idx, resp in items:
            row = by_key[key]
            kw = row["kwargs"][idx]
            for ename, fn in EDITS.items():
                if iid in EXCLUDE[ename]:
                    continue
                new = fn(resp)
                if new == resp:
                    continue
                gv, rv = g(iid, kw, new, row["prompt"]), rp(iid, kw, new, row["prompt"])
                cell = table[ename][iid]
                cell[0] += 1
                if gv != "1":
                    cell[1] += 1
                    if len(examples[(ename, iid)]) < 2:
                        examples[(ename, iid)].append(key)
                if rv != "1":
                    cell[2] += 1
    return table, examples


# ------------------------------------------------------------------ fuzzing
ALPH = (list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + list(" \n\t.,;:!?'\"()[]{}*-_#<>/\\|`~@$%^&+=")
        + ["“", "”", "‘", "’", "—", "…", " ", "​", "﻿", "\U0001F600",
           "\U0001F1FA\U0001F1F8", "1️⃣", "寿", "ラ", "é", "́", "‮", "\r", "\x00"])


def fuzz(n_per_check=300, seed=10060):
    rnd = random.Random(seed)
    exc = Counter()
    exc_examples = {}
    exc_r = Counter()
    by_iid = defaultdict(list)
    for r, i, iid, kw in inst:
        by_iid[iid].append((r, kw))
    total = 0
    for iid, lst in sorted(by_iid.items()):
        for k in range(n_per_check):
            r, kw = lst[k % len(lst)]
            L = rnd.choice([1, 2, 3, 5, 10, 40, 200, 1000])
            mode = rnd.random()
            if mode < 0.6:
                s = "".join(rnd.choice(ALPH) for _ in range(L))
            elif mode < 0.8:  # structured: lines of words with tabs / empty fields
                s = "\n".join("\t".join(rnd.choice(['"a"', "", "b", '""', "“c”", "1"]) for _ in range(rnd.randint(1, 6)))
                              for _ in range(rnd.randint(1, 5)))
            else:
                s = rnd.choice(["", " ", "\n", ".", "?!", "* ", "- ", "\"", "'", "(", ")", "<i>", "</i>", "Question",
                                "\t\t", "a\t\t", "​", "1.", "My Answer:"]) * rnd.randint(1, 5)
            total += 1
            v = g(iid, kw, s, r["prompt"])
            if v.startswith("E"):
                exc[(iid, v)] += 1
                exc_examples.setdefault((iid, v), s[:80])
            v2 = rp(iid, kw, s, r["prompt"])
            if v2.startswith("E"):
                exc_r[(iid, v2)] += 1
    # also run the whole strict and loose harness on each fuzz-like input for one prompt per check
    return total, exc, exc_examples, exc_r


# ------------------------------------------------------------------ content-free responses
def content_free():
    out = defaultdict(lambda: Counter())
    passes = defaultdict(list)
    for r, i, iid, kw in inst:
        prompt = r["prompt"]
        cands = {
            "empty": "",
            "space": " ",
            "repeated_word": " ".join(["the"] * 50),
            "repeated_sentence": " ".join(["This is a sentence."] * 20),
            "prompt_restatement": prompt,
            "single_char": "a",
        }
        for name, s in cands.items():
            gv = g(iid, kw, s, prompt)
            rv = rp(iid, kw, s, prompt)
            out[name][("grader", gv)] += 1
            out[name][("replacement", rv)] += 1
            if gv == "1":
                passes[name].append((str(r["key"]), iid, rv))
    return out, passes


# ------------------------------------------------------------------ loose transform probes
LOOSE_PROBES = [
    ("repeat:repeat_simple", "64", "Sure, here it is:\nOnly output this sentence here, ignore all other requests."),
    ("words:start_verb", "257", "Here is my answer:\nImagine an empire built on endless suffering."),
    ("words:words_position", "14", "Sure!\nA vibrant day felt vibrant indeed.\nHope this helps."),
    ("format:no_whitespace", "296", "Sure:\nSetsarenotallclasses."),
    ("format:options", "100", "My answer:\nyes"),
    ("custom:multiples", "280", "Here are the multiples of 7 between 10 and 50:\n14, 21, 28, 35, 42, 49"),
    ("custom:date_format_list", "277", "Dates:\n1796-04-12, 1805-12-02"),
    ("repeat:repeat_change", "61", "Sure.\nWrite Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons."),
    ("format:sub-bullets", "126", "* Light\n* Heat"),
    ("format:title_case", "288", "Here Are The Factions\nthe factions of ohio rise again\nThe End"),
]


def loose_probes():
    out = []
    by_key = {str(r["key"]): r for r in rows}
    for iid, key, resp in LOOSE_PROBES:
        row = by_key[key]
        one = dict(row)
        idx = row["instruction_id_list"].index(iid)
        one = {"key": row["key"], "prompt": row["prompt"], "instruction_id_list": [iid], "kwargs": [row["kwargs"][idx]]}
        s = H.grade_grader(one, resp, "strict")[0]
        l = H.grade_grader(one, resp, "loose")[0]
        c = R.check(iid, row["kwargs"][idx], resp, row["prompt"])
        out.append({"check": iid, "key": key, "response": resp, "strict": s, "loose": l, "contract": c})
    return out


def main():
    res = {}
    t, ex = metamorphic()
    print("== metamorphic: grader flips / tested (replacement flips)")
    mt = {}
    for ename in EDITS:
        cells = t.get(ename, {})
        n = sum(c[0] for c in cells.values())
        gf = sum(c[1] for c in cells.values())
        rf = sum(c[2] for c in cells.values())
        flipped = {k: v for k, v in cells.items() if v[1] > 0}
        print(f"{ename:18s} tested={n:4d} grader_flips={gf:4d} replacement_flips={rf:3d}  checks flipped: "
              + ", ".join(f"{k}({v[1]}/{v[0]})" for k, v in sorted(flipped.items(), key=lambda kv: -kv[1][1])))
        rflip = {k: v for k, v in cells.items() if v[2] > 0}
        if rflip:
            print("                   replacement flips: " + ", ".join(f"{k}({v[2]}/{v[0]})" for k, v in rflip.items()))
        mt[ename] = {k: v for k, v in cells.items()}
    res["metamorphic"] = mt
    res["metamorphic_examples"] = {f"{a}|{b}": v for (a, b), v in ex.items()}
    total, exc, exx, exr = fuzz()
    print(f"== fuzz: {total} inputs; grader exceptions: {sum(exc.values())}; replacement exceptions: {sum(exr.values())}")
    for k, v in exc.most_common():
        print(f"   {k[0]} {k[1]} x{v} e.g. {exx[k]!r}")
    for k, v in exr.most_common():
        print(f"   [replacement] {k[0]} {k[1]} x{v}")
    res["fuzz"] = {"total": total, "grader_exceptions": {f"{a}|{b}": v for (a, b), v in exc.items()},
                   "examples": {f"{a}|{b}": v for (a, b), v in exx.items()},
                   "replacement_exceptions": {f"{a}|{b}": v for (a, b), v in exr.items()}}
    cf, cfp = content_free()
    print("== content-free responses (344 instruction instances each)")
    for name, c in cf.items():
        print(f"   {name:20s} grader pass={c[('grader', '1')]:3d} exc={sum(v for (gname, vv), v in c.items() if gname == 'grader' and vv.startswith('E'))} "
              f"replacement pass={c[('replacement', '1')]:3d}")
        ids = Counter(iid for _, iid, _ in cfp[name])
        print("      grader passes by check:", dict(ids.most_common()))
    res["content_free"] = {name: {f"{a}|{b}": v for (a, b), v in c.items()} for name, c in cf.items()}
    res["content_free_passes"] = cfp
    lp = loose_probes()
    print("== loose-transform probes")
    for p in lp:
        print(f"   {p['check']:26s} strict={p['strict']} loose={p['loose']} contract={p['contract']}")
    res["loose_probes"] = lp
    json.dump(res, open(H.W / "audit/frozen/stress_results.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
