"""Step 4 generators: property, metamorphic, content-free and fuzz fixtures.

Writes audit/fixtures_generated/{property,metamorphic,content_free,fuzz}.jsonl. Property and
metamorphic labels are known by construction from the contract; content-free labels follow the
contract (D-empty and the per-check rules) and were checked by hand; a fuzz fixture is the
smallest response, found by deletion, on which a grader disagrees with the replacement, and its
label is the replacement's verdict, checked by hand before it was kept.

Usage: python stress_tests.py [property|metamorphic|content_free|fuzz|all]
"""
from __future__ import annotations

import collections
import json
import os
import random
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_lib as F  # noqa: E402
import graders as G  # noqa: E402

AUDIT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AUDIT, "fixtures_generated")
DATA = os.path.join(AUDIT, "..", "case", "data", "rlvr1_instruction_following.jsonl")

VOCAB = ("garden river window silver morning travel simple yellow orange planet forest little "
         "market summer winter number people moment family coffee bottle pencil camera doctor "
         "letter mirror rocket tunnel violin wallet zebra ocean puzzle quiet humble jungle "
         "kitten lemon magnet noodle pepper radio sugar tomato velvet wonder").split()


def load_kwargs():
    by_id = collections.defaultdict(list)
    with open(DATA, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
            for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
                by_id[iid].append(G.clean_kwargs(kw))
    return by_id


def words_without(rng, n, banned=(), letters_banned=""):
    pool = [w for w in VOCAB if w not in banned and not any(b in w for b in banned)
            and not any(ch in w for ch in letters_banned)]
    if len(pool) < 5:
        letters = [ch for ch in "bcdfghklmnoprsuvwy" if ch not in letters_banned]
        pool = ["".join(rng.choice(letters) for _ in range(5)) for _ in range(20)]
    return [rng.choice(pool) for _ in range(n)]


def sentence(ws):
    return " ".join(ws).capitalize() + "."


def text_of(rng, n_sent=3, banned=(), letters_banned=""):
    return " ".join(sentence(words_without(rng, rng.randint(4, 8), banned, letters_banned)) for _ in range(n_sent))


def rel(actual, relation, n):
    return {"at least": actual >= n, "less than": actual < n, "at most": actual <= n}[relation]


def lab(b):
    return "pass" if b else "fail"

# ---------------------------------------------------------------- property tests


def prop_cases(iid, kw, rng):
    """Yield (response, label, note) known by construction."""
    if iid == "punctuation:no_comma":
        t = text_of(rng)
        yield t, "pass", "no comma"
        ws = t.split(" ")
        k = rng.randrange(len(ws) - 1)
        yield " ".join(ws[:k] + [ws[k] + ","] + ws[k + 1:]), "fail", "one comma inserted"
    elif iid == "punctuation:punctuation_dot":
        t = " ".join(words_without(rng, 12))
        yield t, "pass", "no dot"
        yield t + " version 2.5", "fail", "decimal point"
    elif iid == "punctuation:punctuation_exclamation":
        t = text_of(rng)
        yield t, "pass", "no exclamation"
        yield t[:-1] + "!", "fail", "exclamation at the end"
    elif iid in ("keywords:existence", "keywords:forbidden_words"):
        keys = kw.get("keywords") or kw.get("forbidden_words")
        base = words_without(rng, 15, banned=keys)
        with_all = list(base)
        for k in keys:
            with_all.insert(rng.randrange(len(with_all) + 1), k)
        present = sentence(with_all)
        absent = sentence(base)
        if iid == "keywords:existence":
            yield present, "pass", "all keywords inserted as words"
            yield absent, "fail", "no keyword, not even as a substring"
        else:
            yield absent, "pass", "no forbidden word, not even as a substring"
            one = list(base)
            one.insert(rng.randrange(len(one) + 1), rng.choice(keys))
            yield sentence(one), "fail", "one forbidden word inserted"
    elif iid in ("keywords:frequency", "keywords:word_count_different_numbers", "keywords:word_once"):
        key = kw["keyword"]
        for k in sorted({0, 1, 2, 3, 4, kw.get("frequency", 1)}):
            ws = words_without(rng, 20, banned=[key])
            for _ in range(k):
                ws.insert(rng.randrange(len(ws) + 1), key)
            t = sentence(ws)
            if iid == "keywords:frequency":
                yield t, lab(rel(k, kw["relation"], kw["frequency"])), f"keyword {k} times"
            elif iid == "keywords:word_count_different_numbers":
                yield t, lab(k == kw["frequency"]), f"keyword {k} times; the text says exactly {kw['frequency']}"
            else:
                yield t, lab(k >= 1), f"keyword {k} times"
    elif iid in ("keywords:letter_frequency", "letters:letter_counting2"):
        letter = kw["letter"]
        n = kw["let_frequency"]
        for k in sorted({0, max(n - 1, 0), n, n + 1}):
            ws = words_without(rng, 10, letters_banned=letter + letter.upper())
            filler = [letter * 1 for _ in range(k)]
            t = " ".join(ws + filler)
            yield t, lab(rel(k, kw["let_relation"], n)), f"letter {k} times, lowercase text"
    elif iid == "length_constraints:number_words":
        n = kw["num_words"]
        for k in (n - 1, n, n + 1):
            yield " ".join(words_without(rng, k)) + ".", lab(rel(k, kw["relation"], n)), f"{k} plain words"
    elif iid == "length_constraints:number_sentences":
        n = kw["num_sentences"]
        for k in sorted({max(n - 1, 1), n, n + 1}):
            yield " ".join(sentence(words_without(rng, 5)) for _ in range(k)), lab(rel(k, kw["relation"], n)), f"{k} sentences"
    elif iid == "change_case:capital_word_frequency":
        n = kw["capital_frequency"]
        for k in sorted({max(n - 1, 0), n, n + 1}):
            ws = words_without(rng, 30)
            for i in rng.sample(range(30), k):
                ws[i] = ws[i].upper()
            yield " ".join(ws) + ".", lab(rel(k, kw["capital_relation"], n)), f"{k} all-capital words"
    elif iid == "detectable_format:number_bullet_lists":
        n = kw["num_bullets"]
        for k in sorted({max(n - 1, 0), n, n + 1}):
            lines = ["Here is the list:"] + ["* " + sentence(words_without(rng, 4)) for _ in range(k)]
            yield "\n".join(lines), lab(k == n), f"{k} star bullets"
    elif iid == "detectable_format:number_highlighted_sections":
        n = kw["num_highlights"]
        for k in sorted({max(n - 1, 0), n}):
            parts = [sentence(words_without(rng, 5)) for _ in range(5)]
            for i in range(k):
                parts[i] = "*" + " ".join(words_without(rng, 2)) + "* " + parts[i]
            yield " ".join(parts), lab(k >= n), f"{k} italic spans"
    elif iid == "detectable_content:number_placeholders":
        n = kw["num_placeholders"]
        for k in sorted({max(n - 1, 0), n}):
            parts = [sentence(words_without(rng, 5)) for _ in range(5)]
            for i in range(k):
                parts[i] += " [" + rng.choice(VOCAB) + "]"
            yield " ".join(parts), lab(k >= n), f"{k} placeholders"
    elif iid == "detectable_format:title":
        yield "<<" + " ".join(words_without(rng, 3)) + ">>\n" + text_of(rng), "pass", "title line"
        yield text_of(rng), "fail", "no title"
    elif iid == "detectable_content:postscript":
        m = kw["postscript_marker"]
        yield text_of(rng) + "\n\n" + m + " " + text_of(rng, 1), "pass", "postscript line"
        yield text_of(rng), "fail", "no postscript"
    elif iid == "startend:end_checker":
        p = kw["end_phrase"]
        yield text_of(rng) + " " + p, "pass", "phrase at the end"
        yield text_of(rng) + " " + p + " " + sentence(words_without(rng, 3)), "fail", "words after the phrase"
    elif iid == "startend:quotation":
        t = text_of(rng)
        yield '"' + t + '"', "pass", "wrapped"
        yield t, "fail", "not wrapped"
    elif iid == "first_word:first_word_answer":
        w = kw["first_word"]
        yield sentence([w] + words_without(rng, 6, banned=[w])) + " " + text_of(rng, 1, banned=[w]), "pass", "first word"
        yield sentence(words_without(rng, 6, banned=[w]) + [w]), "fail", "word not first"
    elif iid == "last_word:last_word_answer":
        w = kw["last_word"]
        yield text_of(rng, 1, banned=[w]) + " " + sentence(words_without(rng, 5, banned=[w]) + [w]), "pass", "last word"
        yield sentence([w] + words_without(rng, 6, banned=[w])), "fail", "word not last"
    elif iid == "keywords:start_end":
        w = rng.choice(VOCAB)
        body = " ".join(words_without(rng, 8, banned=[w]))
        yield w.capitalize() + " " + body + " " + w, "pass", "same first and last word"
        yield w.capitalize() + " " + body, "fail", "different last word"
    elif iid == "combination:two_responses":
        a, b = text_of(rng, 2), text_of(rng, 2)
        yield a + "\n******\n" + b, "pass", "two different responses"
        yield a, "fail", "one response"
        yield a + "\n******\n" + a, "fail", "identical responses"
    elif iid == "detectable_format:multiple_sections":
        n, sp = kw["num_sections"], kw["section_spliter"]
        for k in sorted({max(n - 1, 1), n, n + 1}):
            yield "\n".join(f"{sp} {i}\n{text_of(rng, 1)}" for i in range(1, k + 1)), lab(k == n), f"{k} sections"
    elif iid in ("length_constraints:number_paragraphs", "paragraphs:paragraphs"):
        n = kw.get("num_paragraphs", 2)
        for k in sorted({max(n - 1, 1), n, n + 1}):
            yield "\n***\n".join(text_of(rng, 2) for _ in range(k)), lab(k == n), f"{k} parts"
    elif iid == "paragraphs:paragraphs2":
        for k in (1, 2, 3):
            yield "\n\n".join(text_of(rng, 2) for _ in range(k)), lab(k == 2), f"{k} blocks"
    elif iid == "length_constraints:nth_paragraph_first_word":
        P, i, w = kw["num_paragraphs"], kw["nth_paragraph"], kw["first_word"]
        blocks = [text_of(rng, 2, banned=[w]) for _ in range(P)]
        if i <= P:
            blocks[i - 1] = sentence([w] + words_without(rng, 5, banned=[w]))
            yield "\n\n".join(blocks), "pass", f"{P} blocks, block {i} starts with the word"
        yield "\n\n".join(blocks + [sentence([w] + words_without(rng, 4, banned=[w]))]), "fail", f"{P + 1} blocks"
    elif iid == "detectable_format:json_format":
        obj = {rng.choice(VOCAB): rng.choice(VOCAB) for _ in range(3)}
        yield json.dumps(obj), "pass", "object"
        yield "```json\n" + json.dumps(obj, indent=2) + "\n```", "pass", "fenced object"
        yield "Here it is: " + json.dumps(obj), "fail", "text before the object"
    elif iid == "detectable_format:constrained_response":
        yield rng.choice(G.R.OPTIONS), "pass", "an option"
        yield "Maybe.", "fail", "not an option"
    elif iid == "copy:repeat_phrase":
        phrase = kw["phrase"].split()
        L = len(phrase)
        center = [(L + 1) // 2 - 1] if L % 2 else [L // 2 - 1, L // 2]
        n = kw["small_n"]
        def variant():
            p = list(phrase)
            j = rng.choice(center)
            p[j] = rng.choice([w for w in VOCAB if w != p[j].lower()])
            return " ".join(p) + "."
        yield " ".join(variant() for _ in range(n)), "pass", f"{n} center variants"
        yield " ".join(variant() for _ in range(n - 1)), "fail", f"{n - 1} center variants"
    elif iid == "count:count_unique":
        ws = rng.sample(VOCAB, 12)
        yield sentence(ws), "pass", "distinct words"
        yield sentence(ws + [ws[3]]), "fail", "one word twice"
    elif iid == "count:lowercase_counting":
        n = kw["N"]
        ws = rng.sample(VOCAB, 10)
        yield " ".join(ws * n), "pass", f"each lowercase word {n} times"
        yield " ".join(ws * n + [ws[0]]), "fail", f"one lowercase word {n + 1} times"
    elif iid == "keywords:no_adjacent_consecutive":
        def ok_seq(k):
            out = [rng.choice(VOCAB)]
            while len(out) < k:
                w = rng.choice(VOCAB)
                if abs(ord(w[0]) - ord(out[-1][0])) != 1:
                    out.append(w)
            return out
        ws = ok_seq(12)
        yield " ".join(ws), "pass", "no consecutive initials"
        i = rng.randrange(len(ws) - 1)
        nxt = [w for w in VOCAB if ord(w[0]) == ord(ws[i][0]) + 1]
        if nxt:
            ws2 = ws[:i + 1] + [rng.choice(nxt)] + ws[i + 1:]
            yield " ".join(ws2), "fail", "one pair in alphabetical order"
    elif iid == "keywords:palindrome":
        t = text_of(rng)
        yield t + " The level is fine.", "pass", "level"
        yield t, "fail", "no palindrome of three letters"
    elif iid == "keywords:keyword_specific_position":
        k, n, m = kw["keyword"], kw["n"], kw["m"]
        ss = [words_without(rng, max(m + 2, 5), banned=[k]) for _ in range(n + 1)]
        good = [list(s) for s in ss]
        good[n - 1][m - 1] = k
        yield " ".join(sentence(s) for s in good), "pass", f"keyword is word {m} of sentence {n}"
        bad = [list(s) for s in ss]
        bad[n - 1][m] = k
        yield " ".join(sentence(s) for s in bad), "fail", f"keyword is word {m + 1} of sentence {n}"
    elif iid in ("first_word:first_word_sent", "last_word:last_word_sent"):
        w = kw.get("first_word") or kw.get("last_word")
        first = iid.startswith("first")
        ss = []
        for _ in range(3):
            body = words_without(rng, 5, banned=[w])
            ss.append(sentence([w] + body) if first else sentence(body + [w]))
        yield " ".join(ss), "pass", "every sentence"
        ss[1] = sentence(words_without(rng, 6, banned=[w]))
        yield " ".join(ss), "fail", "one sentence without the word"
    elif iid == "detectable_format:sentence_hyphens":
        ss = [sentence(words_without(rng, 4)) for _ in range(3)]
        yield "-".join(ss), "pass", "joined by hyphens"
        yield " ".join(ss), "fail", "joined by spaces"
    elif iid == "detectable_format:square_brackets":
        ws = words_without(rng, 8)
        yield " ".join("[" + w + "]" for w in ws), "pass", "every word bracketed"
        yield " ".join("[" + w + "]" for w in ws[:-1]) + " " + ws[-1], "fail", "last word bare"
    elif iid == "detectable_format:bigram_wrapping":
        ws = words_without(rng, 8)
        yield " ".join("<<" + ws[i] + " " + ws[i + 1] + ">>" for i in range(0, 8, 2)), "pass", "four bigrams"
        yield " ".join("<<" + ws[i] + " " + ws[i + 1] + ">>" for i in range(0, 6, 2)) + " " + ws[6] + " " + ws[7], "fail", "last two words bare"
    elif iid == "letters:letter_counting":
        n = kw["N"]
        for k in sorted({max(n - 1, 0), n, n + 1}):
            yield "x" * k, lab(rel(k, kw["relation"], n)), f"{k} letters"
    elif iid == "change_case:english_lowercase":
        t = "the weather is nice today and we are going to the park with our friends after lunch."
        yield t, "pass", "lowercase English"
        yield t.replace("park", "Park"), "fail", "one capital"
    elif iid == "change_case:english_capital":
        t = "THE WEATHER IS NICE TODAY AND WE ARE GOING TO THE PARK WITH OUR FRIENDS AFTER LUNCH."
        yield t, "pass", "all caps English"
        yield t.replace("PARK", "park"), "fail", "one lowercase word"


def gen_property(rng, by_id):
    out = []
    for iid in sorted(by_id):
        for _ in range(12):
            kw = rng.choice(by_id[iid])
            for resp, label, note in prop_cases(iid, kw, rng):
                out.append({"kind": "property", "instruction_id": iid, "kwargs": kw, "response": resp,
                            "label": label, "note": note})
    return out

# ---------------------------------------------------------------- metamorphic tests


def gen_metamorphic(prop):
    """Edits the contract ignores; the label stays the one known by construction."""
    out = []
    for p in prop:
        iid, t = p["instruction_id"], p["response"]
        edits = []
        if iid in ("keywords:existence", "keywords:frequency", "keywords:word_once",
                   "keywords:word_count_different_numbers", "keywords:forbidden_words",
                   "keywords:keyword_specific_position"):
            keys = p["kwargs"].get("keywords") or p["kwargs"].get("forbidden_words") or [p["kwargs"]["keyword"]]
            e = t
            for k in keys:
                e = e.replace(" " + k + " ", " " + k.upper() + " ")
            if e != t:
                edits.append((e, "keyword upper-cased"))
        if iid in ("length_constraints:number_words", "length_constraints:number_sentences", "punctuation:no_comma",
                   "keywords:frequency", "change_case:capital_word_frequency"):
            edits.append((t.replace(" ", "  "), "double spaces"))
        if iid == "detectable_format:number_bullet_lists":
            edits.append((t.replace("\n* ", "\n  * "), "bullets indented"))
        if iid == "last_word:last_word_answer" and not t.endswith("."):
            edits.append((t + ".", "period after the last word"))
        if iid in ("startend:end_checker",):
            edits.append((t + "\n", "trailing newline"))
        for e, note in edits:
            out.append({"kind": "metamorphic", "instruction_id": iid, "kwargs": p["kwargs"], "response": e,
                        "label": p["label"], "note": "metamorphic: " + note + " (from: " + p["note"] + ")"})
    return out

# ---------------------------------------------------------------- content-free responses

EMPTY_PASS_REASON = "D-empty: a prohibition passes on empty text"


def gen_content_free(by_id):
    out = []
    texts = {}
    with open(os.path.join(AUDIT, "scripts", "instruction_texts.jsonl"), encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            texts.setdefault(e["id"], e)
    for iid in sorted(by_id):
        e = texts[iid]
        kw = e["kwargs"]
        restate = e["text"]
        for resp, kind in (("", "empty"), (" ".join(["the"] * 40), "repeated word"), (restate, "restated instruction")):
            label = G.check_r(iid, kw, resp)
            out.append({"kind": "content_free", "instruction_id": iid, "kwargs": kw, "response": resp,
                        "label": lab(label), "note": f"content-free: {kind}; label from the contract"})
    return out

# ---------------------------------------------------------------- fuzzing

ALPHABET = list(string.ascii_letters + string.digits) + list(" \n\n\t.,;:!?-*#[]<>\"'()`_/|") + \
    ["**", "***", "******", "<<", ">>", "P.S.", "P.P.S", "SECTION ", "Section ", "\n\n", "\n***\n", "* ",
     "- ", "1. ", "“", "”", "，", "。", "！", "…", "你", "好", "é", "Д",
     "<think>", "</think>"]


def fuzz_text(rng, kw):
    pieces = list(ALPHABET)
    for v in kw.values():
        if isinstance(v, str):
            pieces += [v, v.upper(), v.capitalize()]
        elif isinstance(v, list):
            pieces += [str(x) for x in v]
    n = rng.randint(0, 40)
    return "".join(rng.choice(pieces) for _ in range(n))


def shrink(iid, kw, text, disagrees):
    changed = True
    while changed:
        changed = False
        for size in (8, 4, 2, 1):
            i = 0
            while i < len(text):
                cand = text[:i] + text[i + size:]
                if cand != text and disagrees(cand):
                    text = cand
                    changed = True
                else:
                    i += size
    return text


def gen_fuzz(rng, by_id, per_id=300):
    stats = collections.Counter()
    exceptions = collections.defaultdict(list)
    kept = []
    for iid in sorted(by_id):
        found = {"A": 0, "B": 0}
        for _ in range(per_id):
            kw = rng.choice(by_id[iid])
            t = fuzz_text(rng, kw)
            a, a_err = G.check_a(iid, kw, t)
            b, b_detail = G.check_b(iid, kw, t)
            r = G.check_r(iid, kw, t)
            stats[(iid, "runs")] += 1
            if a_err:
                stats[(iid, "A_exception")] += 1
                exceptions[iid].append(("A", a_err.split(":")[0], t))
            if b is not None and isinstance(b_detail, str) and b_detail.startswith("exception"):
                stats[(iid, "B_exception")] += 1
                exceptions[iid].append(("B", b_detail[:60], t))
            for g, v in (("A", a), ("B", b)):
                if v is None or v == r:
                    continue
                stats[(iid, g + "_disagree")] += 1
                if found[g] >= 2:
                    continue
                if g == "A":
                    dis = lambda s, kw=kw: G.check_a(iid, kw, s)[0] != G.check_r(iid, kw, s)
                else:
                    dis = lambda s, kw=kw: G.check_b(iid, kw, s)[0] != G.check_r(iid, kw, s)
                small = shrink(iid, kw, t, dis)
                # Labels of these rest on the langdetect approximation or on a single-character
                # CJK "phrase"; they are counted in the stats but not kept as fixtures.
                if iid.startswith("change_case:english_") or (
                        iid == "keywords:palindrome" and any("一" <= ch <= "鿿" for ch in small)):
                    continue
                found[g] += 1
                kept.append({"kind": "fuzz", "instruction_id": iid, "kwargs": kw, "response": small,
                             "label": lab(G.check_r(iid, kw, small)),
                             "note": f"fuzz: smallest response on which grader {g} disagrees with the replacement"})
    return kept, stats, exceptions


def write(name, rows):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows))


def main(which):
    by_id = load_kwargs()
    if which in ("property", "metamorphic", "all"):
        prop = gen_property(random.Random(20261112), by_id)
        write("property", prop)
        write("metamorphic", gen_metamorphic(prop))
    if which in ("content_free", "all"):
        write("content_free", gen_content_free(by_id))
    if which in ("fuzz", "all"):
        kept, stats, exc = gen_fuzz(random.Random(7), by_id)
        write("fuzz", kept)
        with open(os.path.join(AUDIT, "results", "fuzz_stats.json"), "w", encoding="utf-8") as f:
            json.dump({"stats": {f"{k[0]}|{k[1]}": v for k, v in sorted(stats.items())},
                       "exception_examples": {k: v[:3] for k, v in exc.items()}}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    os.makedirs(os.path.join(AUDIT, "results"), exist_ok=True)
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
