"""Replacement grader: the contracts of audit/contracts.md, with one switch per decision entry.

`grade(text, instruction_id, kwargs, prompt, readings)` returns True or False for one
constraint on the graded text. The graded text is the model's visible answer (see
`graded_text`). Every decision entry `D-<topic>` is a field of `Readings`; the
defaults are the proposed readings. The language checks (english_*, response_language)
use langdetect with seed 0 as an approximation of "is written in language X"; the
contracts cannot be implemented exactly without a human or a judge.
"""

from __future__ import annotations

import dataclasses
import json
import re
import unicodedata

# ---------------------------------------------------------------- readings


@dataclasses.dataclass(frozen=True)
class Readings:
    markup_transparent: bool = True  # D-markup-transparent
    word_hyphen_one: bool = True  # D-word-hyphen
    unspaced_run_one_word: bool = True  # D-word-unspaced
    sentence_lines: bool = True  # D-sentence-lines
    list_label_not_sentence: bool = True  # D-list-label
    word_case_insensitive: bool = True  # D-word-case
    keyword_whole_word: bool = True  # D-keyword-boundary
    letter_case_insensitive: bool = True  # D-letter-case
    blank_line_run_one_separator: bool = True  # D-paragraph-blank-lines
    divider_own_line: bool = True  # D-divider-line
    divider_empty_fails: bool = True  # D-divider-empty
    capital_single_counts: bool = True  # D-capital-single
    empty_not_english: bool = True  # D-empty-english
    two_separator_exactly_six: bool = True  # D-two-separator
    repeat_any_inner_word: bool = True  # D-repeat-center
    repeat_unchanged_copy_fails: bool = True  # D-repeat-original
    unique_case_insensitive: bool = True  # D-unique-case
    lowercase_per_word: bool = True  # D-lowercase-counting
    placeholder_link_counts: bool = True  # D-placeholder
    postscript_at_end: bool = True  # D-postscript-end
    postscript_case_insensitive: bool = True  # D-postscript-case
    postscript_line_start_only: bool = False  # D-postscript-line (proposed: line start or after a sentence end)
    consecutive_any_alphabet: bool = True  # D-consecutive-script
    bigram_odd_allowed: bool = True  # D-bigram-odd
    constrained_extra_allowed: bool = True  # D-constrained-extra
    json_scalar_ok: bool = True  # D-json-scalar
    section_case_insensitive: bool = True  # D-section-case
    section_markup_ok: bool = True  # D-section-markup
    section_preamble_ok: bool = True  # D-section-preamble
    bullet_plus_minus: bool = True  # D-bullet-markers
    bullet_nested_counts: bool = True  # D-bullet-nested
    highlight_bold_counts: bool = True  # D-highlight-bold
    hyphen_single_passes: bool = True  # D-hyphen-single
    bracket_one_word_per_pair: bool = True  # D-bracket-group
    title_anywhere: bool = True  # D-title-position
    empty_each_fails: bool = True  # D-empty-each
    consecutive_either_order: bool = True  # D-consecutive-order
    palindrome_min_letters: int = 3  # D-palindrome-length (3, 2 or 1)
    start_end_trailing_whitespace_ok: bool = True  # D-start-end-trailing
    start_end_single_word_passes: bool = True  # D-start-end-single
    letters_any_script: bool = True  # D-letter-def
    comma_all_forms: bool = True  # D-comma-unicode
    dot_all_forms: bool = True  # D-dot-unicode
    exclamation_all_forms: bool = True  # D-exclamation-unicode
    end_case_exact: bool = True  # D-end-case
    end_only_whitespace_after: bool = True  # D-end-trailing
    quotation_typographic: bool = True  # D-quotation-typographic


PROPOSED = Readings()

# Map each decision entry to its Readings field and the value of its other reading.
DECISIONS = {
    "D-markup-transparent": ("markup_transparent", False),
    "D-word-hyphen": ("word_hyphen_one", False),
    "D-word-unspaced": ("unspaced_run_one_word", False),
    "D-sentence-lines": ("sentence_lines", False),
    "D-list-label": ("list_label_not_sentence", False),
    "D-word-case": ("word_case_insensitive", False),
    "D-keyword-boundary": ("keyword_whole_word", False),
    "D-letter-case": ("letter_case_insensitive", False),
    "D-paragraph-blank-lines": ("blank_line_run_one_separator", False),
    "D-divider-line": ("divider_own_line", False),
    "D-divider-empty": ("divider_empty_fails", False),
    "D-capital-single": ("capital_single_counts", False),
    "D-empty-english": ("empty_not_english", False),
    "D-two-separator": ("two_separator_exactly_six", False),
    "D-repeat-center": ("repeat_any_inner_word", False),
    "D-repeat-original": ("repeat_unchanged_copy_fails", False),
    "D-unique-case": ("unique_case_insensitive", False),
    "D-lowercase-counting": ("lowercase_per_word", False),
    "D-placeholder": ("placeholder_link_counts", False),
    "D-postscript-end": ("postscript_at_end", False),
    "D-postscript-case": ("postscript_case_insensitive", False),
    "D-postscript-line": ("postscript_line_start_only", True),
    "D-consecutive-script": ("consecutive_any_alphabet", False),
    "D-bigram-odd": ("bigram_odd_allowed", False),
    "D-constrained-extra": ("constrained_extra_allowed", False),
    "D-json-scalar": ("json_scalar_ok", False),
    "D-section-case": ("section_case_insensitive", False),
    "D-section-markup": ("section_markup_ok", False),
    "D-section-preamble": ("section_preamble_ok", False),
    "D-bullet-markers": ("bullet_plus_minus", False),
    "D-bullet-nested": ("bullet_nested_counts", False),
    "D-highlight-bold": ("highlight_bold_counts", False),
    "D-hyphen-single": ("hyphen_single_passes", False),
    "D-bracket-group": ("bracket_one_word_per_pair", False),
    "D-title-position": ("title_anywhere", False),
    "D-empty-each": ("empty_each_fails", False),
    "D-consecutive-order": ("consecutive_either_order", False),
    "D-palindrome-length": ("palindrome_min_letters", 1),
    "D-start-end-trailing": ("start_end_trailing_whitespace_ok", False),
    "D-start-end-single": ("start_end_single_word_passes", False),
    "D-letter-def": ("letters_any_script", False),
    "D-comma-unicode": ("comma_all_forms", False),
    "D-dot-unicode": ("dot_all_forms", False),
    "D-exclamation-unicode": ("exclamation_all_forms", False),
    "D-end-case": ("end_case_exact", False),
    "D-end-trailing": ("end_only_whitespace_after", False),
    "D-quotation-typographic": ("quotation_typographic", False),
}

# ---------------------------------------------------------------- graded text

THINK_CLOSE = "</think>"


def graded_text(raw: str, reasoning_model: bool) -> str | None:
    """G1: the visible answer, or None for an extraction failure (reasoning never closed)."""
    if reasoning_model:
        if THINK_CLOSE not in raw:
            return None
        raw = raw[raw.rfind(THINK_CLOSE) + len(THINK_CLOSE):]
    return raw.strip()


# ---------------------------------------------------------------- words

_UNSPACED = (
    "぀-ヿ"  # kana
    "㐀-䶿一-鿿豈-﫿"  # han
    "฀-๿"  # thai
)
# A word character is a letter, a digit, or a combining mark after one (Indic vowel signs
# belong to their word). An abbreviation of single letters joined by periods (U.S., P.P.S,
# e.g.) is one word. Uses the `regex` module for \p{..} classes.
import regex as _rx  # noqa: E402

_WC = r"[\p{L}\p{N}][\p{L}\p{N}\p{M}]*"
_ABBR = r"(?<![\p{L}\p{N}\p{M}])\p{L}(?:\.\p{L})+\.?(?![\p{L}\p{N}])"
_WORD_HYPHEN = _rx.compile(_ABBR + r"|" + _WC + r"(?:(?:['’\-]|(?<=\d)[.,](?=\d))" + _WC + r")*")
_WORD_NO_HYPHEN = _rx.compile(_ABBR + r"|" + _WC + r"(?:(?:['’]|(?<=\d)[.,](?=\d))" + _WC + r")*")
_UNSPACED_CHAR = re.compile("[" + _UNSPACED + "]")


_HTML_TAG = re.compile(r"(?<!<)</?[A-Za-z][A-Za-z0-9]*(?:\s[^<>\n]*)?/?>(?!>)")


def _blank_tags(text: str, r: Readings) -> str:
    """D-markup-transparent: an HTML tag is markup, not words (blanked, keeping offsets)."""
    if not r.markup_transparent:
        return text
    return _HTML_TAG.sub(lambda m: " " * len(m.group(0)), text)


def words(text: str, r: Readings = PROPOSED) -> list[str]:
    pattern = _WORD_HYPHEN if r.word_hyphen_one else _WORD_NO_HYPHEN
    found = pattern.findall(_blank_tags(text, r))
    if r.unspaced_run_one_word:
        return found
    out: list[str] = []
    for w in found:
        if _UNSPACED_CHAR.search(w):
            buf = ""
            for ch in w:
                if _UNSPACED_CHAR.match(ch):
                    if buf:
                        out.append(buf)
                        buf = ""
                    out.append(ch)
                else:
                    buf += ch
            if buf:
                out.append(buf)
        else:
            out.append(w)
    return out


def word_spans(text: str, r: Readings = PROPOSED) -> list[tuple[int, int, str]]:
    pattern = _WORD_HYPHEN if r.word_hyphen_one else _WORD_NO_HYPHEN
    return [(m.start(), m.end(), m.group(0)) for m in pattern.finditer(_blank_tags(text, r))]


def _drop_list_label(text: str, r: Readings) -> str:
    """D-list-label: a leading list label is not a word of the text (blanked, keeping offsets)."""
    if not r.list_label_not_sentence:
        return text
    return _LIST_MARKER.sub(lambda m: " " * len(m.group(0)), text, count=1)


def same_word(a: str, b: str, r: Readings = PROPOSED) -> bool:
    if r.word_case_insensitive:
        return a.casefold() == b.casefold()
    return a == b


def _first_token_raw(text: str) -> str:
    parts = text.split()
    return parts[0].rstrip(".,;:!?") if parts else ""


def _last_token_raw(text: str) -> str:
    parts = text.split()
    return parts[-1].rstrip(".,;:!?") if parts else ""


def first_word(text: str, r: Readings = PROPOSED) -> str:
    text = _drop_list_label(text, r)
    if not r.markup_transparent:
        return _first_token_raw(text)
    w = words(text, r)
    return w[0] if w else ""


def last_word(text: str, r: Readings = PROPOSED) -> str:
    if not r.markup_transparent:
        return _last_token_raw(text)
    w = words(text, r)
    return w[-1] if w else ""


def keyword_count(text: str, keyword: str, r: Readings = PROPOSED) -> int:
    if not r.keyword_whole_word:
        return len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))
    target = words(keyword, r)
    if not target:
        return 0
    toks = words(text, r)
    k = len(target)
    n = 0
    for i in range(len(toks) - k + 1):
        if all(same_word(toks[i + j], target[j], r) for j in range(k)):
            n += 1
    return n


def letter_count(text: str, letter: str, r: Readings = PROPOSED) -> int:
    if r.letter_case_insensitive:
        return sum(1 for c in text if c.casefold() == letter.casefold())
    return text.count(letter)


def relation_ok(count: int, relation: str, n: int) -> bool:
    if relation == "less than":
        return count < n
    if relation == "at least":
        return count >= n
    if relation == "at most":
        return count <= n
    if relation in ("exactly", "equal"):
        return count == n
    raise ValueError(f"unknown relation {relation!r}")


# ---------------------------------------------------------------- sentences

_ABBREV = {
    "e.g", "i.e", "mr", "mrs", "ms", "dr", "prof", "st", "vs", "etc", "inc", "ltd", "jr", "sr",
    "co", "no", "fig", "approx", "dept", "est", "u.s", "u.k", "a.m", "p.m", "ph.d", "cf", "al",
}
_ALWAYS_ABBREV = {"e.g", "i.e", "cf", "vs", "mr", "mrs", "ms", "dr", "prof"}
_TERMINATORS = ".!?…。！？"
_CLOSERS = "\"'”’)]」』*_"
_LIST_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)]|[A-Za-z][.)]|#{1,6})\s+")
_BOUNDARY = re.compile(
    "([" + re.escape(_TERMINATORS) + "]+)([" + re.escape(_CLOSERS) + r"]*)(\s+|$)"
)
_CJK_BOUNDARY = re.compile("([。！？]+)")


def _split_line(line: str) -> list[str]:
    out = []
    start = 0
    for m in _BOUNDARY.finditer(line):
        end_punct = m.start(1)
        prev = line[start:end_punct]
        tail_word = re.search(r"([A-Za-z.]+)$", prev)
        nxt = line[m.end():m.end() + 1]
        if m.group(1) == "." and tail_word:
            tw = tail_word.group(1).lower().rstrip(".")
            if tw in _ALWAYS_ABBREV:
                continue
            if (tw in _ABBREV or (len(tw) == 1 and tw.isalpha())) and nxt and (nxt.islower() or nxt.isdigit()):
                continue
        out.append(line[start:m.end()])
        start = m.end()
    if start < len(line):
        out.append(line[start:])
    # CJK terminators need no following space
    final = []
    for piece in out:
        parts = _CJK_BOUNDARY.split(piece)
        buf = ""
        for p in parts:
            buf += p
            if _CJK_BOUNDARY.fullmatch(p):
                final.append(buf)
                buf = ""
        if buf:
            final.append(buf)
    return final


def sentences(text: str, r: Readings = PROPOSED) -> list[str]:
    """G3. Pieces without a letter or digit are not sentences."""
    def strip(ln: str) -> str:
        return _LIST_MARKER.sub("", ln) if r.list_label_not_sentence else ln

    if r.sentence_lines:
        lines = text.split("\n")
    else:
        lines = [" ".join(strip(ln) for ln in text.split("\n"))]
    out = []
    for ln in lines:
        ln = strip(ln)
        for s in _split_line(ln):
            s = s.strip()
            if s and words(s, r):
                out.append(s)
    return out


# ---------------------------------------------------------------- paragraphs

_BLANK_RUN = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)*")


def blank_line_paragraphs(text: str, r: Readings = PROPOSED) -> list[str] | None:
    """G7. None when the text has an empty paragraph (other reading of D-paragraph-blank-lines)."""
    text = text.strip()
    if not text:
        return []
    if r.blank_line_run_one_separator:
        return [p for p in _BLANK_RUN.split(text) if p.strip()]
    pieces = text.split("\n\n")
    if any(not p.strip() for p in pieces):
        return None
    return pieces


def divider_paragraphs(text: str, dividers: tuple[str, ...], r: Readings = PROPOSED) -> list[str] | None:
    """G8. None when an empty piece makes the split invalid (D-divider-empty)."""
    if r.divider_own_line:
        pieces = [[]]
        for line in text.split("\n"):
            if line.strip() in dividers:
                pieces.append([])
            else:
                pieces[-1].append(line)
        texts = ["\n".join(p) for p in pieces]
    else:
        pattern = "|".join(re.escape(d) for d in dividers)
        texts = re.split(pattern, text)
    if r.divider_empty_fails:
        if any(not t.strip() for t in texts):
            if len(texts) == 1:
                return []
            return None
        return texts
    return [t for t in texts if t.strip()]


# ---------------------------------------------------------------- language

def _detect(text: str) -> str | None:
    import langdetect
    from langdetect import DetectorFactory

    DetectorFactory.seed = 0
    try:
        return langdetect.detect(text)
    except Exception:
        return None


def is_language(text: str, code: str) -> bool:
    """Approximation of D-english / response_language: langdetect on lower-cased text."""
    if not re.search(r"[^\W\d_]", text):
        return False
    return _detect(text.lower()) == code


def is_english(text: str, r: Readings = PROPOSED) -> bool:
    if not text.strip():
        return not r.empty_not_english
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    ascii_share = sum(1 for c in letters if c.isascii()) / len(letters)
    if ascii_share < 0.9:
        return False
    return _detect(text.lower()) == "en"


# ---------------------------------------------------------------- checks

COMMA_FORMS = {",", "，", "、", "،", "﹐", "﹑"}
DOT_FORMS = {".", "．", "…"}
EXCLAMATION_FORMS = {"!", "！", "¡", "‼", "⁉"}
CONSTRAINED = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


def _has_cased(w: str) -> bool:
    return any(c.isupper() or c.islower() for c in w)


def check(text: str, iid: str, kw: dict, prompt: str = "", r: Readings = PROPOSED) -> bool:
    kw = {k: v for k, v in (kw or {}).items() if v is not None}
    fn = CHECKS[iid]
    return bool(fn(text, kw, prompt, r))


def c_capital_word_frequency(t, kw, p, r):
    n = 0
    for w in words(t, r):
        if not _has_cased(w) or any(c.islower() for c in w):
            continue
        letters = sum(1 for c in w if c.isalpha())
        if letters < (1 if r.capital_single_counts else 2):
            continue
        n += 1
    return relation_ok(n, kw["capital_relation"], kw["capital_frequency"])


def c_english_capital(t, kw, p, r):
    if not t.strip():
        return not r.empty_not_english
    if any(c.islower() for c in t):
        return False
    return is_english(t, r)


def c_english_lowercase(t, kw, p, r):
    if not t.strip():
        return not r.empty_not_english
    if any(c.isupper() or unicodedata.category(c) == "Lt" for c in t):
        return False
    return is_english(t, r)


def c_two_responses(t, kw, p, r):
    runs = [m for m in re.finditer(r"\*+", t)]
    if r.two_separator_exactly_six:
        seps = [m for m in runs if len(m.group(0)) == 6]
    else:
        seps = [m for m in runs if len(m.group(0)) >= 6]
    if len(seps) != 1:
        return False
    a, b = t[: seps[0].start()].strip(), t[seps[0].end():].strip()
    if not a or not b:
        return False
    return " ".join(a.split()) != " ".join(b.split())


def c_repeat_phrase(t, kw, p, r):
    fold = (lambda w: w.casefold()) if r.word_case_insensitive else (lambda w: w)
    target = [fold(w) for w in words(kw["phrase"], r)]
    k = len(target)
    toks = [fold(w) for w in words(t, r)]
    n_changed = n_same = 0
    i = 0
    if k <= 2:
        inner = []
    elif r.repeat_any_inner_word:
        inner = list(range(1, k - 1))
    else:
        inner = sorted({(k - 1) // 2, k // 2}) if k % 2 == 0 else [k // 2]
    while i <= len(toks) - k:
        window = toks[i:i + k]
        diffs = [j for j in range(k) if window[j] != target[j]]
        if not diffs:
            n_same += 1
            i += k
        elif len(diffs) == 1 and diffs[0] in inner:
            n_changed += 1
            i += k
        else:
            i += 1
    if r.repeat_unchanged_copy_fails and n_same:
        return False
    return n_changed == kw["small_n"]


def c_count_unique(t, kw, p, r):
    ws = words(t, r)
    if r.unique_case_insensitive:
        ws = [w.casefold() for w in ws]
    return len(ws) == len(set(ws))


def c_counting_composition(t, kw, p, r):
    paras = divider_paragraphs(t, ("* * *", "***"), r)
    if not paras or len(paras) != 3:
        return False
    for para in paras:
        ss = sentences(para, r)
        if len(ss) != kw["n_sent"]:
            return False
        if any(len(words(s, r)) != kw["n_words"] for s in ss):
            return False
    return True


def c_lowercase_counting(t, kw, p, r):
    lower = [w for w in words(t, r) if _has_cased(w) and not any(c.isupper() for c in w)]
    if r.lowercase_per_word:
        counts = {}
        for w in lower:
            counts[w] = counts.get(w, 0) + 1
        return all(v <= kw["N"] for v in counts.values())
    return len(lower) <= kw["N"]


def c_number_placeholders(t, kw, p, r):
    n = 0
    for m in re.finditer(r"\[([^\[\]\n]*)\]", t):
        if not m.group(1).strip():
            continue
        if not r.placeholder_link_counts and t[m.end():m.end() + 1] == "(":
            continue
        n += 1
    return n >= kw["num_placeholders"]


def shown_postscript_marker(marker: str, prompt: str) -> str:
    """The marker as the prompt shows it (147 rows show `P.S.` as `P.S`)."""
    if not prompt:
        return marker
    if ("postscript starting with " + marker) in prompt:
        return marker
    if marker.endswith(".") and ("postscript starting with " + marker[:-1]) in prompt:
        return marker[:-1]
    return marker


def c_postscript(t, kw, p, r):
    marker = shown_postscript_marker(kw["postscript_marker"], p)
    flags = re.IGNORECASE if r.postscript_case_insensitive else 0
    lead_markup = r"[*_#>\s]*" if r.markup_transparent else r"[ \t]*"
    hits = []
    for m in re.finditer(re.escape(marker), t, flags):
        if m.start() > 0 and re.match(r"[\w.]", t[m.start() - 1]):
            continue  # inside a word, or the P.S of P.P.S
        line_start = t.rfind("\n", 0, m.start()) + 1
        before = t[line_start:m.start()]
        if re.fullmatch(lead_markup, before):
            hits.append(m.start())
        elif not r.postscript_line_start_only and re.search(
                "[" + re.escape(_TERMINATORS) + "][" + re.escape(_CLOSERS) + r"]*\s+" + lead_markup + "$", before):
            hits.append(m.start())  # D-postscript-line: after the end of a sentence
    if not hits:
        return False
    if not r.postscript_at_end:
        return True
    # the postscript (from the last marker on) must end the response: no later blank-line block
    after = t[hits[-1]:]
    return not re.search(r"\n[ \t]*\n\s*\S", after)


def c_bigram_wrapping(t, kw, p, r):
    groups = list(re.finditer(r"<<(.*?)>>", t))
    outside = re.sub(r"<<.*?>>", " ", t)
    if words(outside, r):
        return False
    if not groups:
        return not r.empty_each_fails
    counts = [len(words(g.group(1), r)) for g in groups]
    for i, c in enumerate(counts):
        if c == 2:
            continue
        if c == 1 and r.bigram_odd_allowed and i == len(counts) - 1:
            continue
        return False
    return True


def c_constrained_response(t, kw, p, r):
    if not r.constrained_extra_allowed:
        return t.strip() in CONSTRAINED
    present = [o for o in CONSTRAINED if o in t]
    return len(present) == 1


def c_json_format(t, kw, p, r):
    s = t.strip()
    m = re.match(r"^```[A-Za-z]*[ \t]*\n(.*)\n[ \t]*```$", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    elif s.startswith("```") and s.endswith("```") and len(s) >= 6:
        s = s[3:-3].strip()
    try:
        v = json.loads(s)
    except ValueError:
        return False
    return r.json_scalar_ok or isinstance(v, (dict, list))


def c_multiple_sections(t, kw, p, r):
    spl = kw["section_spliter"].strip()
    flags = re.IGNORECASE if r.section_case_insensitive else 0
    lead = r"^[ \t]*(?:#{1,6}[ \t]*)?(?:[*_]{1,3})?" if r.section_markup_ok else r"^[ \t]*"
    header = re.compile(lead + re.escape(spl) + r"[ \t]+(?:\d+|[IVXLC]+)\b", flags | re.MULTILINE)
    hits = list(header.finditer(t))
    if len(hits) != kw["num_sections"]:
        return False
    if not r.section_preamble_ok and t[: hits[0].start()].strip() if hits else False:
        return False
    for i, h in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(t)
        if not words(t[h.end():end], r):
            return False
    return True


_HR = re.compile(r"^\s*([*\-_])(?:\s*\1){2,}\s*$")


def c_number_bullet_lists(t, kw, p, r):
    marks = "*+-" if r.bullet_plus_minus else "*"
    pat = re.compile(r"^([ \t]*)[" + re.escape(marks) + r"][ \t]+\S")
    n = 0
    for line in t.split("\n"):
        if _HR.match(line):
            continue
        m = pat.match(line)
        if not m:
            continue
        if not r.bullet_nested_counts and len(m.group(1).expandtabs(4)) >= 2:
            continue
        n += 1
    return n == kw["num_bullets"]


_ITALIC = re.compile(r"(?<!\*)\*(?![\s*])([^*\n]+?)(?<![\s*])\*(?!\*)")
_BOLD = re.compile(r"(?<!\*)\*\*(?![\s*])([^*\n]+?)(?<![\s*])\*\*(?!\*)")


def c_number_highlighted_sections(t, kw, p, r):
    n = len(_ITALIC.findall(t))
    if r.highlight_bold_counts:
        n += len(_BOLD.findall(t))
    return n >= kw["num_highlights"]


_JOIN = re.compile("([" + re.escape(_TERMINATORS) + "][" + re.escape(_CLOSERS) + "]*)-(?=\\S)")


def c_sentence_hyphens(t, kw, p, r):
    s = t.strip()
    if not s:
        return not r.empty_each_fails
    if re.search("[" + re.escape(_TERMINATORS) + "][" + re.escape(_CLOSERS) + r"]*(?:[ \t]+-|-[ \t]+)", s):
        return False
    # a hyphen or dash with whitespace next to it connects with a space (also when the
    # sentences have no final punctuation, as in "one clause - another clause")
    body = "\n".join(_LIST_MARKER.sub("", ln) if r.list_label_not_sentence else ln for ln in s.split("\n"))
    if re.search(r"\s[-–—]|[-–—]\s", body):
        return False
    joined = _JOIN.sub(lambda m: m.group(1) + "⁠", s)  # word joiner: no whitespace, no boundary
    pieces = sentences(joined, r)
    n_joins = len(_JOIN.findall(s))
    if len(pieces) > 1:
        return False
    if n_joins == 0 and not r.hyphen_single_passes:
        return False
    return True


def c_square_brackets(t, kw, p, r):
    spans = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r"\[([^\[\]]*)\]", t)]
    ws = word_spans(t, r)
    if not ws:
        return not r.empty_each_fails
    for a, b, _ in ws:
        if not any(sa < a and b < sb for sa, sb, _ in spans):
            return False
    if r.bracket_one_word_per_pair:
        for _, _, inner in spans:
            if len(words(inner, r)) > 1:
                return False
    return True


def c_title(t, kw, p, r):
    for m in re.finditer(r"<<([^\n]*?)>>", t):
        if m.group(1).strip():
            if r.title_anywhere:
                return True
            first_line = next((ln for ln in t.split("\n") if ln.strip()), "")
            return m.group(0) in first_line
    return False


def c_first_word_answer(t, kw, p, r):
    fw = first_word(t, r)
    return bool(fw) and same_word(fw, kw["first_word"], r)


def c_first_word_sent(t, kw, p, r):
    ss = sentences(t, r)
    if not ss:
        return not r.empty_each_fails
    return all(same_word(first_word(s, r), kw["first_word"], r) for s in ss)


def c_existence(t, kw, p, r):
    return all(keyword_count(t, k, r) >= 1 for k in kw["keywords"])


def c_forbidden(t, kw, p, r):
    return all(keyword_count(t, k, r) == 0 for k in kw["forbidden_words"])


def c_frequency(t, kw, p, r):
    return relation_ok(keyword_count(t, kw["keyword"], r), kw["relation"], kw["frequency"])


def c_keyword_specific_position(t, kw, p, r):
    ss = sentences(t, r)
    n, m = kw["n"], kw["m"]
    if len(ss) < n:
        return False
    ws = words(ss[n - 1], r)
    if len(ws) < m:
        return False
    return same_word(ws[m - 1], kw["keyword"], r)


def c_letter_frequency(t, kw, p, r):
    return relation_ok(letter_count(t, kw["letter"], r), kw["let_relation"], kw["let_frequency"])


def c_no_adjacent_consecutive(t, kw, p, r):
    ws = words(t, r) if r.markup_transparent else t.split()
    alphabets = [("a", "z")] + ([("α", "ω"), ("а", "я")] if r.consecutive_any_alphabet else [])
    for a, b in zip(ws, ws[1:]):
        x, y = a[0].lower(), b[0].lower()
        if len(x) != 1 or len(y) != 1:
            continue
        if not any(lo <= x <= hi and lo <= y <= hi for lo, hi in alphabets):
            continue
        d = ord(y) - ord(x)
        if d == 1 or (r.consecutive_either_order and d == -1):
            return False
    return True


def c_palindrome(t, kw, p, r):
    # letters only: a word with digits ("Noon2024") is not a palindrome word; ' and - are dropped
    ws = [re.sub(r"['’\-.]", "", w).casefold() for w in words(t, r)]
    ws = [w if re.fullmatch(r"[^\W\d_]+", w) else "" for w in ws]
    for w in ws:
        if w and len(w) >= r.palindrome_min_letters and w == w[::-1]:
            return True
    # deliberate phrase palindromes: 2 to 10 whole words, at least 7 letters
    for i in range(len(ws)):
        s = ""
        for j in range(i, min(i + 10, len(ws))):
            s += ws[j]
            if j > i and len(s) >= 7 and s == s[::-1]:
                return True
    return False


def c_start_end(t, kw, p, r):
    s = t.strip() if r.start_end_trailing_whitespace_ok else t
    ws = word_spans(_drop_list_label(s, r), r)
    if not ws:
        return False
    if len(ws) == 1 and not r.start_end_single_word_passes:
        return False
    if s[ws[-1][1]:]:
        return False
    if not r.markup_transparent and s[: ws[0][0]].strip():
        return False
    return same_word(ws[0][2], ws[-1][2], r)


def c_word_count_different_numbers(t, kw, p, r):
    return keyword_count(t, kw["keyword"], r) == kw["frequency"]


def c_word_once(t, kw, p, r):
    return keyword_count(t, kw["keyword"], r) >= 1


def c_response_language(t, kw, p, r):
    if not t.strip():
        return False
    return is_language(t, kw["language"])


def c_last_word_answer(t, kw, p, r):
    lw = last_word(t, r)
    return bool(lw) and same_word(lw, kw["last_word"], r)


def c_last_word_sent(t, kw, p, r):
    ss = sentences(t, r)
    if not ss:
        return not r.empty_each_fails
    return all(same_word(last_word(s, r), kw["last_word"], r) for s in ss)


def c_nth_paragraph_first_word(t, kw, p, r):
    paras = blank_line_paragraphs(t, r)
    if paras is None or len(paras) != kw["num_paragraphs"]:
        return False
    i = kw["nth_paragraph"]
    if not 1 <= i <= len(paras):
        return False
    fw = first_word(paras[i - 1], r)
    return bool(fw) and same_word(fw, kw["first_word"], r)


def c_number_paragraphs(t, kw, p, r):
    paras = divider_paragraphs(t, ("***",), r)
    return paras is not None and len(paras) == kw["num_paragraphs"]


def c_paragraphs(t, kw, p, r):
    paras = divider_paragraphs(t, ("***",), r)
    return paras is not None and len(paras) == 2


def c_paragraphs2(t, kw, p, r):
    paras = blank_line_paragraphs(t, r)
    return paras is not None and len(paras) == 2


def c_number_sentences(t, kw, p, r):
    return relation_ok(len(sentences(t, r)), kw["relation"], kw["num_sentences"])


def c_number_words(t, kw, p, r):
    return relation_ok(len(words(t, r)), kw["relation"], kw["num_words"])


def c_letter_counting(t, kw, p, r):
    if r.letters_any_script:
        n = sum(1 for c in t if c.isalpha())
    else:
        n = len(re.findall(r"[A-Za-z]", t))
    return relation_ok(n, kw["relation"], kw["N"])


def c_no_comma(t, kw, p, r):
    forms = COMMA_FORMS if r.comma_all_forms else {","}
    return not any(c in forms for c in t)


def c_punctuation_dot(t, kw, p, r):
    forms = DOT_FORMS if r.dot_all_forms else {"."}
    return not any(c in forms for c in t)


def c_punctuation_exclamation(t, kw, p, r):
    forms = EXCLAMATION_FORMS if r.exclamation_all_forms else {"!"}
    return not any(c in forms for c in t)


def c_end_checker(t, kw, p, r):
    phrase = kw["end_phrase"].strip()
    s = t.rstrip()
    if not r.end_only_whitespace_after:
        s = re.sub(r"[\W_]+$", "", s)
        phrase = re.sub(r"[\W_]+$", "", phrase)
    if r.end_case_exact:
        return s.endswith(phrase)
    return s.casefold().endswith(phrase.casefold())


def c_quotation(t, kw, p, r):
    s = t.strip()
    if len(s) <= 2:
        return False
    opens = ('"', "“") if r.quotation_typographic else ('"',)
    closes = ('"', "”") if r.quotation_typographic else ('"',)
    return s[0] in opens and s[-1] in closes


CHECKS = {
    "change_case:capital_word_frequency": c_capital_word_frequency,
    "change_case:english_capital": c_english_capital,
    "change_case:english_lowercase": c_english_lowercase,
    "combination:two_responses": c_two_responses,
    "copy:repeat_phrase": c_repeat_phrase,
    "count:count_unique": c_count_unique,
    "count:counting_composition": c_counting_composition,
    "count:lowercase_counting": c_lowercase_counting,
    "detectable_content:number_placeholders": c_number_placeholders,
    "detectable_content:postscript": c_postscript,
    "detectable_format:bigram_wrapping": c_bigram_wrapping,
    "detectable_format:constrained_response": c_constrained_response,
    "detectable_format:json_format": c_json_format,
    "detectable_format:multiple_sections": c_multiple_sections,
    "detectable_format:number_bullet_lists": c_number_bullet_lists,
    "detectable_format:number_highlighted_sections": c_number_highlighted_sections,
    "detectable_format:sentence_hyphens": c_sentence_hyphens,
    "detectable_format:square_brackets": c_square_brackets,
    "detectable_format:title": c_title,
    "first_word:first_word_answer": c_first_word_answer,
    "first_word:first_word_sent": c_first_word_sent,
    "keywords:existence": c_existence,
    "keywords:forbidden_words": c_forbidden,
    "keywords:frequency": c_frequency,
    "keywords:keyword_specific_position": c_keyword_specific_position,
    "keywords:letter_frequency": c_letter_frequency,
    "keywords:no_adjacent_consecutive": c_no_adjacent_consecutive,
    "keywords:palindrome": c_palindrome,
    "keywords:start_end": c_start_end,
    "keywords:word_count_different_numbers": c_word_count_different_numbers,
    "keywords:word_once": c_word_once,
    "language:response_language": c_response_language,
    "last_word:last_word_answer": c_last_word_answer,
    "last_word:last_word_sent": c_last_word_sent,
    "length_constraints:nth_paragraph_first_word": c_nth_paragraph_first_word,
    "length_constraints:number_paragraphs": c_number_paragraphs,
    "length_constraints:number_sentences": c_number_sentences,
    "length_constraints:number_words": c_number_words,
    "letters:letter_counting": c_letter_counting,
    "letters:letter_counting2": c_letter_frequency,
    "paragraphs:paragraphs": c_paragraphs,
    "paragraphs:paragraphs2": c_paragraphs2,
    "punctuation:no_comma": c_no_comma,
    "punctuation:punctuation_dot": c_punctuation_dot,
    "punctuation:punctuation_exclamation": c_punctuation_exclamation,
    "startend:end_checker": c_end_checker,
    "startend:quotation": c_quotation,
}

# Which checks each decision can change (used to re-grade only the affected constraints).
_ALL = set(CHECKS)
_WORDISH = _ALL - {
    "punctuation:no_comma", "punctuation:punctuation_dot", "punctuation:punctuation_exclamation",
    "startend:quotation", "detectable_format:json_format", "detectable_format:constrained_response",
    "keywords:letter_frequency", "letters:letter_counting2", "letters:letter_counting",
    "combination:two_responses", "length_constraints:number_paragraphs", "paragraphs:paragraphs",
    "paragraphs:paragraphs2", "detectable_format:number_bullet_lists",
    "detectable_format:number_highlighted_sections", "detectable_format:title",
    "detectable_content:number_placeholders", "change_case:english_capital",
    "change_case:english_lowercase", "language:response_language", "startend:end_checker",
}
AFFECTS = {
    "D-markup-transparent": {"first_word:first_word_answer", "first_word:first_word_sent", "last_word:last_word_answer",
                             "last_word:last_word_sent", "length_constraints:nth_paragraph_first_word",
                             "detectable_content:postscript", "keywords:start_end",
                             "keywords:no_adjacent_consecutive"},
    "D-word-hyphen": _WORDISH,
    "D-word-unspaced": _WORDISH,
    "D-sentence-lines": {"length_constraints:number_sentences", "first_word:first_word_sent", "last_word:last_word_sent",
                         "keywords:keyword_specific_position", "detectable_format:sentence_hyphens",
                         "count:counting_composition"},
    "D-list-label": {"first_word:first_word_answer", "length_constraints:nth_paragraph_first_word", "keywords:start_end",
                     "length_constraints:number_sentences", "first_word:first_word_sent", "last_word:last_word_sent",
                     "keywords:keyword_specific_position", "detectable_format:sentence_hyphens",
                     "count:counting_composition"},
    "D-word-case": {"first_word:first_word_answer", "first_word:first_word_sent", "last_word:last_word_answer",
                    "last_word:last_word_sent", "length_constraints:nth_paragraph_first_word", "keywords:existence",
                    "keywords:forbidden_words", "keywords:frequency", "keywords:keyword_specific_position",
                    "keywords:word_count_different_numbers", "keywords:word_once", "keywords:start_end",
                    "copy:repeat_phrase"},
    "D-keyword-boundary": {"keywords:existence", "keywords:forbidden_words", "keywords:frequency",
                           "keywords:word_count_different_numbers", "keywords:word_once"},
    "D-letter-case": {"keywords:letter_frequency", "letters:letter_counting2"},
    "D-paragraph-blank-lines": {"length_constraints:nth_paragraph_first_word", "paragraphs:paragraphs2"},
    "D-divider-line": {"length_constraints:number_paragraphs", "paragraphs:paragraphs", "count:counting_composition"},
    "D-divider-empty": {"length_constraints:number_paragraphs", "paragraphs:paragraphs", "count:counting_composition"},
    "D-capital-single": {"change_case:capital_word_frequency"},
    "D-empty-english": {"change_case:english_capital", "change_case:english_lowercase"},
    "D-two-separator": {"combination:two_responses"},
    "D-repeat-center": {"copy:repeat_phrase"},
    "D-repeat-original": {"copy:repeat_phrase"},
    "D-unique-case": {"count:count_unique"},
    "D-lowercase-counting": {"count:lowercase_counting"},
    "D-placeholder": {"detectable_content:number_placeholders"},
    "D-postscript-end": {"detectable_content:postscript"},
    "D-postscript-case": {"detectable_content:postscript"},
    "D-postscript-line": {"detectable_content:postscript"},
    "D-consecutive-script": {"keywords:no_adjacent_consecutive"},
    "D-bigram-odd": {"detectable_format:bigram_wrapping"},
    "D-constrained-extra": {"detectable_format:constrained_response"},
    "D-json-scalar": {"detectable_format:json_format"},
    "D-section-case": {"detectable_format:multiple_sections"},
    "D-section-markup": {"detectable_format:multiple_sections"},
    "D-section-preamble": {"detectable_format:multiple_sections"},
    "D-bullet-markers": {"detectable_format:number_bullet_lists"},
    "D-bullet-nested": {"detectable_format:number_bullet_lists"},
    "D-highlight-bold": {"detectable_format:number_highlighted_sections"},
    "D-hyphen-single": {"detectable_format:sentence_hyphens"},
    "D-bracket-group": {"detectable_format:square_brackets"},
    "D-title-position": {"detectable_format:title"},
    "D-empty-each": {"first_word:first_word_sent", "last_word:last_word_sent", "detectable_format:sentence_hyphens",
                     "detectable_format:square_brackets", "detectable_format:bigram_wrapping"},
    "D-consecutive-order": {"keywords:no_adjacent_consecutive"},
    "D-palindrome-length": {"keywords:palindrome"},
    "D-start-end-trailing": {"keywords:start_end"},
    "D-start-end-single": {"keywords:start_end"},
    "D-letter-def": {"letters:letter_counting"},
    "D-comma-unicode": {"punctuation:no_comma"},
    "D-dot-unicode": {"punctuation:punctuation_dot"},
    "D-exclamation-unicode": {"punctuation:punctuation_exclamation"},
    "D-end-case": {"startend:end_checker"},
    "D-end-trailing": {"startend:end_checker"},
    "D-quotation-typographic": {"startend:quotation"},
}
assert set(AFFECTS) == set(DECISIONS)
