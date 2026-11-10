"""Replacement grader: an implementation of audit/CONTRACT.md (version 2).

check(iid, kwargs, prompt, response, sw=None) -> bool
    sw maps a decision id to a reading letter, for example {"D-vacuous": "B"}; every entry not
    given uses reading A, the contract's proposed reading.

Approximations (the contract asks for a judgment code cannot make exactly) are marked APPROX:
whether a word functions as a conjunction, pronoun or verb, syllable counts (syllapy, no
pronouncing dictionary is available offline), whether a palindrome is a real word, and facts
in the custom checks. The blinded review, not this module, decides those cases.
"""
import csv
import datetime
import io
import os
import re
import string
import unicodedata
from functools import lru_cache

os.environ.setdefault("NLTK_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "case", "deps", "nltk_data"))

import emoji  # noqa: E402
import nltk  # noqa: E402
import syllapy  # noqa: E402

# ----------------------------------------------------------------------------- helpers


def R(sw, d):
    return (sw or {}).get(d, "A")


HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
LIST_MARKER = re.compile(r"^\s*(?:[-*+•>]+|\d+[.)]|[A-Za-z][.)])\s+")
APOS = {"’": "'", "‘": "'", "ʼ": "'"}


def norm_apos(s):
    for a, b in APOS.items():
        s = s.replace(a, b)
    return s


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def is_wc(ch):
    return unicodedata.category(ch)[0] in "LN"


def strip_token(tok):
    i, j = 0, len(tok)
    while i < j and not is_wc(tok[i]):
        i += 1
    while j > i and not is_wc(tok[j - 1]):
        j -= 1
    return tok[i:j]


def has_letter(w):
    return any(c.isalpha() for c in w)


def is_number(w):
    return bool(w) and not has_letter(w) and any(c.isdigit() for c in w)


def words(text, sw=None):
    """D-word. A: whitespace tokens with surrounding punctuation removed, letter or digit required."""
    r = R(sw, "D-word")
    text = norm_apos(HTML_TAG.sub(" ", text))
    toks = text.split()
    if r == "C":
        return [strip_token(t) or t for t in toks]
    out = []
    for t in toks:
        s = strip_token(t)
        if not s:
            continue
        if r == "B":
            for part in re.split(r"[-/‐-―]", s):
                part = strip_token(part)
                if part:
                    out.append(part)
        else:
            out.append(s)
    return out


def first_letter(w):
    """First character if it is a letter (accents removed, lower case), else None."""
    if not w:
        return None
    c = strip_accents(w[0]).lower()
    return c if c.isalpha() else None


def is_heading_or_label(line):
    l = line.strip()
    if not l:
        return True
    if l.startswith("#"):
        return True
    if re.fullmatch(r"(\*\*|__)[^*_]+(\*\*|__):?", l):
        return True
    if l.endswith(":") and not re.search(r"[.!?]\s", l):
        return True
    if re.fullmatch(r"[\s\-=*_|:~`#>]+", l):
        return True
    if l.startswith("|") and l.endswith("|"):
        return True
    return False


def sentences(text, sw=None, keep_all=False):
    """D-sentence. A: punctuation and line breaks end sentences; headings and label lines are not sentences.

    keep_all keeps segments without words (an emoji after the last period), for format:emoji."""
    r = R(sw, "D-sentence")
    text = norm_apos(HTML_TAG.sub("", text))
    keep = (lambda x: x.strip()) if keep_all else words
    if r == "B":
        return [s for s in nltk.sent_tokenize(text) if keep(s)]
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        if r == "A" and is_heading_or_label(line):
            continue
        l = LIST_MARKER.sub("", line).strip()
        for s in nltk.sent_tokenize(l):
            if keep(s):
                out.append(s)
    return out


def paragraphs(text, sw=None, lines_default=False):
    r = R(sw, "D-paragraph")
    if r == "C" or (r == "A" and lines_default):
        return [l for l in text.split("\n") if l.strip()]
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


TRAIL_CLOSERS = "\"'”’)]}*_`>"


def sentence_type(s):
    t = s.rstrip()
    while t and (t[-1] in TRAIL_CLOSERS or t[-1].isspace() or emoji.is_emoji(t[-1]) or t[-1] in "️‍"):
        t = t[:-1]
    if not t:
        return None
    if t[-1] == "?":
        return "q"
    if t[-1] == "!":
        return "e"
    if t[-1] in ".…":
        return "d"
    return None


def kw_count(text, kw, sw=None):
    r = R(sw, "D-match")
    text = norm_apos(text)
    if r == "B":
        return text.lower().count(kw.lower())
    if r == "C":
        pat = r"(?<![\w\-])" + re.escape(kw) + r"(?:s|es|ed|d|ing)?(?![\w\-])"
    else:
        pat = r"(?<![\w\-])" + re.escape(kw) + r"(?![\w\-])"
    return len(re.findall(pat, text, flags=re.IGNORECASE))


def kw_in(text, kw, sw=None):
    return kw_count(text, kw, sw) > 0


@lru_cache(maxsize=1)
def stopword_set():
    return frozenset(nltk.corpus.stopwords.words("english"))


EMOJI_EXTRA = "️‍⃣"


def ends_with_emoji(t):
    t = t.rstrip()
    while t and t[-1] in EMOJI_EXTRA:
        t = t[:-1]
    if t and unicodedata.category(t[-1]) == "Sk" and "\U0001F3FB" <= t[-1] <= "\U0001F3FF":
        t = t[:-1]
    return bool(t) and emoji.is_emoji(t[-1])


def leading_emoji(s):
    i = 0
    while i < len(s) and (emoji.is_emoji(s[i]) or s[i] in EMOJI_EXTRA or s[i].isspace()
                          or "\U0001F3FB" <= s[i] <= "\U0001F3FF"):
        i += 1
    return s[:i], s[i:]


# ----------------------------------------------------------------------------- checks

FANBOYS = ("for", "and", "nor", "but", "or", "yet", "so")
SUBJECTS = {"i", "you", "he", "she", "it", "we", "they", "the", "this", "that", "these", "those", "there", "his",
            "her", "its", "their", "our", "my", "a", "an", "no", "nothing", "everyone", "many", "some", "one"}


def c_conjunctions(t, kw, sw):  # APPROX for reading A
    n = int(kw["small_n"])
    toks = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[,;:.!?()\"]", norm_apos(t))
    low = [x.lower() for x in toks]
    found = set()
    for i, w in enumerate(low):
        if w not in FANBOYS:
            continue
        if R(sw, "D-conj") == "B":
            found.add(w)
            continue
        prev = low[i - 1] if i else "."
        nxt = low[i + 1] if i + 1 < len(low) else "."
        if w in ("and", "or", "nor"):
            found.add(w)
        elif w == "but":
            if prev not in ("all", "nothing", "anything", "everything", "none", "everyone", "nobody", "anyone", "last"):
                found.add(w)
        elif w == "so":
            if nxt in ("that", "far", "much", "many", "called", "on", "forth", "long", "few", "little"):
                continue
            if prev in (",", ";", ".", "!", "?", "(", "and", "\"") or i == 0 or nxt in SUBJECTS:
                found.add(w)
        elif w == "for":
            if prev in (",", ";") and nxt in SUBJECTS:
                found.add(w)
        elif w == "yet":
            if prev in ("not", "as", "have", "has", "had") or nxt in ("another", "again", "more"):
                continue
            if prev in (",", ";", "and", "but", ".", "!", "?", "(") or i == 0 or nxt in SUBJECTS:
                found.add(w)
    return len(found) >= n


def c_keywords_multiple(t, kw, sw):
    for k, need in zip([kw[f"keyword{i}"] for i in range(1, 6)], [1, 2, 3, 5, 7]):
        c = kw_count(t, k.strip(), sw)
        if R(sw, "D-keyword-count") == "B":
            if c < need:
                return False
        elif c != need:
            return False
    return True


NUMWORDS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
            "seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand "
            "million billion").split()


def count_numbers(t, sw):
    r = R(sw, "D-number")
    n = 0
    for m in re.finditer(r"\d+(?:[.,]\d+)*", t):
        s = m.start()
        if s > 0 and t[s - 1].isalpha():
            continue
        if r == "B":
            line_start = t.rfind("\n", 0, s) + 1
            if t[line_start:s].strip() == "" and re.match(r"\d+[.)]\s", t[s:]):
                continue
        n += 1
    if r == "C":
        n += len(re.findall(r"(?<![\w-])(?:" + "|".join(NUMWORDS) + r")(?:-(?:" + "|".join(NUMWORDS) + r"))?(?![\w-])",
                            t, flags=re.IGNORECASE))
    return n


def c_numbers(t, kw, sw):
    return count_numbers(t, sw) == int(kw["N"])


NAMES = ("Emma, Liam, Sophia, Jackson, Olivia, Noah, Ava, Lucas, Isabella, Mason, Mia, Ethan, Charlotte, Alexander, "
         "Amelia, Benjamin, Harper, Leo, Zoe, Daniel, Chloe, Samuel, Lily, Matthew, Grace, Owen, Abigail, Gabriel, Ella, "
         "Jacob, Scarlett, Nathan, Victoria, Elijah, Layla, Nicholas, Audrey, David, Hannah, Christopher, Penelope, "
         "Thomas, Nora, Andrew, Aria, Joseph, Claire, Ryan, Stella, Jonathan").split(", ")


def c_person_names(t, kw, sw):
    flags = re.IGNORECASE if R(sw, "D-names-case") == "B" else 0
    found = {n for n in NAMES if re.search(r"(?<![\w\-])" + n + r"(?![\w\-])", norm_apos(t), flags)}
    return len(found) >= int(kw["N"])


PERSONAL = set("i me you he him she her it we us they them".split())
POSS_DET = set("my your his her its our their".split())
POSS_IND = set("mine yours hers ours theirs".split())
REFLEX = set("myself yourself himself herself itself ourselves yourselves themselves oneself".split())
DEMON = set("this that these those".split())
WH = set("who whom whose which what whoever whomever whatever whichever".split())
INDEF = set("anybody anyone anything everybody everyone everything nobody nothing somebody someone something none "
            "each either neither both all some any another many few several most".split())


def count_pronouns(t, sw):  # APPROX for reading A
    r = R(sw, "D-pronoun")
    toks = nltk.word_tokenize(norm_apos(t).replace("/", " "))
    low = [x.lower() for x in toks]
    if r in ("B", "C"):
        base = PERSONAL | POSS_IND | REFLEX | (set() if r == "C" else POSS_DET)
        if r == "C":
            return sum(1 for w in low if w in base and w not in ("my", "your", "its", "our", "their"))
        return sum(1 for w in low if w in base)
    tags = [tg for _, tg in nltk.pos_tag(toks)] if toks else []
    n = 0
    for i, w in enumerate(low):
        nxt_tag = tags[i + 1] if i + 1 < len(tags) else "."
        standalone = not (nxt_tag.startswith("NN") or nxt_tag.startswith("JJ") or nxt_tag in ("CD", "DT", "PRP$"))
        if w in PERSONAL or w in POSS_DET or w in POSS_IND or w in REFLEX:
            n += 1
        elif w in DEMON:
            if w == "that" and tags[i] == "IN":
                continue
            if tags[i] == "WDT" or standalone:
                n += 1
        elif w in WH:
            if w in ("which", "what", "whose") and not standalone:
                continue
            n += 1
        elif w in INDEF:
            if standalone and not (w in ("all", "both", "each") and nxt_tag in ("DT", "PRP$")):
                n += 1
    return n


def c_pronouns(t, kw, sw):
    return count_pronouns(t, sw) >= int(kw["N"])


def c_punctuation(t, kw, sw):
    t = t.replace("‘", "'").replace("’", "'")
    has_ib = "?!" in t or "!?" in t or "‽" in t
    if not has_ib:
        return False
    rest = t
    for ib in ("?!", "!?"):
        if ib in rest:
            rest = rest.replace(ib, "", 1)
            break
    core = [".", ",", "?", "!", ";", ":", "'", "-", "(", ")"]
    ok = all(c in rest for c in core) and ('"' in rest or "“" in rest or "”" in rest)
    if R(sw, "D-punct-set") == "B":
        return ok
    dash = "—" in rest or "–" in rest or "--" in rest or " - " in rest
    ell = "..." in rest or "…" in rest
    return ok and dash and ell and all(c in rest for c in "[]{}")


def c_unique(t, kw, sw):
    ws = words(t, sw)
    r = R(sw, "D-unique")
    if r == "B":
        n = len(set(ws))
    elif r == "C":
        from collections import Counter
        cnt = Counter(w.lower() for w in ws)
        n = sum(1 for v in cnt.values() if v == 1)
    else:
        n = len({w.lower() for w in ws})
    return n >= int(kw["N"])


def c_word_range(t, kw, sw):
    n = len(words(t, sw))
    lo, hi = int(kw["min_words"]), int(kw["max_words"])
    if R(sw, "D-between") == "B":
        return lo < n < hi
    return lo <= n <= hi


JP = re.compile(r"[぀-ヿㇰ-ㇿ㐀-䶿一-鿿ｦ-ﾟ々ー]")


def c_japanese(t, kw, sw):
    N = int(kw["N"])
    ws = words(t, sw)
    if len(ws) < N:
        return R(sw, "D-vacuous") == "B"
    for i in range(N - 1, len(ws), N):
        w = ws[i]
        if R(sw, "D-japanese") == "C" and re.fullmatch(r"[A-Za-z]+", w):
            continue
        if not JP.search(w) or re.search(r"[A-Za-z]", w):
            return False
    return True


NORMAL_BIGRAMS = ["the national", "national symbol", "symbol of", "of the", "is the", "bald eagle", "the bald",
                  "american bald", "the united", "united states", "national animal", "national bird", "is a", "is an",
                  "the us", "us is", "symbol is", "animal is", "bird is"]


def _order_score(text):
    low = " ".join(re.findall(r"[a-z']+", text.lower()))
    return sum(low.count(b) for b in NORMAL_BIGRAMS)


def c_char_reverse(t, kw, sw):
    s = t.strip()
    rev = " ".join(w[::-1] for w in s.split()) if R(sw, "D-char-reverse") == "B" else s[::-1]
    if _order_score(s) > 0 or re.search(r"\beagle\b", s, re.I):
        return False  # normal-order text in the response
    flipped = " ".join(reversed(rev.split()))
    if _order_score(rev) <= _order_score(flipped):
        return False
    if R(sw, "D-custom-facts") == "B":
        return True
    return bool(re.search(r"\beagle\b", rev, re.I))


def c_word_reverse(t, kw, sw):
    ws = [w.lower() for w in words(t, sw)]
    if not ws:
        return False
    rev = " ".join(reversed(ws))
    fwd = " ".join(ws)
    inner_ends = re.findall(r"[.!?](?=\s+\S)", t.strip())
    if inner_ends:
        return False
    if R(sw, "D-custom-facts") == "B":
        return "eagle bald" not in fwd and "the" in ws
    return "bald eagle" in rev and "bald eagle" not in fwd


def _csv_block(t, sw):
    """Return the CSV lines (list of str) or None if text outside the CSV is not allowed."""
    lines = t.strip("\n").split("\n")
    fence = [i for i, l in enumerate(lines) if l.strip().startswith("```")]
    if R(sw, "D-csv") == "C":
        if fence:
            return None
        return [l for l in lines]
    if len(fence) >= 2:
        lines = lines[fence[0] + 1:fence[1]]
    return lines


def _parse_fields(line, delim):
    """Split one CSV line into (text, quoted) pairs."""
    out, i, n = [], 0, len(line)
    while True:
        while i < n and line[i] == " " and delim != " ":
            i += 1
        if i < n and line[i] == '"':
            j, buf = i + 1, []
            while j < n:
                if line[j] == '"':
                    if j + 1 < n and line[j + 1] == '"':
                        buf.append('"')
                        j += 2
                        continue
                    break
                buf.append(line[j])
                j += 1
            k = j + 1
            while k < n and line[k] != delim:
                k += 1
            out.append(("".join(buf), True, line[i:k].rstrip()))
            i = k
        else:
            k = line.find(delim, i)
            k = n if k < 0 else k
            out.append((line[i:k].strip(), False, line[i:k].strip()))
            i = k
        if i >= n:
            break
        i += 1
        if i == n:
            out.append(("", False, ""))
            break
    return out


def _csv_rows(t, sw, header, delim):
    lines = _csv_block(t, sw)
    if lines is None:
        return None
    hdr_re = re.compile(r"^\s*" + (r"\s*" + re.escape(delim) + r"\s*").join(r'"?' + re.escape(h) + r'"?' for h in header) + r"\s*$")
    idx = next((i for i, l in enumerate(lines) if hdr_re.match(l)), None)
    if idx is None:
        return None
    if R(sw, "D-csv") == "C" and any(l.strip() for l in lines[:idx]):
        return None
    rows, end = [], len(lines)
    for l in lines[idx + 1:]:
        if not l.strip():
            break
        rows.append(l)
    tail = lines[idx + 1 + len(rows):]
    if R(sw, "D-csv") == "C" and any(l.strip() for l in tail):
        return None
    return lines[idx], rows


def _want_rows(n, sw):
    return n - 1 if R(sw, "D-csv") == "B" else n


def c_csv_city(t, kw, sw):
    got = _csv_rows(t, sw, ["ID", "Country", "City", "Year", "Count"], ",")
    if not got:
        return False
    _, rows = got
    return len(rows) == _want_rows(7, sw) and all(len(_parse_fields(r, ",")) == 5 for r in rows)


def c_csv_quotes(t, kw, sw):
    got = _csv_rows(t, sw, ["StudentID", "Subject", "Grade", "Semester", "Score"], "\t")
    if not got:
        return False
    hdr, rows = got
    if len(rows) != _want_rows(3, sw):
        return False
    check = rows if R(sw, "D-csv") == "D" else [hdr] + rows
    for r in [hdr] + rows:
        if len(_parse_fields(r, "\t")) != 5:
            return False
    return all(q for r in check for _, q, _ in _parse_fields(r, "\t"))


def _special(s):
    s2 = re.sub(r"(?<=\d)[.,](?=\d)", "", s)
    return any(not (c.isalnum() or c.isspace()) for c in s2)


def c_csv_special(t, kw, sw):
    got = _csv_rows(t, sw, ["ProductID", "Category", "Brand", "Price", "Stock"], ",")
    if not got:
        return False
    _, rows = got
    if len(rows) != _want_rows(14, sw):
        return False
    fields = []
    for r in rows:
        f = _parse_fields(r, ",")
        if len(f) != 5:
            return False
        fields.extend(f)
    spec = [(txt, q) for txt, q, _ in fields if _special(txt)]
    quoted_spec = [x for x in spec if x[1]]
    if R(sw, "D-csv") == "E":
        return len(quoted_spec) >= 1
    return len(spec) == 1 and len(quoted_spec) == 1


def c_dates(t, kw, sw):
    s = t.strip()
    if R(sw, "D-custom-extra-text") == "B":
        m = re.search(r"\d{4}-\d{2}-\d{2}(?:\s*,\s*\d{4}-\d{2}-\d{2})*", s)
        s = m.group(0) if m else s
    items = [x.strip() for x in s.split(",")]
    if len(items) < 2:
        return False
    for it in items:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", it):
            return False
        try:
            d = datetime.date(int(it[:4]), int(it[5:7]), int(it[8:]))
        except ValueError:
            return False
        if R(sw, "D-custom-facts") == "C" and not (1793 <= d.year <= 1815):
            return False
    return True


CAPS28 = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius", "Minsk",
          "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg", "Paris",
          "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
CAP_ALIASES = {"kiev": "kyiv", "luxembourg city": "luxembourg", "berne": "bern", "reykjavik": "reykjavik"}


def c_capitals(t, kw, sw):
    s = strip_accents(t).strip()
    if R(sw, "D-custom-extra-text") == "B" and ":" in s:
        s = s.split(":", 1)[1]
    s = s.strip().rstrip(".")
    items = [re.sub(r"\s+", " ", x.strip().strip("*").strip()) for x in s.split(",")]
    if len(items) < 2 or any(not x for x in items):
        return False
    if R(sw, "D-custom-facts") == "B":
        return all(len(x.split()) <= 3 and x[:1].isupper() for x in items)
    got = [CAP_ALIASES.get(x.lower(), x.lower()) for x in items]
    return got == [c.lower() for c in CAPS28]


def c_mcq(t, kw, sw):
    lines = [re.sub(r"[*_#]", "", l).strip() for l in t.strip().split("\n")]
    nonempty = [l for l in lines if l]
    if not nonempty or not nonempty[0].startswith("Question"):
        return False
    blocks, cur = [], None
    for l in lines:
        if l.startswith("Question"):
            cur = {"stem": re.sub(r"^Question\s*\d*\s*[:.)\-]?\s*", "", l), "opts": 0, "extra": 0, "in_opts": False}
            blocks.append(cur)
        elif cur is None or not l:
            continue
        elif re.match(r"^\(?[A-Ea-e][\).:]\s*\S", l):
            cur["opts"] += 1
            cur["in_opts"] = True
        elif not cur["in_opts"]:
            cur["stem"] += " " + l
        elif re.match(r"^(explanation|because|reason)", l, re.I) or "because" in l.lower():
            cur["extra"] += 1
    if len(blocks) != 4 or any(b["opts"] != 5 or b["extra"] for b in blocks):
        return False
    if R(sw, "D-mcq") == "B":
        lens = [len(b["stem"].split()) for b in blocks]
    else:
        lens = [len(b["stem"].strip()) for b in blocks]
    return all(a < b for a, b in zip(lens, lens[1:]))


MULT = [14, 21, 28, 35, 42, 49]


def c_multiples(t, kw, sw):
    nums = [int(x) for x in re.findall(r"\d+", t)]
    r = R(sw, "D-custom-extra-text")
    if r == "C":
        return re.fullmatch(r"[\s,;.\-\n]*(?:\d+[\s,;.\-\n]*)+", t) is not None and nums == MULT
    if r == "B":
        return nums[-6:] == MULT and (len(nums) == 6 or t.find(str(MULT[0])) > t.find(":"))
    return nums == MULT


AFRICA_CANON = {
    "algeria": "algeria", "angola": "angola", "benin": "benin", "botswana": "botswana", "burkina faso": "burkina faso",
    "burundi": "burundi", "cape verde": "cabo verde", "cabo verde": "cabo verde", "cameroon": "cameroon",
    "central african republic": "central african republic", "chad": "chad", "comoros": "comoros",
    "republic of the congo": "congo", "congo": "congo", "congo-brazzaville": "congo", "congo, republic of the": "congo",
    "congo (brazzaville)": "congo", "republic of congo": "congo",
    "democratic republic of the congo": "drc", "dr congo": "drc", "drc": "drc", "congo-kinshasa": "drc",
    "congo, democratic republic of the": "drc", "congo (kinshasa)": "drc", "democratic republic of congo": "drc",
    "ivory coast": "civ", "cote d'ivoire": "civ", "cote divoire": "civ", "djibouti": "djibouti", "egypt": "egypt",
    "equatorial guinea": "equatorial guinea", "eritrea": "eritrea", "eswatini": "eswatini", "swaziland": "eswatini",
    "eswatini (swaziland)": "eswatini", "ethiopia": "ethiopia", "gabon": "gabon", "gambia": "gambia",
    "the gambia": "gambia", "ghana": "ghana", "guinea": "guinea", "guinea-bissau": "guinea-bissau", "kenya": "kenya",
    "lesotho": "lesotho", "liberia": "liberia", "libya": "libya", "madagascar": "madagascar", "malawi": "malawi",
    "mali": "mali", "mauritania": "mauritania", "mauritius": "mauritius", "morocco": "morocco",
    "mozambique": "mozambique", "namibia": "namibia", "niger": "niger", "nigeria": "nigeria", "rwanda": "rwanda",
    "sao tome and principe": "stp", "senegal": "senegal", "seychelles": "seychelles", "sierra leone": "sierra leone",
    "somalia": "somalia", "south africa": "south africa", "south sudan": "south sudan", "sudan": "sudan",
    "tanzania": "tanzania", "united republic of tanzania": "tanzania", "togo": "togo", "tunisia": "tunisia",
    "uganda": "uganda", "zambia": "zambia", "zimbabwe": "zimbabwe", "western sahara": "EXTRA", "somaliland": "EXTRA",
    "congo (republic of the)": "congo", "congo (republic)": "congo", "republic of the congo (congo-brazzaville)": "congo",
    "congo (democratic republic of the)": "drc", "congo, the democratic republic of the": "drc",
    "democratic republic of the congo (drc)": "drc", "democratic republic of congo (drc)": "drc",
    "cape verde (cabo verde)": "cabo verde", "cabo verde (cape verde)": "cabo verde",
    "cote d'ivoire (ivory coast)": "civ", "ivory coast (cote d'ivoire)": "civ", "swaziland (eswatini)": "eswatini",
    "gambia, the": "gambia", "sao tome & principe": "stp", "tanzania, united republic of": "tanzania",
}
AFRICA_ALL = {v for v in AFRICA_CANON.values() if v != "EXTRA"}


def c_reverse_newline(t, kw, sw):
    lines = [l for l in t.split("\n") if l.strip()]
    names = []
    for l in lines:
        l2 = LIST_MARKER.sub("", l).strip().strip("*_").strip().rstrip(".,;")
        names.append(l2)
    keys = [strip_accents(n).lower().replace("’", "'") for n in names]
    if R(sw, "D-custom-extra-text") == "B":
        while keys and keys[0] not in AFRICA_CANON:
            keys.pop(0)
            names.pop(0)
        while keys and keys[-1] not in AFRICA_CANON:
            keys.pop()
            names.pop()
    if len(keys) < 2:
        return False
    if any(len(re.split(r",\s+(?!republic|democratic)|\s+and\s+(?!principe)", k)) > 1 and k not in AFRICA_CANON for k in keys):
        return False
    sort_keys = [re.sub(r"^the\s+", "", k) for k in keys]
    if sort_keys != sorted(sort_keys, reverse=True):
        return False
    if R(sw, "D-custom-facts") == "B":
        return True
    canon = [AFRICA_CANON.get(k) for k in keys]
    if any(c is None for c in canon):
        return False
    real = [c for c in canon if c != "EXTRA"]
    return len(real) == len(set(real)) and set(real) == AFRICA_ALL


def c_sentence_alphabet(t, kw, sw):
    ss = sentences(t, sw)
    if len(ss) != 26:
        return False
    for i, s in enumerate(ss):
        ws = words(s, sw)
        if not ws or first_letter(ws[0]) != chr(97 + i):
            return False
    return True


def c_emoji(t, kw, sw):
    ss = sentences(t, sw, keep_all=True)
    if not ss:
        return R(sw, "D-vacuous") == "B"
    # an emoji right after a sentence's punctuation is split into the next sentence: move it back
    fixed = []
    for s in ss:
        lead, rest = leading_emoji(s)
        if lead.strip() and fixed:
            fixed[-1] = fixed[-1] + " " + lead.strip()
            s = rest
        if s.strip():
            fixed.append(s)
        elif lead.strip() and not fixed:
            fixed.append(lead)
    fixed = [s for s in fixed if words(s, sw)]
    if not fixed:
        return R(sw, "D-vacuous") == "B"
    for s in fixed:
        s2 = s.rstrip()
        while s2 and s2[-1] in TRAIL_CLOSERS:
            s2 = s2[:-1].rstrip()
        if ends_with_emoji(s2):
            continue
        if R(sw, "D-emoji-position") == "A":
            s3 = s2.rstrip(".!?…").rstrip()
            while s3 and s3[-1] in TRAIL_CLOSERS:
                s3 = s3[:-1].rstrip()
            if s3 != s2 and ends_with_emoji(s3):
                continue
        return False
    return True


def c_line_indent(t, kw, sw):
    lines = t.split("\n")
    if R(sw, "D-indent") != "C":
        lines = [l for l in lines if l.strip()]
    else:
        while lines and not lines[-1].strip():
            lines.pop()
    if len(lines) < 2:
        return R(sw, "D-vacuous") == "B" and len(lines) == 1
    ind = [len(l.expandtabs(4)) - len(l.expandtabs(4).lstrip()) if l.strip() else -1 for l in lines]
    if any(i < 0 for i in ind):
        return False
    if any(b <= a for a, b in zip(ind, ind[1:])):
        return False
    if R(sw, "D-indent") == "B":
        steps = {b - a for a, b in zip(ind, ind[1:])}
        return len(steps) == 1
    return True


def c_list(t, kw, sw):
    sep = kw["sep"]
    r = R(sw, "D-list")
    lines = [l for l in t.split("\n") if l.strip()]
    starts = [l for l in lines if l.lstrip().startswith(sep)]
    other_bullet = [l for l in lines if re.match(r"^\s*[*•]\s", l) or
                    (sep != "-" and re.match(r"^\s*-\s", l))]
    if other_bullet:
        return False
    prefix_ok = len(starts) >= 2
    inline_ok = False
    if sep != "-":
        parts = [p for p in re.split(re.escape(sep), t)]
        inner = parts[1:-1] if len(parts) > 2 else []
        # inline form: at least two separators with text between them (a lone separator in prose is not a list)
        inline_ok = t.count(sep) >= 2 and len([p for p in inner if p.strip()]) >= 1 and \
            len([p for p in parts if p.strip()]) >= 3
    if r == "B":
        ok = prefix_ok
    elif r == "C":
        ok = inline_ok and not prefix_ok
    else:
        ok = prefix_ok or inline_ok
    if ok and r == "D":
        non_items = [l for l in lines if not l.lstrip().startswith(sep) and sep not in l]
        ok = not non_items
    return ok


def c_newline(t, kw, sw):
    any_word = False
    for l in t.split("\n"):
        n = len(words(l, sw))
        if n > 1:
            return False
        any_word = any_word or n == 1
    return any_word or R(sw, "D-vacuous") == "B"


def c_no_bullets_bullets(t, kw, sw):
    lines = t.split("\n")
    first = next((i for i, l in enumerate(lines) if re.match(r"^\s*\*\s+\S", l)), None)
    if first is None:
        return False
    before = "\n".join(lines[:first])
    n_period = sum(1 for s in sentences(before, sw) if sentence_type(s) == "d" and s.rstrip().rstrip(TRAIL_CLOSERS).endswith("."))
    bullets = sum(1 for l in lines[first:] if re.match(r"^\s*\*\s+\S", l))
    return n_period >= 2 and bullets >= 2


def c_no_whitespace(t, kw, sw):
    s = t.rstrip() if R(sw, "D-trailing-ws") == "B" else t
    if not s:
        return R(sw, "D-vacuous") == "B"
    return not any(c.isspace() for c in s)


def _options_list(kw):
    o = kw["options"]
    if "/" in o:
        return [x.strip() for x in o.split("/")], False
    if " or " in o:
        return [x.strip() for x in o.split(" or ")], False
    return [x.strip() for x in o.split(",")], True


def _opt_norm(s):
    s = norm_apos(s).strip()
    s = re.sub(r"^[*_`\s]+|[*_`\s]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    s = s.rstrip(".").strip()
    return s.lower()


def _mc_texts(prompt):
    out = {}
    for m in re.finditer(r"(?:^|\s)([A-Da-d])[.)]\s+(.+?)(?=\s{2,}[A-Da-d][.)]\s|\s*$)", prompt):
        out[m.group(1).lower()] = _opt_norm(m.group(2))
    return out


def c_options(t, kw, sw, prompt=""):
    opts, mc = _options_list(kw)
    v = _opt_norm(t)
    r = R(sw, "D-options")
    normed = [_opt_norm(o) for o in opts]
    if v in normed:
        return True
    if mc:
        letters = [o[0].lower() for o in opts]
        if r == "C" and v in letters:
            return True
        if r == "D":
            return False
        texts = _mc_texts(prompt)
        for L in letters:
            if v.startswith(L + ")") and texts.get(L) and _opt_norm(v[2:]) == texts[L]:
                return True
    if r == "B":
        hits = [o for o in normed if re.match(re.escape(o) + r"(?![\w'])", v)]
        if len(hits) >= 1:
            longest = max(hits, key=len)
            return all(o == longest or longest.startswith(o) for o in hits)
    return False


LABELS = ["My Answer:", "My Conclusion:", "Future Outlook:"]
PLACEHOLDERS = ["[answer]", "[conclusion]", "[outlook]"]


def c_template(t, kw, sw):
    r = R(sw, "D-template")
    s = t if r == "B" else re.sub(r"(\*\*|__|\*|_)", "", t)
    pos = []
    for lab in LABELS:
        if s.count(lab) != 1:
            return False
        pos.append(s.index(lab))
    if pos != sorted(pos):
        return False
    if r != "C" and s[:pos[0]].strip():
        return False
    ends = pos[1:] + [len(s)]
    for lab, p, e, ph in zip(LABELS, pos, ends, PLACEHOLDERS):
        content = s[p + len(lab):e].strip()
        if not content or content.lower() == ph or content.lower().startswith(ph):
            return False
    return True


def c_parentheses(t, kw, sw):
    r = R(sw, "D-paren")
    pairs = {")": "(", "]": "[", "}": "{"}
    opens = "([{" if r != "B" else "("
    closes = ")]}" if r != "B" else ")"
    if r == "C":
        depth = best = 0
        for ch in t:
            if ch in opens:
                depth += 1
                best = max(best, depth)
            elif ch in closes and depth:
                depth -= 1
        return best >= 5
    stack, matched = [], []
    for i, ch in enumerate(t):
        if ch in opens:
            stack.append((ch, i))
        elif ch in closes:
            if stack and stack[-1][0] == pairs[ch]:
                o = stack.pop()
                matched.append((o[1], i))
            else:
                stack = []
    for (s, e) in matched:
        d = sum(1 for (s2, e2) in matched if s2 <= s and e2 >= e)
        if d >= 5:
            return True
    return False


def _quoted_phrases(t):
    spans = []
    for m in re.finditer(r'«[^»]+»|„[^“”]+[“”]|"[^"\n]+"|“[^”]+”|‘[^’]+’(?![a-z])|(?<![A-Za-z])\'[^\'\n]+\'(?![A-Za-z])', t):
        if words(m.group(0)[1:-1]):
            spans.append((m.start(), m.end()))
    return spans


def c_quote_unquote(t, kw, sw):
    spans = _quoted_phrases(norm_apos(t) if False else t)
    if not spans:
        return R(sw, "D-vacuous") == "B"
    for k, (s, e) in enumerate(spans):
        nxt = spans[k + 1][0] if k + 1 < len(spans) else len(t)
        between = t[e:nxt]
        if not words(between, sw):
            return False
    return True


def c_quotes(t, kw, sw):
    stack, matched = [], []
    for i, ch in enumerate(t):
        if ch in "\"“”":
            kind = "d"
        elif ch in "'‘’":
            prev = t[i - 1] if i else " "
            nxt = t[i + 1] if i + 1 < len(t) else " "
            if prev.isalnum() and nxt.isalnum():
                continue
            if ch in "'’" and prev.isalpha() and prev.lower() == "s" and not (stack and stack[-1][0] == "s"):
                continue
            kind = "s"
        else:
            continue
        can_open = ch not in "”’"
        can_close = ch not in "“‘"
        if stack and stack[-1][0] == kind and can_close:
            o = stack.pop()
            matched.append((o[1], i, len(stack) + 1))
        elif can_open:
            stack.append((kind, i))
    for (s, e, d) in matched:
        if d >= 3:
            enclosing = [(s2, e2) for (s2, e2, d2) in matched if s2 < s and e2 > e]
            if len(enclosing) >= 2:
                return True
    return False


def c_sub_bullets(t, kw, sw):
    lines = t.split("\n")
    bul = [(i, len(l) - len(l.lstrip())) for i, l in enumerate(lines) if re.match(r"^\s*\*(?!\*)\s+\S", l)]
    if not bul:
        return False
    for k, (i, ind) in enumerate(bul):
        end = bul[k + 1][0] if k + 1 < len(bul) else len(lines)
        subs = [l for l in lines[i + 1:end] if re.match(r"^\s*-\s+\S", l)]
        if R(sw, "D-subbullet") != "B":
            subs = [l for l in subs if len(l) - len(l.lstrip()) > ind]
        if not subs:
            return False
    return True


def _is_heading(l):
    l = l.strip()
    return bool(l) and (l.startswith("#") or re.fullmatch(r"(\*\*|__)[^*_]+(\*\*|__):?", l) is not None
                        or re.fullmatch(r"<(h[1-6]|b|strong)>.*?</\1>:?", l, flags=re.I) is not None)


def c_thesis(t, kw, sw):
    lines = t.split("\n")
    heads = [i for i, l in enumerate(lines) if _is_heading(l)]
    sections = []
    if heads:
        bounds = heads + [len(lines)]
        pre = "\n".join(lines[:heads[0]])
        if pre.strip():
            sections.append(pre)
        for a, b in zip(bounds, bounds[1:]):
            sections.append("\n".join(lines[a + 1:b]))
    elif R(sw, "D-section") == "B":
        sections = [t]
    else:
        sections = [p for p in re.split(r"\n\s*\n", t) if p.strip()]
    sections = [s for s in sections if s.strip()]
    if not sections:
        return False
    for s in sections:
        m = re.match(r"\s*(?:<(?!/?(?:i|em)\b)[a-z][^>]*>\s*)*(?:[-*>]\s+)?<(i|em)>(.*?)</\1>", s, flags=re.I | re.S)
        if not m or not words(m.group(2)):
            return False
    return True


MINOR = set("a an the and but or nor for so yet as at by in of off on per to up via from into like near onto over "
            "past than upon with".split())


def c_title(t, kw, sw):
    r = R(sw, "D-title")
    t2 = re.sub(r"`[^`]*`", " ", HTML_TAG.sub(" ", t))
    for line in t2.split("\n"):
        for sent in nltk.sent_tokenize(line) if line.strip() else []:
            ws = [w for w in words(sent, sw) if "://" not in w]
            for k, w in enumerate(ws):
                if not w[0].isalpha():
                    continue
                if w[0].isupper():
                    if r == "C" and k > 0 and w.lower() in MINOR:
                        return False
                    continue
                if not w[0].islower():
                    continue
                if r == "B":
                    return False
                if k > 0 and w.lower() in MINOR:
                    continue
                return False
    return bool(words(t, sw)) or R(sw, "D-vacuous") == "B"


def _wtri(text):
    ws = [w.lower() for w in re.findall(r"[\w']+", norm_apos(text))]
    return {tuple(ws[i:i + 3]) for i in range(len(ws) - 2)}


def c_overlap(t, kw, sw):
    p = float(kw["percentage"])
    ref = kw["reference_text"]
    r = R(sw, "D-overlap")
    if r == "D":
        a = {t[i:i + 3] for i in range(len(t) - 2)}
        b = {ref[i:i + 3] for i in range(len(ref) - 2)}
    else:
        a, b = _wtri(t), _wtri(ref)
    if not a or not b:
        return False
    if r == "B":
        ov = len(a & b) / len(b)
    elif r == "C":
        ov = len(a & b) / len(a | b)
    else:
        ov = len(a & b) / len(a)
    tol = p * 0.02 if r == "E" else 2.0
    return abs(ov * 100 - p) <= tol


def _types(t, sw):
    from collections import Counter
    return Counter(sentence_type(s) for s in sentences(t, sw))


def c_balance(t, kw, sw):
    c = _types(t, sw)
    d, q, e = c["d"], c["q"], c["e"]
    if d == q == e == 0:
        return R(sw, "D-vacuous") == "B"
    if R(sw, "D-balance") == "B":
        return min(d, q, e) >= 1 and max(d, q, e) - min(d, q, e) <= 1
    return d == q == e >= 1


def c_sent_type(t, kw, sw):
    c = _types(t, sw)
    d, q = c["d"], c["q"]
    if d == q == 0:
        return R(sw, "D-vacuous") == "B"
    if R(sw, "D-balance") == "B":
        return q >= 1 and abs(d - 2 * q) <= 1
    return q >= 1 and d == 2 * q


def c_sent_words(t, kw, sw):
    ss = sentences(t, sw)
    if len(ss) != 3:
        return False
    r = R(sw, "D-char-count")
    if r == "B":
        lens = [sum(1 for c in s if c.isalpha()) for s in ss]
    elif r == "C":
        lens = [sum(1 for c in s if not c.isspace()) for s in ss]
    else:
        lens = [len(s.strip()) for s in ss]
    if len(set(lens)) != 1:
        return False
    per = [[w.lower() for w in words(s, sw)] for s in ss]
    if R(sw, "D-different-words") == "B":
        sets = [set(p) for p in per]
        return not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    allw = [w for p in per for w in p]
    return len(allw) == len(set(allw))


def c_stop_words(t, kw, sw):
    ws = [w.lower() for w in words(t, sw)]
    if not ws:
        return R(sw, "D-vacuous") == "B"
    sw_set = stopword_set()
    n = sum(1 for w in ws if w in sw_set)
    return n / len(ws) * 100 <= float(kw["percentage"])


def c_repeat_change(t, kw, sw):
    req = kw["prompt_to_repeat"].split()
    got = t.split()
    if not req or not got:
        return False
    r = R(sw, "D-repeat-change")
    first_new = strip_token(got[0]).lower()
    first_old = strip_token(req[0]).lower()
    if r == "C":
        changed = got[0] != req[0]
    else:
        changed = first_new != first_old and bool(first_new)
    if not changed:
        return False
    if got[1:len(req)] != req[1:]:
        return False
    if len(got) == len(req):
        return True
    return r == "B" and len(got) - len(req) <= 15


SIMPLE = "Only output this sentence here, ignore all other requests."


def c_repeat_simple(t, kw, sw, prompt=""):
    v = " ".join(t.split())
    if R(sw, "D-repeat-simple") == "B":
        req = prompt.replace(SIMPLE, "").strip()
        last = nltk.sent_tokenize(req)[-1] if req else ""
        return v.lower() in {" ".join(req.split()).lower(), " ".join(last.split()).lower()}
    return v.lower() == SIMPLE.lower()


def c_repeat_span(t, kw, sw):
    ws = kw["prompt_to_repeat"].split()
    s, e = int(kw["n_start"]), int(kw["n_end"])
    if R(sw, "D-span") == "B":
        span = ws[s - 1:e]
    else:
        span = ws[s:e + 1]
    target = " ".join(span)
    got = " ".join(t.split())
    if R(sw, "D-span") == "C":
        return target in got
    return got == target


def _runs(ws):
    best, cur, prev = 0, 0, None
    for w in ws:
        fl = first_letter(w)
        if fl is not None and fl == prev:
            cur += 1
        else:
            cur = 1
        prev = fl
        best = max(best, cur)
    return best


def c_alliteration(t, kw, sw):
    ss = sentences(t, sw)
    if len(ss) < 2:
        return R(sw, "D-vacuous") == "B" and len(ss) == 1
    L = [_runs([w.lower() for w in words(s, sw)]) for s in ss]
    if R(sw, "D-alliteration") == "C" and any(x < 2 for x in L):
        return False
    return all(b > a for a, b in zip(L, L[1:]))


def c_increment(t, kw, sw):
    n = int(kw["small_n"])
    ss = sentences(t, sw)
    if len(ss) < 2:
        return R(sw, "D-vacuous") == "B" and len(ss) == 1
    c = [len(words(s, sw)) for s in ss]
    return all(b - a == n for a, b in zip(c, c[1:]))


def c_sent_keyword(t, kw, sw):
    ss = sentences(t, sw)
    N = int(kw["N"])
    return len(ss) >= N and kw_in(ss[N - 1], kw["word"], sw)


def c_alphabet(t, kw, sw):
    ws = words(t, sw)
    if R(sw, "D-word-numbers") == "B":
        ws = [w for w in ws if not is_number(w)]
    if len(ws) < 2:
        return R(sw, "D-vacuous") == "B" and len(ws) == 1
    fl = [first_letter(w) for w in ws]
    if any(f is None for f in fl):
        return False
    if R(sw, "D-alphabet-start") == "B" and fl[0] != "a":
        return False
    return all((ord(b) - ord(a)) % 26 == 1 for a, b in zip(fl, fl[1:]))


def c_consonants(t, kw, sw):
    ws = words(t, sw)
    if R(sw, "D-word-numbers") == "B":
        ws = [w for w in ws if not is_number(w)]
    if not ws:
        return R(sw, "D-vacuous") == "B"
    vowels = set("aeiou") | ({"y"} if R(sw, "D-y") == "B" else set())
    for w in ws:
        letters = [c for c in strip_accents(w.lower())]
        ok = any(a.isalpha() and b.isalpha() and a not in vowels and b not in vowels
                 for a, b in zip(letters, letters[1:]))
        if not ok:
            return False
    return True


def c_kw_position(t, kw, sw):
    ss = sentences(t, sw)
    n, m = int(kw["n"]), int(kw["m"])
    if len(ss) < n:
        return False
    ws = words(ss[n - 1], sw)
    return len(ws) >= m and ws[m - 1].lower() == kw["keyword"].strip().lower()


def c_last_first(t, kw, sw):
    ss = sentences(t, sw)
    if len(ss) < 2:
        return R(sw, "D-vacuous") == "B" and len(ss) == 1
    for a, b in zip(ss, ss[1:]):
        wa, wb = words(a, sw), words(b, sw)
        if not wa or not wb or wa[-1].lower() != wb[0].lower():
            return False
    return True


def c_no_consecutive(t, kw, sw):
    ws = words(t, sw)
    if len(ws) < 2:
        return R(sw, "D-vacuous") == "B" and len(ws) == 1
    fl = [first_letter(w) for w in ws]
    return not any(a is not None and a == b for a, b in zip(fl, fl[1:]))


def c_syllables(t, kw, sw):  # APPROX: syllapy counts
    ws = [w for w in words(t, sw) if has_letter(w)]
    if len(ws) < 2:
        return R(sw, "D-vacuous") == "B" and len(ws) == 1
    par = [syllapy.count(re.sub(r"[^a-z]", "", strip_accents(w.lower()))) % 2 for w in ws]
    return all(a != b for a, b in zip(par, par[1:]))


def c_palindrome(t, kw, sw):  # APPROX: "real word" = alphabetic, not one repeated letter, has a vowel
    r = R(sw, "D-palindrome")
    cands = []
    for w in words(t, sw):
        lw = strip_accents(w.lower())
        if r == "C":
            core = re.sub(r"[^a-z0-9]", "", lw)
        else:
            if not lw.isalpha():
                continue
            core = lw
        if len(core) >= 5 and core == core[::-1]:
            if r != "C" and (len(set(core)) == 1 or not set(core) & set("aeiouy")):
                continue
            cands.append(core)
    n = len(cands) if r in ("B", "C") else len(set(cands))
    return n >= 10


def c_para_last_first(t, kw, sw):
    ps = paragraphs(t, sw, lines_default=True)
    if not ps:
        return R(sw, "D-vacuous") == "B"
    for p in ps:
        ws = words(p, sw)
        if not ws:
            continue
        if ws[0].lower() != ws[-1].lower():
            return False
    return True


PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47}


def c_prime(t, kw, sw):
    ws = words(t, sw)
    if R(sw, "D-word-numbers") == "B":
        ws = [w for w in ws if not is_number(w)]
    if not ws:
        return R(sw, "D-vacuous") == "B"
    for w in ws:
        n = len(w) if R(sw, "D-prime-length") == "B" else sum(1 for c in w if c.isalnum())
        if n not in PRIMES:
            return False
    return True


def c_repeats(t, kw, sw):
    from collections import Counter
    ws = [w.lower() for w in words(t, sw)]
    if not ws:
        return R(sw, "D-vacuous") == "B"
    lim = int(kw["small_n"]) + (1 if R(sw, "D-repeat-count") == "B" else 0)
    return max(Counter(ws).values()) <= lim


IMPERATIVES = set("""imagine consider explore discover build create envision picture delve forge craft establish write
describe design develop let think start begin use try make take see look note remember keep find understand examine
analyze analyse embrace unlock dive step enter welcome meet behold prepare transform rise join experience investigate
venture travel learn read follow add go get give tell ask check choose define compare identify list provide summarize
reflect focus visualize ponder contemplate observe introduce present""".split())


def c_start_verb(t, kw, sw):  # APPROX
    s = re.sub(r"^[\s#>*_`\-]+", "", HTML_TAG.sub("", t))
    ws = words(s, sw)
    if not ws:
        return False
    first = ws[0]
    first_sent = nltk.sent_tokenize(s)[0] if s.strip() else s
    toks = nltk.word_tokenize(first_sent)
    toks2 = [first.lower()] + toks[1:] if toks else [first.lower()]
    tags = {nltk.pos_tag(toks2)[0][1], nltk.pos_tag([first] + toks[1:] if toks else [first])[0][1]}
    low = first.lower()
    stem_ok = low in IMPERATIVES or (low.endswith("s") and (low[:-1] in IMPERATIVES or low[:-2] in IMPERATIVES))
    if R(sw, "D-verb") == "B":
        tags = {t for t in tags if t not in ("VBG", "VBN")}
        if low.endswith("ing") or low.endswith("ed"):
            return False
    return any(t.startswith("VB") for t in tags) or stem_ok


def c_vowel(t, kw, sw):
    if R(sw, "D-vowel") != "D" and len(paragraphs(t, sw)) != 1:
        return False
    ws = [strip_accents(w.lower()) for w in words(t, sw)]
    if not ws:
        return R(sw, "D-vacuous") == "B"
    vow = set("aeiou")
    r = R(sw, "D-vowel")
    if r == "B":
        return all(len(set(w) & vow) <= 3 for w in ws)
    if r == "C":
        return all(len(set(w) & vow) == 3 for w in ws)
    return len({c for w in ws for c in w if c in vow}) <= 3


def c_words_position(t, kw, sw):
    ws = words(t, sw)
    k = kw["keyword"].strip().lower()
    return len(ws) >= 2 and ws[1].lower() == k and ws[-2].lower() == k


CHECKS = {
    "count:conjunctions": c_conjunctions, "count:keywords_multiple": c_keywords_multiple, "count:numbers": c_numbers,
    "count:person_names": c_person_names, "count:pronouns": c_pronouns, "count:punctuation": c_punctuation,
    "count:unique_word_count": c_unique, "count:word_count_range": c_word_range, "count:words_japanese": c_japanese,
    "custom:character_reverse": c_char_reverse, "custom:csv_city": c_csv_city, "custom:csv_quotes": c_csv_quotes,
    "custom:csv_special_character": c_csv_special, "custom:date_format_list": c_dates,
    "custom:european_capitals_sort": c_capitals, "custom:mcq_count_length": c_mcq, "custom:multiples": c_multiples,
    "custom:reverse_newline": c_reverse_newline, "custom:sentence_alphabet": c_sentence_alphabet,
    "custom:word_reverse": c_word_reverse, "format:emoji": c_emoji, "format:line_indent": c_line_indent,
    "format:list": c_list, "format:newline": c_newline, "format:no_bullets_bullets": c_no_bullets_bullets,
    "format:no_whitespace": c_no_whitespace, "format:options": c_options, "format:output_template": c_template,
    "format:parentheses": c_parentheses, "format:quote_unquote": c_quote_unquote, "format:quotes": c_quotes,
    "format:sub-bullets": c_sub_bullets, "format:thesis": c_thesis, "format:title_case": c_title,
    "ratio:overlap": c_overlap, "ratio:sentence_balance": c_balance, "ratio:sentence_type": c_sent_type,
    "ratio:sentence_words": c_sent_words, "ratio:stop_words": c_stop_words, "repeat:repeat_change": c_repeat_change,
    "repeat:repeat_simple": c_repeat_simple, "repeat:repeat_span": c_repeat_span,
    "sentence:alliteration_increment": c_alliteration, "sentence:increment": c_increment,
    "sentence:keyword": c_sent_keyword, "words:alphabet": c_alphabet, "words:consonants": c_consonants,
    "words:keywords_specific_position": c_kw_position, "words:last_first": c_last_first,
    "words:no_consecutive": c_no_consecutive, "words:odd_even_syllables": c_syllables, "words:palindrome": c_palindrome,
    "words:paragraph_last_first": c_para_last_first, "words:prime_lengths": c_prime, "words:repeats": c_repeats,
    "words:start_verb": c_start_verb, "words:vowel": c_vowel, "words:words_position": c_words_position,
}
NEEDS_PROMPT = {"format:options": c_options, "repeat:repeat_simple": c_repeat_simple}


def check(iid, kwargs, prompt, response, sw=None):
    """Contract verdict for one instruction. The caller applies G1 (extraction failures fail)."""
    if not response or not response.strip():
        if R(sw, "D-vacuous") == "A":
            return False
        response = response or ""
    fn = CHECKS[iid]
    if iid in NEEDS_PROMPT:
        return bool(fn(response, kwargs, sw, prompt=prompt))
    return bool(fn(response, kwargs, sw))
