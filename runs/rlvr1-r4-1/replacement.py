"""Replacement grader: the contracts of audit/CONTRACTS.md, one switch per decision entry.

``Readings()`` holds the proposed reading of every decision entry; ``Readings(<field>=False)``
(or another value) selects the alternative. ``grade_row`` returns the SkyRL-style binary reward
and the per-constraint verdicts; ``graded_text`` applies the contract's extraction rule.

Written from the contracts. Known approximations (stated in the docstrings): English and
response-language identification use langdetect (seeded) on the text without code blocks.
"""
from __future__ import annotations

import dataclasses
import json
import re
import unicodedata

# ---------------------------------------------------------------- readings


@dataclasses.dataclass(frozen=True)
class Readings:
    literal_think: bool = True  # D-literal-think: non-reasoning answer graded whole
    word_mode: str = "runs"  # D-word: letter/digit runs with internal ' and - ("whitespace": tokens; "split": split at ' and -)
    markup_transparent: bool = True  # D-word-markup: markdown around a word or marker is not part of it
    word_ignore_case: bool = True  # D-word-case
    keyword_whole_word: bool = True  # D-keyword-match (False: substring)
    sentence_split_lines: bool = True  # D-sentence (False: terminal punctuation only)
    paragraph_blank_runs: bool = True  # D-paragraph-split (False: exact "\n\n", every piece counts)
    divider_line_only: bool = True  # D-divider (False: any "***" substring)
    letter_ignore_case: bool = True  # D-letter-case
    letters_any_script: bool = True  # D-letter-counting (False: Latin letters only)
    capital_single_letter: bool = True  # D-capital-word
    two_resp_exact_six: bool = True  # D-two-responses-separator
    repeat_any_inner_word: bool = True  # D-repeat-center (False: middle word(s) only)
    repeat_copies_neutral: bool = True  # D-repeat-exact-copy (False: copies count as repetitions)
    lowercase_exact_form: bool = True  # D-lowercase-count
    lowercase_each_word: bool = True  # D-lowercase-scope (False: total count)
    placeholder_any: bool = True  # D-placeholder
    ps_accept_without_dot: bool = True  # D-ps-marker
    ps_case_sensitive: bool = True  # D-ps-case
    bigram_odd_final_single: bool = True  # D-bigram-odd
    constrained_exact: bool = True  # D-constrained-surround
    json_object_or_array: bool = True  # D-json-value
    sections_case_sensitive: bool = True  # D-sections-case
    sections_exact: bool = True  # D-sections-exact (False: at least)
    bullet_all_markers: bool = True  # D-bullet-marker (False: '*' only)
    bullet_nested: bool = True  # D-bullet-nested
    highlight_bold_counts: bool = True  # D-highlight-markup
    hyphens_single_ok: bool = True  # D-hyphens-single
    brackets_each_word: bool = True  # D-brackets-each
    title_anywhere: bool = True  # D-title-position
    consecutive_either_order: bool = True  # D-consecutive-order
    palindrome_min3: bool = True  # D-palindrome
    word_count_exact: bool = True  # D-word-count-relation (False: at least)
    unicode_commas: bool = True  # D-comma-chars
    unicode_dots: bool = True  # D-dot-chars
    unicode_exclamations: bool = True  # D-exclamation-chars
    end_strict: bool = True  # D-end-trailing (False: trailing non-word chars allowed)
    end_case_sensitive: bool = True  # D-end-case
    curly_quotes: bool = True  # D-quote-chars
    divider_edges_strict: bool = True  # D-divider-edges (False: a divider before the first/after the last paragraph is ignored)
    two_resp_edges_strict: bool = True  # D-two-responses-edges (False: a separator at the very start/end is ignored)
    consecutive_latin_only: bool = True  # D-consecutive-alphabet (False: adjacent letters of any alphabet)
    start_end_single_ok: bool = True  # D-start-end-single (False: needs two or more words)


PROPOSED = Readings()

# ---------------------------------------------------------------- graded text


def graded_text(raw: str, reasoning_model: bool, readings: Readings = PROPOSED) -> str | None:
    """Contract section 0. None marks an extraction failure (fails every check)."""
    if reasoning_model:
        if "</think>" not in raw:
            return None
        return raw[raw.rfind("</think>") + len("</think>"):].strip()
    if not readings.literal_think and "<think>" in raw and "</think>" not in raw:
        return raw[: raw.index("<think>")].strip()
    return raw


# ---------------------------------------------------------------- tokenization

_WORD_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")


def words(text: str, r: Readings = PROPOSED) -> list[str]:
    if r.word_mode == "runs":
        return _WORD_RE.findall(text)
    if r.word_mode == "split":
        return re.findall(r"[^\W_]+", text)
    return [t for t in text.split() if re.search(r"[^\W_]", t)]


def _norm(w: str, r: Readings) -> str:
    if r.word_mode != "whitespace":
        out = w
    else:  # whitespace token: compare without surrounding punctuation
        out = re.sub(r"^[^\w]+|[^\w]+$", "", w)
    return out.lower() if r.word_ignore_case else out


def count_word(text: str, keyword: str, r: Readings = PROPOSED) -> int:
    if not r.keyword_whole_word:
        return len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE if r.word_ignore_case else 0))
    k = keyword.lower() if r.word_ignore_case else keyword
    return sum(1 for w in words(text, r) if _norm(w, r) == k)


_ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "vs", "etc", "e.g", "i.e", "u.s", "u.k", "no", "fig",
    "inc", "ltd", "co", "approx", "dept", "est", "vol",
}
_TERMINAL = re.compile(r"([.!?]+|[。！？]+)([\"'”’)\]*_]*)(?=\s|$)|[。！？]+")


def _split_line(line: str) -> list[str]:
    out = []
    start = 0
    for m in _TERMINAL.finditer(line):
        end = m.end()
        punct = m.group(0)
        if punct.startswith(".") and not punct.startswith(".."):
            before = line[start:m.start()]
            tail = re.search(r"([\w.]+)$", before)
            token = tail.group(1).lower() if tail else ""
            nxt = line[end:].lstrip()[:1]
            if token in _ABBREV and not (token == "etc" and nxt[:1].isupper()):
                continue
            if re.fullmatch(r"[a-z]", token) and nxt[:1].isupper() is False:
                continue
            if re.fullmatch(r"[A-Za-z]", tail.group(1) if tail else "") and nxt[:1].isupper():
                # an initial such as "J. Smith": keep together only when preceded by a capital initial
                if tail and tail.group(1).isupper() and len(tail.group(1)) == 1:
                    continue
        out.append(line[start:end])
        start = end
    out.append(line[start:])
    return out


def sentences(text: str, r: Readings = PROPOSED) -> list[str]:
    chunks = text.split("\n") if r.sentence_split_lines else [text.replace("\n", " ")]
    out = []
    for chunk in chunks:
        for piece in _split_line(chunk):
            p = piece.strip()
            if p and re.search(r"[^\W_]", p):
                out.append(p)
    return out


def paragraphs_blank(text: str, r: Readings = PROPOSED) -> list[str]:
    t = text.strip()
    if not t:
        return []
    if r.paragraph_blank_runs:
        return [p for p in re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", t) if p.strip()]
    return t.split("\n\n")  # every piece counts, empty pieces included


def divider_pieces(text: str, r: Readings = PROPOSED, divider: str = "***") -> list[str]:
    if r.divider_line_only:
        lines = text.strip().split("\n")
        pieces, cur = [], []
        for line in lines:
            if line.strip() == divider:
                pieces.append("\n".join(cur))
                cur = []
            else:
                cur.append(line)
        pieces.append("\n".join(cur))
    else:
        pieces = re.split(re.escape(divider), text.strip())
    if not r.divider_edges_strict:  # a divider before the first or after the last paragraph is ignored
        while len(pieces) > 1 and not pieces[0].strip():
            pieces = pieces[1:]
        while len(pieces) > 1 and not pieces[-1].strip():
            pieces = pieces[:-1]
    return pieces


def rel(actual: int, relation: str, n: int) -> bool:
    if relation == "less than":
        return actual < n
    if relation == "at least":
        return actual >= n
    raise ValueError(relation)


def _strip_markup_start(line: str) -> str:
    return re.sub(r"^[\s*_#>`~]+", "", line)


# ---------------------------------------------------------------- language ID


def _lang(text: str) -> str | None:
    import langdetect
    from langdetect import DetectorFactory

    DetectorFactory.seed = 0
    body = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    body = re.sub(r"https?://\S+", " ", body)
    if not re.search(r"[^\W\d_]", body):
        return None
    try:
        return langdetect.detect(body.lower())
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- checks

CHECKS = {}


def check(name):
    def reg(f):
        CHECKS[name] = f
        return f

    return reg


@check("change_case:capital_word_frequency")
def _capital(t, kw, r, ctx):
    def is_cap(w):
        cased = [c for c in w if c.isupper() or c.islower()]
        if not cased or any(c.islower() for c in cased):
            return False
        return r.capital_single_letter or sum(c.isalpha() for c in w) >= 2

    n = sum(is_cap(w) for w in words(t, r))
    return rel(n, kw["capital_relation"], kw["capital_frequency"])


@check("change_case:english_capital")
def _eng_cap(t, kw, r, ctx):
    if any(c.islower() for c in t) or not any(c.isupper() for c in t):
        return False
    return _lang(t) == "en"


@check("change_case:english_lowercase")
def _eng_low(t, kw, r, ctx):
    if any(c.isupper() for c in t) or not any(c.islower() for c in t):
        return False
    return _lang(t) == "en"


@check("combination:two_responses")
def _two(t, kw, r, ctx):
    pat = r"(?<!\*)\*{6}(?!\*)" if r.two_resp_exact_six else r"\*{6,}"
    seps = list(re.finditer(pat, t))
    if not r.two_resp_edges_strict:  # ignore separators with nothing before them or after them
        seps = [m for m in seps if t[: m.start()].strip() and t[m.end():].strip()]
    if len(seps) != 1:
        return False
    a, b = t[: seps[0].start()].strip(), t[seps[0].end():].strip()
    if not r.two_resp_edges_strict:
        a, b = re.sub(pat, "", a).strip(), re.sub(pat, "", b).strip()
    return bool(a) and bool(b) and a != b


def _tokens_for_phrase(t: str) -> list[str]:
    return [re.sub(r"^[^\w']+|[^\w']+$", "", tok) for tok in t.split()]


@check("copy:repeat_phrase")
def _repeat(t, kw, r, ctx):
    phrase = kw["phrase"].split()
    k = len(phrase)
    fold = (lambda x: x.lower()) if r.word_ignore_case else (lambda x: x)
    ref = [fold(p) for p in phrase]
    toks = [fold(x) for x in _tokens_for_phrase(t)]
    if r.repeat_any_inner_word:
        allowed = set(range(1, k - 1))
    else:
        allowed = {k // 2} if k % 2 else {k // 2 - 1, k // 2}
    variants = copies = 0
    i = 0
    while i + k <= len(toks):
        window = toks[i : i + k]
        if window[0] == ref[0] and window[-1] == ref[-1]:
            diff = [j for j in range(k) if window[j] != ref[j]]
            if not diff:
                copies += 1
                i += k
                continue
            if len(diff) == 1 and diff[0] in allowed:
                variants += 1
                i += k
                continue
        i += 1
    if r.repeat_copies_neutral:
        return variants == kw["small_n"]
    return variants >= 1 and variants + copies == kw["small_n"]


@check("count:count_unique")
def _unique(t, kw, r, ctx):
    ws = [_norm(w, r) for w in words(t, r)]
    return len(ws) == len(set(ws))


@check("count:counting_composition")
def _composition(t, kw, r, ctx):
    lines = t.strip().split("\n")
    pieces, cur = [], []
    for line in lines:
        if line.strip() in ("* * *", "***"):
            pieces.append("\n".join(cur))
            cur = []
        else:
            cur.append(line)
    pieces.append("\n".join(cur))
    if len(pieces) != 3 or any(not p.strip() for p in pieces):
        return False
    for p in pieces:
        ss = sentences(p, r)
        if len(ss) != kw["n_sent"] or any(len(words(s, r)) != kw["n_words"] for s in ss):
            return False
    return True


@check("count:lowercase_counting")
def _lowercase(t, kw, r, ctx):
    lw, other = [], []
    for w in words(t, r):
        w = _norm(w, Readings(word_ignore_case=False, word_mode=r.word_mode))
        cased = [c for c in w if c.isupper() or c.islower()]
        if not cased:
            continue
        if not any(c.isupper() for c in cased):
            lw.append(w)
        else:
            other.append(w)
    if not r.lowercase_exact_form:  # `The` counts as an occurrence of `the` when `the` is used
        forms = set(lw)
        lw += [w.lower() for w in other if w.lower() in forms]
    if not r.lowercase_each_word:
        return len(lw) <= kw["N"]
    counts = {}
    for w in lw:
        counts[w] = counts.get(w, 0) + 1
    return all(v <= kw["N"] for v in counts.values())


@check("detectable_content:number_placeholders")
def _placeholders(t, kw, r, ctx):
    spans = re.findall(r"\[([^\[\]]*)\]", t)
    n = sum(1 for s in spans if s.strip())
    return n >= kw["num_placeholders"]


@check("detectable_content:postscript")
def _postscript(t, kw, r, ctx):
    marker = kw["postscript_marker"]
    prompt_shows_no_dot = marker == "P.S." and ctx.get("prompt") is not None and (
        "postscript starting with P.S." not in ctx["prompt"]
    )
    for line in t.split("\n"):
        s = _strip_markup_start(line) if r.markup_transparent else line.lstrip()
        cmp_s = s if r.ps_case_sensitive else s.upper()
        if cmp_s.startswith(marker):
            return True
        if r.ps_accept_without_dot and prompt_shows_no_dot and re.match(r"P\.S(?=[:\s]|$)", cmp_s):
            return True
    return False


@check("detectable_format:bigram_wrapping")
def _bigram(t, kw, r, ctx):
    groups = list(re.finditer(r"<<(.*?)>>", t, flags=re.DOTALL))
    outside = re.sub(r"<<.*?>>", " ", t, flags=re.DOTALL)
    if words(outside, r) or not groups:
        return False
    for i, g in enumerate(groups):
        n = len(words(g.group(1), r))
        if n == 2:
            continue
        if n == 1 and r.bigram_odd_final_single and i == len(groups) - 1:
            continue
        return False
    return True


_OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


@check("detectable_format:constrained_response")
def _constrained(t, kw, r, ctx):
    if r.constrained_exact:
        return t.strip() in _OPTIONS
    return sum(1 for o in _OPTIONS if o in t) == 1


@check("detectable_format:json_format")
def _json(t, kw, r, ctx):
    s = t.strip()
    m = re.fullmatch(r"```[A-Za-z0-9_+-]*[ \t]*\n?(.*?)\n?[ \t]*```", s, flags=re.DOTALL)
    if m:
        s = m.group(1).strip()
    try:
        v = json.loads(s)
    except ValueError:
        return False
    return isinstance(v, (dict, list)) if r.json_object_or_array else True


@check("detectable_format:multiple_sections")
def _sections(t, kw, r, ctx):
    sp = kw["section_spliter"].strip()
    flags = 0 if r.sections_case_sensitive else re.IGNORECASE
    n = 0
    for line in t.split("\n"):
        s = _strip_markup_start(line) if r.markup_transparent else line.lstrip()
        if re.match(re.escape(sp) + r"\s+\d+\b", s, flags=flags):
            n += 1
    return n == kw["num_sections"] if r.sections_exact else n >= kw["num_sections"]


_HR = re.compile(r"^\s*([*\-_])(\s*\1){2,}\s*$")


@check("detectable_format:number_bullet_lists")
def _bullets(t, kw, r, ctx):
    markers = "*+-" if r.bullet_all_markers else "*"
    n = 0
    for line in t.split("\n"):
        if _HR.match(line):
            continue
        m = re.match(r"^(\s*)([" + re.escape(markers) + r"])\s+\S", line)
        if not m:
            continue
        if not r.bullet_nested and m.group(1):
            continue
        n += 1
    return n == kw["num_bullets"]


@check("detectable_format:number_highlighted_sections")
def _highlights(t, kw, r, ctx):
    n = 0
    rest = t
    if r.highlight_bold_counts:
        bold = re.findall(r"\*\*([^*\n]+?)\*\*", rest)
        n += sum(1 for b in bold if b.strip())
        rest = re.sub(r"\*\*([^*\n]+?)\*\*", " ", rest)
    else:
        rest = re.sub(r"\*\*([^*\n]+?)\*\*", " ", rest)
    ital = re.findall(r"(?<![*\w])\*(?![\s*])([^*\n]*?[^\s*])\*(?![*\w])", rest)
    n += len(ital)
    return n >= kw["num_highlights"]


@check("detectable_format:sentence_hyphens")
def _hyphens(t, kw, r, ctx):
    s = t.strip()
    if "\n" in s:
        return False
    joins = 0
    for m in re.finditer(r"[.!?]+", s):
        after = s[m.end():]
        if not after:
            continue
        if re.match(r"[\"'”’)]*\s", after):
            # punctuation then whitespace then more text: a sentence boundary separated by a space
            if after.strip():
                before = s[: m.start()]
                tail = re.search(r"([\w.]+)$", before)
                if tail and tail.group(1).lower() in _ABBREV:
                    continue
                return False
            continue
        if after.startswith("-"):
            if after[1:2].isspace() or after[1:2] == "":
                return False
            joins += 1
    if re.search(r"\s[-–—]|[-–—]\s", s):
        # a connecting hyphen or dash with a space on either side (contract: fail)
        return False
    return joins >= 1 or r.hyphens_single_ok


@check("detectable_format:square_brackets")
def _brackets(t, kw, r, ctx):
    groups = re.findall(r"\[([^\[\]]*)\]", t)
    outside = re.sub(r"\[[^\[\]]*\]", " ", t)
    if re.search(r"[^\W_]", outside):
        return False
    if r.brackets_each_word:
        return all(len(words(g, r)) <= 1 for g in groups)
    return True


@check("detectable_format:title")
def _title(t, kw, r, ctx):
    if r.title_anywhere:
        return bool(re.search(r"<<[^\n]*?\S[^\n]*?>>", t))
    first = next((l for l in t.split("\n") if l.strip()), "")
    return bool(re.search(r"<<[^\n]*?\S[^\n]*?>>", first))


def _eq(a: str, b: str, r: Readings) -> bool:
    return a.lower() == b.lower() if r.word_ignore_case else a == b


_MD = "*_#`~"


def first_word(text: str, r: Readings) -> str | None:
    """The first word; under the D-word-markup alternative a markdown-wrapped first token is not a word."""
    toks = text.split()
    if not toks:
        return None
    if not r.markup_transparent and toks[0][0] in _MD:
        return toks[0]
    ws = words(text, r)
    return _norm(ws[0], r) if ws else None


def last_word(text: str, r: Readings) -> str | None:
    toks = text.split()
    if not toks:
        return None
    if not r.markup_transparent and toks[-1].rstrip(".!?,;:\"'")[-1:] in tuple(_MD):
        return toks[-1]
    ws = words(text, r)
    return _norm(ws[-1], r) if ws else None


@check("first_word:first_word_answer")
def _first_answer(t, kw, r, ctx):
    w = first_word(t, r)
    return w is not None and _eq(w, kw["first_word"], r)


@check("first_word:first_word_sent")
def _first_sent(t, kw, r, ctx):
    ss = sentences(t, r)
    if not ss:
        return False
    for s in ss:
        w = first_word(s, r)
        if w is None or not _eq(w, kw["first_word"], r):
            return False
    return True


@check("keywords:existence")
def _existence(t, kw, r, ctx):
    return all(count_word(t, k, r) > 0 for k in kw["keywords"])


@check("keywords:forbidden_words")
def _forbidden(t, kw, r, ctx):
    return all(count_word(t, k, r) == 0 for k in kw["forbidden_words"])


@check("keywords:frequency")
def _frequency(t, kw, r, ctx):
    return rel(count_word(t, kw["keyword"], r), kw["relation"], kw["frequency"])


@check("keywords:keyword_specific_position")
def _position(t, kw, r, ctx):
    ss = sentences(t, r)
    if len(ss) < kw["n"]:
        return False
    ws = words(ss[kw["n"] - 1], r)
    if len(ws) < kw["m"]:
        return False
    return _eq(_norm(ws[kw["m"] - 1], r), kw["keyword"], r)


def _letter_count(t, letter, r):
    if r.letter_ignore_case:
        return sum(1 for c in t if c.lower() == letter.lower())
    return t.count(letter.lower())


@check("keywords:letter_frequency")
def _letter_freq(t, kw, r, ctx):
    return rel(_letter_count(t, kw["letter"], r), kw["let_relation"], kw["let_frequency"])


CHECKS["letters:letter_counting2"] = _letter_freq


@check("keywords:no_adjacent_consecutive")
def _adjacent(t, kw, r, ctx):
    firsts = []
    for w in words(t, r):
        w2 = re.sub(r"^[^\w]+", "", w)
        c = w2[:1].lower()
        if r.consecutive_latin_only:
            firsts.append(c if "a" <= c <= "z" else None)
        else:  # any alphabet: compare letters of the same script by code point
            firsts.append(c if c.isalpha() else None)
    for a, b in zip(firsts, firsts[1:]):
        if a is None or b is None:
            continue
        if not r.consecutive_latin_only and unicodedata.name(a, "").split()[0] != unicodedata.name(b, "").split()[0]:
            continue
        d = ord(b) - ord(a)
        if d == 1 or (r.consecutive_either_order and d == -1):
            return False
    return True


@check("keywords:palindrome")
def _palindrome(t, kw, r, ctx):
    ws = ["".join(c for c in w.lower() if c.isalpha()) for w in words(t, r)]
    if not r.palindrome_min3:
        return any(w and w == w[::-1] for w in ws)
    for i in range(len(ws)):
        acc = ""
        for j in range(i, min(i + 8, len(ws))):
            acc += ws[j]
            if len(acc) >= 3 and acc == acc[::-1]:
                return True
    return False


@check("keywords:start_end")
def _start_end(t, kw, r, ctx):
    s = t.strip()
    if not s or not re.search(r"[^\W_]$", s):
        return False
    a, b = first_word(s, r), last_word(s, r)
    if not r.start_end_single_ok and len(words(s, r)) < 2:
        return False
    return a is not None and b is not None and _eq(a, b, r)


@check("keywords:word_count_different_numbers")
def _wcdn(t, kw, r, ctx):
    n = count_word(t, kw["keyword"], r)
    return n == kw["frequency"] if r.word_count_exact else n >= kw["frequency"]


@check("keywords:word_once")
def _word_once(t, kw, r, ctx):
    return count_word(t, kw["keyword"], r) >= 1


@check("language:response_language")
def _language(t, kw, r, ctx):
    return _lang(t) == kw["language"]


@check("last_word:last_word_answer")
def _last_answer(t, kw, r, ctx):
    w = last_word(t, r)
    return w is not None and _eq(w, kw["last_word"], r)


@check("last_word:last_word_sent")
def _last_sent(t, kw, r, ctx):
    ss = sentences(t, r)
    if not ss:
        return False
    for s in ss:
        w = last_word(s, r)
        if w is None or not _eq(w, kw["last_word"], r):
            return False
    return True


@check("length_constraints:nth_paragraph_first_word")
def _nth_para(t, kw, r, ctx):
    ps = paragraphs_blank(t, r)
    n, k = kw["num_paragraphs"], kw["nth_paragraph"]
    if len(ps) != n or not 1 <= k <= len(ps) or not ps[k - 1].strip():
        return False
    w = first_word(ps[k - 1], r)
    return w is not None and _eq(w, kw["first_word"], r)


@check("length_constraints:number_paragraphs")
def _num_para(t, kw, r, ctx):
    ps = divider_pieces(t, r)
    return all(p.strip() for p in ps) and len(ps) == kw["num_paragraphs"]


@check("length_constraints:number_sentences")
def _num_sent(t, kw, r, ctx):
    return rel(len(sentences(t, r)), kw["relation"], kw["num_sentences"])


@check("length_constraints:number_words")
def _num_words(t, kw, r, ctx):
    return rel(len(words(t, r)), kw["relation"], kw["num_words"])


@check("letters:letter_counting")
def _letters(t, kw, r, ctx):
    if r.letters_any_script:
        n = sum(1 for c in t if c.isalpha())
    else:
        n = sum(1 for c in t if "a" <= c.lower() <= "z")
    return rel(n, kw["relation"], kw["N"])


@check("paragraphs:paragraphs")
def _paras(t, kw, r, ctx):
    ps = divider_pieces(t, r)
    return all(p.strip() for p in ps) and len(ps) == 2


@check("paragraphs:paragraphs2")
def _paras2(t, kw, r, ctx):
    ps = paragraphs_blank(t, r)
    return all(p.strip() for p in ps) and len(ps) == 2


_COMMAS = ",，、،﹐﹑"
_DOTS = ".．。…"
_EXCL = "!！¡"


@check("punctuation:no_comma")
def _no_comma(t, kw, r, ctx):
    chars = _COMMAS if r.unicode_commas else ","
    return not any(c in t for c in chars)


@check("punctuation:punctuation_dot")
def _no_dot(t, kw, r, ctx):
    chars = _DOTS if r.unicode_dots else "."
    return not any(c in t for c in chars)


@check("punctuation:punctuation_exclamation")
def _no_excl(t, kw, r, ctx):
    chars = _EXCL if r.unicode_exclamations else "!"
    return not any(c in t for c in chars)


@check("startend:end_checker")
def _end(t, kw, r, ctx):
    phrase = kw["end_phrase"]
    s = t.rstrip()
    cand = [s]
    if not r.end_strict:
        stripped = s
        while stripped and not re.search(r"[^\W_]$", stripped) and not stripped.endswith(phrase[-1]):
            stripped = stripped[:-1].rstrip()
            cand.append(stripped)
        cand.append(re.sub(r"[^\w?.!]+$", "", s))
    for c in cand:
        if (c.endswith(phrase) if r.end_case_sensitive else c.lower().endswith(phrase.lower())):
            return True
    return False


@check("startend:quotation")
def _quotation(t, kw, r, ctx):
    s = t.strip()
    if len(s) < 2:
        return False
    if s[0] == '"' and s[-1] == '"':
        return True
    return r.curly_quotes and s[0] == "“" and s[-1] == "”"


# ---------------------------------------------------------------- rows


def check_constraint(iid: str, kwargs: dict, text: str | None, readings: Readings = PROPOSED, prompt=None) -> bool:
    if text is None:  # extraction failure
        return False
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    return bool(CHECKS[iid](text, kw, readings, {"prompt": prompt}))


def grade_row(text: str | None, record: dict, readings: Readings = PROPOSED, prompt=None) -> tuple[float, list[bool]]:
    res = [
        check_constraint(i, k, text, readings, prompt=prompt)
        for i, k in zip(record["instruction_id_list"], record["kwargs"])
    ]
    return float(all(res)), res


def gate_row(text: str | None, record: dict, readings: Readings = PROPOSED, prompt=None,
             semantic=frozenset({"count:count_unique", "detectable_format:bigram_wrapping",
                                 "language:response_language", "letters:letter_counting"})):
    """The contract verdicts of a row's deterministic (gated) constraints."""
    res = []
    for i, k in zip(record["instruction_id_list"], record["kwargs"]):
        res.append(None if i in semantic else check_constraint(i, k, text, readings, prompt=prompt))
    return all(x is not False for x in res), res


# ---------------------------------------------------------------- "fixes only" readings
# The grader's own reading of every decision entry, per check, so that the replacement under these
# readings differs from a grader only where the grader is wrong under every reading (a defect).

_SK = {
    "count:count_unique": dict(word_ignore_case=False),
    "keywords:keyword_specific_position": dict(word_ignore_case=False, sentence_split_lines=False),
    "keywords:palindrome": dict(palindrome_min3=False),
    "copy:repeat_phrase": dict(word_ignore_case=False, repeat_copies_neutral=False),
    "count:lowercase_counting": dict(lowercase_each_word=False),
    "keywords:existence": dict(keyword_whole_word=False),
    "keywords:frequency": dict(keyword_whole_word=False),
    "keywords:word_once": dict(keyword_whole_word=False),
    "keywords:word_count_different_numbers": dict(keyword_whole_word=False, word_count_exact=False),
    "detectable_content:postscript": dict(ps_case_sensitive=False, ps_accept_without_dot=False),
    "detectable_format:constrained_response": dict(constrained_exact=False),
    "detectable_format:json_format": dict(json_object_or_array=False),
    "detectable_format:multiple_sections": dict(sections_exact=False),
    "keywords:no_adjacent_consecutive": dict(consecutive_either_order=False, consecutive_latin_only=False),
    "keywords:start_end": dict(start_end_single_ok=False, markup_transparent=False),
    "first_word:first_word_answer": dict(markup_transparent=False),
    "first_word:first_word_sent": dict(markup_transparent=False, sentence_split_lines=False),
    "last_word:last_word_sent": dict(sentence_split_lines=False),
    "length_constraints:number_sentences": dict(sentence_split_lines=False),
    "length_constraints:number_words": dict(word_mode="split"),
    "letters:letter_counting": dict(letters_any_script=False),
    "paragraphs:paragraphs2": dict(paragraph_blank_runs=False),
    "length_constraints:nth_paragraph_first_word": dict(paragraph_blank_runs=False, markup_transparent=False),
    "length_constraints:number_paragraphs": dict(divider_line_only=False, divider_edges_strict=False),
    "paragraphs:paragraphs": dict(divider_line_only=False, divider_edges_strict=False),
    "combination:two_responses": dict(two_resp_exact_six=False, two_resp_edges_strict=False),
    "punctuation:no_comma": dict(unicode_commas=False),
    "punctuation:punctuation_dot": dict(unicode_dots=False),
    "punctuation:punctuation_exclamation": dict(unicode_exclamations=False),
    "startend:end_checker": dict(end_case_sensitive=False, end_strict=False),
    "startend:quotation": dict(curly_quotes=False),
}
_VI = {
    "change_case:capital_word_frequency": dict(capital_single_letter=False),
    "detectable_format:multiple_sections": dict(sections_case_sensitive=False, markup_transparent=False),
    "detectable_content:postscript": dict(ps_case_sensitive=False, markup_transparent=False, ps_accept_without_dot=False),
    "detectable_format:square_brackets": dict(brackets_each_word=False),
    "detectable_format:json_format": dict(json_object_or_array=False),
    "combination:two_responses": dict(two_resp_exact_six=False, two_resp_edges_strict=False),
    "punctuation:no_comma": dict(unicode_commas=False),
    "punctuation:punctuation_dot": dict(unicode_dots=False),
    "punctuation:punctuation_exclamation": dict(unicode_exclamations=False),
    "keywords:word_count_different_numbers": dict(word_count_exact=False),
    "keywords:keyword_specific_position": dict(sentence_split_lines=False),
    "first_word:first_word_sent": dict(sentence_split_lines=False),
    "last_word:last_word_sent": dict(sentence_split_lines=False),
    "length_constraints:number_sentences": dict(sentence_split_lines=False),
}
OFFICIAL = {"skyrl": {k: dataclasses.replace(PROPOSED, **v) for k, v in _SK.items()},
            "verifyit": {k: dataclasses.replace(PROPOSED, **v) for k, v in _VI.items()}}


def check_official(which: str, iid: str, kwargs: dict, text: str | None, prompt=None) -> bool:
    """The replacement under the grader's own reading of each decision entry ("fixes only")."""
    return check_constraint(iid, kwargs, text, OFFICIAL[which].get(iid, PROPOSED), prompt=prompt)
