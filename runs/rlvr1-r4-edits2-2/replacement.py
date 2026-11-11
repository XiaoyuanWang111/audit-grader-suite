"""Replacement grader written from audit/CONTRACTS.md (not from either grader's code).

`check(iid, kwargs, text, opts)` returns the contract verdict for one constraint on the graded text.
`graded_text(raw, reasoning)` applies the contract's extraction rule. Each decision entry with a switch
is a key of DEFAULTS; the default value is the proposed reading ("A"), "B" the other reading.

Approximations, stated in the report:
- "in English" (D-english) and language:response_language use langdetect (seeded) because no
  deterministic contract exists for a language; english_* checks run it on the lowercased text so that
  all-capital English is not misdetected. These two parts are not contract-exact.
- Sentence splitting is a rule-based splitter (abbreviation list below), not a human reading.
"""

from __future__ import annotations

import json
import re
from collections import Counter

DEFAULTS = {
    "D-empty": "A",
    "D-word": "A",
    "D-sentence": "A",
    "D-keyword-match": "A",
    "D-first-last-case": "A",
    "D-capital-word": "A",
    "D-two-responses": "A",
    "D-repeat-center": "A",
    "D-repeat-original": "A",
    "D-count-unique-case": "A",
    "D-lowercase-counting": "A",
    "D-lowercase-total": "A",
    "D-placeholder": "A",
    "D-postscript": "A",
    "D-postscript-case": "A",
    "D-bigram-odd": "A",
    "D-constrained-exact": "A",
    "D-json-value": "A",
    "D-sections-preamble": "A",
    "D-sections-case": "A",
    "D-sections-numbering": "A",
    "D-bullets": "A",
    "D-highlight": "A",
    "D-hyphens-single": "A",
    "D-square-brackets": "A",
    "D-title": "A",
    "D-consecutive-order": "A",
    "D-palindrome-length": "A",
    "D-start-end-lead": "A",
    "D-word-count-exact": "A",
    "D-paragraph-separator": "A",
    "D-divider": "A",
    "D-letter-case": "A",
    "D-letters-count": "A",
    "D-punct-variants": "A",
    "D-end-phrase-markup": "A",
    "D-end-phrase-case": "A",
    "D-quotation-typographic": "A",
    "D-literal-think": "A",
    "D-alphabet": "A",
    "D-palindrome-phrase": "A",
    "D-postscript-line": "A",
}

# ---------------------------------------------------------------- graded text


def graded_text(raw: str, reasoning: bool, opts=DEFAULTS) -> str | None:
    """Contract extraction. None = extraction failure (reasoning never closes): fails every check."""
    if reasoning:
        if "</think>" not in raw:
            return None
        return raw.rsplit("</think>", 1)[1].strip()
    if opts["D-literal-think"] == "B" and "<think>" in raw:
        if "</think>" not in raw.split("<think>")[-1]:
            return None
        return raw.rsplit("</think>", 1)[1].strip()
    return raw.strip()


# ---------------------------------------------------------------- words, sentences, paragraphs

WORD_A = re.compile(r"[^\W_]+(?:['’\-.][^\W_]+)*")  # contract change 10: internal periods join (3.5, a.b.c)
WORD_B = re.compile(r"[^\W_]+")
TOKEN = re.compile(r"[^\W_]+")  # keyword matching splits at hyphens and apostrophes


HTML_TAG = re.compile(r"</?(?:b|i|u|em|strong|span|p|br|div|code|mark|sup|sub|h[1-6]|a|li|ul|ol)\b[^<>]*>", re.IGNORECASE)


def words(text: str, opts=DEFAULTS) -> list[str]:
    text = HTML_TAG.sub(" ", text)  # HTML tags are markup, not words
    return (WORD_A if opts["D-word"] == "A" else WORD_B).findall(text)


ABBREVIATIONS = {
    "e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "inc", "ltd", "co",
    "no", "fig", "approx", "dept", "est", "u.s", "u.k", "a.m", "p.m", "ph.d", "cf", "al",
}
_END = re.compile(r"[.!?]+[\"'”’)\]*_]*(?=\s|$)|[。！？]+[\"'”’)\]」』]*")  # change 7: CJK sentence ends


def sentences(text: str, opts=DEFAULTS) -> list[str]:
    """Contract sentences: end at [.!?]+ followed by whitespace or end (not after an abbreviation or a
    single capital initial); under D-sentence A also at every line end. Sentences without a word are dropped."""
    chunks = text.split("\n") if opts["D-sentence"] == "A" else [text.replace("\n", " ")]
    out = []
    for chunk in chunks:
        start = 0
        for m in _END.finditer(chunk):
            before = chunk[start:m.start()]
            tail = re.search(r"([A-Za-z.]+)$", before)
            if m.group(0).startswith(".") and tail:
                token = tail.group(1).lower().rstrip(".")
                if token in ABBREVIATIONS or (len(token) == 1 and tail.group(1)[-1].isupper()):
                    continue
            out.append(chunk[start:m.end()])
            start = m.end()
        out.append(chunk[start:])
    return [s.strip() for s in out if words(s, opts)]


def blank_line_paragraphs(text: str, opts=DEFAULTS) -> list[str] | None:
    """Paragraphs split at two line breaks. Under D-paragraph-separator B the split is exactly at '\\n\\n'
    and an empty middle part is an empty paragraph (returned as '')."""
    if opts["D-paragraph-separator"] == "A":
        return [p for p in re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", text.strip()) if p.strip()]
    parts = text.strip().split("\n\n")
    return parts


def divider_parts(text: str, divider: str, opts=DEFAULTS) -> list[str]:
    if opts["D-divider"] == "A":
        parts = re.split(r"(?m)^[ \t]*" + re.escape(divider) + r"[ \t]*$", text)
        return [p for p in parts if words(p, opts)]
    parts = text.split(divider)
    return parts


def _strip_lead(text: str) -> str:
    return re.sub(r"^[\s*_#>`\"'“‘(\[]+", "", text)


def same_word(a: str, b: str, opts=DEFAULTS) -> bool:
    return a.lower() == b.lower() if opts["D-first-last-case"] == "A" else a == b


def keyword_count(text: str, keyword: str, opts=DEFAULTS) -> int:
    if opts["D-keyword-match"] == "B":
        return len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))
    tokens = [t.lower() for t in TOKEN.findall(text)]
    target = [t.lower() for t in TOKEN.findall(keyword)]
    if not target:
        return 0
    k = len(target)
    return sum(1 for i in range(len(tokens) - k + 1) if tokens[i:i + k] == target)


def relation(actual: int, rel: str, n: int) -> bool:
    if rel == "at least":
        return actual >= n
    if rel == "less than":
        return actual < n
    raise ValueError(f"unknown relation {rel!r}")


# ---------------------------------------------------------------- language (approximation)

_LD = None


def detect(text: str) -> str | None:
    global _LD
    if _LD is None:
        import langdetect
        from langdetect import DetectorFactory

        DetectorFactory.seed = 0
        _LD = langdetect
    from langdetect import DetectorFactory

    DetectorFactory.seed = 0
    try:
        return _LD.detect(text)
    except _LD.LangDetectException:
        return None


# ---------------------------------------------------------------- checks

CHECKS = {}


def contract(name):
    def reg(f):
        CHECKS[name] = f
        return f
    return reg


@contract("change_case:capital_word_frequency")
def _(t, kw, o):
    count = 0
    for w in words(t, o):
        cased = [c for c in w if c.isupper() or c.islower()]
        if cased and not any(c.islower() for c in cased):
            if o["D-capital-word"] == "B" and len([c for c in w if c.isalpha()]) < 2:
                continue
            count += 1
    return relation(count, kw["capital_relation"], kw["capital_frequency"])


@contract("change_case:english_capital")
def _(t, kw, o):
    return not any(c.islower() for c in t) and any(c.isupper() for c in t) and detect(t.lower()) == "en"


@contract("change_case:english_lowercase")
def _(t, kw, o):
    return not any(c.isupper() for c in t) and any(c.islower() for c in t) and detect(t) == "en"


@contract("combination:two_responses")
def _(t, kw, o):
    runs = [m for m in re.finditer(r"\*{6,}", t)]
    if len(runs) != 1 or len(runs[0].group(0)) != 6:
        return False
    a, b = t[:runs[0].start()].strip(), t[runs[0].end():].strip()
    if not words(a, o) or not words(b, o):
        return False
    if o["D-two-responses"] == "A":
        return a != b
    return [w.lower() for w in words(a, o)] != [w.lower() for w in words(b, o)]


@contract("copy:repeat_phrase")
def _(t, kw, o):
    phrase = [w.lower() for w in words(kw["phrase"], o)]
    toks = [w.lower() for w in words(t, o)]
    L = len(phrase)
    if o["D-repeat-center"] == "A":
        allowed = set(range(1, L - 1))
    else:
        allowed = {L // 2} if L % 2 else {L // 2 - 1, L // 2}
    variants = unchanged = 0
    i = 0
    while i <= len(toks) - L:
        window = toks[i:i + L]
        diff = [j for j in range(L) if window[j] != phrase[j]]
        if not diff:
            unchanged += 1
            i += L
        elif len(diff) == 1 and diff[0] in allowed:
            variants += 1
            i += L
        else:
            i += 1
    if variants != kw["small_n"]:
        return False
    return unchanged == 0 if o["D-repeat-original"] == "A" else True


@contract("count:count_unique")
def _(t, kw, o):
    ws = words(t, o)
    if o["D-count-unique-case"] == "A":
        ws = [w.lower() for w in ws]
    return bool(ws) and len(ws) == len(set(ws))


@contract("count:counting_composition")
def _(t, kw, o):
    parts = [p for p in re.split(r"(?m)^[ \t]*\* \* \*[ \t]*$", t) if words(p, o)]
    if len(parts) != 3:
        return False
    for p in parts:
        ss = sentences(p, o)
        if len(ss) != kw["n_sent"] or any(len(words(s, o)) != kw["n_words"] for s in ss):
            return False
    return True


@contract("count:lowercase_counting")
def _(t, kw, o):
    ws = words(t, o)
    if o["D-lowercase-counting"] == "A":
        lower = [w for w in ws if any(c.islower() for c in w) and not any(c.isupper() for c in w)]
    else:
        lower = [w.lower() for w in ws if any(c.isalpha() for c in w)]
    if o["D-lowercase-total"] == "B":
        return len(lower) <= kw["N"]
    counts = Counter(lower)
    return max(counts.values(), default=0) <= kw["N"]


@contract("detectable_content:number_placeholders")
def _(t, kw, o):
    spans = [m for m in re.finditer(r"\[([^\[\]\n]*)\]", t) if m.group(1).strip()]
    if o["D-placeholder"] == "B":
        spans = [m for m in spans if not t[m.end():m.end() + 1] == "(" and not m.group(1).strip().isdigit()]
    return len(spans) >= kw["num_placeholders"]


@contract("detectable_content:postscript")
def _(t, kw, o):
    marker = kw["postscript_marker"]
    flags = re.IGNORECASE if o["D-postscript-case"] == "B" else 0
    if o["D-postscript-line"] == "B":
        # B: the marker may start mid-line; the postscript is everything after its last occurrence
        # ...but it must start a sentence: at a line start or right after a sentence end (". P.S.", ".-P.S.")
        found = [m for m in re.finditer(r"(?<![\w.])" + re.escape(marker), t, flags)
                 if not (marker == "P.S." and re.match(r"P\.P\.S", t[max(0, m.start() - 2):], flags))
                 and re.search(r"(?:^|[.!?。！？][\"'”’)\]*_]*[ \t]*-?[ \t]*|\n[ \t]*[*_#>]*[ \t]*)$", t[:m.start()])]
        if not found:
            return False
        rest = t[found[-1].end():]
        if not words(rest, o):
            return False
        return o["D-postscript"] == "B" or len(blank_line_paragraphs(rest, {**o, "D-paragraph-separator": "A"})) <= 1
    pat = re.compile(r"^[ \t]*[*_#>]*[ \t]*" + re.escape(marker) + r"[*_]*(.*)$", flags)
    lines = t.split("\n")
    hits = []
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        if marker == "P.S." and re.match(r"^[ \t]*[*_#>]*[ \t]*P\.P\.S", line, flags):
            continue
        rest = m.group(1) + "\n" + "\n".join(lines[i + 1:])
        if words(rest, o):
            hits.append(i)
    if not hits:
        return False
    if o["D-postscript"] == "B":
        return True
    # A: the postscript is the last part: no blank-line-separated block after the marker's paragraph
    i = hits[-1]
    after = "\n".join(lines[i:])
    paras = blank_line_paragraphs(after, {**o, "D-paragraph-separator": "A"})
    return len(paras) == 1


@contract("detectable_format:bigram_wrapping")
def _(t, kw, o):
    groups = re.findall(r"<<([^<>]*)>>", t)
    outside = re.sub(r"<<[^<>]*>>", " ", t)
    if words(outside, o) or not groups:
        return False
    sizes = [len(words(g, o)) for g in groups]
    if all(s == 2 for s in sizes):
        return True
    if o["D-bigram-odd"] == "A":
        return all(s == 2 for s in sizes[:-1]) and sizes[-1] == 1
    return False


OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")


@contract("detectable_format:constrained_response")
def _(t, kw, o):
    if o["D-constrained-exact"] == "B":
        return t.strip() in OPTIONS
    return sum(1 for opt in OPTIONS if opt in t) == 1


def _no_constants(x):
    raise ValueError(f"not JSON: {x}")


@contract("detectable_format:json_format")
def _(t, kw, o):
    s = t.strip()
    m = re.fullmatch(r"```[A-Za-z]*[ \t]*\n(.*)\n[ \t]*```", s, flags=re.DOTALL)
    if m:
        s = m.group(1)
    try:
        value = json.loads(s, parse_constant=_no_constants)
    except ValueError:
        return False
    return True if o["D-json-value"] == "A" else isinstance(value, (dict, list))


@contract("detectable_format:multiple_sections")
def _(t, kw, o):
    sp = kw["section_spliter"]
    flags = re.IGNORECASE if o["D-sections-case"] == "B" else 0
    pat = re.compile(r"^[ \t]*[#*_>]*[ \t]*" + re.escape(sp) + r"[*_]*[ \t]+[*_]*(\d+)\b", flags)
    lines = t.split("\n")
    marks = [(i, int(m.group(1))) for i, line in enumerate(lines) if (m := pat.match(line))]
    if len(marks) != kw["num_sections"]:
        return False
    if o["D-sections-numbering"] == "A" and [n for _, n in marks] != list(range(1, len(marks) + 1)):
        return False
    if o["D-sections-preamble"] == "B" and words("\n".join(lines[:marks[0][0]]), o):
        return False
    bounds = [i for i, _ in marks] + [len(lines)]
    for k in range(len(marks)):
        body = pat.sub("", lines[bounds[k]]) + "\n" + "\n".join(lines[bounds[k] + 1:bounds[k + 1]])
        if not words(body, o):
            return False
    return True


@contract("detectable_format:number_bullet_lists")
def _(t, kw, o):
    n = 0
    for line in t.split("\n"):
        if re.fullmatch(r"[ \t]*([*_-][ \t]*){3,}", line):
            continue  # a divider
        m = re.match(r"^([ \t]*)([*+-])[ \t]+\S", line)
        if not m:
            continue
        if o["D-bullets"] == "B" and (m.group(2) != "*" or m.group(1)):
            continue
        n += 1
    return n == kw["num_bullets"]


@contract("detectable_format:number_highlighted_sections")
def _(t, kw, o):
    s = re.sub(r"(?m)^([ \t]*)[*+-][ \t]+", r"\1", t)  # drop bullet markers
    count = 0
    if o["D-highlight"] == "A":
        bold = re.findall(r"\*\*([^*\n]+?)\*\*", s)
        count += sum(1 for b in bold if b.strip())
    s = re.sub(r"\*\*([^*\n]+?)\*\*", " ", s)
    singles = re.findall(r"\*([^*\n]+?)\*", s)
    count += sum(1 for x in singles if x.strip() and not x.startswith(" ") and not x.endswith(" "))
    return count >= kw["num_highlights"]


@contract("detectable_format:sentence_hyphens")
def _(t, kw, o):
    if re.search(r"[.!?][\"'”’)\]]*[ \t]*-[ \t]+\S|[.!?][\"'”’)\]]*[ \t]+-", t):
        return False
    # contract change 8: a hyphen with a space next to it, between two words, is not "no spaces between them"
    if re.search(r"[^\W_][\"'”’)\].!?,;:]*[ \t]+-+[ \t]*[^\W_\s]|[^\W_][\"'”’)\].!?,;:]*-+[ \t]+[^\W_]", t):
        return False
    ss = sentences(t, o)
    if len(ss) > 1:
        return False
    if len(ss) == 1 and o["D-hyphens-single"] == "B":
        return bool(re.search(r"[.!?]-\S", t))
    return len(ss) == 1


@contract("detectable_format:square_brackets")
def _(t, kw, o):
    if o["D-square-brackets"] == "B":
        outside = re.sub(r"\[[^\[\]]*\]", " ", t)
        return not words(outside, o) and bool(words(t, o))
    groups = re.findall(r"\[([^\[\]]*)\]", t)
    if any(len(words(g, o)) > 1 for g in groups):
        return False
    outside = re.sub(r"\[[^\[\]]*\]", " ", t)
    return not words(outside, o) and bool(words(t, o))


@contract("detectable_format:title")
def _(t, kw, o):
    titles = [m for m in re.finditer(r"<<([^<>\n]*)>>", t) if m.group(1).strip()]
    if not titles:
        return False
    if o["D-title"] == "B":
        return _strip_lead(t).startswith("<<") or t.lstrip().startswith(titles[0].group(0))
    return True


@contract("first_word:first_word_answer")
def _(t, kw, o):
    ws = words(t, o)
    return bool(ws) and same_word(ws[0], kw["first_word"], o)


@contract("first_word:first_word_sent")
def _(t, kw, o):
    ss = sentences(t, o)
    return bool(ss) and all(same_word(words(s, o)[0], kw["first_word"], o) for s in ss)


@contract("keywords:existence")
def _(t, kw, o):
    return all(keyword_count(t, k, o) > 0 for k in kw["keywords"])


@contract("keywords:forbidden_words")
def _(t, kw, o):
    return not any(keyword_count(t, k, o) > 0 for k in kw["forbidden_words"])


@contract("keywords:frequency")
def _(t, kw, o):
    return relation(keyword_count(t, kw["keyword"], o), kw["relation"], kw["frequency"])


@contract("keywords:keyword_specific_position")
def _(t, kw, o):
    ss = sentences(t, o)
    if len(ss) < kw["n"]:
        return False
    ws = words(ss[kw["n"] - 1], o)
    return len(ws) >= kw["m"] and ws[kw["m"] - 1].lower() == kw["keyword"].lower()


def _letter_count(t, letter, o):
    if o["D-letter-case"] == "A":
        return sum(1 for c in t if c.lower() == letter.lower())
    return t.count(letter)


@contract("keywords:letter_frequency")
def _(t, kw, o):
    return relation(_letter_count(t, kw["letter"], o), kw["let_relation"], kw["let_frequency"])


ALPHABETS = (
    "abcdefghijklmnopqrstuvwxyz",
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "αβγδεζηθικλμνξοπρστυφχψω",
)


@contract("keywords:no_adjacent_consecutive")
def _(t, kw, o):
    firsts = [w[0].lower()[0] for w in words(t, o)]  # "İ".lower() is two characters
    for a, b in zip(firsts, firsts[1:]):
        if o["D-alphabet"] == "A":  # contract change 11: the alphabet of the words' script
            alpha = next((x for x in ALPHABETS if a in x and b in x), None)
            if alpha is None:
                continue
            d = alpha.index(b) - alpha.index(a)
        else:  # B: consecutive Unicode code points of any two letters
            if not (a.isalpha() and b.isalpha()):
                continue
            d = ord(b) - ord(a)
        if d == 1 or (o["D-consecutive-order"] == "A" and d == -1):
            return False
    return True


@contract("keywords:palindrome")
def _(t, kw, o):
    minimum = 3 if o["D-palindrome-length"] == "A" else 1
    phrase_minimum = 7 if o["D-palindrome-phrase"] == "A" else minimum  # contract change 9
    letters = ["".join(c for c in w.lower() if c.isalpha()) for w in words(t, o)]
    for i in range(len(letters)):
        joined = ""
        for j in range(i, min(i + 8, len(letters))):
            joined += letters[j]
            need = minimum if j == i else phrase_minimum
            if len(joined) >= need and joined == joined[::-1]:
                return True
    return False


@contract("keywords:start_end")
def _(t, kw, o):
    ws = words(t, o)
    if not ws or not same_word(ws[0], ws[-1], o):
        return False
    s = t.rstrip()
    if not s.endswith(ws[-1]):
        return False
    if o["D-start-end-lead"] == "B" and not t.lstrip().startswith(ws[0]):
        return False
    return True


@contract("keywords:word_count_different_numbers")
def _(t, kw, o):
    c = keyword_count(t, kw["keyword"], o)
    return c == kw["frequency"] if o["D-word-count-exact"] == "A" else c >= kw["frequency"]


@contract("keywords:word_once")
def _(t, kw, o):
    return keyword_count(t, kw["keyword"], o) >= 1


@contract("language:response_language")
def _(t, kw, o):
    return detect(t) == kw["language"]


@contract("last_word:last_word_answer")
def _(t, kw, o):
    ws = words(t, o)
    return bool(ws) and same_word(ws[-1], kw["last_word"], o)


@contract("last_word:last_word_sent")
def _(t, kw, o):
    ss = sentences(t, o)
    return bool(ss) and all(same_word(words(s, o)[-1], kw["last_word"], o) for s in ss)


@contract("length_constraints:nth_paragraph_first_word")
def _(t, kw, o):
    ps = blank_line_paragraphs(t, o)
    if len(ps) != kw["num_paragraphs"] or kw["nth_paragraph"] > len(ps):
        return False
    ws = words(ps[kw["nth_paragraph"] - 1], o)
    return bool(ws) and same_word(ws[0], kw["first_word"], o)


@contract("length_constraints:number_paragraphs")
def _(t, kw, o):
    return len(divider_parts(t, "***", o)) == kw["num_paragraphs"]


@contract("length_constraints:number_sentences")
def _(t, kw, o):
    return relation(len(sentences(t, o)), kw["relation"], kw["num_sentences"])


@contract("length_constraints:number_words")
def _(t, kw, o):
    return relation(len(words(t, o)), kw["relation"], kw["num_words"])


@contract("letters:letter_counting")
def _(t, kw, o):
    n = sum(1 for c in t if c.isalpha()) if o["D-letters-count"] == "A" else len(re.findall(r"[A-Za-z]", t))
    return relation(n, kw["relation"], kw["N"])


@contract("letters:letter_counting2")
def _(t, kw, o):
    return relation(_letter_count(t, kw["letter"], o), kw["let_relation"], kw["let_frequency"])


@contract("paragraphs:paragraphs")
def _(t, kw, o):
    return len(divider_parts(t, "***", o)) == 2


@contract("paragraphs:paragraphs2")
def _(t, kw, o):
    return len(blank_line_paragraphs(t, o)) == 2


PUNCT = {
    "punctuation:no_comma": (",", ",，،、"),
    "punctuation:punctuation_dot": (".", ".…．。"),
    "punctuation:punctuation_exclamation": ("!", "!！"),
}


def _punct(name):
    def f(t, kw, o):
        chars = PUNCT[name][1] if o["D-punct-variants"] == "A" else PUNCT[name][0]
        return not any(c in t for c in chars)
    return f


for _name in PUNCT:
    CHECKS[_name] = _punct(_name)


@contract("startend:end_checker")
def _(t, kw, o):
    s = t.rstrip()
    if o["D-end-phrase-markup"] == "A":
        s = s.rstrip("*_`\"'”’ \t\n")
    phrase = kw["end_phrase"]
    if o["D-end-phrase-case"] == "B":
        return s.lower().endswith(phrase.lower())
    return s.endswith(phrase)


@contract("startend:quotation")
def _(t, kw, o):
    s = t.strip()
    opens = '"“' if o["D-quotation-typographic"] == "A" else '"'
    closes = '"”' if o["D-quotation-typographic"] == "A" else '"'
    return len(s) >= 2 and s[0] in opens and s[-1] in closes and bool(words(s[1:-1], o))


def check(iid: str, kwargs: dict | None, text: str | None, opts=DEFAULTS) -> bool:
    """Contract verdict. text None = extraction failure."""
    if text is None:
        return False
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    if opts["D-empty"] == "A" and not words(text, opts):
        return False
    return bool(CHECKS[iid](text, kw, opts))


assert len(CHECKS) == 47, len(CHECKS)
