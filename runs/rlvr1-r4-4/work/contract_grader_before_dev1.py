"""Replacement grader written from audit/CONTRACTS.md, with one switch per decision entry.

Usage:
    from contract_grader import check, graded_text, PROPOSED
    passed = check("keywords:existence", {"keywords": ["a", "b"]}, text)            # proposed readings
    passed = check(iid, kwargs, text, readings={**PROPOSED, "D-keyword-boundary": "alt"})

Every reading is "proposed" or "alt" (the alternative reading in the contract's decision table).
`check` never raises on text input; a malformed kwarg raises ValueError (a task defect, not a verdict).
Dependencies: the `regex` package (Unicode classes) and langdetect (only for the "in English" and
language checks, seeded).
"""

from __future__ import annotations

import json
import unicodedata

import regex as re

DECISIONS = [
    "D-think-markup", "D-word", "D-keyword-boundary", "D-sentence", "D-appear-n-times",
    "D-capital-single-letter", "D-english-part", "D-repeat-original", "D-repeat-center",
    "D-unique-case", "D-divider-form", "D-divider-empty", "D-lowercase-count", "D-lowercase-scope",
    "D-placeholder-kind", "D-postscript-end", "D-postscript-case", "D-bigram-odd",
    "D-constrained-exact", "D-json-toplevel", "D-sections-numbering", "D-sections-preamble",
    "D-sections-case", "D-bullet-marker", "D-bullet-nested", "D-highlight-bold", "D-hyphen-dash",
    "D-bracket-group", "D-title-position", "D-letter-case", "D-consecutive-order",
    "D-palindrome-length", "D-language-mixed", "D-blank-run", "D-letters-unit", "D-comma-chars",
    "D-dot-chars", "D-excl-chars", "D-end-trailing", "D-end-case", "D-quote-chars",
    "D-start-end-one-word",
]
PROPOSED = {d: "proposed" for d in DECISIONS}

SEMANTIC = frozenset({"count:count_unique", "detectable_format:bigram_wrapping",
                      "language:response_language", "letters:letter_counting"})

# ---------------------------------------------------------------------------- graded text

REASONING_MODELS = {"Qwen/Qwen3-4B-Thinking-2507"}


def graded_text(raw: str, reasoning_model: bool, readings: dict | None = None) -> str | None:
    """G1: the visible answer, or None for an extraction failure (reasoning never closed)."""
    r = readings or PROPOSED
    if reasoning_model:
        if "</think>" not in raw:
            return None
        return raw.rsplit("</think>", 1)[1].strip()
    if r["D-think-markup"] == "alt":
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
        raw = raw.split("<think>", 1)[0]  # an unclosed span runs to the end (Change 4)
    return raw.strip()


# ---------------------------------------------------------------------------- words

WORD_CHARS = r"[\p{L}\p{M}\p{N}]"
WORD_RE = re.compile(WORD_CHARS + r"+(?:['’\-]" + WORD_CHARS + r"+)*")


def words(text: str, r: dict) -> list[str]:
    """G3."""
    if r["D-word"] == "alt":
        return [t for t in text.split() if re.search(WORD_CHARS, t)]
    return WORD_RE.findall(text)


def core(word: str) -> str:
    """G4: a word without surrounding punctuation or markdown, lowercased."""
    m = re.search(WORD_CHARS + r"(?:.*" + WORD_CHARS + r")?", word, flags=re.DOTALL)
    return (m.group(0) if m else "").lower()


def same_word(a: str, b: str) -> bool:
    return core(a) == core(b) and core(a) != ""


def keyword_count(text: str, kw: str, r: dict) -> int:
    """G5."""
    kw = kw.strip()
    if not kw:
        raise ValueError("empty keyword")
    if r["D-keyword-boundary"] == "alt":
        return text.lower().count(kw.lower())
    pat = r"(?<![\p{L}\p{M}\p{N}_])" + re.escape(kw) + r"(?![\p{L}\p{M}\p{N}_])"
    return len(re.findall(pat, text, flags=re.IGNORECASE))


# ---------------------------------------------------------------------------- sentences

ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "st", "vs", "etc", "e.g", "i.e", "no", "prof", "jr", "sr",
                 "inc", "ltd", "co", "fig", "approx", "dept", "est", "u.s", "a.m", "p.m"}
END_RE = re.compile(r"[.!?。！？]+[\"'”’)\]*_]*(?=\s|$)")


def _split_line(line: str) -> list[str]:
    parts, start = [], 0
    for m in END_RE.finditer(line):
        punct = m.group(0)
        before = line[start:m.start()]
        tok = before.split()[-1] if before.split() else ""
        tok_core = tok.lstrip("([\"'*_").lower()
        if punct.startswith(".") and len(punct.rstrip("\"'”’)]*_")) == 1:
            if tok_core in ABBREVIATIONS:
                continue
            if len(tok_core) == 1 and tok_core.isalpha() and tok_core not in ("i",):
                continue  # an initial such as "J."
            if tok_core.isdigit() and not line[:m.start()].strip().replace(tok, "", 1).strip():
                continue  # a list number such as "1." at the start of the line
        parts.append(line[start:m.end()])
        start = m.end()
    parts.append(line[start:])
    return parts


def sentences(text: str, r: dict) -> list[str]:
    """G6."""
    if r["D-sentence"] == "alt":
        lines = [" ".join(text.split("\n"))]
    else:
        lines = text.split("\n")
    out = []
    for line in lines:
        for part in _split_line(line.strip()):
            part = part.strip()
            if part and re.search(WORD_CHARS, part):
                out.append(part)
    return out


def relation_ok(actual: int, relation: str, n: int) -> bool:
    if relation == "at least":
        return actual >= n
    if relation == "less than":
        return actual < n
    if relation == "at most":
        return actual <= n
    raise ValueError(f"unknown relation {relation!r}")


# ---------------------------------------------------------------------------- paragraphs

DIVIDER_LINE = re.compile(r"(?m)^[ \t]*\*(?:[ \t]*\*){2,}[ \t]*$")


def divider_paragraphs(text: str, r: dict) -> list[str] | None:
    """Parts between `***` dividers; None when an empty part makes the layout invalid."""
    if r["D-divider-form"] == "alt":
        parts = re.split(r"(?m)^[ \t]*\*\*\*[ \t]*$", text)
    else:
        parts = DIVIDER_LINE.split(text)
    if r["D-divider-empty"] == "alt":
        return [p for p in parts if p.strip()]
    if any(not p.strip() for p in parts):
        return None
    return parts


def blank_paragraphs(text: str, r: dict) -> list[str] | None:
    t = text.strip()
    if not t:
        return []
    if r["D-blank-run"] == "alt":
        parts = t.split("\n\n")
        if any(not p.strip() for p in parts):
            return None
        return parts
    return [p for p in re.split(r"\n[ \t]*\n\s*", t) if p.strip()]


# ---------------------------------------------------------------------------- language

SCRIPT_OF = {
    "ar": "Arabic", "fa": "Arabic", "ur": "Arabic", "he": "Hebrew",
    "ru": "Cyrillic", "uk": "Cyrillic", "bg": "Cyrillic",
    "hi": "Devanagari", "mr": "Devanagari", "ne": "Devanagari",
    "bn": "Bengali", "pa": "Gurmukhi", "gu": "Gujarati", "ta": "Tamil", "te": "Telugu",
    "kn": "Kannada", "ml": "Malayalam", "th": "Thai", "ko": "Hangul", "ja": "Japanese",
}


def _in_script(ch: str, script: str) -> bool:
    if script == "Japanese":
        return bool(re.match(r"[\p{Han}\p{Hiragana}\p{Katakana}]", ch))
    if script == "Latin":
        return bool(re.match(r"\p{Latin}", ch))
    return bool(re.match(r"\p{" + script + "}", ch))


def _detect(text: str) -> str | None:
    import langdetect
    from langdetect import DetectorFactory
    DetectorFactory.seed = 0
    try:
        return langdetect.detect(text)
    except langdetect.LangDetectException:
        return None


EN_STOP = {"the", "and", "of", "to", "a", "in", "is", "it", "you", "that", "for", "on", "with", "as",
           "are", "this", "be", "or", "your", "my", "i", "we", "can", "will", "not", "an", "at", "by"}


def is_language(text: str, code: str, r: dict) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    script = SCRIPT_OF.get(code, "Latin")
    share = sum(1 for c in letters if _in_script(c, script)) / len(letters)
    need = 0.6 if r["D-language-mixed"] == "proposed" else 0.999
    if share < need:
        return False
    if script == "Latin":
        if code == "en":
            ws = [w.lower() for w in WORD_RE.findall(text)]
            if ws and sum(1 for w in ws if w in EN_STOP) / len(ws) >= 0.12:
                return True
            if len(ws) <= 3 and all(c.isascii() for c in letters):
                return True  # too short to tell: an ASCII answer of three words or fewer counts as English
        return _detect(text.lower()) == code
    if script in ("Arabic", "Cyrillic", "Devanagari"):
        kept = "".join(c if (_in_script(c, script) or not c.isalpha()) else " " for c in text)
        return _detect(kept) == code
    return True


def is_english(text: str, r: dict) -> bool:
    return is_language(text, "en", {**r, "D-language-mixed": "proposed"})


# ---------------------------------------------------------------------------- checks

def _c_capital_word_frequency(t, kw, r):
    n = 0
    for w in words(t, r):
        letters = [c for c in w if c.isalpha()]
        if not letters or any(c.islower() for c in letters) or not any(c.isupper() for c in letters):
            continue
        if r["D-capital-single-letter"] == "alt" and len(letters) < 2:
            continue
        n += 1
    return relation_ok(n, kw["capital_relation"], kw["capital_frequency"])


def _c_english_capital(t, kw, r):
    if any(c.islower() for c in t) or not any(c.isupper() for c in t):
        return False
    return is_english(t, r) if r["D-english-part"] == "proposed" else True


def _c_english_lowercase(t, kw, r):
    if any(c.isupper() for c in t) or not any(c.islower() for c in t):
        return False
    return is_english(t, r) if r["D-english-part"] == "proposed" else True


def _c_two_responses(t, kw, r):
    runs = re.findall(r"\*{6,}", t)
    if len(runs) != 1 or len(runs[0]) != 6:
        return False
    a, b = t.split("******")
    a, b = " ".join(a.split()), " ".join(b.split())
    return bool(a) and bool(b) and a != b


def _c_repeat_phrase(t, kw, r):
    phrase = [core(w) for w in words(kw["phrase"], {**r, "D-word": "proposed"})]
    seq = [core(w) for w in words(t, {**r, "D-word": "proposed"})]
    k = len(phrase)
    transformed = unchanged = 0
    i = 0
    while i + k <= len(seq):
        win = seq[i:i + k]
        if win[0] == phrase[0] and win[-1] == phrase[-1]:
            diff = [j for j in range(k) if win[j] != phrase[j]]
            if not diff:
                unchanged += 1
                i += k
                continue
            if len(diff) == 1:
                j = diff[0]
                center_ok = (0 < j < k - 1) if r["D-repeat-center"] == "proposed" else j in {(k - 1) // 2, k // 2}
                if center_ok:
                    transformed += 1
                    i += k
                    continue
        i += 1
    if r["D-repeat-original"] == "proposed":
        return transformed == kw["small_n"] and unchanged == 0
    return transformed + unchanged == kw["small_n"]


def _c_count_unique(t, kw, r):
    ws = words(t, r)
    ws = [core(w) for w in ws] if r["D-unique-case"] == "proposed" else [
        (re.search(WORD_CHARS + r"(?:.*" + WORD_CHARS + r")?", w).group(0)) for w in ws]
    return len(ws) == len(set(ws))


def _c_counting_composition(t, kw, r):
    parts = divider_paragraphs(t, r)
    if parts is None or len(parts) != 3:
        return False
    for p in parts:
        ss = sentences(p, r)
        if len(ss) != kw["n_sent"]:
            return False
        if any(len(words(s, r)) != kw["n_words"] for s in ss):
            return False
    return True


def _c_lowercase_counting(t, kw, r):
    ws = words(t, r)
    lower_forms = [core(w) for w in ws if any(c.isalpha() for c in w) and not any(c.isupper() for c in w)]
    if r["D-lowercase-scope"] == "alt":
        return len(lower_forms) <= kw["N"]
    if r["D-lowercase-count"] == "proposed":
        counts = {}
        for w in lower_forms:
            counts[w] = counts.get(w, 0) + 1
    else:
        allc = {}
        for w in ws:
            allc[core(w)] = allc.get(core(w), 0) + 1
        counts = {w: allc[w] for w in set(lower_forms)}
    return all(v <= kw["N"] for v in counts.values())


def _c_number_placeholders(t, kw, r):
    found = []
    for m in re.finditer(r"\[([^\[\]\n]*)\]", t):
        if not m.group(1).strip():
            continue
        if r["D-placeholder-kind"] == "alt":
            after = t[m.end():m.end() + 1]
            if after == "(" or m.group(1).strip().isdigit():
                continue
        found.append(m)
    return len(found) >= kw["num_placeholders"]


MARKDOWN_LEAD = r"[ \t>#*_~`]*"


def _marker_re(marker: str, ci: bool):
    m = marker.strip().rstrip(".").upper()
    if m == "P.S":
        core_pat = r"(?<![Pp]\.\s?)P\.\s?S"
    elif m == "P.P.S":
        core_pat = r"P\.\s?P\.\s?S"
    else:
        core_pat = re.escape(m)
    pat = r"(?m)^" + MARKDOWN_LEAD + core_pat + r"\.?(?=[\s:.\-–—*_)]|$)"
    return re.compile(pat, flags=re.IGNORECASE if ci else 0)


ANY_PS = re.compile(r"(?mi)^" + MARKDOWN_LEAD + r"(?:P\.\s?)+S\.?(?=[\s:.\-*_)]|$)")


def _c_postscript(t, kw, r):
    pat = _marker_re(kw["postscript_marker"], r["D-postscript-case"] == "proposed")
    hits = list(pat.finditer(t))
    if not hits:
        return False
    if r["D-postscript-end"] == "alt":
        return True
    for h in hits:
        rest = t[h.end():]
        blocks = [b for b in re.split(r"\n[ \t]*\n", rest) if b.strip()]
        if all(ANY_PS.match(b.strip()) for b in blocks[1:]):
            return True
    return False


def _c_bigram_wrapping(t, kw, r):
    groups = re.findall(r"<<([^<>]*)>>", t)
    outside = re.sub(r"<<[^<>]*>>", " ", t)
    if words(outside, r) or not groups:
        return False
    sizes = [len(words(g, r)) for g in groups]
    if any(s == 0 for s in sizes):
        return False
    if all(s == 2 for s in sizes):
        return True
    if r["D-bigram-odd"] == "proposed" and all(s == 2 for s in sizes[:-1]) and sizes[-1] == 1:
        return True
    return False


OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


def _c_constrained_response(t, kw, r):
    if r["D-constrained-exact"] == "alt":
        s = re.sub(r"[*_`]", "", t).strip()
        return s in OPTIONS
    hits = [o for o in OPTIONS if o in t]
    return len(hits) == 1


def _c_json_format(t, kw, r):
    s = t.strip()
    m = re.match(r"^```[A-Za-z]*[ \t]*\n?(.*?)\n?[ \t]*```$", s, flags=re.DOTALL)
    if m:
        s = m.group(1).strip()
    try:
        v = json.loads(s)
    except ValueError:
        return False
    if r["D-json-toplevel"] == "alt":
        return isinstance(v, (dict, list))
    return True


def _c_multiple_sections(t, kw, r):
    spl = kw["section_spliter"].strip()
    flags = re.IGNORECASE if r["D-sections-case"] == "proposed" else 0
    pat = re.compile(r"(?m)^" + MARKDOWN_LEAD + re.escape(spl) + r"[ \t]+(\d+|[IVXLC]+|[A-Za-z])\b(.*)$", flags)
    ms = list(pat.finditer(t))
    if len(ms) != kw["num_sections"]:
        return False
    if r["D-sections-preamble"] == "alt" and t[:ms[0].start()].strip():
        return False
    if r["D-sections-numbering"] == "alt":
        if [m.group(1) for m in ms] != [str(i) for i in range(1, len(ms) + 1)]:
            return False
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
        content = m.group(2).strip(" \t:.-*_#") + t[m.end():end]
        if not re.search(WORD_CHARS, content):
            return False
    return True


THEMATIC = re.compile(r"^\s*([*\-_])(?:\s*\1){2,}\s*$")


def _c_number_bullet_lists(t, kw, r):
    n = 0
    for line in t.split("\n"):
        if THEMATIC.match(line):
            continue
        m = re.match(r"^([ \t]*)([*\-+])[ \t]+\S", line)
        if not m:
            continue
        if r["D-bullet-marker"] == "alt" and m.group(2) != "*":
            continue
        if r["D-bullet-nested"] == "alt" and len(m.group(1).expandtabs(4)) >= 2:
            continue
        n += 1
    return n == kw["num_bullets"]


def _c_number_highlighted_sections(t, kw, r):
    n = 0
    bold = re.compile(r"(?<![*\w])(\*\*\*?|__)(?![\s*_])([^\n*]+?)(?<![\s*_])\1(?![*\w])")
    ital = re.compile(r"(?<![*\w])([*_])(?![\s*_])([^\n*_]+?)(?<![\s*_])\1(?![*\w])")
    if r["D-highlight-bold"] == "proposed":
        n += len([m for m in bold.finditer(t) if m.group(2).strip()])
        t2 = bold.sub(" ", t)
    else:
        t2 = bold.sub(" ", t)
    n += len([m for m in ital.finditer(t2) if m.group(2).strip() and
              (r["D-highlight-bold"] == "proposed" or m.group(1) == "*")])
    return n >= kw["num_highlights"]


def _c_sentence_hyphens(t, kw, r):
    s = t.strip()
    if "\n" in s:
        return False
    hy = "-‐‑" + ("–—" if r["D-hyphen-dash"] == "alt" else "")
    for m in re.finditer(r"[.!?]+[\"'”’)\]]*", s):
        nxt = s[m.end():m.end() + 1]
        if nxt == "":
            continue
        if nxt in hy:
            after = s[m.end() + 1:m.end() + 2]
            if after == "" or after.isspace():
                return False
            continue
        if nxt.isspace():
            before = s[:m.start()].split()
            tok = before[-1].lstrip("([\"'*_").lower() if before else ""
            if m.group(0) == "." and (tok in ABBREVIATIONS or (len(tok) == 1 and tok.isalpha())):
                continue
            return False
        # letter, digit or other character right after the punctuation: not a boundary (3.5, U.S.A)
    return True


def _c_square_brackets(t, kw, r):
    spans = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r"\[([^\[\]]*)\]", t)]
    outside = t
    for a, b, _ in reversed(spans):
        outside = outside[:a] + " " + outside[b:]
    if words(outside, {**r, "D-word": "proposed"}):
        return False
    if not spans:
        return not words(t, {**r, "D-word": "proposed"})
    for _, _, inner in spans:
        k = len(words(inner, {**r, "D-word": "proposed"}))
        if r["D-bracket-group"] == "proposed" and k > 1:
            return False
    return True


def _c_title(t, kw, r):
    pat = re.compile(r"<<([^<>\n]*\S[^<>\n]*)>>")
    if r["D-title-position"] == "alt":
        return bool(re.match(r"^[ \t#*_]*<<([^<>\n]*\S[^<>\n]*)>>", t.strip()))
    return bool(pat.search(t))


def _c_first_word_answer(t, kw, r):
    ws = words(t, r)
    return bool(ws) and same_word(ws[0], kw["first_word"])


def _c_first_word_sent(t, kw, r):
    ss = sentences(t, r)
    if not ss:
        return False
    for s in ss:
        ws = words(s, r)
        if not ws or not same_word(ws[0], kw["first_word"]):
            return False
    return True


def _c_existence(t, kw, r):
    return all(keyword_count(t, k, r) >= 1 for k in kw["keywords"])


def _c_forbidden(t, kw, r):
    return all(keyword_count(t, k, r) == 0 for k in kw["forbidden_words"])


def _c_frequency(t, kw, r):
    return relation_ok(keyword_count(t, kw["keyword"], r), kw["relation"], kw["frequency"])


def _c_keyword_specific_position(t, kw, r):
    ss = sentences(t, r)
    n, m = kw["n"], kw["m"]
    if len(ss) < n:
        return False
    ws = words(ss[n - 1], r)
    return len(ws) >= m and same_word(ws[m - 1], kw["keyword"])


def _letter_count(t, letter, r):
    if r["D-letter-case"] == "proposed":
        return t.lower().count(letter.lower())
    return t.count(letter)


def _c_letter_frequency(t, kw, r):
    return relation_ok(_letter_count(t, kw["letter"], r), kw["let_relation"], kw["let_frequency"])


def _c_no_adjacent_consecutive(t, kw, r):
    ws = words(t, r)
    firsts = []
    for w in ws:
        c = core(w)[:1]
        firsts.append(c if c and "a" <= c <= "z" else None)
    for a, b in zip(firsts, firsts[1:]):
        if a is None or b is None:
            continue
        d = ord(b) - ord(a)
        if d == 1 or (r["D-consecutive-order"] == "proposed" and d == -1):
            return False
    return True


def _c_palindrome(t, kw, r):
    minlen = 3 if r["D-palindrome-length"] == "proposed" else 1
    ws = [re.sub(r"[^\p{L}\p{N}]", "", w).lower() for w in words(t, {**r, "D-word": "proposed"})]
    for w in ws:
        if len(w) >= minlen and w == w[::-1]:
            return True
    letters_only = [re.sub(r"[^\p{L}]", "", w) for w in ws]
    for i in range(len(letters_only)):
        acc = ""
        for j in range(i, min(i + 8, len(letters_only))):
            acc += letters_only[j]
            if j > i and len(acc) >= 7 and acc == acc[::-1]:
                return True
    return False


def _c_start_end(t, kw, r):
    ws = words(t, r)
    if not ws:
        return False
    s = t.strip()
    last_char = s[-1]
    if not (last_char.isalnum() or unicodedata.category(last_char).startswith("M")):
        return False
    if r["D-word"] == "alt" and not (ws[-1][-1].isalnum()):
        return False
    if len(ws) == 1:
        return r["D-start-end-one-word"] == "proposed"
    return same_word(ws[0], ws[-1])


def _c_word_count_different_numbers(t, kw, r):
    c = keyword_count(t, kw["keyword"], r)
    return c == kw["frequency"] if r["D-appear-n-times"] == "proposed" else c >= kw["frequency"]


def _c_word_once(t, kw, r):
    return keyword_count(t, kw["keyword"], r) >= 1


def _c_response_language(t, kw, r):
    return is_language(t, kw["language"], r)


def _c_last_word_answer(t, kw, r):
    ws = words(t, r)
    return bool(ws) and same_word(ws[-1], kw["last_word"])


def _c_last_word_sent(t, kw, r):
    ss = sentences(t, r)
    if not ss:
        return False
    for s in ss:
        ws = words(s, r)
        if not ws or not same_word(ws[-1], kw["last_word"]):
            return False
    return True


def _c_nth_paragraph_first_word(t, kw, r):
    ps = blank_paragraphs(t, r)
    if ps is None or len(ps) != kw["num_paragraphs"]:
        return False
    nth = kw["nth_paragraph"]
    if not 1 <= nth <= len(ps):
        return False
    ws = words(ps[nth - 1], r)
    return bool(ws) and same_word(ws[0], kw["first_word"])


def _c_number_paragraphs(t, kw, r, n=None):
    ps = divider_paragraphs(t, r)
    return ps is not None and len(ps) == (kw["num_paragraphs"] if n is None else n)


def _c_number_sentences(t, kw, r):
    return relation_ok(len(sentences(t, r)), kw["relation"], kw["num_sentences"])


def _c_number_words(t, kw, r):
    return relation_ok(len(words(t, r)), kw["relation"], kw["num_words"])


def _c_letter_counting(t, kw, r):
    n = len(words(t, r)) if r["D-letters-unit"] == "alt" else sum(1 for c in t if c.isalpha())
    return relation_ok(n, kw["relation"], kw["N"])


def _c_paragraphs2(t, kw, r):
    ps = blank_paragraphs(t, r)
    return ps is not None and len(ps) == 2


def _chars_absent(chars_proposed, char_alt):
    def f(t, kw, r):
        chars = chars_proposed if r[DECISION_FOR[char_alt]] == "proposed" else char_alt
        return not any(c in t for c in chars)
    return f


DECISION_FOR = {",": "D-comma-chars", ".": "D-dot-chars", "!": "D-excl-chars"}


def _c_end_checker(t, kw, r):
    phrase = kw["end_phrase"].strip()
    s = t.strip()
    if r["D-end-case"] == "alt":
        phrase, s = phrase.lower(), s.lower()
    if s.endswith(phrase):
        return True
    if r["D-end-trailing"] == "alt":
        return False
    while s and not (s[-1].isalnum()) and not s.endswith(phrase):
        s = s[:-1]
    return s.endswith(phrase)


def _c_quotation(t, kw, r):
    s = t.strip()
    if len(s) < 2:
        return False
    if r["D-quote-chars"] == "alt":
        return s[0] == '"' and s[-1] == '"'
    return s[0] in '"“' and s[-1] in '"”'


CHECKS = {
    "change_case:capital_word_frequency": _c_capital_word_frequency,
    "change_case:english_capital": _c_english_capital,
    "change_case:english_lowercase": _c_english_lowercase,
    "combination:two_responses": _c_two_responses,
    "copy:repeat_phrase": _c_repeat_phrase,
    "count:count_unique": _c_count_unique,
    "count:counting_composition": _c_counting_composition,
    "count:lowercase_counting": _c_lowercase_counting,
    "detectable_content:number_placeholders": _c_number_placeholders,
    "detectable_content:postscript": _c_postscript,
    "detectable_format:bigram_wrapping": _c_bigram_wrapping,
    "detectable_format:constrained_response": _c_constrained_response,
    "detectable_format:json_format": _c_json_format,
    "detectable_format:multiple_sections": _c_multiple_sections,
    "detectable_format:number_bullet_lists": _c_number_bullet_lists,
    "detectable_format:number_highlighted_sections": _c_number_highlighted_sections,
    "detectable_format:sentence_hyphens": _c_sentence_hyphens,
    "detectable_format:square_brackets": _c_square_brackets,
    "detectable_format:title": _c_title,
    "first_word:first_word_answer": _c_first_word_answer,
    "first_word:first_word_sent": _c_first_word_sent,
    "keywords:existence": _c_existence,
    "keywords:forbidden_words": _c_forbidden,
    "keywords:frequency": _c_frequency,
    "keywords:keyword_specific_position": _c_keyword_specific_position,
    "keywords:letter_frequency": _c_letter_frequency,
    "keywords:no_adjacent_consecutive": _c_no_adjacent_consecutive,
    "keywords:palindrome": _c_palindrome,
    "keywords:start_end": _c_start_end,
    "keywords:word_count_different_numbers": _c_word_count_different_numbers,
    "keywords:word_once": _c_word_once,
    "language:response_language": _c_response_language,
    "last_word:last_word_answer": _c_last_word_answer,
    "last_word:last_word_sent": _c_last_word_sent,
    "length_constraints:nth_paragraph_first_word": _c_nth_paragraph_first_word,
    "length_constraints:number_paragraphs": _c_number_paragraphs,
    "length_constraints:number_sentences": _c_number_sentences,
    "length_constraints:number_words": _c_number_words,
    "letters:letter_counting": _c_letter_counting,
    "letters:letter_counting2": _c_letter_frequency,
    "paragraphs:paragraphs": lambda t, kw, r: _c_number_paragraphs(t, kw, r, n=2),
    "paragraphs:paragraphs2": _c_paragraphs2,
    "punctuation:no_comma": _chars_absent(",，、،﹐﹑", ","),
    "punctuation:punctuation_dot": _chars_absent(".。．…", "."),
    "punctuation:punctuation_exclamation": _chars_absent("!！¡‼⁉❗❕", "!"),
    "startend:end_checker": _c_end_checker,
    "startend:quotation": _c_quotation,
}


def check(instruction_id: str, kwargs: dict | None, text: str | None, readings: dict | None = None) -> bool:
    """Contract verdict for one constraint on graded text (None = extraction failure -> False)."""
    if text is None:
        return False
    r = {**PROPOSED, **(readings or {})}
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    return bool(CHECKS[instruction_id](text.strip(), kw, r))


def row_verdicts(record: dict, text: str | None, readings: dict | None = None) -> list[bool]:
    return [check(i, k, text, readings) for i, k in zip(record["instruction_id_list"], record["kwargs"])]
