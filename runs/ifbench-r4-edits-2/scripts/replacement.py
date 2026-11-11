"""Replacement IFBench grader built from audit/CONTRACTS.md (v2).

check(instruction_id, kwargs, response, prompt="", **switches) -> bool

Each decision entry that the panel can exercise has a switch; the default is the
contract's proposal. Switch names are the decision ids in lower case with '-' -> '_'
(for example d_vacuous="pass" selects the non-proposed reading of D-vacuous).
Not modelled: D-syllables (syllapy, as in the grader), D-content, D-reverse-content.
"""
import calendar
import csv
import io
import re
import string
import unicodedata
from collections import Counter

import emoji
import nltk
import syllapy

DEFAULTS = dict(
    d_vacuous="fail",          # D-vacuous: missing presupposed structure fails
    d_typographic=True,        # D-typographic: curly quotes = straight
    d_count_exact=True,        # D-count-exact
    d_keyword_form="word",     # D-keyword-form: word | substring
    d_punct_set="broad",       # D-punct-set: broad | narrow (. , ? ! ; : + interrobang)
    d_punct_separate=False,    # D-punct-separate: True requires ? and ! outside the interrobang
    d_overlap_unit="word",     # D-overlap-def: word | char
    d_overlap_side="response",  # D-overlap-def: response | reference
    d_balance="equal",         # D-balance: equal | near
    d_list_inline=False,       # D-list-inline
    d_nows_trailing=True,      # D-nows-trailing: ignore one trailing newline
    d_options_whitespace=True,  # D-options-whitespace
    d_template_outside=False,  # D-template-outside: True allows prose outside
    d_csv_wrapper=True,        # D-csv-wrapper: fenced payload allowed
    d_palin_distinct=True,     # D-palin-distinct
    d_vowel_paragraph="blank",  # D-vowel-paragraph: blank | newline
    d_vowel="whole",           # D-vowel: whole | word
    d_span_base=0,             # D-span-base
    d_empty_output="prohibitions_pass",  # D-empty-output
    d_europe_moscow=True,      # D-europe-set
    d_africa_complete=True,    # D-africa-list
    d_indent_blank=True,       # D-indent-blank: ignore blank lines
    d_section="blank_or_heading",  # D-section
)

# ------------------------------------------------------------------ text helpers
_TYPO = str.maketrans({"‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
                       "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"'})
_LABEL = re.compile(r"^\s*(?:[-*•+]\s+|\d+[.)]\s+|\(?[a-zA-Z]\)\s+|#{1,6}\s+|>\s+)")
_DASHES = re.compile(r"[—–‒―]")


def norm(text, sw):
    text = text.replace("\r\n", "\n").replace("\r", "\n")  # a carriage return is a line break
    return text.translate(_TYPO) if sw["d_typographic"] else text


def has_alnum(s):
    return any(ch.isalnum() for ch in s)


def strip_edges(tok):
    i, j = 0, len(tok)
    while i < j and not tok[i].isalnum():
        i += 1
    while j > i and not tok[j - 1].isalnum():
        j -= 1
    return tok[i:j]


def clean_line(line):
    return _LABEL.sub("", line, count=1)


def words(text):
    out = []
    for line in text.split("\n"):
        for tok in _DASHES.sub(" ", clean_line(line)).split():
            t = strip_edges(tok)
            if t and has_alnum(t):
                out.append(t)
    return out


def sentences(text):
    out = []
    for line in text.split("\n"):
        line = clean_line(line).strip()
        if not has_alnum(line):
            continue
        for s in nltk.sent_tokenize(line):
            if has_alnum(s):
                out.append(s.strip())
    return out


def end_mark(sentence):
    s = sentence.rstrip()
    s = re.sub(r"[\s\"')\]*_`]+$", "", s)
    ems = emoji.emoji_list(s)
    while ems and ems[-1]["match_end"] == len(s):
        s = s[: ems[-1]["match_start"]].rstrip()
        s = re.sub(r"[\s\"')\]*_`]+$", "", s)
        ems = emoji.emoji_list(s)
    return s[-1:] if s else ""


def wlow(w):
    return w.lower()


def payload(text, sw):
    if sw["d_csv_wrapper"]:
        m = re.search(r"```[^\n]*\n(.*?)```", text, re.S)
        if m:
            return m.group(1)
    return text


def is_prime(n):
    return n >= 2 and all(n % k for k in range(2, int(n ** 0.5) + 1))


# ------------------------------------------------------------------ data
FANBOYS = {"and", "but", "or", "nor", "for", "yet", "so"}
PERSON_NAMES = ("Emma Liam Sophia Jackson Olivia Noah Ava Lucas Isabella Mason Mia Ethan Charlotte Alexander Amelia "
                "Benjamin Harper Leo Zoe Daniel Chloe Samuel Lily Matthew Grace Owen Abigail Gabriel Ella Jacob "
                "Scarlett Nathan Victoria Elijah Layla Nicholas Audrey David Hannah Christopher Penelope Thomas Nora "
                "Andrew Aria Joseph Claire Ryan Stella Jonathan").split()
PRONOUNS = set("""i me you he him she her it we us they them my mine your yours his hers its our ours their theirs
myself yourself himself herself itself ourselves yourselves themselves this that these those who whom whose which
what whoever whomever whatever whichever anybody anyone anything everybody everyone everything nobody nothing
somebody someone something each either neither both all some any none one""".split())
MINOR = set("a an the and but or nor for so yet as at by in of off on per to up via".split())
CAPS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius", "Minsk",
        "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg", "Paris",
        "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
CAP_ALIASES = {"kiev": "kyiv", "luxembourg city": "luxembourg", "reykjavík": "reykjavik", "chişinău": "chisinau"}
AFRICA = {
    "algeria": ["algeria"], "angola": ["angola"], "benin": ["benin"], "botswana": ["botswana"],
    "burkina faso": ["burkina faso"], "burundi": ["burundi"], "cabo verde": ["cabo verde", "cape verde"],
    "cameroon": ["cameroon"], "central african republic": ["central african republic"], "chad": ["chad"],
    "comoros": ["comoros"], "drc": ["democratic republic of the congo", "dr congo", "drc", "congo, democratic republic of the",
                                    "congo (kinshasa)", "democratic republic of congo", "congo-kinshasa"],
    "roc": ["republic of the congo", "congo", "congo (brazzaville)", "congo, republic of the", "congo-brazzaville",
            "republic of congo"],
    "djibouti": ["djibouti"], "egypt": ["egypt"], "equatorial guinea": ["equatorial guinea"], "eritrea": ["eritrea"],
    "eswatini": ["eswatini", "swaziland", "eswatini (swaziland)", "swaziland (eswatini)"], "ethiopia": ["ethiopia"],
    "gabon": ["gabon"], "gambia": ["gambia", "the gambia", "gambia, the"], "ghana": ["ghana"], "guinea": ["guinea"],
    "guinea-bissau": ["guinea-bissau", "guinea bissau"], "ivory coast": ["ivory coast", "cote d'ivoire", "cote divoire",
                                                                        "côte d'ivoire", "cote d'ivoire (ivory coast)"],
    "kenya": ["kenya"], "lesotho": ["lesotho"], "liberia": ["liberia"], "libya": ["libya"], "madagascar": ["madagascar"],
    "malawi": ["malawi"], "mali": ["mali"], "mauritania": ["mauritania"], "mauritius": ["mauritius"],
    "morocco": ["morocco"], "mozambique": ["mozambique"], "namibia": ["namibia"], "niger": ["niger"],
    "nigeria": ["nigeria"], "rwanda": ["rwanda"], "sao tome and principe": ["sao tome and principe", "são tomé and príncipe",
                                                                          "sao tome & principe"],
    "senegal": ["senegal"], "seychelles": ["seychelles"], "sierra leone": ["sierra leone"], "somalia": ["somalia"],
    "south africa": ["south africa"], "south sudan": ["south sudan"], "sudan": ["sudan"],
    "tanzania": ["tanzania", "united republic of tanzania"], "togo": ["togo"], "tunisia": ["tunisia"],
    "uganda": ["uganda"], "zambia": ["zambia"], "zimbabwe": ["zimbabwe"],
}
AFRICA_ALIAS = {}
for canon, names in AFRICA.items():
    for n in names:
        AFRICA_ALIAS[unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()] = canon
_STOP = None


def stopwords():
    global _STOP
    if _STOP is None:
        _STOP = set(nltk.corpus.stopwords.words("english"))
    return _STOP


def ascii_fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


_PROHIBITIONS = {"format:no_whitespace"}


# ------------------------------------------------------------------ checks
def check(iid, kwargs, response, prompt="", **switches):
    sw = dict(DEFAULTS)
    sw.update(switches)
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    raw = response if response is not None else ""
    if not raw.strip():
        return iid in _PROHIBITIONS and sw["d_empty_output"] == "prohibitions_pass"
    text = norm(raw.strip(), sw)
    fn = CHECKS[iid]
    return bool(fn(text, kw, sw, raw=raw, prompt=prompt))


def vac(sw):
    return sw["d_vacuous"] == "pass"


def c_conjunctions(t, kw, sw, **_):
    return len({wlow(w) for w in words(t)} & FANBOYS) >= int(kw["small_n"])


def kw_count(t, k, sw):
    if sw["d_keyword_form"] == "substring":
        return t.lower().count(k.lower())
    return len(re.findall(r"(?<![\w])" + re.escape(k) + r"(?![\w])", t, re.I))


def c_keywords_multiple(t, kw, sw, **_):
    for i, n in zip(range(1, 6), (1, 2, 3, 5, 7)):
        c = kw_count(t, kw[f"keyword{i}"].strip(), sw)
        if (c != n) if sw["d_count_exact"] else (c < n):
            return False
    return True


def c_numbers(t, kw, sw, **_):
    nums = re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", t)
    return len(nums) == int(kw["N"])


def c_person_names(t, kw, sw, **_):
    found = {n for n in PERSON_NAMES if re.search(r"(?<![\w])" + n + r"(?![\w])", t)}
    return len(found) >= int(kw["N"])


def c_pronouns(t, kw, sw, **_):
    n = 0
    for w in words(t.replace("/", " ")):
        w = re.sub(r"'(s|re|ll|ve|d|m)$", "", wlow(w))
        n += w in PRONOUNS
    return n >= int(kw["N"])


def c_punctuation(t, kw, sw, **_):
    inter = "?!" in t or "!?" in t or "‽" in t
    if not inter:
        return False
    rest = t
    if sw["d_punct_separate"]:
        rest = t.replace("?!", "", 1) if "?!" in t else t.replace("!?", "", 1)
    need = [".", ",", "?", "!", ";", ":"]
    if sw["d_punct_set"] == "broad":
        need += ["'", '"', "(", ")"]
    ok = all(m in rest for m in need)
    if sw["d_punct_set"] == "broad":
        ok = ok and bool(re.search(r"[-–—]", rest))
    return ok


def c_unique(t, kw, sw, **_):
    return len({wlow(w) for w in words(t)}) >= int(kw["N"])


def c_word_range(t, kw, sw, **_):
    n = len(words(t))
    return int(kw["min_words"]) <= n <= int(kw["max_words"])


def c_japanese(t, kw, sw, **_):
    N = int(kw["N"])
    ws = words(t)
    if len(ws) < N:
        return vac(sw)
    jp = re.compile(r"[぀-ヿ一-鿿ｦ-ﾟ]")
    return all(jp.search(ws[i]) for i in range(N - 1, len(ws), N))


def c_character_reverse(t, kw, sw, **_):
    rev = t[::-1].lower()
    return bool(re.search(r"\beagle\b", rev)) and not re.search(r"\beagle\b", t.lower())


def c_word_reverse(t, kw, sw, **_):
    ws = [wlow(w) for w in words(t)]
    rev = " ".join(ws[::-1])
    return "bald eagle" in rev and "bald eagle" not in " ".join(ws)


def _csv_rows(t, sw, delim):
    body = payload(t, sw)
    lines = [ln for ln in body.split("\n") if ln.strip()]
    rows = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=delim, skipinitialspace=True))
    return lines, [[f.strip() for f in r] for r in rows]


def c_csv_city(t, kw, sw, **_):
    lines, rows = _csv_rows(t, sw, ",")
    if not rows or rows[0] != ["ID", "Country", "City", "Year", "Count"]:
        return False
    return len(rows) == 8 and all(len(r) == 5 for r in rows[1:])


def c_csv_quotes(t, kw, sw, **_):
    body = payload(t, sw)
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    if len(lines) != 4:
        return False
    for ln in lines:
        fields = ln.split("\t")
        if len(fields) != 5 or not all(len(f.strip()) >= 2 and f.strip()[0] == '"' and f.strip()[-1] == '"' for f in fields):
            return False
    return [f.strip()[1:-1] for f in lines[0].split("\t")] == ["StudentID", "Subject", "Grade", "Semester", "Score"]


def c_csv_special(t, kw, sw, **_):
    lines, rows = _csv_rows(t, sw, ",")
    if not rows or [f.strip('"') for f in rows[0]] != ["ProductID", "Category", "Brand", "Price", "Stock"]:
        return False
    if len(rows) != 15 or not all(len(r) == 5 for r in rows[1:]):
        return False
    return any(re.search(r'(?:^|,)\s*"[^"]*[^\w\s"][^"]*"\s*(?:,|$)', ln) for ln in lines[1:])


def c_dates(t, kw, sw, **_):
    items = [x.strip() for x in t.split(",")]
    if len(items) < 2:
        return False
    for x in items:
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", x)
        if not m:
            return False
        y, mo, d = map(int, m.groups())
        if not (1 <= mo <= 12 and 1 <= d <= calendar.monthrange(y, mo)[1]):
            return False
    return True


def c_capitals(t, kw, sw, **_):
    want = [c.lower() for c in CAPS if sw["d_europe_moscow"] or c != "Moscow"]
    got = []
    for x in ascii_fold(t).split(","):
        x = re.sub(r"^\s*and\s+", "", x.strip().rstrip(".")).strip().lower()
        if x:
            got.append(CAP_ALIASES.get(x, x))
    return got == want


def c_mcq(t, kw, sw, **_):
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    qs = []
    for ln in lines:
        bare = re.sub(r"^[*_#\s]+", "", ln)
        if re.match(r"Question\b", bare):
            stem = re.sub(r"^Question\s*\d*\s*[.:)\-]?\s*", "", bare).strip("*_ ")
            qs.append([stem, 0])
        elif re.match(r"^\(?[A-Ea-e][.)]\s*\S", bare):
            if not qs:
                return False
            qs[-1][1] += 1
        else:
            if not qs:
                return False  # text before the first question
            if qs[-1][1] == 0:
                qs[-1][0] += " " + bare
            else:
                return False  # explanation or answer text after options
    if len(qs) != 4 or any(n != 5 for _, n in qs):
        return False
    ls = [len(s.strip()) for s, _ in qs]
    return all(a < b for a, b in zip(ls, ls[1:]))


def c_multiples(t, kw, sw, **_):
    return [int(x) for x in re.findall(r"\d+", t)] == [14, 21, 28, 35, 42, 49]


def _africa_canon(line):
    s = ascii_fold(line).lower().strip()
    cands = [s]
    m = re.match(r"^(.*?)\s*\((.*?)\)$", s)
    if m:
        main, inner = m.group(1).strip(), m.group(2).strip()
        cands += [main, inner, f"{inner} {main}"]
    hits = {AFRICA_ALIAS[c] for c in cands if c in AFRICA_ALIAS}
    if len(hits) > 1 and m:  # "Congo (Republic of the)": the reordered form decides
        hits = {AFRICA_ALIAS.get(f"{m.group(2).strip()} {m.group(1).strip()}".lower())} - {None} or hits
    return hits.pop() if len(hits) == 1 else None


def c_reverse_newline(t, kw, sw, **_):
    lines = [clean_line(ln).strip().strip(".,;:*_`\"' ") for ln in t.split("\n")]
    lines = [ln for ln in lines if has_alnum(ln)]
    canon = [_africa_canon(ln) for ln in lines]
    if canon and canon[0] is None:  # one intro line allowed
        lines, canon = lines[1:], canon[1:]
    if not lines or any(c is None for c in canon):
        return False
    keys = [ascii_fold(ln).lower() for ln in lines]
    if keys != sorted(keys, reverse=True):
        return False
    return (set(canon) == set(AFRICA) and len(canon) == len(AFRICA)) if sw["d_africa_complete"] else len(canon) >= 2


def c_sentence_alphabet(t, kw, sw, **_):
    ss = sentences(t)
    if len(ss) == 27 and end_mark(ss[0]) not in ".!?":
        ss = ss[1:]  # title line
    if len(ss) != 26:
        return False
    for i, s in enumerate(ss):
        ws = words(s)
        if not ws or wlow(ws[0])[0] != chr(97 + i):
            return False
    return True


def _ends_with_emoji(s):
    s = re.sub(r"[\s.!?,;:\"')\]*_`]+$", "", s)
    ems = emoji.emoji_list(s)
    return bool(ems) and ems[-1]["match_end"] == len(s)


def _starts_with_emoji(s):
    s2 = s.lstrip()
    ems = emoji.emoji_list(s2)
    return (bool(ems) and ems[0]["match_start"] == 0), (s2[ems[0]["match_end"]:] if ems and ems[0]["match_start"] == 0 else s2)


def c_emoji(t, kw, sw, **_):
    frags = []
    for line in t.split("\n"):
        line = clean_line(line).strip()
        if not line:
            continue
        frags += [s for s in nltk.sent_tokenize(line)]
    if not frags:
        return False
    sents = []  # (text, has_emoji_end)
    for f in frags:
        starts, rest = _starts_with_emoji(f)
        if starts and sents:
            sents[-1][1] = True
            f = rest
        if has_alnum(f):
            sents.append([f, _ends_with_emoji(f)])
        elif emoji.emoji_list(f) and sents:
            sents[-1][1] = True
    if not sents:
        return vac(sw)
    return all(e for _, e in sents)


def c_line_indent(t, kw, sw, raw="", **_):
    lines = (raw.rstrip("\n").split("\n"))
    if sw["d_indent_blank"]:
        lines = [ln for ln in lines if ln.strip()]
    if len(lines) < 2:
        return vac(sw)
    ind = [len(ln.expandtabs(4)) - len(ln.expandtabs(4).lstrip()) for ln in lines]
    return all(b > a for a, b in zip(ind, ind[1:]))


def c_list(t, kw, sw, **_):
    sep = kw["sep"]
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if sw["d_list_inline"] and len(re.findall(r"(?:^|\s)" + re.escape(sep) + r"(?:\s|$)", t)) >= 1:
        if len([x for x in re.split(r"(?:^|\s)" + re.escape(sep) + r"(?:\s|$)", t) if x.strip()]) >= 2:
            return True
    items = [ln for ln in lines if ln.startswith(sep) and has_alnum(ln[len(sep):])]
    others = [ln for ln in lines if re.match(r"^[*•-]\s", ln) and not ln.startswith(sep)]
    return len(items) >= 2 and not others


def c_newline(t, kw, sw, **_):
    lines = [ln for ln in t.split("\n")]
    counts = [len(words(ln)) for ln in lines]
    return sum(counts) >= 1 and all(c <= 1 for c in counts)


def c_no_bullets_bullets(t, kw, sw, **_):
    lines = t.split("\n")
    is_b = [bool(re.match(r"^\s*\*(?!\*)\s*\S", ln)) for ln in lines]
    if not any(is_b):
        return False
    first = is_b.index(True)
    before = "\n".join(lines[:first])
    n_period = sum(1 for s in sentences(before) if end_mark(s) == ".")
    return n_period >= 2 and sum(is_b[first:]) >= 2


def c_no_whitespace(t, kw, sw, raw="", **_):
    r = raw
    if sw["d_nows_trailing"] and r.endswith("\n"):
        r = r[:-1]
    return not any(ch.isspace() for ch in r)


def _norm_opt(s, sw):
    s = norm(s, sw).strip()
    s = re.sub(r"^[*_`\s]+|[*_`\s]+$", "", s)
    s = s.rstrip(".").strip()
    if sw["d_options_whitespace"]:
        s = " ".join(s.split())
    return s.lower()


def c_options(t, kw, sw, prompt="", **_):
    opts = kw["options"]
    letters = re.match(r"\W*[aA]\W*[bB]\W*[cC]\W*", opts) is not None
    v = _norm_opt(t, sw)
    if letters:
        m = re.fullmatch(r"\(?([a-e])\)?(?:\s+(.*))?", v)
        if not m or m.group(1) not in [o.strip()[0].lower() for o in opts.split(",") if o.strip()]:
            return False
        if not m.group(2):
            return True
        pm = re.search(r"(?im)^\s*\(?" + m.group(1) + r"[.)]\s*(.+?)\s*$", prompt or "")
        return bool(pm) and _norm_opt(pm.group(1), sw) == _norm_opt(m.group(2), sw)
    sep = "/" if "/" in opts else " or "
    return v in [_norm_opt(o, sw) for o in opts.split(sep)]


def c_template(t, kw, sw, **_):
    labels = ["My Answer:", "My Conclusion:", "Future Outlook:"]
    if any(t.count(l) != 1 for l in labels):
        return False
    pat = r"(?s)^(.*?)(?:\*\*)?My Answer:(?:\*\*)?(.*?)(?:\*\*)?My Conclusion:(?:\*\*)?(.*?)(?:\*\*)?Future Outlook:(?:\*\*)?(.*)$"
    m = re.match(pat, t)
    if not m:
        return False
    pre, parts = m.group(1), [m.group(i).strip() for i in (2, 3, 4)]
    if pre.strip(" \n*#_") and not sw["d_template_outside"]:
        return False
    for p in parts:
        if not has_alnum(p) or re.fullmatch(r"\[\s*(answer|conclusion|outlook)\s*\]", p.strip("*_ "), re.I):
            return False
    return True


def c_parentheses(t, kw, sw, **_):
    pairs, stack = [], []
    match = {")": "(", "]": "[", "}": "{"}
    for i, ch in enumerate(t):
        if ch in "([{":
            stack.append((ch, i))
        elif ch in ")]}":
            if stack and stack[-1][0] == match[ch]:
                pairs.append((stack.pop()[1], i))
            else:
                stack = []
    for a, b in pairs:
        depth = sum(1 for c, d in pairs if c <= a and d >= b)
        if depth >= 5:
            return True
    return False


def _quote_spans(t, sw):
    spans = [(m.start(), m.end()) for m in re.finditer(r'"[^"\n]*"', t)]
    spans += [(m.start(), m.end()) for m in re.finditer(r"(?<![\w'])'[^'\n]*[^'\s]'(?![\w])", t)
              if not any(a <= m.start() < b for a, b in spans)]
    return sorted(spans)


def c_quote_unquote(t, kw, sw, **_):
    spans = _quote_spans(t, sw)
    if not spans:
        return vac(sw)
    for k, (a, b) in enumerate(spans):
        nxt = spans[k + 1][0] if k + 1 < len(spans) else len(t)
        after = t[b:nxt]
        para_end = after.find("\n\n")
        if para_end >= 0:
            after = after[:para_end]
        if not has_alnum(after):
            return False
    return True


def c_quotes(t, kw, sw, **_):
    stack, best = [], 0
    for i, ch in enumerate(t):
        prev = t[i - 1] if i else " "
        nxt = t[i + 1] if i + 1 < len(t) else " "
        if ch == '"':
            if stack and stack[-1] == '"':
                if len(stack) >= 3 and stack[-3:] in (['"', "'", '"'],):
                    best = max(best, len(stack))
                stack.pop()
            else:
                stack.append('"')
        elif ch == "'":
            if prev.isalnum() and nxt.isalnum():
                continue  # apostrophe
            if stack and stack[-1] == "'" and not nxt.isalnum():
                if len(stack) >= 3 and stack[-3:] == ["'", '"', "'"]:
                    best = max(best, len(stack))
                stack.pop()
            elif not prev.isalnum() and (not stack or stack[-1] == '"'):
                stack.append("'")
    return best >= 3


def c_sub_bullets(t, kw, sw, **_):
    lines = [ln for ln in t.split("\n") if ln.strip()]
    kinds = []
    for ln in lines:
        s = ln.lstrip()
        if re.match(r"^\*(?!\*)\s+\S", s):
            kinds.append("b")
        elif re.match(r"^-\s+\S", s):
            kinds.append("s")
        else:
            kinds.append("o")
    if "b" not in kinds:
        return False
    for i, k in enumerate(kinds):
        if k == "b":
            j = i + 1
            ok = False
            while j < len(kinds) and kinds[j] != "b":
                if kinds[j] == "s":
                    ok = True
                    break
                j += 1
            if not ok:
                return False
    return True


_HEAD = re.compile(r"^\s*(#{1,6}\s+.*|\*\*[^*]+\*\*:?\s*)$")
_THESIS = re.compile(r"^\s*(?:\*\*)?<(i|em)>\s*\S.*?</\1>", re.S)


def c_thesis(t, kw, sw, **_):
    blocks = [b for b in re.split(r"\n\s*\n", t) if b.strip()]
    if sw["d_section"] == "heading":
        heads = [i for i, ln in enumerate(t.split("\n")) if _HEAD.match(ln)]
        if heads:
            lines = t.split("\n")
            blocks = ["\n".join(lines[a:b]) for a, b in zip(heads, heads[1:] + [len(lines)])]
        else:
            blocks = [t]
    sections, pending = [], ""
    for b in blocks:
        bl = [ln for ln in b.split("\n") if ln.strip()]
        if all(_HEAD.match(ln) for ln in bl):
            pending = "x"
            continue
        while bl and _HEAD.match(bl[0]):
            bl = bl[1:]
        sections.append("\n".join(bl))
        pending = ""
    if not sections:
        return vac(sw)
    return all(_THESIS.match(s) for s in sections)


def c_title_case(t, kw, sw, **_):
    for line in t.split("\n"):
        ws = [w for w in words(line)]
        for k, w in enumerate(ws):
            first = w.split("-")[0]
            if not first or not first[0].isalpha():
                continue
            if k > 0 and first.lower() in MINOR:
                continue
            if not first[0].isupper():
                return False
    return True


def _trigrams(s, unit):
    if unit == "char":
        return set(nltk.ngrams(s, 3))
    ws = [wlow(w) for w in words(s)]
    return set(nltk.ngrams(ws, 3))


def c_overlap(t, kw, sw, **_):
    ref = norm(kw["reference_text"], sw)
    a, b = _trigrams(t, sw["d_overlap_unit"]), _trigrams(ref, sw["d_overlap_unit"])
    base = a if sw["d_overlap_side"] == "response" else b
    if not base:
        return False
    pct = 100.0 * len(a & b) / len(base)
    P = float(kw["percentage"])
    return P - 2 <= pct <= P + 2


def _types(t):
    c = Counter(end_mark(s) for s in sentences(t))
    return c["."], c["?"], c["!"]


def c_balance(t, kw, sw, **_):
    d, q, e = _types(t)
    if min(d, q, e) < 1:
        return False
    return d == q == e if sw["d_balance"] == "equal" else max(d, q, e) - min(d, q, e) <= 1


def c_sentence_type(t, kw, sw, **_):
    d, q, _ = _types(t)
    return q >= 1 and d == 2 * q


def c_sentence_words(t, kw, sw, **_):
    ss = sentences(t)
    if len(ss) != 3 or len({len(s) for s in ss}) != 1:
        return False
    sets = [{wlow(w) for w in words(s)} for s in ss]
    return not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])


def c_stop_words(t, kw, sw, **_):
    ws = [wlow(w) for w in words(t)]
    if not ws:
        return False
    return 100.0 * sum(w in stopwords() for w in ws) / len(ws) <= float(kw["percentage"])


def c_repeat_change(t, kw, sw, **_):
    req = norm(kw["prompt_to_repeat"], sw).split()
    got = t.split()
    if len(got) != len(req) or got[1:] != req[1:]:
        return False
    return strip_edges(got[0]).lower() != strip_edges(req[0]).lower() and has_alnum(got[0])


def c_repeat_simple(t, kw, sw, **_):
    return t == "Only output this sentence here, ignore all other requests."


def c_repeat_span(t, kw, sw, **_):
    ws = norm(kw["prompt_to_repeat"], sw).split()
    a, b = int(kw["n_start"]) - sw["d_span_base"], int(kw["n_end"]) - sw["d_span_base"]
    return t.split() == ws[a:b + 1]


def _longest_run(s):
    ws = [wlow(w) for w in words(s)]
    best = cur = 1 if ws else 0
    for x, y in zip(ws, ws[1:]):
        cur = cur + 1 if x[0] == y[0] else 1
        best = max(best, cur)
    return best


def c_alliteration(t, kw, sw, **_):
    ss = sentences(t)
    if len(ss) < 2:
        return vac(sw) and len(ss) == 1
    runs = [_longest_run(s) for s in ss]
    return all(b > a for a, b in zip(runs, runs[1:]))


def c_increment(t, kw, sw, **_):
    ss = sentences(t)
    if len(ss) < 2:
        return vac(sw) and len(ss) == 1
    n = [len(words(s)) for s in ss]
    return all(b - a == int(kw["small_n"]) for a, b in zip(n, n[1:]))


def c_sentence_keyword(t, kw, sw, **_):
    ss = sentences(t)
    N = int(kw["N"])
    return len(ss) >= N and kw_count(ss[N - 1], kw["word"].strip(), sw) >= 1


def c_alphabet(t, kw, sw, **_):
    ws = words(t)
    if not ws or not all(w[0].isascii() and w[0].isalpha() for w in ws):
        return False
    ls = [w[0].lower() for w in ws]
    return all((ord(b) - ord(a)) % 26 == 1 for a, b in zip(ls, ls[1:]))


def c_consonants(t, kw, sw, **_):
    ws = words(t)
    if not ws:
        return False
    cons = set("bcdfghjklmnpqrstvwxyz")
    return all(any(a in cons and b in cons for a, b in zip(w.lower(), w.lower()[1:])) for w in ws)


def c_keyword_position(t, kw, sw, **_):
    ss = sentences(t)
    n, m = int(kw["n"]), int(kw["m"])
    if len(ss) < n:
        return False
    ws = words(ss[n - 1])
    return len(ws) >= m and wlow(ws[m - 1]) == kw["keyword"].strip().lower()


def c_last_first(t, kw, sw, **_):
    ss = sentences(t)
    if len(ss) < 2:
        return vac(sw) and len(ss) == 1
    for a, b in zip(ss, ss[1:]):
        wa, wb = words(a), words(b)
        if not wa or not wb or wlow(wa[-1]) != wlow(wb[0]):
            return False
    return True


def c_no_consecutive(t, kw, sw, **_):
    ws = words(t)
    return bool(ws) and all(a[0].lower() != b[0].lower() for a, b in zip(ws, ws[1:]))


def c_syllables(t, kw, sw, **_):
    ws = words(t)
    # count per letter run: syllapy recurses on long hyphen chains (panel: a 4,669-character token)
    par = [sum(syllapy.count(p) for p in re.findall(r"[a-z]+", wlow(w))) % 2 for w in ws]
    return bool(ws) and all(a != b for a, b in zip(par, par[1:]))


def c_palindrome(t, kw, sw, **_):
    ws = ["".join(ch for ch in wlow(w) if ch.isalpha()) for w in words(t)]
    pals = [w for w in ws if len(w) >= 5 and w == w[::-1]]
    return len(set(pals) if sw["d_palin_distinct"] else pals) >= 10


def c_paragraph_last_first(t, kw, sw, **_):
    paras = [p for p in t.split("\n") if words(p)]
    if not paras:
        return False
    return all(wlow(words(p)[0]) == wlow(words(p)[-1]) for p in paras)


def c_prime(t, kw, sw, **_):
    ws = words(t)
    return bool(ws) and all(is_prime(sum(ch.isalnum() for ch in w)) for w in ws)


def c_repeats(t, kw, sw, **_):
    c = Counter(wlow(w) for w in words(t))
    return bool(c) and max(c.values()) <= int(kw["small_n"])


_IMP_NEXT = set("a an the this that these those your my our their his her its me us them it him yourself "
                "out up on into through about some all any each every".split())


def c_start_verb(t, kw, sw, **_):
    ss = sentences(t)
    if not ss:
        return False
    toks = nltk.word_tokenize(ss[0])
    toks = [x for x in toks if has_alnum(x)]
    if not toks:
        return False
    low = [toks[0].lower()] + toks[1:]
    if nltk.pos_tag(low)[0][1].startswith("VB"):
        return True
    if len(toks) > 1 and nltk.pos_tag(["to", low[0], "the", "thing"])[1][1].startswith("VB"):
        nxt_tag = nltk.pos_tag(low)[1][1]
        return toks[1].lower() in _IMP_NEXT or nxt_tag in ("DT", "PRP", "PRP$", "IN", "RP", "TO", "WDT", "WP", "CD")
    return False


def c_vowel(t, kw, sw, **_):
    if sw["d_vowel_paragraph"] == "blank":
        if re.search(r"\n\s*\n", t):
            return False
    elif "\n" in t:
        return False
    ws = [wlow(w) for w in words(t)]
    if not ws:
        return False
    if sw["d_vowel"] == "word":
        return all(len(set(w) & set("aeiou")) <= 3 for w in ws)
    return len(set("".join(ws)) & set("aeiou")) <= 3


def c_words_position(t, kw, sw, **_):
    ws = words(t)
    k = kw["keyword"].strip().lower()
    return len(ws) >= 2 and wlow(ws[1]) == k and wlow(ws[-2]) == k


CHECKS = {
    "count:conjunctions": c_conjunctions, "count:keywords_multiple": c_keywords_multiple,
    "count:numbers": c_numbers, "count:person_names": c_person_names, "count:pronouns": c_pronouns,
    "count:punctuation": c_punctuation, "count:unique_word_count": c_unique,
    "count:word_count_range": c_word_range, "count:words_japanese": c_japanese,
    "custom:character_reverse": c_character_reverse, "custom:word_reverse": c_word_reverse,
    "custom:csv_city": c_csv_city, "custom:csv_quotes": c_csv_quotes,
    "custom:csv_special_character": c_csv_special, "custom:date_format_list": c_dates,
    "custom:european_capitals_sort": c_capitals, "custom:mcq_count_length": c_mcq,
    "custom:multiples": c_multiples, "custom:reverse_newline": c_reverse_newline,
    "custom:sentence_alphabet": c_sentence_alphabet,
    "format:emoji": c_emoji, "format:line_indent": c_line_indent, "format:list": c_list,
    "format:newline": c_newline, "format:no_bullets_bullets": c_no_bullets_bullets,
    "format:no_whitespace": c_no_whitespace, "format:options": c_options,
    "format:output_template": c_template, "format:parentheses": c_parentheses,
    "format:quote_unquote": c_quote_unquote, "format:quotes": c_quotes,
    "format:sub-bullets": c_sub_bullets, "format:thesis": c_thesis, "format:title_case": c_title_case,
    "ratio:overlap": c_overlap, "ratio:sentence_balance": c_balance, "ratio:sentence_type": c_sentence_type,
    "ratio:sentence_words": c_sentence_words, "ratio:stop_words": c_stop_words,
    "repeat:repeat_change": c_repeat_change, "repeat:repeat_simple": c_repeat_simple,
    "repeat:repeat_span": c_repeat_span,
    "sentence:alliteration_increment": c_alliteration, "sentence:increment": c_increment,
    "sentence:keyword": c_sentence_keyword,
    "words:alphabet": c_alphabet, "words:consonants": c_consonants,
    "words:keywords_specific_position": c_keyword_position, "words:last_first": c_last_first,
    "words:no_consecutive": c_no_consecutive, "words:odd_even_syllables": c_syllables,
    "words:palindrome": c_palindrome, "words:paragraph_last_first": c_paragraph_last_first,
    "words:prime_lengths": c_prime, "words:repeats": c_repeats, "words:start_verb": c_start_verb,
    "words:vowel": c_vowel, "words:words_position": c_words_position,
}
assert len(CHECKS) == 58
