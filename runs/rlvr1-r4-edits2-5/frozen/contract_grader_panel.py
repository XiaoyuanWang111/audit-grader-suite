"""Replacement grader for the 47 RLVR1 instruction checks, written from audit/CONTRACTS.md.

Each decision entry D-<topic> of the contract is one key of DECISIONS; the default value is the
proposed reading, and ALTERNATIVES gives the other reading. grade_constraint returns a bool.
The module needs only the standard library and langdetect (for the three language checks).
"""
from __future__ import annotations

import json
import re
import unicodedata

PROPOSED = {
    "D-strip": True,
    "D-empty": "fail",
    "D-word": "joined",
    "D-sentence": "lines",
    "D-keyword-match": "word_ci",
    "D-edge-word": "skip_markup",
    "D-capital-single-letter": True,
    "D-english": True,
    "D-asterisk-run": "exact",
    "D-repeat-center": "inner",
    "D-repeat-unchanged": "fail",
    "D-repeat-distinct": False,
    "D-unique-case": "ci",
    "D-lowercase-counting-scope": "per_word",
    "D-placeholder-form": "any",
    "D-postscript-marker": "optional_dot",
    "D-postscript-position": "end",
    "D-postscript-pps": False,
    "D-postscript-case": "cs",
    "D-bigram-odd": True,
    "D-constrained-extra": "exact",
    "D-json-scalar": "container",
    "D-sections-count": "exact",
    "D-sections-case": "cs",
    "D-sections-preamble": True,
    "D-sections-numbering": False,
    "D-bullet-dash": True,
    "D-bullet-nested": True,
    "D-highlight-bold": True,
    "D-hyphen-single": True,
    "D-hyphen-scope": "between",
    "D-brackets-one-word": True,
    "D-title-position": "anywhere",
    "D-letter-case": "ci",
    "D-consecutive-order": "both",
    "D-palindrome-length": 3,
    "D-start-end-leading": True,
    "D-start-end-one-word": True,
    "D-bare-count": "exact",
    "D-language-mixed": "strict",
    "D-paragraph-blank-run": True,
    "D-divider-edge": "fail",
    "D-letters-unit": "alpha",
    "D-comma-variants": True,
    "D-dot-variants": True,
    "D-exclamation-variants": True,
    "D-end-trailing-markup": "fail",
    "D-end-case": "cs",
    "D-quotation-typographic": True,
}

ALTERNATIVES = {
    "D-strip": False,
    "D-empty": "literal",
    "D-word": ["whitespace", "split"],
    "D-sentence": "punct",
    "D-keyword-match": ["substring", "word_cs"],
    "D-edge-word": "raw",
    "D-capital-single-letter": False,
    "D-english": False,
    "D-asterisk-run": "substring",
    "D-repeat-center": "middle",
    "D-repeat-unchanged": "ignore",
    "D-repeat-distinct": True,
    "D-unique-case": "cs",
    "D-lowercase-counting-scope": "total",
    "D-placeholder-form": ["wordlike", "blank_ok"],
    "D-postscript-marker": "exact",
    "D-postscript-position": "anywhere",
    "D-postscript-pps": True,
    "D-postscript-case": "ci",
    "D-bigram-odd": False,
    "D-constrained-extra": "contains",
    "D-json-scalar": "any",
    "D-sections-count": "at_least",
    "D-sections-case": "ci",
    "D-sections-preamble": False,
    "D-sections-numbering": True,
    "D-bullet-dash": False,
    "D-bullet-nested": False,
    "D-highlight-bold": False,
    "D-hyphen-single": False,
    "D-hyphen-scope": "within",
    "D-brackets-one-word": False,
    "D-title-position": "first_line",
    "D-letter-case": "cs",
    "D-consecutive-order": "ascending",
    "D-palindrome-length": 1,
    "D-start-end-leading": False,
    "D-start-end-one-word": False,
    "D-bare-count": "at_least",
    "D-language-mixed": "main",
    "D-paragraph-blank-run": False,
    "D-divider-edge": "ignore",
    "D-letters-unit": "ascii",
    "D-comma-variants": False,
    "D-dot-variants": False,
    "D-exclamation-variants": False,
    "D-end-trailing-markup": "allow",
    "D-end-case": "ci",
    "D-quotation-typographic": False,
}

# Checks whose verdict a decision can change (used to attribute disagreements).
DECISIONS_BY_CHECK = {
    "change_case:capital_word_frequency": ["D-word", "D-capital-single-letter"],
    "change_case:english_capital": ["D-english"],
    "change_case:english_lowercase": ["D-english"],
    "combination:two_responses": ["D-asterisk-run"],
    "copy:repeat_phrase": ["D-word", "D-repeat-center", "D-repeat-unchanged", "D-repeat-distinct"],
    "count:count_unique": ["D-word", "D-unique-case"],
    "count:counting_composition": ["D-word", "D-sentence"],
    "count:lowercase_counting": ["D-word", "D-lowercase-counting-scope"],
    "detectable_content:number_placeholders": ["D-placeholder-form"],
    "detectable_content:postscript": ["D-postscript-marker", "D-postscript-position", "D-postscript-pps", "D-postscript-case"],
    "detectable_format:bigram_wrapping": ["D-word", "D-bigram-odd"],
    "detectable_format:constrained_response": ["D-constrained-extra"],
    "detectable_format:json_format": ["D-json-scalar"],
    "detectable_format:multiple_sections": ["D-sections-count", "D-sections-case", "D-sections-preamble", "D-sections-numbering"],
    "detectable_format:number_bullet_lists": ["D-bullet-dash", "D-bullet-nested"],
    "detectable_format:number_highlighted_sections": ["D-highlight-bold"],
    "detectable_format:sentence_hyphens": ["D-sentence", "D-hyphen-single", "D-hyphen-scope"],
    "detectable_format:square_brackets": ["D-word", "D-brackets-one-word"],
    "detectable_format:title": ["D-title-position"],
    "first_word:first_word_answer": ["D-edge-word"],
    "first_word:first_word_sent": ["D-sentence", "D-edge-word"],
    "keywords:existence": ["D-keyword-match"],
    "keywords:forbidden_words": ["D-keyword-match"],
    "keywords:frequency": ["D-keyword-match"],
    "keywords:keyword_specific_position": ["D-sentence", "D-word"],
    "keywords:letter_frequency": ["D-letter-case"],
    "keywords:no_adjacent_consecutive": ["D-word", "D-consecutive-order"],
    "keywords:palindrome": ["D-palindrome-length"],
    "keywords:start_end": ["D-start-end-leading", "D-start-end-one-word"],
    "keywords:word_count_different_numbers": ["D-keyword-match", "D-bare-count"],
    "keywords:word_once": ["D-keyword-match"],
    "language:response_language": ["D-language-mixed"],
    "last_word:last_word_answer": ["D-edge-word"],
    "last_word:last_word_sent": ["D-sentence", "D-edge-word"],
    "length_constraints:nth_paragraph_first_word": ["D-paragraph-blank-run", "D-edge-word"],
    "length_constraints:number_paragraphs": ["D-divider-edge"],
    "length_constraints:number_sentences": ["D-sentence"],
    "length_constraints:number_words": ["D-word"],
    "letters:letter_counting": ["D-letters-unit"],
    "letters:letter_counting2": ["D-letter-case"],
    "paragraphs:paragraphs": ["D-divider-edge"],
    "paragraphs:paragraphs2": ["D-paragraph-blank-run"],
    "punctuation:no_comma": ["D-comma-variants"],
    "punctuation:punctuation_dot": ["D-dot-variants"],
    "punctuation:punctuation_exclamation": ["D-exclamation-variants"],
    "startend:end_checker": ["D-end-trailing-markup", "D-end-case"],
    "startend:quotation": ["D-quotation-typographic"],
}
for _ids in DECISIONS_BY_CHECK.values():
    _ids[:0] = ["D-strip", "D-empty"]

# ---------------------------------------------------------------- graded text

REASONING_CLOSE = "</think>"


def graded_text(raw: str, reasoning_model: bool) -> str | None:
    """The contract's graded text; None is an extraction failure (reasoning never closed)."""
    if reasoning_model:
        index = raw.rfind(REASONING_CLOSE)
        if index < 0:
            return None
        return raw[index + len(REASONING_CLOSE):]
    return raw


# ---------------------------------------------------------------- words, sentences, paragraphs

WORD_JOINED = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")
WORD_SPLIT = re.compile(r"[^\W_]+")
MARKUP = "*_#`~><"


def visible(text: str) -> str:
    return INLINE_HTML.sub("", text)


def words(text: str, d: dict) -> list[str]:
    text = visible(text)
    if d["D-word"] == "joined":
        return WORD_JOINED.findall(text)
    if d["D-word"] == "split":
        return WORD_SPLIT.findall(text)
    out = []
    for token in text.split():
        if any(ch.isalnum() for ch in token):
            out.append(token)
    return out


def bare(token: str) -> str:
    """A whitespace token without the punctuation and markup around it."""
    return re.sub(r"^[\W_]+|[\W_]+$", "", token)


ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "vs", "e.g", "i.e", "inc", "ltd", "co",
    "etc.,", "fig", "approx", "dept", "no", "vol", "p", "pp", "u.s", "u.k", "a.m", "p.m", "ph.d",
}
SENT_END = re.compile(r"[.!?…]+[\"'”’)\]*_]*(?=\s|$)|[。！？]+")
LIST_LABEL = re.compile(r"^\s*(?:\d+|[A-Za-z])[.)]\s")


def _split_block(block: str) -> list[str]:
    pieces = []
    start = 0
    for match in SENT_END.finditer(block):
        end = match.end()
        before = block[start:match.start()]
        tail = re.findall(r"[^\s(\[\"']+$", before)
        token = tail[0].lower() if tail else ""
        if match.group(0).startswith(".") and match.group(0).rstrip("\"'”’)]*_") == ".":
            if token.rstrip(".") in ABBREVIATIONS or (len(token) == 1 and token.isalpha()):
                continue
        pieces.append(block[start:end])
        start = end
    pieces.append(block[start:])
    return pieces


def sentences(text: str, d: dict) -> list[str]:
    if d["D-sentence"] == "lines":
        blocks = text.split("\n")
    else:
        blocks = [text.replace("\n", " ")]
    out = []
    for block in blocks:
        block = LIST_LABEL.sub(" ", block, count=1)
        for piece in _split_block(block):
            if WORD_JOINED.search(piece):
                out.append(piece.strip())
    return out


DIVIDER_LINE = re.compile(r"^[ \t]*\*\*\*[ \t]*$")
SPACED_DIVIDER_LINE = re.compile(r"^[ \t]*\*[ \t]*\*[ \t]*\*[ \t]*$")


def divider_chunks(text: str, pattern=DIVIDER_LINE) -> list[str]:
    chunks, current = [], []
    for line in text.split("\n"):
        if pattern.match(line):
            chunks.append("\n".join(current))
            current = []
        else:
            current.append(line)
    chunks.append("\n".join(current))
    return chunks


def divider_paragraph_count(text: str, d: dict, pattern=DIVIDER_LINE) -> int | None:
    """Number of paragraphs, or None when an inner (or, by D-divider-edge, an outer) chunk is empty."""
    chunks = divider_chunks(text, pattern)
    for index, chunk in enumerate(chunks):
        if not chunk.strip():
            outer = index == 0 or index == len(chunks) - 1
            if outer and len(chunks) > 1 and d["D-divider-edge"] == "ignore":
                continue
            if len(chunks) == 1:
                return 0
            return None
    return sum(1 for chunk in chunks if chunk.strip())


def blank_line_paragraphs(text: str, d: dict) -> list[str] | None:
    if d["D-paragraph-blank-run"]:
        return [p for p in re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", text.strip()) if p.strip()]
    parts = text.strip().split("\n\n")
    if any(not p.strip() for p in parts):
        return None
    return parts


def first_word(text: str, d: dict) -> str | None:
    if d["D-edge-word"] == "raw":
        tokens = text.split()
        if not tokens:
            return None
        token = tokens[0]
        if token[0] in MARKUP:
            return token
        return bare(token) or None
    found = words(text, {"D-word": "joined"})
    return found[0] if found else None


def last_word(text: str, d: dict) -> str | None:
    if d["D-edge-word"] == "raw":
        tokens = text.split()
        if not tokens:
            return None
        token = tokens[-1].rstrip(".,;:!?\"'”’)")
        if token and token[-1] in MARKUP:
            return token
        return bare(token) or None
    found = words(text, {"D-word": "joined"})
    return found[-1] if found else None


def keyword_count(text: str, keyword: str, d: dict) -> int:
    mode = d["D-keyword-match"]
    if mode == "substring":
        return text.lower().count(keyword.lower())
    flags = re.IGNORECASE if mode == "word_ci" else 0
    return len(re.findall(r"(?<![^\W_])" + re.escape(keyword) + r"(?![^\W_])", text, flags=flags))


def relation_holds(actual: int, relation: str, expected: int) -> bool:
    if relation == "at least":
        return actual >= expected
    if relation == "less than":
        return actual < expected
    if relation == "at most":
        return actual <= expected
    if relation in ("exactly", "equal"):
        return actual == expected
    raise ValueError(f"unknown relation {relation!r}")


def detect_language(text: str) -> str | None:
    from langdetect import DetectorFactory, detect
    from langdetect.lang_detect_exception import LangDetectException

    DetectorFactory.seed = 0
    try:
        return detect(text)
    except LangDetectException:
        return None


# ---------------------------------------------------------------- checks


def _capital_word_frequency(t, kw, d):
    count = 0
    for w in words(t, d):
        letters = [c for c in w if c.isalpha()]
        if not any(c.isupper() for c in letters) or any(c.islower() for c in letters):
            continue
        if len(letters) == 1 and not d["D-capital-single-letter"]:
            continue
        count += 1
    return relation_holds(count, kw["capital_relation"], kw["capital_frequency"])


def _is_english(t):
    if any(c.isalpha() and not unicodedata.name(c, "").startswith("LATIN") for c in t):
        return False
    lang = detect_language(t.lower())
    return lang == "en"


def _english_capital(t, kw, d):
    if not any(c.isalpha() for c in t) or any(c.islower() for c in t):
        return False
    return _is_english(t) if d["D-english"] else True


def _english_lowercase(t, kw, d):
    if not any(c.isalpha() for c in t) or any(c.isupper() or unicodedata.category(c) == "Lt" for c in t):
        return False
    return _is_english(t) if d["D-english"] else True


SIX = re.compile(r"(?<!\*)\*{6}(?!\*)")


def _two_responses(t, kw, d):
    if d["D-asterisk-run"] == "substring":
        parts = t.split("******")
        if len(parts) != 2:
            return False
        a, b = parts[0].strip(), parts[1].strip()
        return bool(a) and bool(b) and a != b
    seps = list(SIX.finditer(t))
    if len(seps) != 1 or re.search(r"\*{7,}", t):
        return False
    a, b = t[: seps[0].start()].strip(), t[seps[0].end():].strip()
    return bool(a) and bool(b) and a != b


def _repeat_phrase(t, kw, d):
    phrase = [w.lower() for w in WORD_JOINED.findall(kw["phrase"])]
    n = kw["small_n"]
    L = len(phrase)
    text_words = [w.lower() for w in WORD_JOINED.findall(t)]
    if L < 3:
        return False
    if d["D-repeat-center"] == "inner":
        centers = set(range(1, L - 1))
    else:
        centers = {L // 2} if L % 2 else {L // 2 - 1, L // 2}
    i = 0
    transformed, unchanged = [], 0
    while i + L <= len(text_words):
        window = text_words[i:i + L]
        diffs = [k for k in range(L) if window[k] != phrase[k]]
        if not diffs:
            unchanged += 1
            i += L
        elif len(diffs) == 1:
            transformed.append((diffs[0], window[diffs[0]]))
            i += L
        else:
            i += 1
    if len(transformed) != n:
        return False
    if any(pos not in centers for pos, _ in transformed):
        return False
    if unchanged and d["D-repeat-unchanged"] == "fail":
        return False
    if d["D-repeat-distinct"] and len({w for _, w in transformed}) != n:
        return False
    return True


def _count_unique(t, kw, d):
    ws = words(t, d)
    if d["D-unique-case"] == "ci":
        ws = [w.lower() for w in ws]
    return len(ws) == len(set(ws))


def _counting_composition(t, kw, d):
    chunks = divider_chunks(t, SPACED_DIVIDER_LINE)
    if len(chunks) != 3 or any(not c.strip() for c in chunks):
        return False
    for chunk in chunks:
        sents = sentences(chunk, d)
        if len(sents) != kw["n_sent"]:
            return False
        if any(len(words(s, d)) != kw["n_words"] for s in sents):
            return False
    return True


def _lowercase_counting(t, kw, d):
    lower = [w for w in words(t, d) if any(c.isalpha() for c in w) and not any(c.isupper() for c in w)]
    if d["D-lowercase-counting-scope"] == "total":
        return len(lower) <= kw["N"]
    counts = {}
    for w in lower:
        counts[w] = counts.get(w, 0) + 1
    return all(c <= kw["N"] for c in counts.values())


def _number_placeholders(t, kw, d):
    if d["D-placeholder-form"] == "blank_ok":
        found = re.findall(r"\[[^\[\]\n]*\]", t)
    elif d["D-placeholder-form"] == "any":
        found = re.findall(r"\[[^\[\]\n]*\S[^\[\]\n]*\]", t)
    else:
        found = re.findall(r"\[[A-Za-z_][\w \-]*\]", t)
    return len(found) >= kw["num_placeholders"]


def _postscript(t, kw, d):
    marker = kw["postscript_marker"].strip()
    core = re.escape(marker.rstrip("."))
    pattern = core + (r"\.?" if d["D-postscript-marker"] == "optional_dot" else (r"\." if marker.endswith(".") else ""))
    if d["D-postscript-pps"] and marker.rstrip(".") == "P.S":
        pattern = r"(?:P\.)?" + pattern
    flags = re.MULTILINE | (re.IGNORECASE if d["D-postscript-case"] == "ci" else 0)
    line_re = re.compile(r"^[ \t>*_#]*" + pattern + r"(?![A-Za-z.])(.*)$", flags)
    hits = list(line_re.finditer(t))
    if not hits:
        return False
    if d["D-postscript-position"] == "anywhere":
        return True
    last = hits[-1]
    if not WORD_JOINED.search(t[last.start(1):]):
        return False
    # Proposed reading: the postscript is the final paragraph (no blank line after its marker line
    # is followed by more text).
    return not re.search(r"\n[ \t]*\n[ \t]*\S", t[last.end():])


def _bigram_wrapping(t, kw, d):
    groups = list(re.finditer(r"<<(.*?)>>", t, flags=re.DOTALL))
    outside = re.sub(r"<<.*?>>", " ", t, flags=re.DOTALL)
    if "<<" in outside or ">>" in outside:
        return False
    if words(outside, d) or not groups:
        return False
    sizes = [len(words(g.group(1), d)) for g in groups]
    total = sum(sizes)
    for index, size in enumerate(sizes):
        if size == 2:
            continue
        if size == 1 and index == len(sizes) - 1 and total % 2 == 1 and d["D-bigram-odd"]:
            continue
        return False
    return True


OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


def _constrained_response(t, kw, d):
    if d["D-constrained-extra"] == "exact":
        return t.strip() in OPTIONS
    return sum(1 for o in OPTIONS if o in t) == 1


def _json_format(t, kw, d):
    s = t.strip()
    fence = re.match(r"^```[A-Za-z]*[ \t]*\n?(.*?)\n?[ \t]*```$", s, flags=re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    try:
        value = json.loads(s)
    except ValueError:
        return False
    return isinstance(value, (dict, list)) if d["D-json-scalar"] == "container" else True


def _multiple_sections(t, kw, d):
    splitter = kw["section_spliter"].strip()
    flags = re.MULTILINE | (re.IGNORECASE if d["D-sections-case"] == "ci" else 0)
    marker = re.compile(r"^[ \t]*(?:#{1,6}[ \t]*)?(?:[*_]{1,3}[ \t]*)?" + re.escape(splitter) + r"[ \t]+(\d+)\b", flags)
    hits = list(marker.finditer(t))
    n = kw["num_sections"]
    if d["D-sections-count"] == "exact" and len(hits) != n:
        return False
    if d["D-sections-count"] == "at_least" and len(hits) < n:
        return False
    if not hits:
        return False
    if not d["D-sections-preamble"] and WORD_JOINED.search(t[: hits[0].start()]):
        return False
    if d["D-sections-numbering"] and [int(h.group(1)) for h in hits] != list(range(1, len(hits) + 1)):
        return False
    for index, hit in enumerate(hits):
        end = hits[index + 1].start() if index + 1 < len(hits) else len(t)
        if not WORD_JOINED.search(t[hit.end():end]):
            return False
    return True


def _number_bullet_lists(t, kw, d):
    marks = "*-+" if d["D-bullet-dash"] else "*"
    count = 0
    for line in t.split("\n"):
        m = re.match(r"^([ \t]*)([" + re.escape(marks) + r"])[ \t]+(.*)$", line)
        if not m or not WORD_JOINED.search(m.group(3)):
            continue
        if not d["D-bullet-nested"] and len(m.group(1).expandtabs(4)) >= 2:
            continue
        count += 1
    return count == kw["num_bullets"]


ITALIC = re.compile(r"(?<![*\w])\*(?![\s*])([^*\n]*?[^\s*])\*(?![*\w])")
BOLD = re.compile(r"(?<!\*)\*\*(?![\s*])([^*\n]*?[^\s*])\*\*(?!\*)")


def _number_highlighted_sections(t, kw, d):
    count = len(ITALIC.findall(t))
    if d["D-highlight-bold"]:
        count += len(BOLD.findall(t))
    return count >= kw["num_highlights"]


def _sentence_hyphens(t, kw, d):
    if d["D-hyphen-scope"] == "within":
        sents = sentences(t, {**d, "D-sentence": "punct"})
        if not sents:
            return False
        return all(" " not in s.rstrip(".!?") and "-" in s for s in sents)
    if "\n" in t:
        sents = sentences(t, {**d, "D-sentence": "punct"})
        if len(sents) > 1:
            return False
    pieces = re.split(r"(?<=[.!?…])-", t)
    for index, piece in enumerate(pieces):
        if not piece or piece != piece.strip():
            return False
        inner = sentences(piece, {**d, "D-sentence": "punct"})
        if len(inner) != 1:
            return False
    if len(pieces) == 1:
        return d["D-hyphen-single"]
    return True


def _square_brackets(t, kw, d):
    spans = list(re.finditer(r"\[([^\[\]]*)\]", t))
    outside = re.sub(r"\[[^\[\]]*\]", " ", t)
    if "[" in outside or "]" in outside or words(outside, d) or not spans:
        return False
    for span in spans:
        n = len(words(span.group(1), d))
        if d["D-brackets-one-word"] and n != 1:
            return False
        if n == 0:
            return False
    return True


def _title(t, kw, d):
    if d["D-title-position"] == "first_line":
        first = t.strip().split("\n", 1)[0]
        return bool(re.search(r"<<[^\n<>]*\S[^\n<>]*>>", first))
    return bool(re.search(r"<<[^\n<>]*\S[^\n<>]*>>", t))


def _eq(a, b):
    return a is not None and a.lower() == b.strip().lower()


def _first_word_answer(t, kw, d):
    return _eq(first_word(t, d), kw["first_word"])


def _first_word_sent(t, kw, d):
    sents = sentences(t, d)
    return bool(sents) and all(_eq(first_word(s, d), kw["first_word"]) for s in sents)


def _existence(t, kw, d):
    return all(keyword_count(t, k, d) > 0 for k in kw["keywords"])


def _forbidden(t, kw, d):
    return all(keyword_count(t, k, d) == 0 for k in kw["forbidden_words"])


def _frequency(t, kw, d):
    return relation_holds(keyword_count(t, kw["keyword"], d), kw["relation"], kw["frequency"])


def _keyword_specific_position(t, kw, d):
    sents = sentences(t, d)
    n, m = kw["n"], kw["m"]
    if len(sents) < n:
        return False
    ws = words(sents[n - 1], d)
    if d["D-word"] == "whitespace":
        ws = [bare(w) for w in ws]
    return len(ws) >= m and ws[m - 1].lower() == kw["keyword"].strip().lower()


def _letter_frequency(t, kw, d):
    t = visible(t)
    letter = kw["letter"]
    if d["D-letter-case"] == "ci":
        count = sum(1 for c in t.lower() if c == letter.lower())
    else:
        count = t.count(letter)
    return relation_holds(count, kw["let_relation"], kw["let_frequency"])


def _no_adjacent_consecutive(t, kw, d):
    ws = words(t, d)
    if d["D-word"] == "whitespace":
        ws = [bare(w) for w in ws]
    initials = [w[0].lower() if w and "a" <= w[0].lower() <= "z" else None for w in ws]
    for a, b in zip(initials, initials[1:]):
        if a is None or b is None:
            continue
        diff = ord(b) - ord(a)
        if diff == 1 or (diff == -1 and d["D-consecutive-order"] == "both"):
            return False
    return True


def _palindrome(t, kw, d):
    minimum = d["D-palindrome-length"]
    ws = [w.lower() for w in WORD_JOINED.findall(t)]
    letters_only = ["".join(c for c in w if c.isalnum()) for w in ws]
    for w in letters_only:
        if len(w) >= minimum and w == w[::-1] and w:
            return True
    for i in range(len(letters_only)):
        joined = ""
        for j in range(i, min(i + 12, len(letters_only))):
            joined += letters_only[j]
            if j > i and len(joined) >= 5 and joined == joined[::-1]:
                return True
    return False


def _start_end(t, kw, d):
    ws = WORD_JOINED.findall(t)
    if not ws:
        return False
    if len(ws) == 1 and not d["D-start-end-one-word"]:
        return False
    if not t.rstrip()[-1:].isalnum():
        return False
    if not d["D-start-end-leading"] and not t.lstrip()[:1].isalnum():
        return False
    return ws[0].lower() == ws[-1].lower()


def _word_count_different(t, kw, d):
    count = keyword_count(t, kw["keyword"], d)
    return count == kw["frequency"] if d["D-bare-count"] == "exact" else count >= kw["frequency"]


def _word_once(t, kw, d):
    return keyword_count(t, kw["keyword"], d) >= 1


def _strip_code(t):
    return re.sub(r"```.*?```", " ", t, flags=re.DOTALL)


def _response_language(t, kw, d):
    code = kw["language"]
    body = _strip_code(t)
    if detect_language(body) != code:
        return False
    if d["D-language-mixed"] == "strict":
        for para in re.split(r"\n\s*\n", body):
            letters = sum(1 for c in para if c.isalpha())
            if letters >= 40 and detect_language(para) != code:
                return False
    return True


def _last_word_answer(t, kw, d):
    return _eq(last_word(t, d), kw["last_word"])


def _last_word_sent(t, kw, d):
    sents = sentences(t, d)
    return bool(sents) and all(_eq(last_word(s, d), kw["last_word"]) for s in sents)


def _nth_paragraph_first_word(t, kw, d):
    paras = blank_line_paragraphs(t, d)
    n, i = kw["num_paragraphs"], kw["nth_paragraph"]
    if paras is None or len(paras) != n or not 1 <= i <= n:
        return False
    return _eq(first_word(paras[i - 1], d), kw["first_word"])


def _number_paragraphs(t, kw, d, n=None):
    count = divider_paragraph_count(t, d)
    return count is not None and count == (kw["num_paragraphs"] if n is None else n)


def _number_sentences(t, kw, d):
    return relation_holds(len(sentences(t, d)), kw["relation"], kw["num_sentences"])


def _number_words(t, kw, d):
    return relation_holds(len(words(t, d)), kw["relation"], kw["num_words"])


def _letter_counting(t, kw, d):
    t = visible(t)
    if d["D-letters-unit"] == "alpha":
        count = sum(1 for c in t if c.isalpha())
    else:
        count = sum(1 for c in t if "a" <= c.lower() <= "z")
    return relation_holds(count, kw["relation"], kw["N"])


def _paragraphs2(t, kw, d):
    paras = blank_line_paragraphs(t, d)
    return paras is not None and len(paras) == 2


def _no_comma(t, kw, d):
    chars = ",，、،﹐﹑" if d["D-comma-variants"] else ","
    return not any(c in chars for c in t)


def _no_dot(t, kw, d):
    chars = ".。．…｡" if d["D-dot-variants"] else "."
    return not any(c in chars for c in t)


def _no_exclamation(t, kw, d):
    chars = "!！¡" if d["D-exclamation-variants"] else "!"
    return not any(c in chars for c in t)


def _end_checker(t, kw, d):
    phrase = kw["end_phrase"].strip()
    s = t.rstrip()
    if d["D-end-trailing-markup"] == "allow":
        s = s.rstrip("*_\"'”’` \n")
    if d["D-end-case"] == "ci":
        return s.lower().endswith(phrase.lower())
    return s.endswith(phrase)


def _quotation(t, kw, d):
    s = t.strip()
    if len(s) < 2:
        return False
    if s[0] == '"' and s[-1] == '"':
        return True
    return d["D-quotation-typographic"] and s[0] == "“" and s[-1] == "”"


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
    "keywords:word_count_different_numbers": _word_count_different,
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
    "paragraphs:paragraphs": lambda t, kw, d: _number_paragraphs(t, kw, d, n=2),
    "paragraphs:paragraphs2": _paragraphs2,
    "punctuation:no_comma": _no_comma,
    "punctuation:punctuation_dot": _no_dot,
    "punctuation:punctuation_exclamation": _no_exclamation,
    "startend:end_checker": _end_checker,
    "startend:quotation": _quotation,
}


def grade_constraint(instruction_id: str, kwargs: dict | None, text: str | None, decisions: dict | None = None) -> bool:
    """Contract verdict of one constraint on a graded text (None = extraction failure)."""
    d = {**PROPOSED, **(decisions or {})}
    if text is None:
        return False
    if d["D-strip"]:
        text = text.strip()
    if not text.strip() and d["D-empty"] == "fail":
        return False
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    if not text.strip() and d["D-empty"] == "literal" and instruction_id in VACUOUS_PASS:
        return True
    return bool(CHECKS[instruction_id](text, kw, d))


# Under the literal reading of D-empty, an empty text passes the checks that only forbid something
# or quantify over every word or sentence (vacuous truth).
VACUOUS_PASS = {
    "count:count_unique", "detectable_format:bigram_wrapping", "detectable_format:square_brackets",
    "detectable_format:sentence_hyphens", "first_word:first_word_sent", "last_word:last_word_sent",
    "language:response_language", "punctuation:no_comma", "punctuation:punctuation_dot",
    "punctuation:punctuation_exclamation", "keywords:forbidden_words", "keywords:no_adjacent_consecutive",
    "count:lowercase_counting", "change_case:english_lowercase", "change_case:english_capital",
}


# Inline HTML formatting tags are markup, not words (contract v3); checks of the raw layout keep them.
INLINE_HTML = re.compile(r"</?(?:b|i|u|em|strong|mark|span|code|sup|sub)(?:\s[^<>]*)?>", re.IGNORECASE)
EDGE_WORD_CHECKS = {
    "first_word:first_word_answer", "first_word:first_word_sent", "last_word:last_word_answer",
    "last_word:last_word_sent", "length_constraints:nth_paragraph_first_word",
}
RAW_STRUCTURE_CHECKS = {
    "startend:quotation", "detectable_format:json_format", "detectable_format:constrained_response",
    "startend:end_checker", "detectable_format:square_brackets", "detectable_format:bigram_wrapping",
    "detectable_format:title",
}


def grade_row(record: dict, text: str | None, decisions: dict | None = None) -> tuple[float, list[bool]]:
    results = [grade_constraint(i, k, text, decisions) for i, k in zip(record["instruction_id_list"], record["kwargs"])]
    return float(all(results)), results
