"""Replacement grader: the contracts of audit/CONTRACTS.md (version 2), one switch per decision entry.

`check(iid, kwargs, text, readings)` grades one constraint on graded text. `readings` maps a decision
id to "A" (the proposed reading) or "B" (the alternative); missing ids take "A".
`graded_text(raw, reasoning_model)` applies the contract's extraction rule (section 1).
`grade_row(record, raw, ...)` gives the binary row verdict.

Written from the contracts, not from either grader. Language identification uses langdetect with
seed 0 (the only detector installed); `D-language-mixed` reading A runs it per paragraph.
"""

from __future__ import annotations

import json
import re as _re

import regex as re

DECISIONS = (
    "D-outer-whitespace", "D-word", "D-word-cjk", "D-word-case", "D-keyword-match", "D-sentence",
    "D-edge-markup", "D-allcaps-single", "D-english", "D-repeat-center", "D-repeat-original",
    "D-lowercase-counting", "D-placeholder-link", "D-postscript-end", "D-postscript-dot", "D-bigram-odd",
    "D-constrained-exact", "D-json-scalar", "D-section-case", "D-section-preamble", "D-section-numbering",
    "D-bullet-marker", "D-highlight-bold", "D-brackets-per-word", "D-title-position", "D-letter-case",
    "D-consecutive-order", "D-palindrome-length", "D-word-count-relation", "D-language-mixed", "D-blank-run",
    "D-letter-unit", "D-comma-chars", "D-dot-chars", "D-exclamation-chars", "D-end-trailing", "D-quote-chars",
    "D-section-count", "D-end-case", "D-bracket-punct", "D-divider-edge", "D-postscript-case", "D-hyphen-inner", "D-hyphen-plural",
)
PROPOSED = {d: "A" for d in DECISIONS}


class R:
    """Readings in force for one call."""

    def __init__(self, readings=None):
        self.used = set()
        self.r = dict(PROPOSED)
        if readings:
            unknown = set(readings) - set(DECISIONS)
            assert not unknown, unknown
            self.r.update(readings)

    def __call__(self, decision: str) -> bool:
        """True when the proposed reading (A) is in force."""
        self.used.add(decision)
        return self.r[decision] == "A"


# ---------------------------------------------------------------- graded text

def graded_text(raw: str, reasoning_model: bool) -> str | None:
    """Contract section 1. None is an extraction failure (reasoning never closed)."""
    if reasoning_model:
        if "</think>" not in raw:
            return None
        return raw[raw.rindex("</think>") + len("</think>"):]
    return raw


# ---------------------------------------------------------------- words and sentences

CJK = re.compile(r"[\p{Han}\p{Hiragana}\p{Katakana}]")
WORD_A = re.compile(r"[\p{L}\p{M}\p{N}]+(?:['’\-][\p{L}\p{M}\p{N}]+)*")


def words(text: str, r: R) -> list[str]:
    if r("D-word"):
        found = WORD_A.findall(text)
    else:
        found = []
        for token in text.split():
            core = re.sub(r"^[^\p{L}\p{M}\p{N}]+|[^\p{L}\p{M}\p{N}]+$", "", token)
            if core:
                found.append(core)
    if not r("D-word-cjk"):
        return found
    out = []
    for w in found:
        if CJK.search(w):
            out.extend(p.strip("'’-") for p in re.findall(r"[\p{Han}\p{Hiragana}\p{Katakana}]|[^\p{Han}\p{Hiragana}\p{Katakana}]+", w) if p.strip("'’-"))
        else:
            out.append(w)
    return out


def same_word(a: str, b: str, r: R) -> bool:
    return a.lower() == b.lower() if r("D-word-case") else a == b


ABBREV = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e", "eg", "ie", "no", "fig", "approx", "u.s", "a.m", "p.m", "inc", "ltd", "co"}
END = re.compile(r"(?:[.!?…]+|[。！？]+)[\"'”’)\]»」』）>*_]*")
CJK_END = re.compile(r"[。！？]")


def _is_abbrev(text: str, start: int) -> bool:
    """Is the punctuation run at `start` an abbreviation dot?"""
    if text[start] != ".":
        return False
    m = re.search(r"([\p{L}\p{M}.]+)$", text[:start])
    if not m:
        return False
    token = m.group(1).lower().strip(".")
    return token in ABBREV or (len(token) == 1 and "a" <= token <= "z")


def sentences(text: str, r: R) -> list[str]:
    if not r("D-sentence"):
        text = text.replace("\n", " ")
    pieces = []
    for line in text.split("\n"):
        start = 0
        for m in END.finditer(line):
            e = m.end()
            if e < len(line) and not line[e].isspace() and not CJK_END.search(m.group(0)):
                continue
            if _is_abbrev(line, m.start()) and e < len(line):
                continue
            pieces.append(line[start:e])
            start = e
        pieces.append(line[start:])
    return [p.strip() for p in pieces if words(p, r)]


SENT_PUNCT = ".,;:!?…"


def first_word(text: str, r: R) -> str | None:
    if r("D-edge-markup"):
        w = words(text, r)
        return w[0] if w else None
    tokens = text.split()
    if not tokens:
        return None
    tok = tokens[0].rstrip(SENT_PUNCT)
    inner = words(tok, r)
    return tok if inner and inner[0] == tok else (tok or None)


def last_word(text: str, r: R) -> str | None:
    if r("D-edge-markup"):
        w = words(text, r)
        return w[-1] if w else None
    tokens = text.split()
    if not tokens:
        return None
    tok = tokens[-1].rstrip(SENT_PUNCT)
    inner = words(tok, r)
    return tok if inner and inner[-1] == tok else (tok or None)


def _base_forms(w: str) -> list[str]:
    """The word, and its base when it carries a possessive ending or an elided clitic (contract v3)."""
    forms = [w]
    parts = re.split(r"['’]", w)
    if len(parts) > 1:
        if parts[-1].lower() in ("s", "") and parts[0]:
            forms.append(parts[0])
        if len(parts) == 2 and 0 < len(parts[0]) <= 4 and parts[1]:
            forms.append(parts[1])
    return forms


def occurrences(text: str, kw: str, r: R) -> int:
    n = 0
    for w in words(text, r):
        if any(same_word(f, kw, r) for f in _base_forms(w)):
            n += 1
        elif not r("D-keyword-match"):
            lw, k = w.lower() if r("D-word-case") else w, kw
            forms = {k + "s", k + "es", k + "'s", k + "’s", k + "ed", k + "d", k + "ing"}
            if lw in forms or k in re.split(r"[-]", lw):
                n += 1
    return n


def relation(actual: int, rel: str, n: int) -> bool:
    if rel == "at least":
        return actual >= n
    if rel == "less than":
        return actual < n
    if rel == "at most":
        return actual <= n
    if rel in ("exactly", "equal"):
        return actual == n
    raise ValueError(f"unknown relation {rel!r}")


# ---------------------------------------------------------------- language

def _detect_langs(text: str):
    from langdetect import DetectorFactory, detect_langs
    from langdetect.lang_detect_exception import LangDetectException

    DetectorFactory.seed = 0
    try:
        return detect_langs(text)
    except LangDetectException:
        return []


def _prose(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text


NON_LATIN = re.compile(r"[^\P{L}\p{Latin}]")


def in_language(text: str, code: str, r: R) -> bool:
    prose = _prose(text)
    if code == "en" and r("D-language-mixed") and NON_LATIN.search(prose):
        return False
    if not re.search(r"\p{L}", prose):
        return False
    whole = _detect_langs(prose)
    if not whole or whole[0].lang != code:
        return False
    if not r("D-language-mixed"):
        return True
    for para in re.split(r"\n\s*\n", prose):
        letters = len(re.findall(r"\p{L}", para))
        if letters < 40:
            continue
        top = _detect_langs(para)
        if top and top[0].lang != code and top[0].prob > 0.9:
            return False
    return True


# ---------------------------------------------------------------- checks

CHECKS = {}


def chk(name):
    def deco(f):
        CHECKS[name] = f
        return f
    return deco


@chk("change_case:capital_word_frequency")
def _(t, kw, r, ctx):
    def caps(w):
        cased = [c for c in w if c.isupper() or c.islower()]
        return cased and all(c.isupper() for c in cased) and (r("D-allcaps-single") or len(cased) >= 2)
    return relation(sum(1 for w in words(t, r) if caps(w)), kw["capital_relation"], kw["capital_frequency"])


@chk("change_case:english_capital")
def _(t, kw, r, ctx):
    if any(c.islower() for c in t) or not re.search(r"\p{L}", t):
        return False
    return in_language(t, "en", r) if r("D-english") else True


@chk("change_case:english_lowercase")
def _(t, kw, r, ctx):
    if any(c.isupper() or c.istitle() for c in t) or not re.search(r"\p{L}", t):
        return False
    return in_language(t, "en", r) if r("D-english") else True


@chk("combination:two_responses")
def _(t, kw, r, ctx):
    parts = re.split(r"(?<!\*)\*{6}(?!\*)", t)
    if len(parts) != 2:
        return False
    a, b = parts[0].strip(), parts[1].strip()
    return bool(a) and bool(b) and a != b


@chk("copy:repeat_phrase")
def _(t, kw, r, ctx):
    phrase = words(kw["phrase"], R({"D-word-cjk": "B"}))
    n = len(phrase)
    if r("D-repeat-center"):
        centers = {n // 2} if n % 2 else {n // 2 - 1, n // 2}
    else:
        centers = set(range(1, n - 1))
    tw = words(t, r)
    variants = originals = 0
    i = 0
    while i + n <= len(tw):
        window = tw[i:i + n]
        diff = [j for j in range(n) if not same_word(window[j], phrase[j], r)]
        if not diff:
            originals += 1
            i += n
        elif len(diff) == 1 and diff[0] in centers:
            variants += 1
            i += n
        else:
            i += 1
    if not r("D-repeat-original") and originals:
        return False
    return variants == kw["small_n"]


@chk("count:count_unique")
def _(t, kw, r, ctx):
    ws = [w.lower() if r("D-word-case") else w for w in words(t, r)]
    return len(ws) == len(set(ws))


@chk("count:counting_composition")
def _(t, kw, r, ctx):
    paras = re.split(r"(?m)^[ \t]*\* \* \*[ \t]*$", t)
    if len(paras) != 3 or any(not p.strip() for p in paras):
        return False
    for p in paras:
        ss = sentences(p, r)
        if len(ss) != kw["n_sent"] or any(len(words(s, r)) != kw["n_words"] for s in ss):
            return False
    return True


@chk("count:lowercase_counting")
def _(t, kw, r, ctx):
    lower = [w for w in words(t, r) if any(c.islower() for c in w) and not any(c.isupper() for c in w)]
    if r("D-lowercase-counting"):
        counts = {}
        for w in lower:
            counts[w] = counts.get(w, 0) + 1
        return all(c <= kw["N"] for c in counts.values())
    return len(lower) <= kw["N"]


@chk("detectable_content:number_placeholders")
def _(t, kw, r, ctx):
    pat = r"\[([^\[\]\n]*\S[^\[\]\n]*)\]" if r("D-placeholder-link") else r"\[([^\[\]\n]*\S[^\[\]\n]*)\](?!\()"
    return len(re.findall(pat, t)) >= kw["num_placeholders"]


POSTSCRIPT_LINE = r"^[ \t]*(?:[#>*_]+[ \t]*)*"


@chk("detectable_content:postscript")
def _(t, kw, r, ctx):
    marker = kw["postscript_marker"]
    shown = ctx.get("shown_marker", marker) if r("D-postscript-dot") else marker
    if shown == "P.S.":
        pat = r"P\.S\."
    elif shown == "P.S":
        pat = r"P\.S(?![A-Za-z])"
    elif shown == "P.P.S":
        pat = r"P\.P\.S"
    else:
        pat = re.escape(shown)
    flags = re.M if r("D-postscript-case") else re.M | re.I
    lines = t.split("\n")
    hits = [i for i, line in enumerate(lines) if re.match(POSTSCRIPT_LINE + pat, line, flags=flags & ~re.M)]
    if not hits:
        return False
    if not r("D-postscript-end"):
        return True
    i = hits[-1]
    # blocks after the marker's block: each must itself start with a postscript marker
    rest = "\n".join(lines[i:])
    blocks = re.split(r"\n[ \t]*\n", rest)
    later = blocks[1:]
    any_marker = POSTSCRIPT_LINE + r"P\.(?:P\.)?S"
    return all(not b.strip() or re.match(any_marker, b.lstrip("\n"), flags=0 if r("D-postscript-case") else re.I) for b in later)


@chk("detectable_format:bigram_wrapping")
def _(t, kw, r, ctx):
    groups = re.findall(r"<<(.*?)>>", t, flags=re.S)
    rest = re.sub(r"<<.*?>>", " ", t, flags=re.S)
    if words(rest, r) or not groups:
        return False
    sizes = [len(words(g, r)) for g in groups]
    if all(s == 2 for s in sizes):
        return True
    if r("D-bigram-odd") and all(s == 2 for s in sizes[:-1]) and sizes[-1] == 1:
        return True
    return False


OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


@chk("detectable_format:constrained_response")
def _(t, kw, r, ctx):
    if r("D-constrained-exact"):
        return t.strip() in OPTIONS
    return len({o for o in OPTIONS if o in t}) == 1


def _reject_constant(name):
    raise ValueError(name)


@chk("detectable_format:json_format")
def _(t, kw, r, ctx):
    s = t.strip()
    m = re.match(r"^```[A-Za-z0-9_+-]*[ \t]*\n(.*?)\n?```$", s, flags=re.S)
    if m:
        s = m.group(1).strip()
    try:
        value = json.loads(s, parse_constant=_reject_constant)
    except (ValueError, RecursionError):  # RecursionError: nesting deeper than Python's json can parse
        return False
    return isinstance(value, (dict, list)) if r("D-json-scalar") else True


@chk("detectable_format:multiple_sections")
def _(t, kw, r, ctx):
    flags = 0 if r("D-section-case") else re.I
    pat = re.compile(r"^[ \t]*(?:[#>*_]+[ \t]*)*" + re.escape(kw["section_spliter"]) + r"[ \t]+(\d+)\b", flags=flags | re.M)
    ms = list(pat.finditer(t))
    n = kw["num_sections"]
    if not (len(ms) == n if r("D-section-count") else len(ms) >= n):
        return False
    if not r("D-section-preamble") and ms and t[: ms[0].start()].strip():
        return False
    if not r("D-section-numbering") and [int(m.group(1)) for m in ms] != list(range(1, len(ms) + 1)):
        return False
    return True


HR = re.compile(r"^[ \t]*([*\-_])(?:[ \t]*\1){2,}[ \t]*$")


@chk("detectable_format:number_bullet_lists")
def _(t, kw, r, ctx):
    markers = "*-+" if r("D-bullet-marker") else "*"
    n = 0
    for line in t.split("\n"):
        if HR.match(line):
            continue
        m = re.match(r"^[ \t]*([*\-+])[ \t]+\S", line)
        if m and m.group(1) in markers:
            n += 1
    return n == kw["num_bullets"]


@chk("detectable_format:number_highlighted_sections")
def _(t, kw, r, ctx):
    inner = r"(?:[^\s*][^*\n]*?[^\s*]|[^\s*])"
    n = len(re.findall(r"(?<!\*)\*" + inner + r"\*(?!\*)", t))
    if r("D-highlight-bold"):
        n += len(re.findall(r"(?<!\*)\*\*" + inner + r"\*\*(?!\*)", t))
    return n >= kw["num_highlights"]


ABBREV_END = ABBREV


@chk("detectable_format:sentence_hyphens")
def _(t, kw, r, ctx):
    s = t if r("D-sentence") else t.replace("\n", " ")
    if "\n" in s.strip():
        return False
    s = s.strip()
    joins = set()
    for m in END.finditer(s):
        e = m.end()
        if e >= len(s):
            continue
        nxt = s[e]
        if nxt.isspace():
            if _is_abbrev(s, m.start()):
                continue
            return False
        if nxt == "-":
            if e + 1 < len(s) and s[e + 1].isspace():
                return False
            joins.add(e)
        elif CJK_END.search(m.group(0)):
            return False
    if not r("D-hyphen-plural") and not joins:
        return False
    if not r("D-hyphen-inner"):
        return all(i in joins for i, ch in enumerate(s) if ch == "-")
    return True


def _outside_brackets(t: str) -> str:
    depth, out = 0, []
    for ch in t:
        if ch == "[":
            depth += 1
            out.append(" ")
        elif ch == "]" and depth:
            depth -= 1
            out.append(" ")
        else:
            out.append(ch if depth == 0 else " ")
    return "".join(out)


@chk("detectable_format:square_brackets")
def _(t, kw, r, ctx):
    if r("D-brackets-per-word"):
        groups = re.findall(r"\[([^\[\]]*)\]", t)
        rest = re.sub(r"\[[^\[\]]*\]", " ", t)
        if words(rest, r) or any(len(words(g, r)) > 1 for g in groups):
            return False
    elif words(_outside_brackets(t), r):
        return False
    if not r("D-bracket-punct"):
        return all(tok.startswith("[") and tok.endswith("]") for tok in t.split())
    return True


@chk("detectable_format:title")
def _(t, kw, r, ctx):
    m = re.search(r"<<([^\n]*?)>>", t)
    if not r("D-title-position"):
        if not t.lstrip().startswith("<<"):
            return False
    return any(g.strip() for g in re.findall(r"<<([^\n]*?)>>", t))


@chk("first_word:first_word_answer")
def _(t, kw, r, ctx):
    w = first_word(t, r)
    return w is not None and same_word(w, kw["first_word"], r)


@chk("first_word:first_word_sent")
def _(t, kw, r, ctx):
    ss = sentences(t, r)
    return bool(ss) and all((fw := first_word(s, r)) is not None and same_word(fw, kw["first_word"], r) for s in ss)


@chk("keywords:existence")
def _(t, kw, r, ctx):
    return all(occurrences(t, k, r) > 0 for k in kw["keywords"])


@chk("keywords:forbidden_words")
def _(t, kw, r, ctx):
    return all(occurrences(t, k, r) == 0 for k in kw["forbidden_words"])


@chk("keywords:frequency")
def _(t, kw, r, ctx):
    return relation(occurrences(t, kw["keyword"], r), kw["relation"], kw["frequency"])


@chk("keywords:keyword_specific_position")
def _(t, kw, r, ctx):
    ss = sentences(t, r)
    if len(ss) < kw["n"]:
        return False
    ws = words(ss[kw["n"] - 1], r)
    return len(ws) >= kw["m"] and same_word(ws[kw["m"] - 1], kw["keyword"], r)


def _letter_count(t, letter, r):
    if r("D-letter-case"):
        return sum(1 for c in t if c.lower() == letter.lower())
    return t.count(letter.lower())


@chk("keywords:letter_frequency")
def _(t, kw, r, ctx):
    return relation(_letter_count(t, kw["letter"], r), kw["let_relation"], kw["let_frequency"])


CHECKS["letters:letter_counting2"] = CHECKS["keywords:letter_frequency"]


@chk("keywords:no_adjacent_consecutive")
def _(t, kw, r, ctx):
    ws = words(t, r)
    for a, b in zip(ws, ws[1:]):
        x, y = a[0].lower(), b[0].lower()
        if not (len(x) == 1 and len(y) == 1 and "a" <= x <= "z" and "a" <= y <= "z"):
            continue
        d = ord(y) - ord(x)
        if d == 1 or (r("D-consecutive-order") and d == -1):
            return False
    return True


@chk("keywords:palindrome")
def _(t, kw, r, ctx):
    minimum = 3 if r("D-palindrome-length") else 1
    ws = [re.sub(r"[^\p{L}\p{N}]", "", w).lower() for w in words(t, r)]
    ws = [w for w in ws if w]
    for w in ws:
        if len(w) >= minimum and w == w[::-1] and re.search(r"\p{L}", w):
            return True
    for i in range(len(ws)):
        joined = ws[i]
        for j in range(i + 1, min(i + 8, len(ws))):
            joined += ws[j]
            if len(joined) >= max(minimum, 3) and joined == joined[::-1] and re.search(r"\p{L}", joined):
                return True
    return False


@chk("keywords:start_end")
def _(t, kw, r, ctx):
    s = t.rstrip()
    if not s or not re.match(r"[\p{L}\p{M}\p{N}]", s[-1]):
        return False
    a, b = first_word(t, r), last_word(t, r)
    return a is not None and b is not None and same_word(a, b, r)


@chk("keywords:word_count_different_numbers")
def _(t, kw, r, ctx):
    n = occurrences(t, kw["keyword"], r)
    return n == kw["frequency"] if r("D-word-count-relation") else n >= kw["frequency"]


@chk("keywords:word_once")
def _(t, kw, r, ctx):
    return occurrences(t, kw["keyword"], r) >= 1


@chk("language:response_language")
def _(t, kw, r, ctx):
    return in_language(t, kw["language"], r)


@chk("last_word:last_word_answer")
def _(t, kw, r, ctx):
    w = last_word(t, r)
    return w is not None and same_word(w, kw["last_word"], r)


@chk("last_word:last_word_sent")
def _(t, kw, r, ctx):
    ss = sentences(t, r)
    return bool(ss) and all((lw := last_word(s, r)) is not None and same_word(lw, kw["last_word"], r) for s in ss)


def blank_paragraphs(t, r):
    if r("D-blank-run"):
        return [p for p in re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", t) if p.strip()]
    return t.split("\n\n")


@chk("length_constraints:nth_paragraph_first_word")
def _(t, kw, r, ctx):
    ps = blank_paragraphs(t, r)
    n, i = kw["num_paragraphs"], kw["nth_paragraph"]
    if len(ps) != n or not 1 <= i <= n:
        return False
    fw = first_word(ps[i - 1], r)
    return fw is not None and same_word(fw, kw["first_word"], r)


def divider_paragraphs(t, n, r):
    parts = re.split(r"(?m)^[ \t]*\*\*\*[ \t]*$", t)
    if not r("D-divider-edge"):
        if parts and not parts[0].strip():
            parts = parts[1:]
        if parts and not parts[-1].strip():
            parts = parts[:-1]
    return len(parts) == n and all(p.strip() for p in parts)


@chk("length_constraints:number_paragraphs")
def _(t, kw, r, ctx):
    return divider_paragraphs(t, kw["num_paragraphs"], r)


@chk("paragraphs:paragraphs")
def _(t, kw, r, ctx):
    return divider_paragraphs(t, 2, r)


@chk("paragraphs:paragraphs2")
def _(t, kw, r, ctx):
    ps = blank_paragraphs(t, r)
    return len(ps) == 2 and all(p.strip() for p in ps)


@chk("length_constraints:number_sentences")
def _(t, kw, r, ctx):
    return relation(len(sentences(t, r)), kw["relation"], kw["num_sentences"])


@chk("length_constraints:number_words")
def _(t, kw, r, ctx):
    return relation(len(words(t, r)), kw["relation"], kw["num_words"])


@chk("letters:letter_counting")
def _(t, kw, r, ctx):
    n = sum(1 for c in t if c.isalpha()) if r("D-letter-unit") else len(words(t, r))
    return relation(n, kw["relation"], kw["N"])


@chk("punctuation:no_comma")
def _(t, kw, r, ctx):
    chars = ",，、،﹐﹑" if r("D-comma-chars") else ","
    return not any(c in t for c in chars)


@chk("punctuation:punctuation_dot")
def _(t, kw, r, ctx):
    chars = ".．…" if r("D-dot-chars") else "."
    return not any(c in t for c in chars)


@chk("punctuation:punctuation_exclamation")
def _(t, kw, r, ctx):
    chars = "!！¡" if r("D-exclamation-chars") else "!"
    return not any(c in t for c in chars)


@chk("startend:end_checker")
def _(t, kw, r, ctx):
    s = t.rstrip()
    if r("D-end-trailing"):
        s = s.rstrip("*_\"'”’ \t\n")
    p = kw["end_phrase"]
    return s.endswith(p) if r("D-end-case") else s.lower().endswith(p.lower())


@chk("startend:quotation")
def _(t, kw, r, ctx):
    s = t.strip()
    if len(s) < 2:
        return False
    if s[0] == '"' and s[-1] == '"':
        return True
    return r("D-quote-chars") and s[0] == "“" and s[-1] == "”"


assert len(CHECKS) == 47, len(CHECKS)


def check(iid: str, kwargs, text: str, readings=None, ctx=None) -> bool:
    return check_used(iid, kwargs, text, readings, ctx)[0]


def check_used(iid: str, kwargs, text: str, readings=None, ctx=None) -> tuple[bool, set]:
    """The verdict and the decision entries the check consulted (only those can change it)."""
    r = R(readings)
    t = text.strip() if r("D-outer-whitespace") else text
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    return bool(CHECKS[iid](t, kw, r, ctx or {})), set(r.used)


def shown_postscript_marker(prompt: str, marker: str) -> str:
    """The marker as the prompt shows it (contract section 5)."""
    if marker == "P.S." and not re.search(r"postscript starting with P\.S\.", prompt):
        return "P.S"
    return marker


def grade_row(record: dict, raw: str, prompt: str, reasoning_model: bool, readings=None):
    """(reward, per-constraint verdicts, extraction_failed)."""
    text = graded_text(raw, reasoning_model)
    if text is None:
        return 0.0, [False] * len(record["instruction_id_list"]), True
    verdicts = []
    for iid, kw in zip(record["instruction_id_list"], record["kwargs"]):
        ctx = {}
        if iid == "detectable_content:postscript":
            ctx["shown_marker"] = shown_postscript_marker(prompt, kw["postscript_marker"])
        verdicts.append(check(iid, kw, text, readings, ctx))
    return float(all(verdicts)), verdicts, False
