"""Replacement grader: an implementation of audit/CONTRACTS.md, one switch per decision entry.

`PROPOSED` uses every proposed reading. `Readings(<field>=<other value>)` flips one decision so that its
effect can be measured. Each field names its decision entry. Checks return True/False; `grade_text`
returns one verdict per constraint.

Approximations (stated in the audit report): English and response-language detection use langdetect
(seed 0) after removing code blocks and URLs, plus a Latin-script share for English; these are semantic
checks that the contract leaves to a reader.
"""
from __future__ import annotations

import json
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace

import regex as re


@dataclass(frozen=True)
class Readings:
    strip_whitespace: bool = True            # D-surrounding-whitespace
    empty_fails: bool = True                 # D-empty-response
    apostrophe_joins: bool = True            # D-word-apostrophe
    hyphen_joins: bool = True                # D-word-hyphen
    case_insensitive_words: bool = True      # D-word-case
    keyword_substring: bool = False          # D-keyword-substring (other reading: True)
    keyword_inflection: bool = False         # D-keyword-inflection (other reading: True)
    linebreak_ends_sentence: bool = True     # D-sentence-linebreak
    protect_abbreviations: bool = True       # D-sentence-abbreviation
    allcaps_short_words: bool = True         # D-allcaps-short-words
    english_lenient: bool = True             # D-english-detection
    two_responses_differ: bool = True        # D-two-responses-different
    repeat_center_middle_only: bool = False  # D-repeat-center (other reading: True)
    repeat_verbatim_fails: bool = True       # D-repeat-verbatim
    lowercase_per_word: bool = True          # D-lowercase-counting-scope
    placeholder_any: bool = True             # D-placeholder-content
    marker_markup_ok: bool = True            # D-markup-around-marker
    postscript_at_end: bool = True           # D-postscript-position
    bigram_odd_ok: bool = True               # D-bigram-odd
    constrained_exact: bool = True           # D-constrained-exact
    json_container_only: bool = True         # D-json-scalar
    section_case_sensitive: bool = True      # D-section-marker-case
    section_numbering: bool = True           # D-section-numbering
    section_preamble_ok: bool = True         # D-section-preamble
    bullet_all_markers: bool = True          # D-bullet-markers
    bullet_nested: bool = True               # D-bullet-nesting
    highlight_bold: bool = True              # D-highlight-bold
    hyphens_single_ok: bool = True           # D-sentence-hyphens-single
    brackets_each_word: bool = True          # D-square-brackets-grouping
    title_anywhere: bool = True              # D-title-position
    letter_case_insensitive: bool = True     # D-letter-case
    adjacent_cross_punct: bool = True        # D-adjacent-scope
    consecutive_both_orders: bool = True     # D-consecutive-order
    palindrome_min3: bool = True             # D-palindrome-length
    start_end_two_words: bool = True         # D-start-end-single
    leading_markup_ok: bool = True           # D-markup-around-word
    wcdn_exact: bool = True                  # D-wcdn-relation (other reading: at least)
    divider_own_line: bool = True            # D-divider-line
    empty_piece_fails: bool = True           # D-paragraph-empty-piece
    letters_are_chars: bool = True           # D-letter-counting-unit
    comma_variants: bool = True              # D-comma-variants
    dot_variants: bool = True                # D-dot-variants
    exclamation_variants: bool = True        # D-exclamation-variants
    end_nonwords_ok: bool = True             # D-end-trailing-nonwords (contract change C1)
    typographic_quotes: bool = True          # D-typographic-quotes
    postscript_case_sensitive: bool = True   # D-postscript-case
    end_case_sensitive: bool = True          # D-end-case
    palindrome_case_insensitive: bool = True # D-palindrome-case
    blank_line_whitespace: bool = True       # D-blank-line-whitespace
    paragraph_sep_any_count: bool = True     # D-paragraph-separator-count
    hyphens_spaces_inside_ok: bool = True    # D-sentence-hyphens-spaces
    letter_any_script: bool = True           # D-letter-script
    adjacent_latin_only: bool = True         # D-adjacent-alphabet
    postscript_line_start: bool = True       # D-postscript-line-start (change C3)
    section_line_start: bool = True          # D-section-line-start (change C3)
    two_responses_extra_sep_fails: bool = True  # D-two-responses-extra-separator (change C3)
    hyphens_spaced_dash_fails: bool = True   # D-sentence-hyphens-dash (change C3)


PROPOSED = Readings()

# Decision entry name for each switch, and the switch value of the other reading.
DECISION_SWITCHES = {
    "D-surrounding-whitespace": ("strip_whitespace", False),
    "D-empty-response": ("empty_fails", False),
    "D-word-apostrophe": ("apostrophe_joins", False),
    "D-word-hyphen": ("hyphen_joins", False),
    "D-word-case": ("case_insensitive_words", False),
    "D-keyword-substring": ("keyword_substring", True),
    "D-keyword-inflection": ("keyword_inflection", True),
    "D-sentence-linebreak": ("linebreak_ends_sentence", False),
    "D-sentence-abbreviation": ("protect_abbreviations", False),
    "D-allcaps-short-words": ("allcaps_short_words", False),
    "D-english-detection": ("english_lenient", False),
    "D-two-responses-different": ("two_responses_differ", False),
    "D-repeat-center": ("repeat_center_middle_only", True),
    "D-repeat-verbatim": ("repeat_verbatim_fails", False),
    "D-lowercase-counting-scope": ("lowercase_per_word", False),
    "D-placeholder-content": ("placeholder_any", False),
    "D-markup-around-marker": ("marker_markup_ok", False),
    "D-postscript-position": ("postscript_at_end", False),
    "D-bigram-odd": ("bigram_odd_ok", False),
    "D-constrained-exact": ("constrained_exact", False),
    "D-json-scalar": ("json_container_only", False),
    "D-section-marker-case": ("section_case_sensitive", False),
    "D-section-numbering": ("section_numbering", False),
    "D-section-preamble": ("section_preamble_ok", False),
    "D-bullet-markers": ("bullet_all_markers", False),
    "D-bullet-nesting": ("bullet_nested", False),
    "D-highlight-bold": ("highlight_bold", False),
    "D-sentence-hyphens-single": ("hyphens_single_ok", False),
    "D-square-brackets-grouping": ("brackets_each_word", False),
    "D-title-position": ("title_anywhere", False),
    "D-letter-case": ("letter_case_insensitive", False),
    "D-adjacent-scope": ("adjacent_cross_punct", False),
    "D-consecutive-order": ("consecutive_both_orders", False),
    "D-palindrome-length": ("palindrome_min3", False),
    "D-start-end-single": ("start_end_two_words", False),
    "D-markup-around-word": ("leading_markup_ok", False),
    "D-wcdn-relation": ("wcdn_exact", False),
    "D-divider-line": ("divider_own_line", False),
    "D-paragraph-empty-piece": ("empty_piece_fails", False),
    "D-letter-counting-unit": ("letters_are_chars", False),
    "D-comma-variants": ("comma_variants", False),
    "D-dot-variants": ("dot_variants", False),
    "D-exclamation-variants": ("exclamation_variants", False),
    "D-end-trailing-nonwords": ("end_nonwords_ok", False),
    "D-typographic-quotes": ("typographic_quotes", False),
    "D-postscript-case": ("postscript_case_sensitive", False),
    "D-end-case": ("end_case_sensitive", False),
    "D-palindrome-case": ("palindrome_case_insensitive", False),
    "D-blank-line-whitespace": ("blank_line_whitespace", False),
    "D-paragraph-separator-count": ("paragraph_sep_any_count", False),
    "D-sentence-hyphens-spaces": ("hyphens_spaces_inside_ok", False),
    "D-letter-script": ("letter_any_script", False),
    "D-adjacent-alphabet": ("adjacent_latin_only", False),
    "D-postscript-line-start": ("postscript_line_start", False),
    "D-section-line-start": ("section_line_start", False),
    "D-two-responses-extra-separator": ("two_responses_extra_sep_fails", False),
    "D-sentence-hyphens-dash": ("hyphens_spaced_dash_fails", False),
}


def flipped(entry: str) -> Readings:
    field, value = DECISION_SWITCHES[entry]
    return replace(PROPOSED, **{field: value})


# ---------------------------------------------------------------- graded text

def graded_text(raw: str, reasoning_model: bool) -> str | None:
    """Contract section 0: text after the last </think>; None is an extraction failure."""
    if reasoning_model:
        if "</think>" not in raw:
            return None
        return raw[raw.rfind("</think>") + len("</think>"):]
    return raw


# ---------------------------------------------------------------- tokens

_ALNUM = r"[\p{L}\p{M}\p{N}]"


def _word_re(r: Readings):
    joiners = []
    if r.apostrophe_joins:
        joiners.append("['’]")
    if r.hyphen_joins:
        joiners.append("-")
    if joiners:
        return re.compile(_ALNUM + "+(?:(?:" + "|".join(joiners) + ")" + _ALNUM + "+)*")
    return re.compile(_ALNUM + "+")


_WORD_RE_CACHE: dict = {}


def word_matches(text: str, r: Readings):
    key = (r.apostrophe_joins, r.hyphen_joins)
    if key not in _WORD_RE_CACHE:
        _WORD_RE_CACHE[key] = _word_re(r)
    return list(_WORD_RE_CACHE[key].finditer(text))


def words(text: str, r: Readings) -> list[str]:
    return [m.group(0) for m in word_matches(text, r)]


def same_word(a: str, b: str, r: Readings) -> bool:
    if r.case_insensitive_words:
        return a.casefold() == b.casefold()
    return a == b


ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e", "u.s", "u.k", "a.m", "p.m",
    "no", "fig", "approx", "inc", "ltd", "co", "mt", "dept", "est", "vol", "ch", "cf", "al",
}
_TERMINAL = "[.!?。！？]+"
_CLOSERS = "[\"'”’)\\]*_]*"  # change C3: markdown emphasis may close a sentence ("done.*")


def sentences(text: str, r: Readings) -> list[str]:
    """Sentences that contain at least one word (contract section 0)."""
    pieces = []
    blocks = text.split("\n") if r.linebreak_ends_sentence else [text.replace("\n", " ")]
    for block in blocks:
        start = 0
        # change C3: a CJK full stop ends a sentence without a following space
        for m in re.finditer(_TERMINAL + _CLOSERS + r"(?=\s|$)|[。！？]+" + _CLOSERS, block):
            end = m.end()
            if r.protect_abbreviations and m.group(0) == ".":
                before = block[start:m.start()]
                tail = re.search(r"([\p{L}.]+)$", before)
                token = tail.group(1).lower() if tail else ""
                if token in ABBREVIATIONS or re.fullmatch(r"\p{L}", token or "") and token.isalpha() and before[-1:].isupper():
                    continue
                if re.fullmatch(r"\s*\d+", before) and not pieces_in_block(block[:start]):
                    # a list label such as "1." at the start of a line
                    continue
            pieces.append(block[start:end])
            start = end
        pieces.append(block[start:])
    return [p.strip() for p in pieces if words(p, r)]


def pieces_in_block(prefix: str) -> bool:
    return bool(prefix.strip())


def blank_line_paragraphs(text: str, r: Readings) -> list[str]:
    ws = "[ \\t\\u00a0\\u3000]*" if r.blank_line_whitespace else ""
    if r.paragraph_sep_any_count:
        sep = "\\n" + ws + "(?:\\n" + ws + ")+"
        parts = re.split(sep, text)
        return [p for p in parts if p.strip()]
    parts = text.split("\n\n")
    if any(not p.strip() for p in parts[1:-1]):
        return ["", ""] + parts  # an empty paragraph breaks the count
    return [p for p in parts if p.strip()]


def first_word_of(text: str, r: Readings) -> str | None:
    ms = word_matches(text, r)
    if not ms:
        return None
    if not r.leading_markup_ok and text.lstrip()[:1] != ms[0].group(0)[:1]:
        return None
    return ms[0].group(0)


def compare(actual: int, relation: str, n: int) -> bool:
    if relation == "less than":
        return actual < n
    if relation == "at least":
        return actual >= n
    if relation == "at most":
        return actual <= n
    if relation in ("exactly", "equal"):
        return actual == n
    raise ValueError(f"unknown relation {relation!r}")


def count_keyword(text: str, keyword: str, r: Readings) -> int:
    if r.keyword_substring:
        return text.casefold().count(keyword.casefold()) if r.case_insensitive_words else text.count(keyword)
    kws = keyword.split()
    ws = words(text, r)
    if r.hyphen_joins and len(kws) == 1 and "-" not in keyword:
        pass
    count = 0
    for i in range(len(ws) - len(kws) + 1):
        ok = True
        for j, k in enumerate(kws):
            w = ws[i + j]
            if same_word(w, k, r):
                continue
            if r.keyword_inflection and j == len(kws) - 1:
                wl, kl = w.casefold(), k.casefold()
                if wl.startswith(kl) and wl[len(kl):] in ("s", "es", "ed", "d", "ing", "er", "ers"):
                    continue
            ok = False
            break
        if ok:
            count += 1
    return count


# ---------------------------------------------------------------- language

def _strip_code(text: str) -> str:
    text = re.sub(r"```.*?(```|$)", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text


def _detect(text: str) -> str | None:
    import langdetect
    from langdetect import DetectorFactory

    DetectorFactory.seed = 0
    try:
        return langdetect.detect(text)
    except Exception:
        return None


def is_latin(c: str) -> bool:
    try:
        return "LATIN" in unicodedata.name(c)
    except ValueError:
        return False


def is_english(text: str, r: Readings) -> bool:
    body = _strip_code(text)
    letters = [c for c in body if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if is_latin(c))
    if r.english_lenient:
        if latin / len(letters) < 0.9:
            return False
        if len(letters) < 30:
            return True
        return _detect(body.lower()) == "en"
    return latin == len(letters) and _detect(body.lower()) == "en"


# ---------------------------------------------------------------- checks

COMMAS = {",", "，", "、", "،", "﹐", "﹑", "⸴"}
DOTS = {".", "．", "。", "…", "｡"}
EXCLAMATIONS = {"!", "！", "¡", "‼", "⁉", "❗", "❕"}
MARKUP_PREFIX = re.compile(r"^[\s>#*_~`\"'“”]*")  # change C3: quotation marks too


def check(iid: str, kw: dict, g: str, r: Readings = PROPOSED) -> bool:
    if r.strip_whitespace:
        g = g.strip()
    if r.empty_fails and not g.strip():
        return False
    fn = CHECKS[iid]
    return bool(fn(kw, g, r))


def _capital_word_frequency(kw, g, r):
    n = 0
    for w in words(g, r):
        letters = [c for c in w if c.isalpha()]
        if not letters or any(c.islower() for c in letters) or not any(c.isupper() for c in letters):
            continue
        if not r.allcaps_short_words and len(letters) < 2:
            continue
        n += 1
    return compare(n, kw["capital_relation"], kw["capital_frequency"])


def _english_capital(kw, g, r):
    return not any(c.islower() for c in g) and any(c.isalpha() for c in g) and is_english(g, r)


def _english_lowercase(kw, g, r):
    return not any(c.isupper() for c in g) and any(c.isalpha() for c in g) and is_english(g, r)


def _two_responses(kw, g, r):
    runs = list(re.finditer(r"\*+", g))
    seps = [m for m in runs if len(m.group(0)) == 6]
    if not r.two_responses_extra_sep_fails:
        # other reading: a separator with nothing before it or after it is ignored
        seps = [m for m in seps if g[: m.start()].strip() and g[m.end():].strip()]
    if len(seps) != 1:
        return False
    a, b = g[: seps[0].start()].strip(), g[seps[0].end():].strip()
    if not r.two_responses_extra_sep_fails:
        a = re.sub(r"^\*{6}|\*{6}$", "", a).strip()
        b = re.sub(r"^\*{6}|\*{6}$", "", b).strip()
    if not a or not b:
        return False
    return a != b if r.two_responses_differ else True


def _repeat_phrase(kw, g, r):
    phrase = kw["phrase"].split()
    n = kw["small_n"]
    ws = words(g, r)
    plen = len(phrase)
    if plen < 3:
        return False
    if r.repeat_center_middle_only:
        allowed = {plen // 2} if plen % 2 else {plen // 2 - 1, plen // 2}
    else:
        allowed = set(range(1, plen - 1))
    transformed = verbatim = 0
    i = 0
    while i <= len(ws) - plen:
        window = ws[i: i + plen]
        diffs = [j for j in range(plen) if not same_word(window[j], phrase[j], r)]
        if not diffs:
            verbatim += 1
            i += plen
        elif len(diffs) == 1 and diffs[0] in allowed:
            transformed += 1
            i += plen
        else:
            i += 1
    if r.repeat_verbatim_fails and verbatim:
        return False
    return transformed == n


def _count_unique(kw, g, r):
    ws = [w.casefold() if r.case_insensitive_words else w for w in words(g, r)]
    return bool(ws) and len(ws) == len(set(ws))


def _counting_composition(kw, g, r):
    parts = re.split(r"(?m)^[ \t]*\*[ \t]*\*[ \t]*\*[ \t]*$", g)
    parts = [p for p in parts]
    if any(not p.strip() for p in parts) or len(parts) != 3:
        return False
    for p in parts:
        ss = sentences(p, r)
        if len(ss) != kw["n_sent"]:
            return False
        if any(len(words(s, r)) != kw["n_words"] for s in ss):
            return False
    return True


def _lowercase_counting(kw, g, r):
    lower = []
    for w in words(g, r):
        cased = [c for c in w if c.isupper() or c.islower()]
        if cased and all(c.islower() for c in cased):
            lower.append(w)
    if r.lowercase_per_word:
        return all(c <= kw["N"] for c in Counter(lower).values())
    return len(lower) <= kw["N"]


def _number_placeholders(kw, g, r):
    n = 0
    for m in re.finditer(r"\[([^\[\]\n]+)\]", g):
        content = m.group(1)
        if not content.strip():
            continue
        if not r.placeholder_any:
            if g[m.end(): m.end() + 1] == "(" or not re.search(r"\p{L}", content):
                continue
        n += 1
    return n >= kw["num_placeholders"]


_PS_ANY = re.compile(r"^(?:P\.\s?)+S\b\.?", re.I)


def _strip_marker_markup(line: str, r: Readings) -> str:
    return MARKUP_PREFIX.sub("", line) if r.marker_markup_ok else line.lstrip()


def _postscript(kw, g, r):
    marker = kw["postscript_marker"]
    lines = g.split("\n")
    idx = None
    for i, line in enumerate(lines):
        body = _strip_marker_markup(line, r)
        if not r.postscript_line_start:
            # other reading of D-postscript-line-start: the marker may follow text on its line
            pos = (line if r.postscript_case_sensitive else line.lower()).find(
                marker if r.postscript_case_sensitive else marker.lower())
            hit = pos >= 0 and not (pos > 0 and line[pos - 1].isalnum()) and \
                not (marker == "P.S." and line[max(0, pos - 2): pos].upper() == "P.")
        elif r.postscript_case_sensitive:
            hit = body.startswith(marker)
        else:
            hit = body.lower().startswith(marker.lower())
        if hit:
            idx = i
            if not r.postscript_at_end:
                return True
    if idx is None:
        return False
    if not r.postscript_at_end:
        return True
    # Every later paragraph must itself be a postscript (P.S., P.P.S, ...).
    rest = "\n".join(lines[idx + 1:])
    for para in blank_line_paragraphs(rest, r):
        if not _PS_ANY.match(_strip_marker_markup(para.lstrip("\n"), r)):
            return False
    return True


def _bigram_wrapping(kw, g, r):
    groups = list(re.finditer(r"<<(.*?)>>", g, flags=re.S))
    outside = re.sub(r"<<.*?>>", " ", g, flags=re.S)
    if words(outside, r) or not groups:
        return False
    counts = [len(words(m.group(1), r)) for m in groups]
    total = sum(counts)
    for i, c in enumerate(counts):
        if c == 2:
            continue
        if c == 1 and r.bigram_odd_ok and total % 2 == 1 and i == len(counts) - 1:
            continue
        return False
    return True


OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


def _constrained_response(kw, g, r):
    s = g.strip()
    if r.constrained_exact:
        return s in OPTIONS
    found = {o for o in OPTIONS if o in s}
    return len(found) == 1


def _json_format(kw, g, r):
    s = g.strip()
    m = re.fullmatch(r"```[A-Za-z]*[ \t]*\n?(.*?)\n?[ \t]*```", s, flags=re.S)
    if m:
        s = m.group(1).strip()

    def bad_constant(x):
        raise ValueError(x)

    try:
        value = json.loads(s, parse_constant=bad_constant)
    except ValueError:
        return False
    return isinstance(value, (dict, list)) if r.json_container_only else True


def _multiple_sections(kw, g, r):
    spliter = kw["section_spliter"].strip()
    prefix = r"[ \t]*(?:[#>*_\"'“”]+[ \t]*)?" if r.marker_markup_ok else r"[ \t]*"
    flags = re.M if r.section_case_sensitive else re.M | re.I
    start = "^" + prefix if r.section_line_start else r"(?<![\p{L}\p{N}])"
    pat = re.compile(start + re.escape(spliter) + r"[ \t]+(\d+)\b", flags)
    ms = list(pat.finditer(g))
    if len(ms) != kw["num_sections"]:
        return False
    nums = [int(m.group(1)) for m in ms]
    if r.section_numbering and nums != list(range(1, len(nums) + 1)):
        return False
    if ms and not r.section_preamble_ok and g[: ms[0].start()].strip():
        return False
    for i, m in enumerate(ms):
        content = g[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(g)]
        content = re.sub(r"^[^\n]*", lambda x: re.sub(r"^[\s*_#:.)\-]*", "", x.group(0)), content, count=1)
        if not words(content, r):
            return False
    return True


_HR = re.compile(r"^[ \t]*([*\-_])(?:[ \t]*\1){2,}[ \t]*$")


def _number_bullet_lists(kw, g, r):
    marker = r"[*+\-]" if r.bullet_all_markers else r"\*"
    pat = re.compile(r"^([ \t]*)" + marker + r"[ \t]+\S")
    n = 0
    for line in g.split("\n"):
        if _HR.match(line):
            continue
        m = pat.match(line)
        if not m:
            continue
        if not r.bullet_nested and len(m.group(1).expandtabs(4)) >= 2:
            continue
        n += 1
    return n == kw["num_bullets"]


def _number_highlighted_sections(kw, g, r):
    n = 0
    text = g
    if r.highlight_bold:
        bold = re.compile(r"\*\*(?=\S)([^*\n]+?)(?<=\S)\*\*")
        n += len(bold.findall(text))
        text = bold.sub(" ", text)
    else:
        text = re.sub(r"\*\*(?=\S)([^*\n]+?)(?<=\S)\*\*", " ", text)
    single = re.compile(r"(?<!\*)\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?!\*)")
    n += len(single.findall(text))
    return n >= kw["num_highlights"]


def _sentence_hyphens(kw, g, r):
    if not r.hyphens_spaces_inside_ok and re.search(r"\s", g):
        return False
    if r.hyphens_spaced_dash_fails and re.search(r"[\p{L}\p{N}.!?。！？][ \t]+[-–—]|[-–—][ \t]+[\p{L}\p{N}]", g):
        # change C3, D-sentence-hyphens-dash: a dash with a space beside it joins sentences with a space
        return False
    boundaries = 0
    for m in re.finditer(_TERMINAL + _CLOSERS, g):
        after = g[m.end(): m.end() + 2]
        if not after:
            continue
        if after[0] == "-":
            if after[1:2].isspace():
                return False
            boundaries += 1
            continue
        if not after[0].isspace() and (m.group(0)[-1] in "。！？" or (m.group(0)[0] in "!?" and after[0].isalpha())):
            # a sentence end directly followed by the next sentence, with no hyphen
            return False
        if after[0].isspace():
            if r.protect_abbreviations and m.group(0) == ".":
                tail = re.search(r"([\p{L}.]+)$", g[: m.start()])
                if tail and tail.group(1).lower() in ABBREVIATIONS:
                    continue
            if words(g[m.end():], r):
                return False
    if r.linebreak_ends_sentence:
        lines = [ln for ln in g.split("\n") if words(ln, r)]
        if len(lines) > 1:
            return False
    if boundaries == 0 and not r.hyphens_single_ok:
        return False
    return True


def _square_brackets(kw, g, r):
    groups = list(re.finditer(r"\[([^\[\]]*)\]", g))
    outside = re.sub(r"\[[^\[\]]*\]", " ", g)
    if words(outside, r) or not groups:
        return False
    for m in groups:
        c = len(words(m.group(1), r))
        if r.brackets_each_word and c > 1:
            return False
    return True


def _title(kw, g, r):
    found = [m for m in re.finditer(r"<<([^\n<>]+)>>", g) if m.group(1).strip()]
    if not found:
        return False
    if r.title_anywhere:
        return True
    first = next((ln for ln in g.split("\n") if ln.strip()), "")
    return any(m.group(0) in first for m in found)


def _first_word_answer(kw, g, r):
    w = first_word_of(g, r)
    return w is not None and same_word(w, kw["first_word"], r)


def _first_word_sent(kw, g, r):
    ss = sentences(g, r)
    if not ss:
        return False
    for s in ss:
        w = first_word_of(s, r)
        if w is None or not same_word(w, kw["first_word"], r):
            return False
    return True


def _existence(kw, g, r):
    return all(count_keyword(g, k, r) > 0 for k in kw["keywords"])


def _forbidden(kw, g, r):
    return all(count_keyword(g, k, r) == 0 for k in kw["forbidden_words"])


def _frequency(kw, g, r):
    return compare(count_keyword(g, kw["keyword"], r), kw["relation"], kw["frequency"])


def _keyword_specific_position(kw, g, r):
    ss = sentences(g, r)
    n, m = kw["n"], kw["m"]
    if len(ss) < n:
        return False
    ws = words(ss[n - 1], r)
    return len(ws) >= m and same_word(ws[m - 1], kw["keyword"], r)


def _letter_frequency(kw, g, r):
    letter = kw["letter"]
    if r.letter_case_insensitive:
        n = sum(1 for c in g if c.lower() == letter.lower())
    else:
        n = g.count(letter)
    return compare(n, kw["let_relation"], kw["let_frequency"])


def _no_adjacent_consecutive(kw, g, r):
    if r.adjacent_cross_punct:
        seqs = [words(g, r)]
    else:
        seqs = [words(p, r) for p in re.split(r"[.!?;:,\n。！？]+", g)]
    for ws in seqs:
        for a, b in zip(ws, ws[1:]):
            x, y = a[0].lower()[:1], b[0].lower()[:1]  # "İ".lower() has two code points
            if r.adjacent_latin_only:
                if not ("a" <= x <= "z" and "a" <= y <= "z"):
                    continue
            elif not (x.isalpha() and y.isalpha()):
                continue
            d = ord(y) - ord(x)
            if d == 1 or (r.consecutive_both_orders and d == -1):
                return False
    return True


def _palindrome(kw, g, r):
    ws = words(g, r)
    norm = [("".join(c for c in w if c.isalnum())) for w in ws]
    if r.palindrome_case_insensitive:
        norm = [w.casefold() for w in norm]
    minimum = 3 if r.palindrome_min3 else 1
    for w in norm:
        letters = sum(1 for c in w if c.isalpha())
        if letters >= minimum and w == w[::-1]:
            return True
    for size in range(2, 11):
        for i in range(len(norm) - size + 1):
            s = "".join(norm[i: i + size])
            if len(s) >= 7 and len(set(norm[i: i + size])) > 1 and s == s[::-1]:
                return True
    return False


def _start_end(kw, g, r):
    ms = word_matches(g, r)
    if not ms:
        return False
    if r.start_end_two_words and len(ms) < 2:
        return False
    if not r.leading_markup_ok and g.lstrip()[:1] != ms[0].group(0)[:1]:
        return False
    if len(g.rstrip()) != ms[-1].end():
        # something (punctuation or markup) follows the last word
        return False
    return same_word(ms[0].group(0), ms[-1].group(0), r)


def _word_count_different_numbers(kw, g, r):
    c = count_keyword(g, kw["keyword"], r)
    return c == kw["frequency"] if r.wcdn_exact else c >= kw["frequency"]


def _word_once(kw, g, r):
    return count_keyword(g, kw["keyword"], r) >= 1


def _response_language(kw, g, r):
    body = _strip_code(g)
    if not any(c.isalpha() for c in body):
        return False
    return _detect(body) == kw["language"]


def _last_word_answer(kw, g, r):
    ws = words(g, r)
    return bool(ws) and same_word(ws[-1], kw["last_word"], r)


def _last_word_sent(kw, g, r):
    ss = sentences(g, r)
    if not ss:
        return False
    for s in ss:
        ws = words(s, r)
        if not ws or not same_word(ws[-1], kw["last_word"], r):
            return False
    return True


def _nth_paragraph_first_word(kw, g, r):
    ps = blank_line_paragraphs(g, r)
    if len(ps) != kw["num_paragraphs"] or kw["nth_paragraph"] > len(ps) or kw["nth_paragraph"] < 1:
        return False
    if any(not p.strip() for p in ps):
        return False
    w = first_word_of(ps[kw["nth_paragraph"] - 1], r)
    return w is not None and same_word(w, kw["first_word"], r)


def _divider_paragraphs(g, r):
    if r.divider_own_line:
        parts = re.split(r"(?m)^[ \t]*\*\*\*[ \t]*$", g)
    else:
        parts = re.split(r"\*\*\*", g)
    if r.empty_piece_fails:
        if any(not p.strip() for p in parts):
            return None
        return parts
    return [p for p in parts if p.strip()]


def _number_paragraphs(kw, g, r):
    parts = _divider_paragraphs(g, r)
    return parts is not None and len(parts) == kw["num_paragraphs"]


def _paragraphs(kw, g, r):
    parts = _divider_paragraphs(g, r)
    return parts is not None and len(parts) == 2


def _paragraphs2(kw, g, r):
    ps = blank_line_paragraphs(g, r)
    return len(ps) == 2 and all(p.strip() for p in ps)


def _number_sentences(kw, g, r):
    return compare(len(sentences(g, r)), kw["relation"], kw["num_sentences"])


def _number_words(kw, g, r):
    return compare(len(words(g, r)), kw["relation"], kw["num_words"])


def _letter_counting(kw, g, r):
    if r.letters_are_chars:
        if r.letter_any_script:
            n = sum(1 for c in g if c.isalpha())
        else:
            n = sum(1 for c in g if c.isascii() and c.isalpha())
    else:
        n = len(words(g, r))
    return compare(n, kw["relation"], kw["N"])


def _no_comma(kw, g, r):
    s = COMMAS if r.comma_variants else {","}
    return not any(c in s for c in g)


def _no_dot(kw, g, r):
    s = DOTS if r.dot_variants else {"."}
    return not any(c in s for c in g)


def _no_exclamation(kw, g, r):
    s = EXCLAMATIONS if r.exclamation_variants else {"!"}
    return not any(c in s for c in g)


def _end_checker(kw, g, r):
    phrase = kw["end_phrase"].strip()
    s = g.rstrip()
    hay, needle = (s, phrase) if r.end_case_sensitive else (s.lower(), phrase.lower())
    if not r.end_nonwords_ok:
        return hay.endswith(needle)
    i = hay.rfind(needle)
    if i < 0:
        return False
    return not re.search(_ALNUM, hay[i + len(needle):])


def _quotation(kw, g, r):
    s = g.strip()
    if len(s) < 2:
        return False
    opens = {'"', "“", "”", "„"} if r.typographic_quotes else {'"'}
    closes = {'"', "”", "“"} if r.typographic_quotes else {'"'}
    return s[0] in opens and s[-1] in closes


CHECKS = {
    "change_case:capital_word_frequency": _capital_word_frequency,
    "change_case:english_capital": _english_capital,
    "change_case:english_lowercase": _english_lowercase,
    "combination:two_responses": _two_responses,
    "copy:repeat_phrase": _repeat_phrase,
    "count:count_unique": _count_unique,
    "count:counting_composition": _counting_composition,
    "count:lowercase_counting": _lowercase_counting,
    "detectable_content:number_placeholders": _number_placeholders,
    "detectable_content:postscript": _postscript,
    "detectable_format:bigram_wrapping": _bigram_wrapping,
    "detectable_format:constrained_response": _constrained_response,
    "detectable_format:json_format": _json_format,
    "detectable_format:multiple_sections": _multiple_sections,
    "detectable_format:number_bullet_lists": _number_bullet_lists,
    "detectable_format:number_highlighted_sections": _number_highlighted_sections,
    "detectable_format:sentence_hyphens": _sentence_hyphens,
    "detectable_format:square_brackets": _square_brackets,
    "detectable_format:title": _title,
    "first_word:first_word_answer": _first_word_answer,
    "first_word:first_word_sent": _first_word_sent,
    "keywords:existence": _existence,
    "keywords:forbidden_words": _forbidden,
    "keywords:frequency": _frequency,
    "keywords:keyword_specific_position": _keyword_specific_position,
    "keywords:letter_frequency": _letter_frequency,
    "keywords:no_adjacent_consecutive": _no_adjacent_consecutive,
    "keywords:palindrome": _palindrome,
    "keywords:start_end": _start_end,
    "keywords:word_count_different_numbers": _word_count_different_numbers,
    "keywords:word_once": _word_once,
    "language:response_language": _response_language,
    "last_word:last_word_answer": _last_word_answer,
    "last_word:last_word_sent": _last_word_sent,
    "length_constraints:nth_paragraph_first_word": _nth_paragraph_first_word,
    "length_constraints:number_paragraphs": _number_paragraphs,
    "length_constraints:number_sentences": _number_sentences,
    "length_constraints:number_words": _number_words,
    "letters:letter_counting": _letter_counting,
    "letters:letter_counting2": _letter_frequency,
    "paragraphs:paragraphs": _paragraphs,
    "paragraphs:paragraphs2": _paragraphs2,
    "punctuation:no_comma": _no_comma,
    "punctuation:punctuation_dot": _no_dot,
    "punctuation:punctuation_exclamation": _no_exclamation,
    "startend:end_checker": _end_checker,
    "startend:quotation": _quotation,
}


def grade_text(g: str | None, ids, kwargs_list, r: Readings = PROPOSED) -> list[bool]:
    """One verdict per constraint; an extraction failure (None) fails every check."""
    out = []
    for iid, kw in zip(ids, kwargs_list):
        kw = {k: v for k, v in (kw or {}).items() if v is not None}
        out.append(False if g is None else check(iid, kw, g, r))
    return out
