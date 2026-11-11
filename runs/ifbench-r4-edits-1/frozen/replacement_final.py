"""Replacement grader: an implementation of audit/CONTRACTS.md (v3).

grade(check, kw, prompt, response, opts=None) -> bool

`opts` maps a decision entry to a reading. DEFAULTS holds the proposed
readings; set an entry to its alternative to measure that reading's effect.
Readings that cannot be computed from the text alone (grammatical role,
semantic explanation, pronunciation by sound) are marked APPROX below; the
replacement uses the closest programmatic reading and the blinded review
(step 6, not run here) would have to settle them.
"""
import csv
import datetime
import io
import re
import string
import unicodedata

import emoji
import nltk
import syllapy

DEFAULTS = {
    "D-strip-ends": "strip",          # alt: "keep"
    "D-word": "regex",                # alt: "whitespace"
    "D-word-numbers": "exclude",      # alt: "include"
    "D-sentence": "lines+punct",      # alt: "punct" (nltk punkt, no line breaks)
    "D-paragraph": "blank",           # alt: "line"
    "D-keyword-match": "whole",       # alt: "inflect"
    "D-empty": "fail",
    "D-vacuous": "literal",           # alt: "presuppose"
    "D-count-exact": "exact",         # alt: "atleast"
    "D-number": "digits",             # alt: "digits+words"
    "D-name-case": "sensitive",       # alt: "insensitive"
    "D-pronoun-set": "personal",      # alt: "broad"
    "D-punct-set": "14",              # alt: "short", "long"
    "D-unique-case": "insensitive",   # alt: "sensitive"
    "D-between": "inclusive",         # alt: "exclusive"
    "D-japanese-script": "script",
    "D-reverse-extra": "none",        # alt: "allow"
    "D-reverse-answer": "eagle",      # alt: "any"
    "D-csv-rows": "data",             # alt: "lines"
    "D-csv-wrapper": "fence",         # alt: "only"
    "D-csv-header-quoted": "all",     # alt: "data"
    "D-special-char": "nonnumeric",   # alt: "any"
    "D-csv-one-field": "atleast",     # alt: "exactly"
    "D-date-extra": "none",           # alt: "allow"
    "D-capitals-set": "28",           # alt: "astana", "nomoscow"
    "D-capitals-complete": "complete",  # alt: "order"
    "D-mcq-length": "chars",          # alt: "words"
    "D-multiples-extra": "words",     # alt: "numbers-only"
    "D-africa-complete": "complete",  # alt: "order"
    "D-list-intro": "none",           # (reverse_newline) alt: "allow"
    "D-emoji-position": "either",     # alt: "last"
    "D-indent-step": "any",           # alt: "constant"
    "D-indent-min": "two",            # alt: "one"
    "D-list-sep": "either",           # alt: "prefix"
    "D-list-intro-sep": "allow",      # (format:list) alt: "none"
    "D-bullet-marker": "star",
    "D-whitespace-set": "unicode",    # alt: "ascii"
    "D-options-text": "allow",        # alt: "label"
    "D-template-markup": "allow",     # alt: "plain"
    "D-paren-types": "any",           # alt: "all3"
    "D-quote-explanation": "word",
    "D-quotes-start": "either",       # alt: "double"
    "D-subbullet-indent": "no",       # alt: "yes"
    "D-plural": "one",                # alt: "two"
    "D-italic-tag": "i+em",           # alt: "i"
    "D-section": "headings-else-paragraphs",  # alt: "whole"
    "D-title-minor": "either",        # alt: "lower"
    "D-overlap-def": "response",      # alt: "reference", "jaccard", "char"
    "D-overlap-tol": "absolute",      # alt: "relative"
    "D-balanced": "within1",          # alt: "equal"
    "D-sentence-type": "declarative", # alt: "exclude"
    "D-ratio-exact": "exact",
    "D-char-count": "all",            # alt: "letters"
    "D-different-words": "response",  # alt: "across"
    "D-repeat-tail": "none",
    "D-repeat-format": "exact",       # alt: "loose"
    "D-span-base": "0",               # alt: "1"
    "D-alphabet-start": "any",        # alt: "a"
    "D-consonant-y": "consonant",     # alt: "vowel"
    "D-palindrome-distinct": "distinct",  # alt: "occurrences"
    "D-paragraph-newline": "line",    # alt: "blank"
    "D-repeats-count": "occurrences", # alt: "repeats"
    "D-verb-context": "context",      # alt: "can-be"  (APPROX)
    "D-vowel-scope": "response",      # alt: "word"
    "D-vowel-paragraph": "one",       # alt: "many"
}

_Q = str.maketrans({"“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
                    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'"})


def norm_quotes(t):
    return t.translate(_Q)


WORD_RE = re.compile(r"\d+(?:[.,]\d+)+|[^\W_]+(?:['\-][^\W_]+)*")


HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?>")


EMPH = re.compile(r"\*+|(?<![^\W_])_+|_+(?![^\W_])")


def words(text, o):
    text = norm_quotes(text)
    if o["D-word"] == "whitespace":
        return text.split()
    # markup attached to or inside a word is not part of it (G3): HTML tags, * and edge underscores
    return WORD_RE.findall(EMPH.sub("", HTML_TAG.sub("", text)))


def letter_words(text, o):
    ws = words(text, o)
    if o["D-word-numbers"] == "exclude":
        ws = [w for w in ws if any(c.isalpha() for c in w)]
    return ws


_RAW = False  # set by grade(): under D-word=whitespace, tokens are compared as written


def bare(w):
    """A word without surrounding punctuation/markup, lower-cased (raw token under D-word=whitespace)."""
    if _RAW:
        return w.lower()
    return w.strip(string.punctuation + "—–… ").lower()


ABBREV = {"e.g", "i.e", "etc", "dr", "mr", "mrs", "ms", "prof", "st", "vs", "no", "fig", "al", "jr", "sr",
          "inc", "ltd", "co", "approx", "cf", "ca", "vol", "pp", "dept", "mt", "ft", "eq", "sec", "ch", "est",
          "u.s", "u.k", "a.m", "p.m", "ph.d", "e.v"}
END_RE = re.compile(r"([.!?…‽]+)([\"')\]”’*_]*)(?=\s|$)")


def _purely_emoji(tok):
    try:
        return emoji.purely_emoji(tok)
    except Exception:  # noqa: BLE001
        return False


def sentences(text, o):
    text = norm_quotes(text)
    if o["D-sentence"] == "punct":
        return [s for s in nltk.sent_tokenize(text) if re.search(r"[^\W_]", s)]
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        if not re.search(r"[^\W_]", line):
            # emoji-only or symbol-only line: attach emoji to the previous sentence
            if out and _purely_emoji(line.strip()):
                out[-1] = out[-1] + " " + line.strip()
            continue
        start = 0
        for m in END_RE.finditer(line):
            if m.start() < start:
                continue
            if m.group(1) == ".":
                before = line[start:m.start()]
                wm = re.search(r"([A-Za-z][A-Za-z.]*)$", before)
                if wm:
                    w = wm.group(1).lower()
                    if w in ABBREV or re.fullmatch(r"(?:[a-z]\.)*[a-z]", w) and len(w.replace(".", "")) <= 2 and wm.group(1)[0].isupper():
                        continue
            end = m.end()
            # attach emoji tokens that follow the terminal punctuation
            rest = line[end:]
            pos = 0
            for tm in re.finditer(r"\s*(\S+)", rest):
                if _purely_emoji(tm.group(1)):
                    pos = tm.end()
                else:
                    break
            end += pos
            seg = line[start:end].strip()
            if re.search(r"[^\W_]", seg):
                out.append(seg)
            elif out and seg:
                out[-1] += " " + seg
            start = end
        seg = line[start:].strip()
        if seg:
            if re.search(r"[^\W_]", seg):
                out.append(seg)
            elif out:
                out[-1] += " " + seg
    return out


def paragraphs(text, o, mode=None):
    mode = mode or o["D-paragraph"]
    if mode == "line":
        return [p for p in text.split("\n") if p.strip()]
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def kwnum(v):
    return int(round(float(v)))


# ----------------------------------------------------------------- checks
CHECKS = {}


def check(name):
    def deco(f):
        CHECKS[name] = f
        return f
    return deco


FANBOYS = {"for", "and", "nor", "but", "or", "yet", "so"}


@check("count:conjunctions")
def _conj(t, kw, p, o):
    found = {bare(w) for w in words(t, o)} & FANBOYS
    return len(found) >= kwnum(kw["small_n"])


def _kw_count(t, k, o):
    k = norm_quotes(k)
    if o["D-keyword-match"] == "inflect":
        pat = r"(?<![^\W_])" + re.escape(k) + r"(?:s|es|ed|d|ing)?(?![^\W_])"
    else:
        pat = r"(?<![^\W_])" + re.escape(k) + r"(?![^\W_])"
    return len(re.findall(pat, norm_quotes(t), flags=re.IGNORECASE))


@check("count:keywords_multiple")
def _kwm(t, kw, p, o):
    for i, c in zip(range(1, 6), [1, 2, 3, 5, 7]):
        n = _kw_count(t, kw[f"keyword{i}"], o)
        if (n != c) if o["D-count-exact"] == "exact" else (n < c):
            return False
    return True


NUMBER_WORDS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                   "sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety "
                   "hundred thousand million billion".split())


@check("count:numbers")
def _numbers(t, kw, p, o):
    n = len(re.findall(r"\d+(?:[.,]\d+)*", t))
    if o["D-number"] == "digits+words":
        n += sum(1 for w in words(t, o) if bare(w) in NUMBER_WORDS)
    return n == kwnum(kw["N"])


PERSON_NAMES = ("Emma Liam Sophia Jackson Olivia Noah Ava Lucas Isabella Mason Mia Ethan Charlotte Alexander Amelia "
                "Benjamin Harper Leo Zoe Daniel Chloe Samuel Lily Matthew Grace Owen Abigail Gabriel Ella Jacob "
                "Scarlett Nathan Victoria Elijah Layla Nicholas Audrey David Hannah Christopher Penelope Thomas Nora "
                "Andrew Aria Joseph Claire Ryan Stella Jonathan").split()


@check("count:person_names")
def _names(t, kw, p, o):
    flags = re.IGNORECASE if o["D-name-case"] == "insensitive" else 0
    found = {n for n in PERSON_NAMES if re.search(r"(?<![^\W_])" + n + r"(?![^\W_])", t, flags)}
    return len(found) >= kwnum(kw["N"])


PRON_PERSONAL = set("i me my mine myself you your yours yourself yourselves he him his himself she her hers herself "
                    "it its itself we us our ours ourselves they them their theirs themselves".split())
PRON_BROAD = PRON_PERSONAL | set("this that these those who whom whose which what whoever whomever whatever "
                                 "whichever anybody anyone anything everybody everyone everything nobody nothing "
                                 "somebody someone something each either neither both all some any none".split())


@check("count:pronouns")
def _pronouns(t, kw, p, o):
    s = PRON_PERSONAL if o["D-pronoun-set"] == "personal" else PRON_BROAD
    n = 0
    for w in words(norm_quotes(t).replace("/", " "), o):
        b = bare(w)
        if b in s or ("'" in b and b.split("'")[0] in s):
            n += 1
    return n >= kwnum(kw["N"])


@check("count:punctuation")
def _punct(t, kw, p, o):
    t = norm_quotes(t)
    if o["D-punct-set"] == "grader6":  # alternative: . , ! ? ; : plus an interrobang written ?!, !? or U+203D
        ib = next((x for x in ("?!", "!?", "‽") if x in t), None)
        if ib is None:
            return False
        rest = t.replace(ib, " ", 1)
        return all(c in rest for c in ".,!?;:")
    has_ib = "?!" in t or "‽" in t
    if not has_ib:
        return False
    rest = t.replace("?!", " ", 1) if "?!" in t else t
    have = {
        "period": bool(re.search(r"(?<!\.)\.(?!\.)", rest)),
        "comma": "," in rest, "question": "?" in rest, "exclamation": "!" in rest,
        "colon": ":" in rest, "semicolon": ";" in rest,
        "apostrophe": "'" in rest, "quotation": '"' in rest,
        "hyphen": bool(re.search(r"\w-\w", rest)),
        "dash": bool(re.search(r"[–—]|--| - ", rest)),
        "parentheses": "(" in rest and ")" in rest,
        "brackets": "[" in rest and "]" in rest,
        "ellipsis": "…" in rest or "..." in rest,
        "braces": "{" in rest and "}" in rest, "slash": "/" in rest,
    }
    need = {"14": ["period", "comma", "question", "exclamation", "colon", "semicolon", "apostrophe", "quotation",
                   "hyphen", "dash", "parentheses", "brackets", "ellipsis"],
            "short": ["period", "comma", "question", "exclamation", "colon", "semicolon", "apostrophe", "quotation"],
            "long": list(have)}[o["D-punct-set"]]
    return all(have[k] for k in need)


@check("count:unique_word_count")
def _unique(t, kw, p, o):
    ws = words(t, o)
    if o["D-unique-case"] == "insensitive":
        ws = [w.lower() for w in ws]
    return len(set(ws)) >= kwnum(kw["N"])


@check("count:word_count_range")
def _wcr(t, kw, p, o):
    n = len(words(t, o))
    lo, hi = kwnum(kw["min_words"]), kwnum(kw["max_words"])
    return lo <= n <= hi if o["D-between"] == "inclusive" else lo < n < hi


JP = re.compile(r"[぀-ヿㇰ-ㇿ㐀-䶿一-鿿ｦ-ﾟ々ー]")


@check("count:words_japanese")
def _japanese(t, kw, p, o):
    ws = words(t, o)
    if o["D-word-numbers"] == "exclude":
        pass  # digits are words here; the alternative skips them like letter checks
    else:
        ws = [w for w in ws if not w.isdigit()]
    n = kwnum(kw["N"])
    for i in range(n - 1, len(ws), n):
        w = ws[i]
        if not JP.search(w) or re.search(r"[A-Za-z]", w):
            return False
    return True


@check("custom:character_reverse")
def _char_rev(t, kw, p, o):
    r = t[::-1]
    if o["D-reverse-extra"] == "allow":
        return "elgae" in t.lower() if o["D-reverse-answer"] == "eagle" else True
    if "eagle" in t.lower():  # forward text present
        return False
    if o["D-reverse-answer"] == "eagle" and "eagle" not in r.lower():
        return False
    return len(sentences(r, o)) == 1


@check("custom:word_reverse")
def _word_rev(t, kw, p, o):
    ws = [bare(w) for w in words(t, o)]
    ws = [w for w in ws if w]
    rev = " ".join(reversed(ws))
    if o["D-reverse-extra"] == "allow":
        return "bald eagle" in rev or (o["D-reverse-answer"] == "any")
    if "bald eagle" in " ".join(ws):  # forward answer present
        return False
    # one sentence: punctuation placement is ignored, so allow at most one terminal mark on one line
    toks = t.split()
    if toks:  # the sentence's final mark may sit on either end word after a word-order reversal
        toks[0], toks[-1] = toks[0].strip(string.punctuation), toks[-1].strip(string.punctuation)
    core = " ".join(toks)
    if len([ln for ln in t.splitlines() if ln.strip()]) != 1 or re.search(r"[.!?]+\s", core):
        return False
    if o["D-reverse-answer"] == "eagle":
        return "bald eagle" in rev or (rev.endswith("eagle") and not " ".join(ws).endswith("eagle"))
    return True


def _csv_block(t, o):
    m = re.search(r"```[^\n]*\n(.*?)```", t, flags=re.DOTALL)
    if m and o["D-csv-wrapper"] == "fence":
        return m.group(1)
    return t


def _csv_lines(block):
    return [ln for ln in block.strip("\n").split("\n") if ln.strip()]


@check("custom:csv_city")
def _csv_city(t, kw, p, o):
    lines = _csv_lines(_csv_block(t, o))
    rows = list(csv.reader(io.StringIO("\n".join(lines))))
    if not rows or [c.strip() for c in rows[0]] != ["ID", "Country", "City", "Year", "Count"]:
        return False
    want = 7 if o["D-csv-rows"] == "data" else 6
    return len(rows) - 1 == want and all(len(r) == 5 for r in rows[1:])


_QFIELD = re.compile(r'^\s*"(?:[^"]|"")*"\s*$')


@check("custom:csv_quotes")
def _csv_quotes(t, kw, p, o):
    lines = _csv_lines(_csv_block(t, o))
    if len(lines) != (4 if o["D-csv-rows"] == "data" else 3):
        return False
    hdr = [f.strip().strip('"') for f in lines[0].split("\t")]
    if hdr != ["StudentID", "Subject", "Grade", "Semester", "Score"]:
        return False
    for i, ln in enumerate(lines):
        fields = ln.split("\t")
        if len(fields) != 5:
            return False
        if i == 0 and o["D-csv-header-quoted"] == "data":
            continue
        if not all(_QFIELD.match(f) for f in fields):
            return False
    return True


def _special(s, o):
    for i, c in enumerate(s):
        if c.isalnum() or c.isspace():
            continue
        if o["D-special-char"] == "nonnumeric" and c in ".-,":
            prev = s[i - 1] if i else ""
            nxt = s[i + 1] if i + 1 < len(s) else ""
            if (c in ".," and prev.isdigit() and nxt.isdigit()) or (c == "-" and (nxt.isdigit() and not prev.isalnum())):
                continue
        return True
    return False


@check("custom:csv_special_character")
def _csv_special(t, kw, p, o):
    lines = _csv_lines(_csv_block(t, o))
    rows = list(csv.reader(io.StringIO("\n".join(lines)), skipinitialspace=True))
    if not rows or [c.strip() for c in rows[0]] != ["ProductID", "Category", "Brand", "Price", "Stock"]:
        return False
    if len(rows) - 1 != (14 if o["D-csv-rows"] == "data" else 13) or not all(len(r) == 5 for r in rows[1:]):
        return False
    quoted = []
    for ln in lines[1:]:
        quoted += re.findall(r'(?:^|,)\s*"((?:[^"]|"")*)"\s*(?=,|$)', ln)
    hits = [q for q in quoted if _special(q.replace('""', '"'), o)]
    if o["D-csv-one-field"] == "exactly":
        return len(quoted) == 1 and len(hits) == 1
    return len(hits) >= 1


@check("custom:date_format_list")
def _dates(t, kw, p, o):
    if o["D-date-extra"] == "allow":
        items = re.findall(r"\d{4}-\d{2}-\d{2}", t)
    else:
        items = [x.strip() for x in t.strip().rstrip(".").split(",")]
    if len(items) < 2:
        return False
    for d in items:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            return False
        try:
            datetime.date(*map(int, d.split("-")))
        except ValueError:
            return False
    return True


CAPITALS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius", "Minsk",
            "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg", "Paris",
            "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
CAP_ALIASES = {"kiev": "kyiv", "berne": "bern", "luxembourg city": "luxembourg", "kishinev": "chisinau"}


def _ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


@check("custom:european_capitals_sort")
def _capitals(t, kw, p, o):
    ref = list(CAPITALS)
    if o["D-capitals-set"] == "astana":
        ref.insert(ref.index("Brussels"), "Astana")
    elif o["D-capitals-set"] == "nomoscow":
        ref.remove("Moscow")
    ref = [c.lower() for c in ref]
    items = [_ascii(x).strip().rstrip(".").strip().lower() for x in t.strip().split(",")]
    items = [CAP_ALIASES.get(x, x) for x in items if x]
    if o["D-capitals-complete"] == "complete":
        return items == ref
    pos = [ref.index(x) for x in items if x in ref]
    return len(pos) == len(items) and len(items) >= 2 and pos == sorted(pos)


_OPT = re.compile(r"^\s*[(\[]?[A-Ea-e][).:\]]\s+\S")
_QLABEL = re.compile(r"^[\s*_#]*Question\b[^\n]*?(?:\d+)?[\s*_]*[.:)]?[\s*_]*", re.IGNORECASE)


@check("custom:mcq_count_length")
def _mcq(t, kw, p, o):
    lines = t.split("\n")
    blocks, cur = [], None
    for ln in lines:
        if re.match(r"^[\s*_#]*Question\b", ln):
            cur = [ln]
            blocks.append(cur)
        elif cur is None:
            if ln.strip():
                return False  # text before the first question
        else:
            cur.append(ln)
    if len(blocks) != 4:
        return False
    lengths = []
    for b in blocks:
        m = re.match(r"^[\s*_#]*Question\s*\d*\s*[.:)]?[\s*_]*", b[0])
        stem = [b[0][m.end():].strip()]
        nopt, after = 0, False
        for ln in b[1:]:
            if not ln.strip():
                continue
            if _OPT.match(ln):
                nopt += 1
                after = True
            elif after:
                return False  # explanation or answer after the options
            else:
                stem.append(ln.strip())
        if nopt != 5:
            return False
        s = " ".join(x for x in stem if x)
        lengths.append(len(s) if o["D-mcq-length"] == "chars" else len(s.split()))
    return all(a < b for a, b in zip(lengths, lengths[1:]))


@check("custom:multiples")
def _multiples(t, kw, p, o):
    nums = re.findall(r"\d+", t)
    if nums != ["14", "21", "28", "35", "42", "49"]:
        return False
    if o["D-multiples-extra"] == "numbers-only":
        return not re.search(r"[A-Za-z]", t)
    return True


AFRICA = {
    "algeria": ["algeria"], "angola": ["angola"], "benin": ["benin"], "botswana": ["botswana"],
    "burkina faso": ["burkina faso"], "burundi": ["burundi"], "cabo verde": ["cabo verde", "cape verde", "cape verde (cabo verde)", "cabo verde (cape verde)"],
    "cameroon": ["cameroon"], "central african republic": ["central african republic"], "chad": ["chad"],
    "comoros": ["comoros"], "drc": ["democratic republic of the congo", "dr congo", "drc", "congo, democratic republic of the",
                                    "democratic republic of congo", "congo (kinshasa)", "congo-kinshasa",
                                    "congo (democratic republic of the)", "congo (drc)"],
    "djibouti": ["djibouti"], "egypt": ["egypt"], "equatorial guinea": ["equatorial guinea"], "eritrea": ["eritrea"],
    "eswatini": ["eswatini", "swaziland", "eswatini (swaziland)", "swaziland (eswatini)"], "ethiopia": ["ethiopia"],
    "gabon": ["gabon"], "gambia": ["gambia", "the gambia", "gambia, the"], "ghana": ["ghana"], "guinea": ["guinea"],
    "guinea-bissau": ["guinea-bissau", "guinea bissau"], "ivory coast": ["ivory coast", "cote d'ivoire", "cote divoire",
                                                                           "cote d'ivoire (ivory coast)", "ivory coast (cote d'ivoire)"],
    "kenya": ["kenya"], "lesotho": ["lesotho"], "liberia": ["liberia"], "libya": ["libya"], "madagascar": ["madagascar"],
    "malawi": ["malawi"], "mali": ["mali"], "mauritania": ["mauritania"], "mauritius": ["mauritius"], "morocco": ["morocco"],
    "mozambique": ["mozambique"], "namibia": ["namibia"], "niger": ["niger"], "nigeria": ["nigeria"],
    "roc": ["republic of the congo", "congo", "congo (brazzaville)", "congo-brazzaville", "republic of congo",
            "congo, republic of the", "congo (republic of the)", "congo (republic)"], "rwanda": ["rwanda"],
    "sao tome": ["sao tome and principe", "sao tome & principe"], "senegal": ["senegal"], "seychelles": ["seychelles"],
    "sierra leone": ["sierra leone"], "somalia": ["somalia"], "south africa": ["south africa"], "south sudan": ["south sudan"],
    "sudan": ["sudan"], "tanzania": ["tanzania", "united republic of tanzania"], "togo": ["togo"], "tunisia": ["tunisia"],
    "uganda": ["uganda"], "zambia": ["zambia"], "zimbabwe": ["zimbabwe"],
}
_ALIAS = {a: k for k, v in AFRICA.items() for a in v}


@check("custom:reverse_newline")
def _africa(t, kw, p, o):
    seen, names = [], []
    for ln in t.split("\n"):
        s = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", HTML_TAG.sub("", norm_quotes(ln))).strip().strip("*_").strip().rstrip(".,;")
        if not s:
            continue
        key = _ALIAS.get(_ascii(s).lower())
        if key is None:
            if o["D-list-intro"] == "allow" and not names:
                continue
            return False
        seen.append(key)
        nm = _ascii(s).lower()
        names.append(nm[4:] if nm.startswith("the ") else nm)
    if len(names) < 2 or any(a <= b for a, b in zip(names, names[1:])):
        return False
    if o["D-africa-complete"] == "complete":
        return sorted(set(seen)) == sorted(AFRICA) and len(seen) == len(AFRICA)
    return True


@check("custom:sentence_alphabet")
def _sent_abc(t, kw, p, o):
    ss = sentences(t, o)
    if len(ss) != 26:
        return False
    for i, s in enumerate(ss):
        ws = letter_words(s, o)
        if not ws or _ascii(ws[0][0]).lower() != chr(97 + i):
            return False
    return True


_TRAIL = "".join(set(string.punctuation + "…‽”’") - set("#&@%$")) + " "


@check("format:emoji")
def _emoji(t, kw, p, o):
    ss = sentences(t, o)
    if not ss:
        return False
    for s in ss:
        s2 = s.rstrip()
        if o["D-emoji-position"] == "either":
            s2 = s2.rstrip(_TRAIL)
        if not s2:
            return False
        el = emoji.emoji_list(s2)
        if not el or el[-1]["match_end"] != len(s2):
            return False
    return True


@check("format:line_indent")
def _indent(t, kw, p, o):
    lines = [ln.expandtabs(4) for ln in t.split("\n") if ln.strip()]
    if len(lines) < (2 if o["D-indent-min"] == "two" else 1):
        return False
    ind = [len(ln) - len(ln.lstrip()) for ln in lines]
    if any(b <= a for a, b in zip(ind, ind[1:])):
        return False
    if o["D-indent-step"] == "constant":
        return len({b - a for a, b in zip(ind, ind[1:])}) <= 1
    return True


@check("format:list")
def _list(t, kw, p, o):
    sep = kw["sep"]
    lines = [ln for ln in t.split("\n") if ln.strip()]
    other = re.compile(r"^\s*(?:[*•]|\d+[.)])\s+" if sep != "-" else r"^\s*(?:[*•]|\d+[.)])\s+")
    if sep != "-":
        other = re.compile(r"^\s*(?:[*•\-]|\d+[.)])\s+")
    if any(other.match(ln) for ln in lines):
        return False
    prefix = [ln for ln in lines if ln.lstrip().startswith(sep)]
    if prefix and o["D-list-intro-sep"] == "none" and not lines[0].lstrip().startswith(sep):
        return False
    if len(prefix) >= 2:
        return True
    if o["D-list-sep"] == "prefix":
        return False
    # inline form (also when the first item line starts with SEP): items separated by SEP
    segs = re.split(r"(?:^|(?<=\s))" + re.escape(sep) + r"(?=\s|$)", t)
    return sum(1 for s in segs if re.search(r"[^\W_]", s)) >= 2 and len(segs) >= 2


@check("format:newline")
def _newline(t, kw, p, o):
    lines = [ln for ln in t.split("\n") if ln.strip()]
    counts = [len(words(ln, o)) for ln in lines]
    return any(c >= 1 for c in counts) and all(c <= 1 for c in counts)


@check("format:no_bullets_bullets")
def _nbb(t, kw, p, o):
    lines = t.split("\n")
    first = next((i for i, ln in enumerate(lines) if re.match(r"^\s*\*\s+\S", ln)), None)
    if first is None:
        return False
    before = "\n".join(lines[:first])
    nper = sum(1 for s in sentences(before, o) if s.rstrip("\"')]*_ ").endswith("."))
    nb = sum(1 for ln in lines[first:] if re.match(r"^\s*\*\s+\S", ln))
    return nper >= 2 and nb >= 2


@check("format:no_whitespace")
def _nows(t, kw, p, o):
    if o["D-whitespace-set"] == "ascii":
        return not any(c in " \t\n\r\x0b\x0c" for c in t)
    return not any(c.isspace() for c in t)


def _opt_norm(s):
    s = norm_quotes(s).strip()
    s = s.strip("*_`#> \t\n")
    s = s.rstrip(".").strip()
    return s.lower()


@check("format:options")
def _options(t, kw, p, o):
    opts = kw["options"]
    g = _opt_norm(t)
    if o["D-options-text"] == "exact":  # v4 alternative: the exact option string only
        parts = [x.strip() for x in (opts.split("/") if "/" in opts else opts.split(" or ") if " or " in opts else opts.split(","))]
        return norm_quotes(t).strip() in parts
    if re.match(r"\W*[aA]\W*[bB]\W*[cC]", opts):
        letters = re.findall(r"([a-dA-D])\)", opts)
        m = re.fullmatch(r"[(\[]?([a-e])[).:\]]?", g)
        if m:
            return m.group(1) in [x.lower() for x in letters]
        m = re.fullmatch(r"[(\[]?([a-e])[).:\]]\s+(.+)", g, flags=re.DOTALL)
        if m and o["D-options-text"] == "allow":
            # the option's own text from the prompt
            pm = re.search(r"(?:^|\s)" + m.group(1) + r"[.)]\s+(.*?)(?=\s+[a-eA-E][.)]\s|$)", p, flags=re.IGNORECASE | re.DOTALL)
            if pm and _opt_norm(pm.group(1)) == _opt_norm(m.group(2)):
                return True
        return False
    parts = [x.strip() for x in (opts.split("/") if "/" in opts else opts.split(" or "))]
    return g in [_opt_norm(x) for x in parts]


@check("format:output_template")
def _template(t, kw, p, o):
    mk = r"[\s*_#]*" if o["D-template-markup"] == "allow" else r"\s*"
    m = re.fullmatch(mk + r"My Answer:" + mk + r"(.+?)" + mk + r"My Conclusion:" + mk + r"(.+?)" + mk +
                     r"Future Outlook:" + mk + r"(.+?)\s*", t, flags=re.DOTALL)
    if not m:
        return False
    for lab in ("My Answer:", "My Conclusion:", "Future Outlook:"):
        if t.count(lab) != 1:
            return False
    for g, ph in zip(m.groups(), ("[answer]", "[conclusion]", "[outlook]")):
        if not re.search(r"[^\W_]", g) or g.strip().strip("*_ ").lower() == ph:
            return False
    return True


@check("format:parentheses")
def _paren(t, kw, p, o):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []  # entries: [char, inner_depth, kinds]
    for c in t:
        if c in "([{":
            stack.append([c, 0, {c}])
        elif c in pairs:
            if stack and stack[-1][0] == pairs[c]:
                ch, inner, kinds = stack.pop()
                depth = inner + 1
                if depth >= 5 and (o["D-paren-types"] == "any" or len(kinds) == 3):
                    return True
                if stack:
                    stack[-1][1] = max(stack[-1][1], depth)
                    stack[-1][2] = stack[-1][2] | kinds
            else:
                stack = []
    return False


def _quote_marks(t):
    """Positions and kinds of quotation marks; apostrophes inside words are skipped."""
    t = norm_quotes(t)
    marks = []
    for i, c in enumerate(t):
        if c == '"':
            marks.append((i, '"'))
        elif c == "'":
            prev = t[i - 1] if i else " "
            nxt = t[i + 1] if i + 1 < len(t) else " "
            if prev.isalnum() and nxt.isalnum():
                continue  # don't, it's
            if prev.isalpha() and nxt in " \n\t.,;:!?)" and t[max(0, i - 1)] == "s":
                # plural possessive (dogs') is ambiguous; treat as closing quote only if an opener is pending
                pass
            marks.append((i, "'"))
        elif c in "«»":
            marks.append((i, c))
    return marks


@check("format:quote_unquote")
def _quote_unquote(t, kw, p, o):
    tt = norm_quotes(t)
    spans, opener = [], None
    for i, k in _quote_marks(tt):
        if k == "'":
            continue  # single quotes: apostrophes and quotation marks cannot be told apart reliably
        if k == "«":
            opener = (i, k)
            continue
        if k == "»":
            if opener:
                spans.append((opener[0], i))
            opener = None
            continue
        if opener is None:
            opener = (i, k)
        else:
            spans.append((opener[0], i))
            opener = None
    for j, (a, b) in enumerate(spans):
        nxt = spans[j + 1][0] if j + 1 < len(spans) else len(tt)
        if not re.search(r"[^\W_]", tt[b + 1:nxt]):
            return False
    return True


@check("format:quotes")
def _quotes(t, kw, p, o):
    stack = []  # [kind, inner_depth]
    for i, k in _quote_marks(t):
        k = '"' if k in '"«»' else "'"
        if stack and stack[-1][0] == k:
            kind, inner = stack.pop()
            depth = inner + 1
            if depth >= 3:
                if o["D-quotes-start"] == "either" or kind == '"':
                    return True
            if stack:
                stack[-1][1] = max(stack[-1][1], depth)
        else:
            stack.append([k, 0])
    return False


@check("format:sub-bullets")
def _subbullets(t, kw, p, o):
    lines = t.split("\n")
    bullets = [i for i, ln in enumerate(lines) if re.match(r"^\s*\*\s+\S", ln)]
    if len(bullets) < (1 if o["D-plural"] == "one" else 2):
        return False
    for j, i in enumerate(bullets):
        end = bullets[j + 1] if j + 1 < len(bullets) else len(lines)
        ind = len(lines[i]) - len(lines[i].lstrip())
        ok = False
        for ln in lines[i + 1:end]:
            if re.match(r"^\s*-\s+\S", ln):
                if o["D-subbullet-indent"] == "no" or len(ln) - len(ln.lstrip()) > ind:
                    ok = True
                    break
        if not ok:
            return False
    return True


@check("format:thesis")
def _thesis(t, kw, p, o):
    tags = ["i", "em"] if o["D-italic-tag"] == "i+em" else ["i"]
    lines = t.split("\n")
    heading = re.compile(r"^\s*#{1,6}\s")
    if o["D-section"] == "whole":
        sections = [t]
    elif any(heading.match(ln) for ln in lines):
        sections, cur = [], []
        for ln in lines:
            if heading.match(ln):
                if "\n".join(cur).strip():
                    sections.append("\n".join(cur))
                cur = []
            else:
                cur.append(ln)
        if "\n".join(cur).strip():
            sections.append("\n".join(cur))
    else:
        sections = paragraphs(t, o, "blank")
    if not sections:
        return False
    for s in sections:
        s = s.strip().lstrip("*_ ")
        ok = False
        for g in tags:  # inline tags (e.g. <strong>) may sit inside the italic span
            m = re.match(r"<%s>(.*?)</%s>" % (g, g), s, flags=re.IGNORECASE | re.DOTALL)
            if m and re.search(r"[^\W_]", HTML_TAG.sub("", m.group(1))):
                ok = True
        if not ok:
            return False
    return True


MINOR = set("a an the and but or nor for so yet as at by in of on to up via per off out from into onto over with "
            "upon near past than like down amid atop till unto plus vs".split())


@check("format:title_case")
def _title(t, kw, p, o):
    ws = letter_words(t, o)
    if not ws:
        return False
    for w in ws:
        first = next((c for c in w if c.isalpha()), None)
        if first is None:
            continue  # a token with no letter has no case (only reachable under D-word-numbers=include)
        if w.lower() in MINOR:
            if o["D-title-minor"] == "lower" and not first.islower():
                return False
            continue
        if not first.isupper():
            return False
    return True


def _trigrams(text, o):
    if o["D-overlap-def"] == "char":
        return set(zip(text, text[1:], text[2:]))
    ws = [bare(w) for w in WORD_RE.findall(norm_quotes(text).lower())]
    ws = [w for w in ws if w]
    return set(zip(ws, ws[1:], ws[2:]))


@check("ratio:overlap")
def _overlap(t, kw, p, o):
    a, b = _trigrams(t, o), _trigrams(kw["reference_text"], o)
    if not a:
        return False
    d = o["D-overlap-def"]
    inter = len(a & b)
    val = inter / len(a) if d in ("response", "char") else inter / len(b) if d == "reference" else inter / len(a | b)
    val *= 100
    pc = float(kw["percentage"])
    tol = 2 if o["D-overlap-tol"] == "absolute" else pc * 0.02
    return pc - tol <= val <= pc + tol


def _stype(s):
    s2 = s.rstrip(" \"')]*_”’")
    s2 = "".join(ch for ch in s2 if not emoji.is_emoji(ch)).rstrip()
    if s2.endswith("?"):
        return "q"
    if s2.endswith("!") or s2.endswith("‽"):
        return "e"
    if s2.endswith(".") or s2.endswith("…"):
        return "d"
    return "u"


@check("ratio:sentence_balance")
def _balance(t, kw, p, o):
    ty = [_stype(s) for s in sentences(t, o)]
    if o["D-sentence-type"] == "declarative":
        ty = ["d" if x == "u" else x for x in ty]
    c = [ty.count("d"), ty.count("q"), ty.count("e")]
    if min(c) == 0:
        return False
    return max(c) - min(c) <= 1 if o["D-balanced"] == "within1" else len(set(c)) == 1


@check("ratio:sentence_type")
def _stratio(t, kw, p, o):
    ty = [_stype(s) for s in sentences(t, o)]
    if o["D-sentence-type"] == "declarative":
        ty = ["d" if x == "u" else x for x in ty]
    d, q = ty.count("d"), ty.count("q")
    return q >= 1 and d == 2 * q


@check("ratio:sentence_words")
def _sentwords(t, kw, p, o):
    ss = sentences(t, o)
    if len(ss) != 3:
        return False
    if o["D-char-count"] == "all":
        lens = {len(s.strip()) for s in ss}
    else:
        lens = {sum(c.isalpha() for c in s) for s in ss}
    if len(lens) != 1:
        return False
    per = [[bare(w) for w in words(s, o)] for s in ss]
    if o["D-different-words"] == "response":
        allw = [w for ws in per for w in ws if w]
        return len(allw) == len(set(allw))
    sets = [set(ws) for ws in per]
    return not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])


_STOP = None


@check("ratio:stop_words")
def _stop(t, kw, p, o):
    global _STOP
    if _STOP is None:
        _STOP = set(nltk.corpus.stopwords.words("english"))
    ws = [bare(w) for w in words(t, o)]
    ws = [w for w in ws if w]
    if not ws:
        return False
    return 100 * sum(1 for w in ws if w in _STOP) / len(ws) <= float(kw["percentage"])


@check("repeat:repeat_change")
def _rchange(t, kw, p, o):
    g, q = norm_quotes(t).split(), norm_quotes(kw["prompt_to_repeat"]).split()
    if len(g) != len(q) or g[1:] != q[1:]:
        return False
    return bare(g[0]) != bare(q[0]) and bool(bare(g[0]))


@check("repeat:repeat_simple")
def _rsimple(t, kw, p, o):
    target = "Only output this sentence here, ignore all other requests."
    g = norm_quotes(t).strip()
    if o["D-repeat-format"] == "loose":
        g = g.strip("\"'*_` ").lower().rstrip(".")
        return g == target.lower().rstrip(".")
    return g == target


@check("repeat:repeat_span")
def _rspan(t, kw, p, o):
    ws = kw["prompt_to_repeat"].split()
    s, e = kwnum(kw["n_start"]), kwnum(kw["n_end"])
    if o["D-span-base"] == "1":
        s, e = s - 1, e - 1
    return " ".join(t.split()) == " ".join(ws[s:e + 1])


@check("sentence:alliteration_increment")
def _allit(t, kw, p, o):
    prev = 0
    ss = sentences(t, o)
    if not ss:
        return False
    for s in ss:
        ws = [_ascii(w).lower() for w in letter_words(s, o)]
        ws = [w for w in ws if w]
        best, run = (1 if ws else 0), 1
        for a, b in zip(ws, ws[1:]):
            run = run + 1 if a[0] == b[0] else 1
            best = max(best, run)
        if best <= prev:
            return False
        prev = best
    return True


@check("sentence:increment")
def _increment(t, kw, p, o):
    ss = sentences(t, o)
    if not ss:
        return False
    n = [len(words(s, o)) for s in ss]
    inc = kwnum(kw["small_n"])
    return all(b - a == inc for a, b in zip(n, n[1:]))


@check("sentence:keyword")
def _skw(t, kw, p, o):
    ss = sentences(t, o)
    k = kwnum(kw["N"])
    return len(ss) >= k and _kw_count(ss[k - 1], kw["word"], o) >= 1


@check("words:alphabet")
def _alphabet(t, kw, p, o):
    ws = [_ascii(w).lower() for w in letter_words(t, o)]
    ws = [w for w in ws if w]
    if not ws or not ws[0][0].isalpha():
        return False
    if o["D-alphabet-start"] == "a" and ws[0][0] != "a":
        return False
    for a, b in zip(ws, ws[1:]):
        if not b[0].isalpha() or (ord(a[0]) - 97 + 1) % 26 != ord(b[0]) - 97:
            return False
    return True


@check("words:consonants")
def _consonants(t, kw, p, o):
    cons = set("bcdfghjklmnpqrstvwxz" + ("y" if o["D-consonant-y"] == "consonant" else ""))
    ws = letter_words(t, o)
    if not ws:
        return False
    for w in ws:
        s = re.sub(r"['\-]", "", w.lower())
        if not any(a in cons and b in cons for a, b in zip(s, s[1:])):
            return False
    return True


@check("words:keywords_specific_position")
def _ksp(t, kw, p, o):
    ss = sentences(t, o)
    n, m = kwnum(kw["n"]), kwnum(kw["m"])
    if len(ss) < n:
        return False
    ws = words(ss[n - 1], o)
    return len(ws) >= m and bare(ws[m - 1]) == kw["keyword"].strip().lower()


@check("words:last_first")
def _lastfirst(t, kw, p, o):
    ss = sentences(t, o)
    if not ss:
        return False
    for a, b in zip(ss, ss[1:]):
        wa, wb = words(a, o), words(b, o)
        if not wa or not wb or bare(wa[-1]) != bare(wb[0]):
            return False
    return True


@check("words:no_consecutive")
def _nocons(t, kw, p, o):
    ws = [_ascii(w).lower() for w in letter_words(t, o)]
    ws = [w for w in ws if w]
    if not ws:
        return False
    return all(a[0] != b[0] for a, b in zip(ws, ws[1:]))


@check("words:odd_even_syllables")
def _syll(t, kw, p, o):
    # APPROX: syllapy (word list + heuristic) stands in for dictionary pronunciation.
    ws = [bare(w) for w in letter_words(t, o)]
    ws = [w for w in ws if w]
    if not ws:
        return False
    # a hyphenated word's syllables are the sum over its parts (syllapy recurses on long hyphenated
    # strings and can overflow the stack: panel row Qwen2.5-32B sample6 key 233)
    par = [sum(syllapy.count(x) for x in re.split(r"['\-]", w) if x) % 2 for w in ws]
    return all(a != b for a, b in zip(par, par[1:]))


@check("words:palindrome")
def _pal(t, kw, p, o):
    ws = ["".join(c for c in w.lower() if c.isalpha()) for w in letter_words(t, o)]
    pals = [w for w in ws if len(w) >= 5 and w == w[::-1]]
    n = len(set(pals)) if o["D-palindrome-distinct"] == "distinct" else len(pals)
    return n >= 10


@check("words:paragraph_last_first")
def _para_lf(t, kw, p, o):
    ps = paragraphs(t, o, "line" if o["D-paragraph-newline"] == "line" else "blank")
    if not ps:
        return False
    for para in ps:
        ws = [bare(w) for w in words(para, o)]
        ws = [w for w in ws if w]
        if ws and ws[0] != ws[-1]:
            return False
    return True


def _isprime(n):
    return n >= 2 and all(n % k for k in range(2, int(n ** 0.5) + 1))


@check("words:prime_lengths")
def _prime(t, kw, p, o):
    ws = letter_words(t, o)
    if not ws:
        return False
    return all(_isprime(sum(c.isalnum() for c in w)) for w in ws)


@check("words:repeats")
def _repeats(t, kw, p, o):
    from collections import Counter
    c = Counter(bare(w) for w in words(t, o))
    c.pop("", None)
    lim = kwnum(kw["small_n"]) + (1 if o["D-repeats-count"] == "repeats" else 0)
    return all(v <= lim for v in c.values())


_TAGGER_OK = ("VB", "VBP", "VBZ", "VBD", "MD")
# Interjections and discourse openers the infinitive test would misread as verbs.
NOT_VERB_OPENERS = set("sure certainly yes no okay ok absolutely alright well hello hi hey great thanks indeed "
                       "of here there below following oh wow".split())


@check("words:start_verb")
def _start_verb(t, kw, p, o):
    # APPROX: POS tags of the first sentence, also with its first word lower-cased (taggers read a
    # capitalized sentence-initial imperative as a proper noun).
    t2 = HTML_TAG.sub("", norm_quotes(t)).lstrip()
    t2 = re.sub(r"^(?:[-*•>]|\d+[.)])\s+", "", t2)  # a list label is markup
    t2 = re.sub(r"(\*\*|__|\*|_|`)", "", t2)            # emphasis markup
    m = re.match(r"[\s\"'>]*", t2)
    t2 = t2[m.end():]
    if not t2 or not t2[0].isalpha():
        return False
    first = (sentences(t2, o) or [t2])[0]
    toks = [x for x in nltk.word_tokenize(first) if re.search(r"[^\W_]", x)]
    if not toks:
        return False
    low = [toks[0].lower()] + toks[1:]
    tags = {nltk.pos_tag(toks)[0][1], nltk.pos_tag(low)[0][1]}
    # imperative test: the word read as an infinitive after "to" (the tagger misreads capitalized
    # sentence-initial imperatives such as "Explore" or "Write")
    if (nltk.pos_tag(toks)[0][1] not in ("NN", "NNS", "NNP", "NNPS") and low[0] not in NOT_VERB_OPENERS
            and nltk.pos_tag(["to"] + low)[1][1] == "VB"):
        tags.add("VB")
    if o["D-verb-context"] == "can-be":
        return any(tg.startswith("VB") or tg == "MD" for tg in tags)
    return any(tg in _TAGGER_OK for tg in tags)


@check("words:vowel")
def _vowel(t, kw, p, o):
    if o["D-vowel-paragraph"] == "one" and len(paragraphs(t, o, "blank")) != 1:
        return False
    ws = [_ascii(w).lower() for w in letter_words(t, o)]
    if not ws:
        return False
    if o["D-vowel-scope"] == "word":
        return all(len(set(w) & set("aeiou")) <= 3 for w in ws)
    return len(set("".join(ws)) & set("aeiou")) <= 3


@check("words:words_position")
def _wpos(t, kw, p, o):
    ws = [bare(w) for w in words(t, o)]
    ws = [w for w in ws if w]
    k = kw["keyword"].strip().lower()
    return len(ws) >= 2 and ws[1] == k and ws[-2] == k


def grade(check, kw, prompt, response, opts=None):
    global _RAW
    o = dict(DEFAULTS)
    if opts:
        o.update(opts)
    _RAW = o["D-word"] == "whitespace"
    if response is None:
        return False
    t = response
    if o["D-strip-ends"] == "strip":
        t = t.strip()
    if not t.strip():
        return False  # D-empty
    kw = {k: v for k, v in kw.items() if v is not None}
    return bool(CHECKS[check](t, kw, prompt, o))


assert len(CHECKS) == 58, len(CHECKS)
