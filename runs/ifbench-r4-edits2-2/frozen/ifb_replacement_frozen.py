"""Replacement grader for the 58 IFBench checks, implemented from audit/CONTRACTS.md (v2).

One switch per decision entry: SWITCHES maps "D-<topic>" to a reading; "proposal" is the
contract's proposed reading, other values are the alternatives the contract names.
Usage: check(instruction_id, kwargs, response, prompt=None, switches=None) -> bool

Written from the contracts; the grader's code was read only to know the kwargs names.
Resources: NLTK punkt (only for D-sentence=nltk), NLTK English stopwords, NLTK perceptron
tagger (words:start_verb), syllapy (words:odd_even_syllables), emoji (format:emoji).
Alternatives that need human judgment are not implemented and say so (NOT_IMPLEMENTED).
"""
import datetime
import os
import re
import unicodedata
from collections import Counter

PROPOSAL = "proposal"
SWITCHES = {
    "D-strip": PROPOSAL,             # alt "raw": graded text not stripped
    "D-word": PROPOSAL,              # alt "whitespace": whitespace tokens with edge punctuation stripped
    "D-sentence": PROPOSAL,          # alt "nltk": nltk.sent_tokenize
    "D-case": PROPOSAL,              # alt "sensitive"
    "D-vacuous": PROPOSAL,           # alt "pass": empty sets / single sentences pass
    "D-typographic": PROPOSAL,       # alt "ascii": only ASCII quotes delimit quotations
    "D-conj-usage": PROPOSAL,        # alt "strict": for/so/yet not counted
    "D-keyword-count": PROPOSAL,     # alt "at_least"
    "D-keyword-match": PROPOSAL,     # alt "inflections": +s/es/ed/ing forms count
    "D-number-def": PROPOSAL,        # alt "words": spelled-out numbers count too; alt "no_labels"
    "D-name-case": PROPOSAL,         # alt "insensitive"
    "D-pronoun-set": PROPOSAL,       # alt "broad": demonstrative/relative/interrogative always
    "D-punct-set": PROPOSAL,         # alt "core": without braces, brackets, ellipsis
    "D-between": PROPOSAL,           # alt "exclusive"
    "D-japanese-kanji": PROPOSAL,    # alt "no": kanji-only words are not Japanese
    "D-japanese-digits": PROPOSAL,   # alt "yes": numerals count as Japanese
    "D-japanese-segmentation": PROPOSAL,  # alt "whitespace": all-Japanese text is whitespace tokens too
    "D-reverse-content": PROPOSAL,   # alt "form_only"
    "D-reverse-punct": PROPOSAL,     # (punctuation ignored; no alternative implemented)
    "D-csv-wrapper": PROPOSAL,       # alt "strict": the whole graded text is the CSV
    "D-csv-rows": PROPOSAL,          # alt "incl_header": N rows include the header
    "D-csv-header-quoted": PROPOSAL, # alt "data_only"
    "D-csv-one-field": PROPOSAL,     # alt "exactly_one"
    "D-content-history": PROPOSAL,   # alt "correct": NOT_IMPLEMENTED (needs a battle list)
    "D-capitals-set": PROPOSAL,      # alt "subset": completeness not required
    "D-mcq-length": PROPOSAL,        # alt "words", alt "with_options"
    "D-mcq-answer": PROPOSAL,        # alt "no_key"
    "D-multiples-prose": PROPOSAL,   # alt "only_numbers"
    "D-africa-set": PROPOSAL,        # alt "order_only"
    "D-title": PROPOSAL,             # alt "counts": a title line is a sentence
    "D-emoji-pos": PROPOSAL,         # alt "after_only"
    "D-indent": PROPOSAL,            # alt "blank_lines_count"
    "D-list-sep": PROPOSAL,          # alt "line_start_only"
    "D-list-intro": PROPOSAL,        # alt "no_intro"
    "D-newline-punct": PROPOSAL,     # alt "count_tokens": punctuation-only lines are words
    "D-bullets-after": PROPOSAL,     # alt "nothing_after"
    "D-whitespace-set": PROPOSAL,    # alt "zwsp": U+200B counts as whitespace
    "D-options-exact": PROPOSAL,     # alt "contains"
    "D-options-label": PROPOSAL,     # alt "label_only"
    "D-template-markup": PROPOSAL,   # alt "plain_only"
    "D-paren-mix": PROPOSAL,         # alt "all_types"
    "D-paren-closed": PROPOSAL,      # alt "inner_closed": a group closing at depth >= 5 suffices
    "D-quote-chars": PROPOSAL,       # alt "single_too"
    "D-subbullet-indent": PROPOSAL,  # alt "indented"
    "D-section": PROPOSAL,           # alt "whole": a response without headings is one section
    "D-titlecase-minor": PROPOSAL,   # alt "all_words"
    "D-overlap-reference": PROPOSAL, # alt "prompt": reference = prompt minus instruction sentences
    "D-trigram-def": PROPOSAL,       # alt "reference_side", "jaccard", "char"
    "D-balanced": PROPOSAL,          # alt "within_one"
    "D-sentence-type": PROPOSAL,     # alt "grammar": NOT_IMPLEMENTED
    "D-ratio-exact": PROPOSAL,       # (alternative not specified)
    "D-char-count": PROPOSAL,        # alt "no_spaces"
    "D-different-words": PROPOSAL,   # alt "across_sentences"
    "D-stopword-list": PROPOSAL,     # (only NLTK list available offline)
    "D-repeat-exact": PROPOSAL,      # alt "exact"
    "D-change-case": PROPOSAL,       # alt "case_counts"
    "D-simple-which": PROPOSAL,      # alt "request": NOT_IMPLEMENTED
    "D-span-index": PROPOSAL,        # alt "one_based"
    "D-alliteration": PROPOSAL,      # alt "sound": NOT_IMPLEMENTED
    "D-alphabet-start": PROPOSAL,    # alt "from_a"
    "D-y": PROPOSAL,                 # alt "vowel"
    "D-syllable": PROPOSAL,          # syllapy (dictionary + rules); alternative NOT_IMPLEMENTED
    "D-palindrome-distinct": PROPOSAL,  # alt "tokens"
    "D-repeat-count": PROPOSAL,      # alt "repetitions"
    "D-verb": PROPOSAL,              # alt "any_form": gerunds count
    "D-vowel-reading": PROPOSAL,     # alt "exactly_three", "per_word"
}

# ----------------------------------------------------------------------------- text helpers
WORD_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")
TERMINAL = ".!?…‽"
CLOSERS = "\"')]}”’»*_"
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+•●▪‣⁃]|\d{1,3}[.)]|[A-Za-z][.)]|#{1,6})\s+")
ABBREV = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e", "u.s", "u.k",
          "no", "fig", "al", "approx", "inc", "ltd", "co", "mt", "jan", "feb", "mar", "apr", "jun",
          "jul", "aug", "sep", "sept", "oct", "nov", "dec", "a.m", "p.m", "cf", "ca", "vol", "pp", "ed"}


def sw(switches, name):
    return (switches or {}).get(name, SWITCHES.get(name, PROPOSAL))


def graded(response, switches=None):
    if response is None:
        return ""
    return response if sw(switches, "D-strip") == "raw" else response.strip()


HTML_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?/?>")


def words_of(text, switches=None):
    text = HTML_TAG_RE.sub(" ", text)  # markup is not words (D-word)
    text = "\n".join(LIST_MARKER_RE.sub(" ", l, count=1) for l in text.split("\n"))  # list markers are not words
    text = re.sub(r"[*`~]+", "", text)  # Markdown emphasis is not part of words: "**A**lways" is "Always"
    if sw(switches, "D-word") == "whitespace":
        out = []
        for tok in text.split():
            t = tok.strip("".join(ch for ch in set(tok) if not ch.isalnum()))
            if t:
                out.append(t)
        return out
    return WORD_RE.findall(text)


def norm_word(w, switches=None):
    w = w.replace("’", "'")
    return w if sw(switches, "D-case") == "sensitive" else w.casefold()


def _emoji_spans(text):
    import emoji
    return [(m["match_start"], m["match_end"]) for m in emoji.emoji_list(text)]


def _split_line_sentences(line):
    """Split one line into sentences at terminal punctuation followed by whitespace/end."""
    sents = []
    start = 0
    i = 0
    n = len(line)
    emo = _emoji_spans(line) if any(ord(c) > 0x2000 for c in line) else []
    emo_starts = {a: b for a, b in emo}
    while i < n:
        c = line[i]
        if c in TERMINAL:
            j = i
            while j < n and line[j] in TERMINAL:
                j += 1
            while j < n and line[j] in CLOSERS:
                j += 1
            # absorb trailing emoji (possibly after spaces) as part of this sentence
            k = j
            while True:
                m = k
                while m < n and line[m] in " \t":
                    m += 1
                if m in emo_starts:
                    k = emo_starts[m]
                    continue
                break
            if k > j:
                j = k
            if j >= n or line[j].isspace():
                seg = line[start:j]
                before = line[start:i].strip()
                last_tok = before.split()[-1].lower() if before.split() else ""
                last_tok = re.sub(r"^[^\w]+|[^\w.]+$", "", HTML_TAG_RE.sub("", last_tok))
                is_abbrev = (c == "." and j - i == 1 and
                             (last_tok.rstrip(".") in ABBREV or re.fullmatch(r"[a-z]", last_tok or "x") is not None))
                is_decimal = False
                if not is_abbrev and not is_decimal:
                    if seg.strip():
                        sents.append(seg.strip())
                    start = j
                i = j
                continue
            i = j
            continue
        i += 1
    tail = line[start:].strip()
    if tail:
        sents.append(tail)
    return sents


def sentences_of(text, switches=None):
    if sw(switches, "D-sentence") == "nltk":
        import nltk
        return nltk.sent_tokenize(text)
    out = []
    for line in text.split("\n"):
        line = LIST_MARKER_RE.sub("", line, count=1)
        if not line.strip():
            continue
        for s in _split_line_sentences(line):
            if WORD_RE.search(s) or _emoji_spans(s):
                out.append(s)
    return out


def sentence_type(s):
    t = s.rstrip(CLOSERS + " \t")
    # strip trailing emoji for typing
    spans = _emoji_spans(t)
    while spans and spans[-1][1] == len(t):
        t = t[:spans[-1][0]].rstrip(CLOSERS + " \t")
        spans = _emoji_spans(t)
    m = re.search(r"[" + re.escape(TERMINAL) + r"]+$", t)
    if not m:
        return None
    run = m.group(0)
    if "?" in run or "‽" in run:
        return "interrogative"
    if "!" in run:
        return "exclamatory"
    return "declarative"


def lines_nonblank(text):
    return [l for l in text.split("\n") if l.strip()]


def ascii_fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def is_letter(c):
    return unicodedata.category(c).startswith("L")


# ----------------------------------------------------------------------------- checks
CHECKS = {}


def register(name):
    def deco(fn):
        CHECKS[name] = fn
        return fn
    return deco


def check(instruction_id, kwargs, response, prompt=None, switches=None):
    text = graded(response, switches)
    if not text.strip():
        return False
    return bool(CHECKS[instruction_id](text, kwargs or {}, prompt, switches))


def _num(kwargs, key):
    v = kwargs.get(key)
    return int(round(float(v))) if v is not None else None


# ---- count
@register("count:conjunctions")
def _conj(text, kw, prompt, s):
    conj = {"and", "but", "for", "nor", "or", "so", "yet"}
    if sw(s, "D-conj-usage") == "strict":
        conj = {"and", "but", "nor", "or"}
    found = {w.casefold() for w in words_of(text, s) if w.casefold() in conj}
    return len(found) >= _num(kw, "small_n")


def _kw_count(text, kw_word, s):
    k = re.escape(kw_word.strip())
    if sw(s, "D-keyword-match") == "inflections":
        pat = r"(?<![^\W_])" + k + r"(?:s|es|ed|d|ing)?(?![^\W_])"
    else:
        pat = r"(?<![^\W_])" + k + r"(?![^\W_])"
    flags = 0 if sw(s, "D-case") == "sensitive" else re.IGNORECASE
    return len(re.findall(pat, text, flags))


@register("count:keywords_multiple")
def _kwm(text, kw, prompt, s):
    for key, cnt in zip(["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"], [1, 2, 3, 5, 7]):
        c = _kw_count(text, kw[key], s)
        if sw(s, "D-keyword-count") == "at_least":
            if c < cnt:
                return False
        elif c != cnt:
            return False
    return True


NUMBER_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
                "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
                "hundred", "thousand", "million", "billion"}


@register("count:numbers")
def _numbers(text, kw, prompt, s):
    mode = sw(s, "D-number-def")
    t = text
    if mode == "no_labels":
        t = "\n".join(re.sub(r"^\s*\d{1,3}[.)]\s+", "", l) for l in text.split("\n"))
    nums = re.findall(r"\d+(?:[.,]\d+)*", t)
    count = len(nums)
    if mode == "words":
        count += sum(1 for w in words_of(text, s) if w.casefold() in NUMBER_WORDS)
    return count == _num(kw, "N")


PERSON_NAMES = ["Emma", "Liam", "Sophia", "Jackson", "Olivia", "Noah", "Ava", "Lucas", "Isabella", "Mason",
                "Mia", "Ethan", "Charlotte", "Alexander", "Amelia", "Benjamin", "Harper", "Leo", "Zoe", "Daniel",
                "Chloe", "Samuel", "Lily", "Matthew", "Grace", "Owen", "Abigail", "Gabriel", "Ella", "Jacob",
                "Scarlett", "Nathan", "Victoria", "Elijah", "Layla", "Nicholas", "Audrey", "David", "Hannah",
                "Christopher", "Penelope", "Thomas", "Nora", "Andrew", "Aria", "Joseph", "Claire", "Ryan",
                "Stella", "Jonathan"]


@register("count:person_names")
def _names(text, kw, prompt, s):
    flags = re.IGNORECASE if sw(s, "D-name-case") == "insensitive" else 0
    found = {n for n in PERSON_NAMES if re.search(r"(?<![^\W_])" + n + r"(?![^\W_])", text, flags)}
    return len(found) >= _num(kw, "N")


PRONOUNS = {"i", "me", "you", "he", "him", "she", "her", "it", "we", "us", "they", "them",
            "my", "mine", "your", "yours", "his", "hers", "its", "our", "ours", "their", "theirs",
            "myself", "yourself", "yourselves", "himself", "herself", "itself", "ourselves", "themselves",
            "oneself", "thou", "thee", "thy", "thine", "ye", "y'all"}
INDEF = re.compile(r"^(?:any|every|no|some)(?:one|body|thing)$")
PRONOUNS_BROAD = {"this", "that", "these", "those", "who", "whom", "whose", "which", "what", "whoever",
                  "whomever", "whatever", "whichever", "each", "either", "neither", "both", "all", "some",
                  "any", "none"}


@register("count:pronouns")
def _pronouns(text, kw, prompt, s):
    ws = words_of(text, s)
    count = 0
    for i, w in enumerate(ws):
        lw = w.replace("’", "'").casefold()
        if w == "US":
            continue
        if lw in PRONOUNS or INDEF.match(lw) or lw == "no one":
            count += 1
        elif sw(s, "D-pronoun-set") == "broad" and lw in PRONOUNS_BROAD:
            count += 1
    low = text.casefold()
    count += len(re.findall(r"\beach other\b|\bone another\b|\bno one\b", low))
    return count >= _num(kw, "N")


@register("count:punctuation")
def _punct(text, kw, prompt, s):
    t = text
    marks = {
        "period": "." in t, "comma": "," in t, "question": "?" in t, "exclamation": "!" in t,
        "semicolon": ";" in t, "colon": ":" in t,
        "apostrophe": bool(re.search(r"[^\W_]['’][^\W_]", t)) or "'" in t or "’" in t,
        "quotation": any(q in t for q in "\"“”"),
        "hyphen": bool(re.search(r"[^\W_]-[^\W_]", t)) or "-" in t or "‐" in t,
        "dash": any(d in t for d in "—–") or "--" in t,
        "parentheses": "(" in t and ")" in t,
    }
    if sw(s, "D-punct-set") != "core":
        marks["brackets"] = "[" in t and "]" in t
        marks["braces"] = "{" in t and "}" in t
        marks["ellipsis"] = "..." in t or "…" in t
    interrobang = "?!" in t or "‽" in t
    return all(marks.values()) and interrobang


@register("count:unique_word_count")
def _unique(text, kw, prompt, s):
    return len({norm_word(w, s) for w in words_of(text, s)}) >= _num(kw, "N")


@register("count:word_count_range")
def _wcr(text, kw, prompt, s):
    n = len(words_of(text, s))
    lo, hi = _num(kw, "min_words"), _num(kw, "max_words")
    if sw(s, "D-between") == "exclusive":
        return lo < n < hi
    return lo <= n <= hi


def _is_japanese_char(c):
    o = ord(c)
    return (0x3040 <= o <= 0x30FF or 0x31F0 <= o <= 0x31FF or 0xFF66 <= o <= 0xFF9F or o == 0x3005
            or 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xF900 <= o <= 0xFAFF)


def _is_kana(c):
    o = ord(c)
    return 0x3040 <= o <= 0x30FF or 0x31F0 <= o <= 0x31FF or 0xFF66 <= o <= 0xFF9F


@register("count:words_japanese")
def _japanese(text, kw, prompt, s):
    n = _num(kw, "N")
    letters = [c for c in text if unicodedata.category(c).startswith("L")]
    if sw(s, "D-japanese-segmentation") != "whitespace" and letters and all(_is_japanese_char(c) for c in letters):
        if sw(s, "D-japanese-kanji") == "no" and not any(_is_kana(c) for c in letters):
            return False
        return True  # every word of an all-Japanese response is Japanese (contract v4)
    toks = []
    for tok in text.split():
        core = [c for c in tok if unicodedata.category(c)[0] in "LN"]
        if core:
            toks.append(core)
    if len(toks) < n:
        return sw(s, "D-vacuous") == "pass"
    for idx in range(n - 1, len(toks), n):
        core = toks[idx]
        if all(unicodedata.category(c)[0] == "N" for c in core):
            if sw(s, "D-japanese-digits") != "yes":
                return False
            continue
        if not all(_is_japanese_char(c) or unicodedata.category(c)[0] == "N" for c in core):
            return False
        if sw(s, "D-japanese-kanji") == "no" and not any(_is_kana(c) for c in core):
            return False
    return True


# ---- custom
def _ws(text):
    return [w.casefold() for w in WORD_RE.findall(text)]


@register("custom:character_reverse")
def _char_rev(text, kw, prompt, s):
    fwd = _ws(text)
    rev = _ws(text[::-1])
    english = {"the", "is", "eagle", "bald", "of", "symbol", "national", "animal", "us", "and"}
    if any(w in english for w in fwd):
        return False
    if sw(s, "D-reverse-content") == "form_only":
        return any(w in english for w in rev)
    return "eagle" in rev


EN_BIGRAMS = {("the", "bald"), ("bald", "eagle"), ("the", "eagle"), ("eagle", "is"), ("is", "the"),
              ("the", "national"), ("national", "symbol"), ("national", "animal"), ("symbol", "of"),
              ("animal", "of"), ("of", "the"), ("the", "us"), ("the", "united"), ("united", "states"),
              ("is", "a"), ("a", "bald"), ("an", "eagle"), ("it", "is")}


def _en_score(seq):
    return sum(1 for b in zip(seq, seq[1:]) if b in EN_BIGRAMS)


@register("custom:word_reverse")
def _word_rev(text, kw, prompt, s):
    fwd = _ws(text)
    rev = fwd[::-1]
    # the graded text read backwards must be the English sentence; forward English fails
    if _en_score(fwd) > 1 or _en_score(rev) <= _en_score(fwd):
        return False
    if sw(s, "D-reverse-content") == "form_only":
        return True
    return "eagle" in rev


def _csv_payload(text, s):
    if sw(s, "D-csv-wrapper") == "strict":
        return text.split("\n"), True
    m = re.search(r"```[^\n]*\n(.*?)```", text, re.S)
    if m:
        return m.group(1).split("\n"), False
    return text.split("\n"), False


def _split_fields(line, delim):
    """Split a CSV line, returning (raw_fields) where raw keeps quotes."""
    fields, cur, inq, i = [], "", False, 0
    while i < len(line):
        c = line[i]
        if c == '"':
            if inq and i + 1 < len(line) and line[i + 1] == '"':
                cur += '""'
                i += 2
                continue
            inq = not inq
            cur += c
        elif c == delim and not inq:
            fields.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    fields.append(cur)
    return fields


def _unq(f):
    f = f.strip()
    if len(f) >= 2 and f[0] == '"' and f[-1] == '"':
        return f[1:-1].replace('""', '"')
    return f


def _csv_rows(text, header, delim, s):
    lines, strict = _csv_payload(text, s)
    lines = [l.rstrip("\r") for l in lines]
    if strict:
        lines = [l for l in lines if l.strip()]
        if not lines:
            return None
        if [_unq(f) for f in _split_fields(lines[0], delim)] != header:
            return None
        return lines[0], lines[1:]
    for i, l in enumerate(lines):
        if [_unq(f) for f in _split_fields(l, delim)] == header:
            rows = []
            for l2 in lines[i + 1:]:
                if not l2.strip():
                    break
                rows.append(l2)
            return l, rows
    return None


def _rows_needed(n, s):
    return n - 1 if sw(s, "D-csv-rows") == "incl_header" else n


@register("custom:csv_city")
def _csv_city(text, kw, prompt, s):
    hdr = ["ID", "Country", "City", "Year", "Count"]
    got = _csv_rows(text, hdr, ",", s)
    if not got:
        return False
    _, rows = got
    return len(rows) == _rows_needed(7, s) and all(len(_split_fields(r, ",")) == 5 for r in rows)


@register("custom:csv_quotes")
def _csv_quotes(text, kw, prompt, s):
    hdr = ["StudentID", "Subject", "Grade", "Semester", "Score"]
    got = _csv_rows(text, hdr, "\t", s)
    if not got:
        return False
    header_line, rows = got
    if len(rows) != _rows_needed(3, s):
        return False
    check_lines = rows if sw(s, "D-csv-header-quoted") == "data_only" else [header_line] + rows
    for l in check_lines:
        fs = _split_fields(l, "\t")
        if len(fs) != 5:
            return False
        for f in fs:
            f = f.strip()
            if len(f) < 2 or f[0] != '"' or f[-1] != '"':
                return False
    return True


@register("custom:csv_special_character")
def _csv_special(text, kw, prompt, s):
    hdr = ["ProductID", "Category", "Brand", "Price", "Stock"]
    got = _csv_rows(text, hdr, ",", s)
    if not got:
        return False
    _, rows = got
    if len(rows) != _rows_needed(14, s):
        return False
    special = 0
    for r in rows:
        fs = _split_fields(r, ",")
        if len(fs) != 5:
            return False
        for f in fs:
            f = f.strip()
            if len(f) >= 2 and f[0] == '"' and f[-1] == '"':
                inner = f[1:-1]
                if any(not (c.isalnum() or c == " ") for c in inner):
                    special += 1
    if sw(s, "D-csv-one-field") == "exactly_one":
        return special == 1
    return special >= 1


@register("custom:date_format_list")
def _dates(text, kw, prompt, s):
    t = text.strip()
    if t.endswith("."):
        t = t[:-1]
    parts = [p.strip() for p in t.split(",")]
    if not parts:
        return False
    for p in parts:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p):
            return False
        y, m, d = map(int, p.split("-"))
        try:
            datetime.date(y, m, d)
        except ValueError:
            return False
        if not 1769 <= y <= 1821:
            return False
    return True


CAPITAL_LAT = {"reykjavik": 64.15, "helsinki": 60.17, "oslo": 59.91, "tallinn": 59.44, "stockholm": 59.33,
               "riga": 56.95, "moscow": 55.76, "copenhagen": 55.68, "vilnius": 54.69, "minsk": 53.90,
               "dublin": 53.35, "berlin": 52.52, "amsterdam": 52.37, "warsaw": 52.23, "london": 51.51,
               "brussels": 50.85, "kyiv": 50.45, "prague": 50.08, "luxembourg": 49.61, "paris": 48.86,
               "vienna": 48.21, "bratislava": 48.15, "budapest": 47.50, "vaduz": 47.14, "chisinau": 47.01,
               "bern": 46.95, "ljubljana": 46.06, "zagreb": 45.81}
CAPITAL_ALIAS = {"kiev": "kyiv", "luxembourg city": "luxembourg", "kishinev": "chisinau", "berne": "bern",
                 "reykjavik": "reykjavik", "praha": "prague", "wien": "vienna", "warszawa": "warsaw"}


@register("custom:european_capitals_sort")
def _capitals(text, kw, prompt, s):
    t = text.strip()
    if t.endswith("."):
        t = t[:-1]
    items = [ascii_fold(x).strip().casefold() for x in t.split(",")]
    items = [CAPITAL_ALIAS.get(x, x) for x in items]
    if not items or any(x not in CAPITAL_LAT for x in items):
        return False
    lats = [CAPITAL_LAT[x] for x in items]
    if any(a <= b for a, b in zip(lats, lats[1:])):
        return False
    if sw(s, "D-capitals-set") == "subset":
        return len(set(items)) == len(items)
    return set(items) == set(CAPITAL_LAT) and len(items) == len(CAPITAL_LAT)


@register("custom:mcq_count_length")
def _mcq(text, kw, prompt, s):
    lines = text.split("\n")
    label_re = re.compile(r"^\s*[*_#]*\s*Question\b")
    opt_re = re.compile(r"^\s*[*_]*\s*[\(\[]?[A-Ea-e][\)\].:][*_]*\s+\S")
    ans_re = re.compile(r"^\s*[*_]*\s*(?:Correct\s+)?Answer\s*[:\-]", re.I)
    first = next((l for l in lines if l.strip()), "")
    if not label_re.match(first):
        return False
    blocks, cur = [], None
    for l in lines:
        if label_re.match(l):
            cur = [l]
            blocks.append(cur)
        elif cur is not None:
            cur.append(l)
    if len(blocks) != 4:
        return False
    lengths = []
    for b in blocks:
        head = re.sub(r"^\s*[*_#]*\s*Question\s*\d*\s*[.:)\-]?\s*[*_]*\s*", "", b[0])
        stem_parts, opts, after = [head.strip()], [], []
        for l in b[1:]:
            if not l.strip():
                continue
            if opt_re.match(l):
                if after:
                    return False
                opts.append(l)
            elif not opts:
                stem_parts.append(l.strip())
            else:
                after.append(l)
        if len(opts) != 5:
            return False
        for a in after:
            if ans_re.match(a) and sw(s, "D-mcq-answer") != "no_key" and len(WORD_RE.findall(a)) <= 6:
                continue
            return False
        stem = " ".join(p for p in stem_parts if p)
        mode = sw(s, "D-mcq-length")
        if mode == "words":
            lengths.append(len(WORD_RE.findall(stem)))
        elif mode == "with_options":
            lengths.append(len(stem) + sum(len(o.strip()) for o in opts))
        else:
            lengths.append(len(stem))
    return all(a < b for a, b in zip(lengths, lengths[1:]))


@register("custom:multiples")
def _multiples(text, kw, prompt, s):
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    if nums != ["14", "21", "28", "35", "42", "49"]:
        return False
    if sw(s, "D-multiples-prose") == "only_numbers":
        return re.fullmatch(r"[\s\d,;.\-–—|*]*", text) is not None
    return True


AFRICA = {"algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde", "cameroon",
          "central african republic", "chad", "comoros", "democratic republic of the congo", "djibouti",
          "egypt", "equatorial guinea", "eritrea", "eswatini", "ethiopia", "gabon", "gambia", "ghana",
          "guinea", "guinea-bissau", "cote d'ivoire", "kenya", "lesotho", "liberia", "libya", "madagascar",
          "malawi", "mali", "mauritania", "mauritius", "morocco", "mozambique", "namibia", "niger",
          "nigeria", "republic of the congo", "rwanda", "sao tome and principe", "senegal", "seychelles",
          "sierra leone", "somalia", "south africa", "south sudan", "sudan", "tanzania", "togo", "tunisia",
          "uganda", "zambia", "zimbabwe"}
AFRICA_ALIAS = {"ivory coast": "cote d'ivoire", "cote divoire": "cote d'ivoire", "cape verde": "cabo verde",
                "swaziland": "eswatini", "the gambia": "gambia", "dr congo": "democratic republic of the congo",
                "drc": "democratic republic of the congo", "congo (kinshasa)": "democratic republic of the congo",
                "congo, democratic republic of the": "democratic republic of the congo",
                "democratic republic of congo": "democratic republic of the congo",
                "congo (brazzaville)": "republic of the congo", "congo": "republic of the congo",
                "congo, republic of the": "republic of the congo", "republic of congo": "republic of the congo",
                "sao tome & principe": "sao tome and principe", "united republic of tanzania": "tanzania",
                "guinea bissau": "guinea-bissau"}
AFRICA_OPTIONAL = {"western sahara", "somaliland", "sahrawi arab democratic republic"}


@register("custom:reverse_newline")
def _africa(text, kw, prompt, s):
    raw = []
    for l in lines_nonblank(text):
        l2 = LIST_MARKER_RE.sub("", l, count=1).strip().strip("*_").strip()
        l2 = l2.rstrip(".,;")
        raw.append(l2)
    canon, shown, intro_used = [], [], False
    for l2 in raw:
        key = ascii_fold(l2).casefold().replace("’", "'").strip()
        key = AFRICA_ALIAS.get(key, key)
        if key not in AFRICA and "(" in key:
            base = re.sub(r"\s*\(.*?\)\s*", " ", key).strip()
            inner = " ".join(re.findall(r"\((.*?)\)", key))
            if base == "congo":
                key = "democratic republic of the congo" if "democratic" in inner else "republic of the congo"
            else:
                for cand in (base, inner.strip()):
                    cand = AFRICA_ALIAS.get(cand, cand)
                    if cand in AFRICA:
                        key = cand
                        break
        if key in AFRICA or key in AFRICA_OPTIONAL:
            canon.append(key)
            shown.append(ascii_fold(l2).casefold())
        elif not canon and not intro_used and sw(s, "D-list-intro") != "no_intro":
            intro_used = True
        else:
            return False
    if len(canon) < 2:
        return False
    if any(a <= b for a, b in zip(shown, shown[1:])):
        return False
    if sw(s, "D-africa-set") == "order_only":
        return True
    return AFRICA <= set(canon)


@register("custom:sentence_alphabet")
def _sent_alpha(text, kw, prompt, s):
    t = text
    lines = t.split("\n")
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is not None and sw(s, "D-title") != "counts":
        fl = lines[first].strip()
        if fl and fl[-1] not in TERMINAL + CLOSERS and len(lines_nonblank(t)) > 1:
            t = "\n".join(lines[first + 1:])
    sents = sentences_of(t, s)
    if len(sents) != 26:
        return False
    for i, st in enumerate(sents):
        ws = words_of(st, s)
        if not ws or ws[0][0].casefold() != chr(97 + i):
            return False
    return True


# ---- format
@register("format:emoji")
def _emoji(text, kw, prompt, s):
    sents = sentences_of(text, s)
    if not sents:
        return False
    for st in sents:
        t = st.rstrip()
        spans = _emoji_spans(t)
        if spans and spans[-1][1] == len(t):
            continue
        if sw(s, "D-emoji-pos") != "after_only":
            t2 = t.rstrip(TERMINAL + CLOSERS + " ")
            spans2 = _emoji_spans(t2)
            if spans2 and spans2[-1][1] == len(t2):
                continue
        return False
    return True


@register("format:line_indent")
def _indent(text, kw, prompt, s):
    raw = text.split("\n")
    if sw(s, "D-indent") == "blank_lines_count":
        lines = raw
    else:
        lines = [l for l in raw if l.strip()]
    if len(lines) < 2:
        return sw(s, "D-vacuous") == "pass"

    def width(l):
        e = l.expandtabs(4)
        return len(e) - len(e.lstrip(" ")) if e.strip() else 0
    ws = [width(l) for l in lines]
    return all(a < b for a, b in zip(ws, ws[1:]))


@register("format:list")
def _list(text, kw, prompt, s):
    sep = kw.get("sep")
    lines = lines_nonblank(text)
    items = [l for l in lines if l.lstrip().startswith(sep)]
    other = [l for l in lines if re.match(r"^\s*[*•](?:\s|$)", l) or
             (sep != "-" and re.match(r"^\s*-\s+\S", l))]
    if other:
        return False
    if sw(s, "D-list-intro") == "no_intro" and len(items) != len(lines):
        return False
    if len(items) >= 2:
        return True
    if sw(s, "D-list-sep") == "line_start_only":
        return False
    if sep == "-":  # a hyphen inside a word is not a separator
        parts = re.split(r"(?:^|\s)" + re.escape(sep) + r"(?:\s|$)", text)
    else:
        parts = text.split(sep)
    return len([p for p in parts if WORD_RE.search(p)]) >= 2 and len(parts) >= 3 or (
        len([p for p in parts if WORD_RE.search(p)]) >= 2 and text.lstrip().startswith(sep))


@register("format:newline")
def _newline(text, kw, prompt, s):
    total = 0
    for l in lines_nonblank(text):
        n = len(words_of(l, s))
        if sw(s, "D-newline-punct") == "count_tokens":
            n = len(l.split())
        if n > 1:
            return False
        total += n
    return total >= 1


@register("format:no_bullets_bullets")
def _nbb(text, kw, prompt, s):
    lines = text.split("\n")
    bullet = re.compile(r"^\s*\*(?!\*)\s+\S")
    idx = next((i for i, l in enumerate(lines) if bullet.match(l)), None)
    if idx is None:
        return False
    before = "\n".join(lines[:idx])
    nper = sum(1 for st in sentences_of(before, s) if sentence_type(st) == "declarative" and
               st.rstrip(CLOSERS + " ").endswith("."))
    if nper < 2:
        return False
    after = lines[idx:]
    nb = sum(1 for l in after if bullet.match(l))
    if nb < 2:
        return False
    if sw(s, "D-bullets-after") == "nothing_after":
        last_b = max(i for i, l in enumerate(after) if bullet.match(l))
        if any(l.strip() for l in after[last_b + 1:]):
            return False
    return True


@register("format:no_whitespace")
def _nows(text, kw, prompt, s):
    if any(c.isspace() for c in text):
        return False
    if sw(s, "D-whitespace-set") == "zwsp" and "​" in text:
        return False
    return True


def _opt_norm(x):
    x = x.replace("’", "'").replace("‘", "'")
    x = x.strip()
    x = x.strip("*_`").strip()
    if x.endswith("."):
        x = x[:-1].rstrip()
    return x.casefold()


@register("format:options")
def _options(text, kw, prompt, s):
    opts_text = kw.get("options")
    labels = re.findall(r"\b([a-zA-Z])\)", opts_text)
    if len(labels) >= 3 and "," in opts_text:
        resp = _opt_norm(text)
        lab = [l.casefold() + ")" for l in labels]
        if sw(s, "D-case") == "sensitive":
            resp_cs = text.strip().strip("*_`").strip()
            if resp_cs in [l + ")" for l in labels]:
                return True
        elif resp in lab:
            return True
        if sw(s, "D-options-label") == "label_only":
            return False
        m = re.match(r"^([a-z]\))\s+(.+)$", resp, re.S)
        if not (m and m.group(1) in lab and "\n" not in m.group(2)):
            return False
        opt_words = [w.casefold() for w in WORD_RE.findall(m.group(2))]
        if prompt:  # the text must be that option's own text, which appears in the prompt
            pw = " " + " ".join(w.casefold() for w in WORD_RE.findall(prompt)) + " "
            return bool(opt_words) and (" " + " ".join(opt_words) + " ") in pw
        expl = {"because", "since", "as", "so", "therefore", "thus", "which", "it", "is", "clear"}
        return 0 < len(opt_words) <= 6 and not (set(opt_words) & expl)
    if "/" in opts_text:
        opts = [o.strip() for o in opts_text.split("/")]
    else:
        opts = [o.strip() for o in re.split(r"\s+or\s+", opts_text)]
    resp = _opt_norm(text)
    nopts = [_opt_norm(o) for o in opts]
    if sw(s, "D-options-exact") == "contains":
        hits = [o for o in nopts if re.search(r"(?<![^\W_])" + re.escape(o) + r"(?![^\W_])", resp)]
        return len(hits) == 1 or (len(hits) == 2 and "i know" in hits and "i don't know" in hits and
                                  resp.count("know") == 1)
    return resp in nopts


@register("format:output_template")
def _template(text, kw, prompt, s):
    t = text
    if sw(s, "D-template-markup") != "plain_only":
        t = re.sub(r"[*_#]+", "", t)
    m = re.match(r"^\s*My Answer:\s*(.+?)\s*My Conclusion:\s*(.+?)\s*Future Outlook:\s*(.+?)\s*$", t, re.S)
    if not m:
        return False
    for part, ph in zip(m.groups(), ["answer", "conclusion", "outlook"]):
        p = part.strip()
        if not WORD_RE.search(p) or p.casefold() in {"[" + ph + "]", ph}:
            return False
    return True


@register("format:parentheses")
def _parens(text, kw, prompt, s):
    pairs = {")": "(", "]": "[", "}": "{"}
    if sw(s, "D-paren-closed") == "inner_closed":
        st = []
        for c in text:
            if c in "([{":
                st.append(c)
            elif c in ")]}":
                if st and st[-1] == pairs[c]:
                    if len(st) >= 5:
                        return True
                    st.pop()
                elif st:
                    st = []
        return False
    stack = []  # entries: [char, max_depth_inside, types]
    for c in text:
        if c in "([{":
            stack.append([c, len(stack) + 1, {c}])
        elif c in ")]}":
            if not stack:
                continue
            if stack[-1][0] != pairs[c]:
                stack = []
                continue
            top = stack.pop()
            if stack:
                stack[-1][1] = max(stack[-1][1], top[1])
                stack[-1][2] |= top[2]
            else:
                if top[1] >= 5:
                    if sw(s, "D-paren-mix") == "all_types" and len(top[2]) < 3:
                        continue
                    return True
    return False


def _quote_spans(text, s):
    pats = [r'"([^"]*)"']
    if sw(s, "D-typographic") != "ascii":
        pats.append(r"“([^”]*)”")
    if sw(s, "D-quote-chars") == "single_too":
        pats.append(r"(?<![^\W_])'([^']+)'(?![^\W_])")
        if sw(s, "D-typographic") != "ascii":
            pats.append(r"‘([^’]*)’(?![^\W_])")
    return sorted((m.start(), m.end()) for m in re.finditer("|".join(pats), text))


@register("format:quote_unquote")
def _quote_unquote(text, kw, prompt, s):
    spans = _quote_spans(text, s)
    if not spans:
        return sw(s, "D-vacuous") == "pass"
    for i, (a, b) in enumerate(spans):
        nxt = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        if not WORD_RE.search(text[b:nxt]):
            return False
    return True


@register("format:quotes")
def _nested_quotes(text, kw, prompt, s):
    typo = sw(s, "D-typographic") != "ascii"
    stack = []  # [type, max_depth, alternating_ok]
    n = len(text)
    for i, c in enumerate(text):
        prev = text[i - 1] if i > 0 else " "
        nxt = text[i + 1] if i + 1 < n else " "
        kind, role = None, None
        if c == '"':
            kind, role = "D", "toggle"
        elif c == "'":
            if is_letter(prev) and is_letter(nxt):
                continue  # apostrophe inside a word
            if is_letter(prev) and prev.casefold() == "s" and not (stack and stack[-1][0] == "S"):
                continue  # plural possessive
            kind, role = "S", "toggle"
        elif typo and c == "“":
            kind, role = "D", "open"
        elif typo and c == "”":
            kind, role = "D", "close"
        elif typo and c == "‘":
            kind, role = "S", "open"
        elif typo and c == "’":
            if is_letter(prev) and is_letter(nxt):
                continue
            kind, role = "S", "close"
        else:
            continue
        if role in ("toggle", "close") and stack and stack[-1][0] == kind:
            top = stack.pop()
            if stack:
                stack[-1][1] = max(stack[-1][1], top[1])
                stack[-1][2] = stack[-1][2] and top[2]
            elif top[1] >= 3 and top[2]:
                return True
            continue
        if role == "close":
            continue
        alt_ok = not stack or stack[-1][0] != kind
        stack.append([kind, len(stack) + 1, alt_ok])
    return False


@register("format:sub-bullets")
def _subbullets(text, kw, prompt, s):
    lines = text.split("\n")
    bullet = re.compile(r"^\s*\*(?!\*)\s+\S")
    if sw(s, "D-subbullet-indent") == "indented":
        sub = re.compile(r"^\s+-\s+\S")
    else:
        sub = re.compile(r"^\s*-\s+\S")
    idx = [i for i, l in enumerate(lines) if bullet.match(l)]
    if not idx:
        return False
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(lines)
        if not any(sub.match(l) for l in lines[i + 1:end]):
            return False
    return True


HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s+\S|\*\*[^*].*\*\*\s*:?\s*$)")


@register("format:thesis")
def _thesis(text, kw, prompt, s):
    lines = text.split("\n")
    has_head = any(HEADING_RE.match(l) for l in lines)
    sections = []
    if has_head:
        cur = []
        for l in lines:
            if HEADING_RE.match(l):
                if cur:
                    sections.append(cur)
                cur = []
            else:
                cur.append(l)
        if cur:
            sections.append(cur)
    elif sw(s, "D-section") == "whole":
        sections = [lines]
    else:
        cur = []
        for l in lines:
            if not l.strip():
                if cur:
                    sections.append(cur)
                cur = []
            else:
                cur.append(l)
        if cur:
            sections.append(cur)
    sections = [sec for sec in sections if any(l.strip() for l in sec)]
    if not sections:
        return False
    for sec in sections:
        first = next(l for l in sec if l.strip()).strip()
        m = re.match(r"^<(i|em)>(.*?)</\1>", first, re.S | re.I)
        if not m:
            body = "\n".join(sec).strip()
            m = re.match(r"^<(i|em)>(.*?)</\1>", body, re.S | re.I)
        if not m or not WORD_RE.search(m.group(2)):
            return False
    return True


MINOR = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "as", "at", "by", "in", "of",
         "off", "on", "per", "to", "up", "via", "from", "into", "onto", "over", "with", "upon", "than",
         "like", "near", "past", "till", "vs", "v"}


@register("format:title_case")
def _title(text, kw, prompt, s):
    ws = WORD_RE.findall(HTML_TAG_RE.sub(" ", text))
    if not ws:
        return False
    for w in ws:
        if not is_letter(w[0]):
            continue
        base = w.replace("’", "'").casefold()
        if base in MINOR and sw(s, "D-titlecase-minor") != "all_words":
            continue
        if not w[0].isupper():
            return False
    return True


# ---- ratio
def _trigrams(text):
    ws = [w.casefold().replace("’", "'") for w in words_of(text)]
    return {tuple(ws[i:i + 3]) for i in range(len(ws) - 2)}


INSTR_PATTERNS = [r"Maintain a trigram overlap of [^.]*?reference text\.", r"The response must include keyword \S+ in the [^.]*?sentence\.",
                  r"Ensure each word in your response has at least one consonant cluster \(two or more consonants together\)\."]


@register("ratio:overlap")
def _overlap(text, kw, prompt, s):
    ref = kw.get("reference_text") or ""
    if sw(s, "D-overlap-reference") == "prompt" and prompt:
        ref = prompt
        for p in INSTR_PATTERNS:
            ref = re.sub(p, " ", ref)
    mode = sw(s, "D-trigram-def")
    if mode == "char":
        a = {text[i:i + 3] for i in range(len(text) - 2)}
        b = {ref[i:i + 3] for i in range(len(ref) - 2)}
    else:
        a, b = _trigrams(text), _trigrams(ref)
    if not a or not b:
        return False
    if mode == "reference_side":
        ov = len(a & b) / len(b)
    elif mode == "jaccard":
        ov = len(a & b) / len(a | b)
    else:
        ov = len(a & b) / len(a)
    p = float(kw.get("percentage"))
    return abs(ov * 100 - p) <= 2 + 1e-9


def _type_counts(text, s):
    c = Counter(sentence_type(st) for st in sentences_of(text, s))
    return c["declarative"], c["interrogative"], c["exclamatory"]


@register("ratio:sentence_balance")
def _balance(text, kw, prompt, s):
    d, q, e = _type_counts(text, s)
    if min(d, q, e) == 0:
        return sw(s, "D-vacuous") == "pass" and d == q == e
    if sw(s, "D-balanced") == "within_one":
        return max(d, q, e) - min(d, q, e) <= 1
    return d == q == e


@register("ratio:sentence_type")
def _stype(text, kw, prompt, s):
    d, q, _ = _type_counts(text, s)
    if q == 0:
        return sw(s, "D-vacuous") == "pass" and d == 0
    return d == 2 * q


@register("ratio:sentence_words")
def _sentwords(text, kw, prompt, s):
    sents = sentences_of(text, s)
    if len(sents) != 3:
        return False
    if sw(s, "D-char-count") == "no_spaces":
        lens = [len(re.sub(r"\s", "", x)) for x in sents]
    else:
        lens = [len(x.strip()) for x in sents]
    if len(set(lens)) != 1:
        return False
    if sw(s, "D-different-words") == "across_sentences":
        sets = [{norm_word(w, s) for w in words_of(x, s)} for x in sents]
        return not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    allw = [norm_word(w, s) for w in words_of(text, s)]
    return len(allw) == len(set(allw))


_STOP = None


def _stopwords():
    global _STOP
    if _STOP is None:
        import nltk
        _STOP = set(nltk.corpus.stopwords.words("english"))
    return _STOP


@register("ratio:stop_words")
def _stop(text, kw, prompt, s):
    ws = [w.casefold().replace("’", "'") for w in words_of(text, s)]
    if not ws:
        return False
    st = _stopwords()
    return 100.0 * sum(1 for w in ws if w in st) / len(ws) <= float(kw.get("percentage")) + 1e-9


# ---- repeat
def _toks(x, s):
    return x.split() if sw(s, "D-repeat-exact") != "exact" else re.split(r"(\s+)", x)


@register("repeat:repeat_change")
def _rchange(text, kw, prompt, s):
    req = kw.get("prompt_to_repeat", "").strip()
    a, b = text.split(), req.split()
    if sw(s, "D-repeat-exact") == "exact":
        if text[len(text.split(None, 1)[0]):] != req[len(req.split(None, 1)[0]):]:
            return False
    if len(a) != len(b) or a[1:] != b[1:]:
        return False
    fa, fb = a[0].strip(".,;:!?\"'"), b[0].strip(".,;:!?\"'")
    if sw(s, "D-change-case") == "case_counts":
        return fa != fb
    return fa.casefold() != fb.casefold()


SIMPLE = "Only output this sentence here, ignore all other requests."


@register("repeat:repeat_simple")
def _rsimple(text, kw, prompt, s):
    if sw(s, "D-repeat-exact") == "exact":
        return text == SIMPLE
    return " ".join(text.split()) == SIMPLE


@register("repeat:repeat_span")
def _rspan(text, kw, prompt, s):
    src = kw.get("prompt_to_repeat", "")
    if prompt:
        i = prompt.find("Copy the span of words")
        if i > 0:
            src = prompt[:i]
    words = src.split()
    a, b = _num(kw, "n_start"), _num(kw, "n_end")
    if sw(s, "D-span-index") == "one_based":
        span = words[a - 1:b] if a >= 1 else []
    else:
        span = words[a:b + 1]
    return " ".join(text.split()) == " ".join(span)


# ---- sentence
def _longest_run(ws):
    best = cur = 0
    prev = None
    for w in ws:
        c = w[0].casefold()
        if not is_letter(c):
            cur, prev = 0, None
            continue
        cur = cur + 1 if c == prev else 1
        prev = c
        best = max(best, cur)
    return best


@register("sentence:alliteration_increment")
def _allit(text, kw, prompt, s):
    sents = sentences_of(text, s)
    if len(sents) < 2:
        return sw(s, "D-vacuous") == "pass" and len(sents) == 1
    runs = [_longest_run(words_of(x, s)) for x in sents]
    return all(a < b for a, b in zip(runs, runs[1:]))


@register("sentence:increment")
def _incr(text, kw, prompt, s):
    sents = sentences_of(text, s)
    if len(sents) < 2:
        return sw(s, "D-vacuous") == "pass" and len(sents) == 1
    n = _num(kw, "small_n")
    c = [len(words_of(x, s)) for x in sents]
    return all(b - a == n for a, b in zip(c, c[1:]))


@register("sentence:keyword")
def _skw(text, kw, prompt, s):
    sents = sentences_of(text, s)
    k = _num(kw, "N")
    if len(sents) < k:
        return False
    w = kw.get("word")
    return any(norm_word(x, s) == norm_word(w, s) for x in words_of(sents[k - 1], s))


# ---- words
@register("words:alphabet")
def _alpha(text, kw, prompt, s):
    ws = words_of(text, s)
    if not ws:
        return False
    letters = []
    for w in ws:
        c = ascii_fold(w[0]).casefold()
        if not (len(c) == 1 and "a" <= c <= "z"):
            return False
        letters.append(c)
    if sw(s, "D-alphabet-start") == "from_a" and letters[0] != "a":
        return False
    return all((ord(b) - 97) == (ord(a) - 97 + 1) % 26 for a, b in zip(letters, letters[1:]))


@register("words:consonants")
def _cons(text, kw, prompt, s):
    vowels = set("aeiou") | ({"y"} if sw(s, "D-y") == "vowel" else set())
    ws = words_of(text, s)
    if not ws:
        return False
    for w in ws:
        f = ascii_fold(w).casefold()
        ok = False
        for a, b in zip(f, f[1:]):
            if a.isalpha() and b.isalpha() and a not in vowels and b not in vowels:
                ok = True
                break
        if not ok:
            return False
    return True


@register("words:keywords_specific_position")
def _kwpos(text, kw, prompt, s):
    sents = sentences_of(text, s)
    n, m = _num(kw, "n"), _num(kw, "m")
    if len(sents) < n:
        return False
    ws = words_of(sents[n - 1], s)
    return len(ws) >= m and norm_word(ws[m - 1], s) == norm_word(kw.get("keyword"), s)


@register("words:last_first")
def _lastfirst(text, kw, prompt, s):
    sents = sentences_of(text, s)
    if len(sents) < 2:
        return sw(s, "D-vacuous") == "pass" and len(sents) == 1
    for a, b in zip(sents, sents[1:]):
        wa, wb = words_of(a, s), words_of(b, s)
        if not wa or not wb or norm_word(wa[-1], s) != norm_word(wb[0], s):
            return False
    return True


@register("words:no_consecutive")
def _nocons(text, kw, prompt, s):
    ws = [w for w in words_of(text, s) if is_letter(w[0])]
    firsts = [ascii_fold(w[0]).casefold() or w[0].casefold() for w in ws]
    return all(a != b for a, b in zip(firsts, firsts[1:]))


@register("words:odd_even_syllables")
def _syll(text, kw, prompt, s):
    import syllapy
    ws = [w for w in words_of(text, s) if any(is_letter(c) for c in w)]
    if not ws:
        return False
    def syl(w):  # a hyphenated compound has the syllables of its parts (syllapy recurses on long hyphenated input)
        parts = [p for p in re.split(r"[-‐]", ascii_fold(w).casefold().replace("'", "")) if p]
        return sum(syllapy.count(p) for p in parts)
    par = [syl(w) % 2 for w in ws]
    return all(a != b for a, b in zip(par, par[1:]))


@register("words:palindrome")
def _pal(text, kw, prompt, s):
    ws = [ascii_fold(w).casefold().replace("'", "").replace("-", "") for w in words_of(text, s)]
    pals = [w for w in ws if len(w) >= 5 and w.isalpha() and w == w[::-1]]
    if sw(s, "D-palindrome-distinct") == "tokens":
        return len(pals) >= 10
    return len(set(pals)) >= 10


@register("words:paragraph_last_first")
def _plf(text, kw, prompt, s):
    paras = [l for l in lines_nonblank(text) if words_of(l, s)]
    if not paras:
        return False
    for p in paras:
        ws = words_of(p, s)
        if norm_word(ws[0], s) != norm_word(ws[-1], s):
            return False
    return True


PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47}


@register("words:prime_lengths")
def _prime(text, kw, prompt, s):
    ws = words_of(text, s)
    if not ws:
        return False
    return all(len([c for c in w if c.isalnum()]) in PRIMES for w in ws)


@register("words:repeats")
def _repeats(text, kw, prompt, s):
    c = Counter(norm_word(w, s) for w in words_of(text, s))
    n = _num(kw, "small_n")
    lim = n + 1 if sw(s, "D-repeat-count") == "repetitions" else n
    return max(c.values()) <= lim if c else False


_TAGDICT = None


def _tagdict():
    global _TAGDICT
    if _TAGDICT is None:
        import json
        import nltk
        p = nltk.data.find("taggers/averaged_perceptron_tagger_eng/")
        fn = os.path.join(str(p), "averaged_perceptron_tagger_eng.tagdict.json")
        _TAGDICT = json.load(open(fn, encoding="utf-8"))
    return _TAGDICT


@register("words:start_verb")
def _startverb(text, kw, prompt, s):
    import nltk
    m = re.search(r"[^\W\d_]", text)
    if not m:
        return False
    rest = text[m.start():]
    first_sent = sentences_of(rest, s)
    if not first_sent:
        return False
    sent = re.sub(r"[*_`#\"“”‘]+", "", first_sent[0])
    sent = re.sub(r"(?<!\w)'|'(?!\w)|(?<!\w)’|’(?!\w)", "", sent)
    toks = nltk.word_tokenize(sent)
    if not toks:
        return False
    tags = nltk.pos_tag(toks)
    t0 = tags[0][1]
    nxt = tags[1][1] if len(tags) > 1 else ""
    if t0.startswith("VB"):
        if t0 == "VBG" and sw(s, "D-verb") != "any_form":
            # gerund used as a subject ("Understanding requires care") is not a verb in context
            later = [t for _, t in tags[1:6]]
            if any(t in ("VBZ", "VBP", "VBD", "MD") for t in later):
                return False
        return True
    w = toks[0].casefold()
    td = _tagdict().get(w)
    if td and not td.startswith("VB"):
        return False
    if nxt in (":", ".", "VBZ", "VBP", "VBD", "MD", "POS") or (t0 == "NNP" and nxt in ("NNP", "NN", "NNS")):
        return False
    if nxt == "," and w in {"sure", "okay", "ok", "yes", "no", "well", "certainly", "absolutely", "hello", "hi",
                            "alright", "great", "indeed", "however", "firstly", "first", "so", "now", "here",
                            "oh", "ah", "thanks", "sorry", "please", "dear", "honestly", "ultimately", "overall"}:
        return False
    modal = nltk.pos_tag(["you", "should", w] + toks[1:])[2][1]
    return modal == "VB"


@register("words:vowel")
def _vowel(text, kw, prompt, s):
    if len(lines_nonblank(text)) != 1:
        return False
    ws = words_of(text, s)
    if not ws:
        return False
    mode = sw(s, "D-vowel-reading")
    if mode == "per_word":
        return all(len({c for c in ascii_fold(w).casefold() if c in "aeiou"}) <= 3 for w in ws)
    vs = {c for w in ws for c in ascii_fold(w).casefold() if c in "aeiou"}
    if mode == "exactly_three":
        return len(vs) == 3
    return len(vs) <= 3


@register("words:words_position")
def _wpos(text, kw, prompt, s):
    ws = words_of(text, s)
    if len(ws) < 2:
        return False
    k = norm_word(kw.get("keyword"), s)
    return norm_word(ws[1], s) == k and norm_word(ws[-2], s) == k


assert len(CHECKS) == 58, len(CHECKS)
