"""Replacement grader: an implementation of audit/CONTRACTS.md with one switch per decision entry.

check(instruction_id, kwargs, response, prompt="", decisions=None) -> bool
`decisions` overrides DEFAULT (the proposed readings). Only the decision entries that change a verdict
mechanically have switches; role-based readings (pronouns, conjunctions, verbs) use NLTK POS tags as
an approximation and their error is what the blinded review (step 6) would measure.
"""
from __future__ import annotations

import csv
import datetime
import io
import re
import string
import unicodedata

import emoji
import nltk
import syllapy

DEFAULT = {
    "D-trailing-ws": "ignore",        # ignore | count
    "D-sentence-fragment": "count",   # count (A) | drop (B)
    "D-word-split": "whole",          # whole (A) | split (B: \w+ pieces)
    "D-list-label": "markup",         # markup (A) | word (B)
    "D-vacuous": "pass",              # pass (A) | fail (B)
    "D-count-exact": "exact",         # exact | atleast
    "D-keyword-form": "exact",        # exact | prefix
    "D-punct-set": "english",         # english (A) | ascii (B) | six (C)
    "D-unique": "types",              # types | hapax
    "D-between": "inclusive",         # inclusive | exclusive
    "D-titlecase-minor": "minor_ok",  # minor_ok (A) | all (B)
    "D-overlap-def": "word_resp",     # word_resp (A) | word_ref | jaccard | char_resp
    "D-balance": "pm1",               # pm1 (A) | equal (B)
    "D-different-words": "all",       # all (A) | across
    "D-repeat-count": "n",            # n (A) | n_plus_1
    "D-palindrome-distinct": "distinct",  # distinct | occurrences
    "D-vowel-scope": "response_atmost3",  # response_atmost3 (A) | per_word_atmost3 | response_exactly3
    "D-vowel-paragraph": "unscored",  # unscored (A) | one_line (B)
    "D-options-extra": "exact",       # exact (A) | contains
    "D-multiples-prose": "numbers_only",  # numbers_only (A) | prose_ok
    "D-custom-content": "form",       # form (A) | complete
    "D-nbb-after": "allowed",         # allowed | forbidden
    "D-emoji-position": "either",
    "D-index-base": 0,                # 0 | 1
    "D-change-case": "not_change",    # not_change (A) | change
    "D-csv-space": "ok",              # ok (A) | strict
    "D-wrapper": "per_check",
    # v3 switches (measurement only; the proposal readings below match v1/v2 behaviour)
    "D-conjunction-role": "role",     # role (A) | surface (B: any occurrence of the seven words)
    "D-section": "paragraphs",        # paragraphs (A) | whole (B: no headings -> one section)
    "D-wrapper-csv": "ok",            # ok (A: fences / a sentence around the CSV) | strict
    "D-wrapper-template": "strict",   # strict (A: response starts with "My Answer:") | ok
    "D-wrapper-list": "strict",       # strict (A: country lines only) | ok (lead-in lines allowed)
    "D-indent-single": "fail",        # fail (A: one line is no stairs) | pass (vacuous)
    "D-options-label": "letter",      # letter (A: "d" or "d." is option d)) | strict (exact label)
    "D-japanese-mixed": "all",        # all (A: all letters Japanese) | contains
}

# ------------------------------------------------------------------ text helpers
_EDGE = set(string.punctuation) | set("“”‘’«»—–‒…·•„‹›¿¡")
_TERMINAL = ".!?…‽"
_CLOSERS = "\"'”’)]}»*_`"
_LABEL_RE = re.compile(r"^\s*(?:[-*•+]|\d+[.)]|[A-Za-z][.)]|#+)\s+")
_ABBREV = {"mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "vs", "etc", "e.g", "i.e", "u.s", "u.k", "a.m", "p.m",
           "no", "fig", "approx", "inc", "ltd", "co", "mt", "gen", "col", "lt", "sgt", "dept", "est", "vol", "u.s.a",
           "e.g.", "i.e.", "cf", "al", "ca"}


def _norm_apos(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'")


def _strip_html(text: str) -> str:
    return re.sub(r"</?[A-Za-z][^<>]{0,40}>", " ", text)


def _strip_token(tok: str) -> str:
    i, j = 0, len(tok)
    while i < j and (tok[i] in _EDGE or emoji.is_emoji(tok[i]) or unicodedata.category(tok[i]).startswith(("P", "S", "M", "C"))):
        i += 1
    while j > i and (tok[j - 1] in _EDGE or emoji.is_emoji(tok[j - 1]) or unicodedata.category(tok[j - 1]).startswith(("P", "S", "M", "C"))):
        j -= 1
    return tok[i:j]


def _has_alnum(s: str) -> bool:
    return any(ch.isalnum() for ch in s)


def strip_labels(text: str, dec) -> str:
    if dec["D-list-label"] != "markup":
        return text
    return "\n".join(_LABEL_RE.sub("", line, count=1) for line in text.split("\n"))


def words(text: str, dec=None) -> list:
    """G3 words, in order (original case)."""
    dec = dec or DEFAULT
    text = strip_labels(_strip_html(text), dec)
    out = []
    for tok in text.split():
        t = _strip_token(tok)
        if not t or not _has_alnum(t):
            continue
        if dec["D-word-split"] == "split":
            out.extend(re.findall(r"\w+", t))
        else:
            out.append(t)
    return out


def lw(text, dec=None):
    return [_norm_apos(w).lower() for w in words(text, dec)]


def _is_abbrev(chunk: str) -> bool:
    m = re.search(r"(\S+)$", chunk)
    if not m:
        return False
    last = m.group(1).rstrip(".").lower().lstrip("(\"'“")
    if last in _ABBREV or last + "." in _ABBREV:
        return True
    if re.fullmatch(r"[a-z]", last):  # an initial such as "J."
        return True
    if re.fullmatch(r"(?:[a-z]\.)+[a-z]", last):  # U.S, e.g
        return True
    return False


_EMOJI_RUN = None


def sentences(text: str, dec=None) -> list:
    """G5 sentences (strings). Line breaks end sentences; list labels and heading marks are removed."""
    dec = dec or DEFAULT
    text = strip_labels(_strip_html(text), dec)
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        buf = ""
        i, n = 0, len(line)
        while i < n:
            ch = line[i]
            buf += ch
            if ch in _TERMINAL:
                j = i + 1
                while j < n and line[j] in _TERMINAL:
                    buf += line[j]
                    j += 1
                while j < n and line[j] in _CLOSERS:
                    buf += line[j]
                    j += 1
                # absorb emoji that follow (optionally after spaces)
                k = j
                while True:
                    m = k
                    while m < n and line[m] == " ":
                        m += 1
                    if m < n and (emoji.is_emoji(line[m]) or unicodedata.category(line[m]) in ("So", "Sk")
                                  or line[m] in "️‍⃣" or "\U0001F3FB" <= line[m] <= "\U0001F3FF"):
                        e = m
                        while e < n and (emoji.is_emoji(line[e]) or unicodedata.category(line[e]) in ("So", "Sk", "Mn", "Me", "Cf")
                                         or "\U0001F3FB" <= line[e] <= "\U0001F3FF"):
                            e += 1
                        buf += line[k:e]
                        k = e
                    else:
                        break
                j = k
                at_end = j >= n
                followed_by_space = (not at_end) and line[j].isspace()
                decimal = ch == "." and i > 0 and line[i - 1].isdigit() and (not at_end) and line[j].isdigit()
                # v3 (contract change C9): an ellipsis followed by a lowercase word marks an omission, not a sentence end
                run = buf.rstrip(_CLOSERS + " ")
                ellipsis_mid = (run.endswith("...") or run.endswith("…")) and followed_by_space and \
                    re.match(r"\s*[a-z]", line[j:]) is not None
                if (at_end or followed_by_space) and not decimal and not ellipsis_mid and \
                        not (ch == "." and j == i + 1 and _is_abbrev(buf[:-1]) and not at_end):
                    out.append(buf.strip())
                    buf = ""
                i = j
                continue
            i += 1
        if buf.strip():
            out.append(buf.strip())
    sents = [s for s in out if _has_alnum(s)]
    if dec["D-sentence-fragment"] == "drop":
        sents = [s for s in sents if _ends_terminal(s)]
    return sents


def _ends_terminal(s: str) -> bool:
    t = s.rstrip()
    while t and (t[-1] in _CLOSERS or emoji.is_emoji(t[-1]) or unicodedata.category(t[-1]) in ("So", "Sk", "Mn", "Me", "Cf")
                 or "\U0001F3FB" <= t[-1] <= "\U0001F3FF" or t[-1] == " "):
        t = t[:-1]
    return bool(t) and t[-1] in _TERMINAL


def _terminal_type(s: str):
    t = s.rstrip()
    while t and (t[-1] in _CLOSERS or emoji.is_emoji(t[-1]) or unicodedata.category(t[-1]) in ("So", "Sk", "Mn", "Me", "Cf")
                 or "\U0001F3FB" <= t[-1] <= "\U0001F3FF" or t[-1] == " "):
        t = t[:-1]
    m = re.search(r"[.!?…‽]+$", t)
    if not m:
        return None
    run = m.group(0)
    if "?" in run or "‽" in run:
        return "?"
    if "!" in run:
        return "!"
    return "."


def _ends_with_emoji(s: str) -> bool:
    t = s.rstrip()
    # remove trailing terminal marks / closers, then look for an emoji at the end, or emoji then marks
    for _ in range(2):
        if t and emoji.emoji_list(t) and emoji.emoji_list(t)[-1]["match_end"] == len(t):
            return True
        while t and (t[-1] in _TERMINAL or t[-1] in _CLOSERS or t[-1] in " ️‍"):
            t = t[:-1]
    if t and (emoji.emoji_list(t) and emoji.emoji_list(t)[-1]["match_end"] == len(t)):
        return True
    return False


# ------------------------------------------------------------------ checks
CHECKS = {}


def check_fn(iid):
    def deco(f):
        CHECKS[iid] = f
        return f
    return deco


def _num(x):
    return int(x) if isinstance(x, float) and x == int(x) else x


@check_fn("count:conjunctions")
def _conj(text, kw, dec, prompt):
    toks = nltk.word_tokenize(text)
    found = set()
    if dec["D-conjunction-role"] == "surface":
        found = {_norm_apos(t).lower() for t in toks} & {"and", "but", "or", "nor", "for", "so", "yet"}
        return len(found) >= kw["small_n"]
    for i, t in enumerate(toks):
        lt = _norm_apos(t).lower()
        if lt in ("and", "but", "or", "nor"):
            found.add(lt)
        elif lt in ("yet", "so", "for"):
            # v2: a conjunction joins clauses: it follows a clause boundary or precedes a clause subject
            prev = toks[i - 1] if i > 0 else "."
            nxt = toks[i + 1].lower() if i + 1 < len(toks) else ""
            subject_next = nxt in ("i", "you", "he", "she", "it", "we", "they", "there", "this", "that", "these",
                                   "those", "the", "a", "an", "his", "her", "their", "our", "my", "its", "nobody",
                                   "no", "not", "many", "most", "some", "everyone", "people")
            if lt == "for" and nxt in ("example", "instance", "now", "all", "more", "the", "a", "an", "this", "that",
                                        "these", "those", "his", "her", "their", "our", "my", "its", "many", "most", "some"):
                continue
            if prev in (",", ";", ".", "!", "?", ":", "--") or subject_next:
                found.add(lt)
    return len(found) >= kw["small_n"]


@check_fn("count:keywords_multiple")
def _kwmulti(text, kw, dec, prompt):
    ws = lw(text, dec)
    ws = [re.sub(r"'s$", "", w) for w in ws]
    for k, cnt in zip([kw[f"keyword{i}"] for i in range(1, 6)], [1, 2, 3, 5, 7]):
        k = k.strip().lower()
        if dec["D-keyword-form"] == "exact":
            c = sum(1 for w in ws if w == k)
        else:
            c = sum(1 for w in ws if w.startswith(k))
        if (c != cnt) if dec["D-count-exact"] == "exact" else (c < cnt):
            return False
    return True


_NUM_RE = re.compile(r"(?<![\w.,])[-+−]?\d+(?:[.,]\d+)*%?")


@check_fn("count:numbers")
def _numbers(text, kw, dec, prompt):
    t = strip_labels(text, dec)
    nums = re.findall(r"(?<![0-9])\d+(?:[.,]\d+)*", t)
    return len(nums) == kw["N"]


PERSON_NAMES = ["Emma", "Liam", "Sophia", "Jackson", "Olivia", "Noah", "Ava", "Lucas", "Isabella", "Mason", "Mia", "Ethan",
                "Charlotte", "Alexander", "Amelia", "Benjamin", "Harper", "Leo", "Zoe", "Daniel", "Chloe", "Samuel", "Lily",
                "Matthew", "Grace", "Owen", "Abigail", "Gabriel", "Ella", "Jacob", "Scarlett", "Nathan", "Victoria", "Elijah",
                "Layla", "Nicholas", "Audrey", "David", "Hannah", "Christopher", "Penelope", "Thomas", "Nora", "Andrew",
                "Aria", "Joseph", "Claire", "Ryan", "Stella", "Jonathan"]


@check_fn("count:person_names")
def _names(text, kw, dec, prompt):
    found = 0
    for name in PERSON_NAMES:
        pat = r"(?<!\w)" + name[0] + "(?i:" + re.escape(name[1:]) + r")(?!\w)"
        if re.search(pat, text):
            found += 1
    return found >= kw["N"]


_PRON_ALWAYS = {"i", "me", "you", "he", "him", "she", "her", "it", "we", "us", "they", "them", "my", "your", "his", "its",
                "our", "their", "mine", "yours", "hers", "ours", "theirs", "myself", "yourself", "himself", "herself",
                "itself", "ourselves", "yourselves", "themselves", "oneself", "anybody", "anyone", "anything",
                "everybody", "everyone", "everything", "nobody", "nothing", "somebody", "someone", "something",
                "whoever", "whomever", "whatever", "whichever", "who", "whom", "whose"}
_PRON_STANDALONE = {"this", "that", "these", "those", "each", "either", "neither", "both", "all", "some", "any", "none",
                    "which", "what", "one"}


@check_fn("count:pronouns")
def _pronouns(text, kw, dec, prompt):
    toks = nltk.word_tokenize(_norm_apos(text).replace("/", " "))
    tags = nltk.pos_tag(toks)
    count = 0
    for i, (t, tag) in enumerate(tags):
        lt = t.lower()
        if lt in _PRON_ALWAYS:
            count += 1
        elif lt in _PRON_STANDALONE:
            nxt = tags[i + 1][1] if i + 1 < len(tags) else "."
            if lt == "that" and tag == "IN":
                continue
            if lt == "none":
                count += 1
                continue
            if lt == "one":
                continue
            if nxt.startswith(("NN", "JJ", "CD")) or (i + 1 < len(tags) and tags[i + 1][0].lower() in ("other", "same", "few", "many", "more", "most")):
                continue
            count += 1
    return count >= kw["N"]


@check_fn("count:punctuation")
def _punct(text, kw, dec, prompt):
    has_ib = ("?!" in text) or ("!?" in text) or ("‽" in text)
    if not has_ib:
        return False
    rd = dec["D-punct-set"]
    if rd == "six":
        need = [".", ",", "?", "!", ";", ":"]
        return all(c in text for c in need)
    if rd == "ascii":
        return all(c in text for c in string.punctuation)
    groups = [["."], [","], ["?"], ["!"], [";"], [":"], ["'", "’"], ['"', "“", "”"], ["-"],
              ["–", "—", "--"], ["("], [")"], ["["], ["]"], ["…", "..."], ["/"]]
    return all(any(g in text for g in grp) for grp in groups)


@check_fn("count:unique_word_count")
def _unique(text, kw, dec, prompt):
    ws = lw(text, dec)
    if dec["D-unique"] == "types":
        return len(set(ws)) >= kw["N"]
    from collections import Counter
    return sum(1 for v in Counter(ws).values() if v == 1) >= kw["N"]


@check_fn("count:word_count_range")
def _wcr(text, kw, dec, prompt):
    n = len(words(text, dec))
    if dec["D-between"] == "inclusive":
        return kw["min_words"] <= n <= kw["max_words"]
    return kw["min_words"] < n < kw["max_words"]


def _is_japanese_token(t):
    letters = [c for c in t if c.isalnum()]
    if not letters:
        return False
    for c in letters:
        o = ord(c)
        if not (0x3040 <= o <= 0x30FF or 0x3400 <= o <= 0x4DBF or 0x4E00 <= o <= 0x9FFF or 0xFF66 <= o <= 0xFF9F or c in "々ー"):
            return False
    return True


@check_fn("count:words_japanese")
def _jp(text, kw, dec, prompt):
    N = int(kw["N"])
    ws = words(text, dec)
    for i, w in enumerate(ws):
        if (i + 1) % N == 0:
            if dec["D-japanese-mixed"] == "contains":
                ok = any(_is_japanese_token(c) for c in w)
            else:
                ok = _is_japanese_token(w)
            if not ok:
                return False
    return True


@check_fn("custom:character_reverse")
def _charrev(text, kw, dec, prompt):
    r = text.strip()
    rev = r[::-1].lower()
    return "eagle" in rev and "eagle" not in r.lower() and len(rev.split()) >= 3


@check_fn("custom:word_reverse")
def _wordrev(text, kw, dec, prompt):
    fw = [w.lower() for w in words(text, dec)]
    if "eagle" not in fw or "elgae" in text.lower():
        return False
    bigrams = list(zip(fw, fw[1:]))
    if "bald" in fw:  # v3: the reversed text must read "... bald eagle ...", the forward text must not
        return ("eagle", "bald") in bigrams and ("bald", "eagle") not in bigrams
    e = fw.index("eagle")
    if "symbol" in fw:
        return fw.index("symbol") < e
    if "is" in fw:
        return fw.index("is") < e
    return False


def _only_table(text, table_lines):
    """D-wrapper-csv reading B: the response holds the table and nothing else."""
    return [ln.strip() for ln in text.split("\n") if ln.strip()] == [ln.strip() for ln in table_lines]


def _csv_block(text):
    lines = text.split("\n")
    return [ln for ln in lines if not ln.strip().startswith("```")]


def _find_table(text, header, delim, dec):
    lines = _csv_block(text)
    names = [h.lower() for h in header]
    for i, ln in enumerate(lines):
        raw = ln.strip()
        if not raw:
            continue
        fields = next(csv.reader([raw], delimiter=delim, skipinitialspace=(dec["D-csv-space"] == "ok")))
        if [f.strip().strip('"').lower() for f in fields] == names:
            rows = []
            for ln2 in lines[i + 1:]:
                if not ln2.strip():
                    if rows:
                        break
                    continue
                if delim not in ln2:
                    break
                rows.append(ln2.strip())
            return raw, rows
    return None, None


@check_fn("custom:csv_city")
def _csv_city(text, kw, dec, prompt):
    header, rows = _find_table(text, ["ID", "Country", "City", "Year", "Count"], ",", dec)
    if header is None:
        return False
    if len(rows) != 7:
        return False
    for r in rows:
        f = next(csv.reader([r], skipinitialspace=(dec["D-csv-space"] == "ok")))
        if len(f) != 5:
            return False
    if dec["D-wrapper-csv"] == "strict" and not _only_table(text, [header] + rows):
        return False
    return True


def _split_quoted(line, delim):
    """Split a delimited line, keeping each field's raw text (with its quotes)."""
    fields, cur, inq = [], "", False
    for ch in line:
        if ch == '"':
            inq = not inq
            cur += ch
        elif ch == delim and not inq:
            fields.append(cur)
            cur = ""
        else:
            cur += ch
    fields.append(cur)
    return fields


@check_fn("custom:csv_quotes")
def _csv_quotes(text, kw, dec, prompt):
    lines = [ln for ln in _csv_block(text) if ln.strip()]
    hdr_idx = None
    for i, ln in enumerate(lines):
        f = [x.strip() for x in _split_quoted(ln.strip(), "\t")]
        if [x.strip('"').lower() for x in f] == ["studentid", "subject", "grade", "semester", "score"]:
            hdr_idx = i
            break
    if hdr_idx is None:
        return False
    table = [lines[hdr_idx]]
    for ln in lines[hdr_idx + 1:]:
        if "\t" not in ln:
            break
        table.append(ln)
    if len(table) != 4:
        return False
    for ln in table:
        f = [x.strip() for x in _split_quoted(ln.strip(), "\t")]
        if len(f) != 5:
            return False
        if not all(len(x) >= 2 and x[0] == '"' and x[-1] == '"' for x in f):
            return False
    if dec["D-wrapper-csv"] == "strict" and not _only_table(text, table):
        return False
    return True


@check_fn("custom:csv_special_character")
def _csv_special(text, kw, dec, prompt):
    lines = [ln for ln in _csv_block(text) if ln.strip()]
    hdr_idx = None
    for i, ln in enumerate(lines):
        f = [x.strip() for x in _split_quoted(ln.strip(), ",")]
        if [x.strip('"').lower() for x in f] == ["productid", "category", "brand", "price", "stock"]:
            hdr_idx = i
            break
    if hdr_idx is None:
        return False
    rows = []
    for ln in lines[hdr_idx + 1:]:
        if "," not in ln:
            break
        rows.append(ln.strip())
    if len(rows) != 14:
        return False
    special = False
    for r in rows:
        f = [x.strip() for x in _split_quoted(r, ",")]
        if len(f) != 5:
            return False
        for x in f:
            if len(x) >= 2 and x[0] == '"' and x[-1] == '"' and re.search(r"[^\w\s]", x[1:-1]):
                special = True
    if dec["D-wrapper-csv"] == "strict" and not _only_table(text, [lines[hdr_idx]] + rows):
        return False
    return special


@check_fn("custom:date_format_list")
def _dates(text, kw, dec, prompt):
    items = [x.strip() for x in text.strip().rstrip(".").split(",")]
    if len(items) < 2:
        return False
    for x in items:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", x):
            return False
        try:
            datetime.date(int(x[:4]), int(x[5:7]), int(x[8:]))
        except ValueError:
            return False
    return True


CAPITALS = {"reykjavik": 64.15, "helsinki": 60.17, "oslo": 59.91, "tallinn": 59.44, "stockholm": 59.33, "riga": 56.95,
            "moscow": 55.76, "copenhagen": 55.68, "vilnius": 54.69, "minsk": 53.90, "dublin": 53.35, "berlin": 52.52,
            "amsterdam": 52.37, "warsaw": 52.23, "london": 51.51, "brussels": 50.85, "kyiv": 50.45, "prague": 50.08,
            "luxembourg": 49.61, "paris": 48.86, "vienna": 48.21, "bratislava": 48.15, "budapest": 47.50,
            "vaduz": 47.14, "chisinau": 47.01, "bern": 46.95, "ljubljana": 46.06, "zagreb": 45.81}
CAP_ALIAS = {"kiev": "kyiv", "luxembourg city": "luxembourg", "reykjavík": "reykjavik", "chișinău": "chisinau"}


def _ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


@check_fn("custom:european_capitals_sort")
def _capitals(text, kw, dec, prompt):
    items = [_ascii(x).strip().strip("*").strip().lower() for x in text.strip().rstrip(".").split(",")]
    items = [CAP_ALIAS.get(x, x) for x in items]
    if len(items) < 2 or any(x not in CAPITALS for x in items) or len(set(items)) != len(items):
        return False
    lats = [CAPITALS[x] for x in items]
    if any(lats[i] <= lats[i + 1] for i in range(len(lats) - 1)):
        return False
    if dec["D-custom-content"] == "complete" and len(items) != len(CAPITALS):
        return False
    return True


@check_fn("custom:mcq_count_length")
def _mcq(text, kw, dec, prompt):
    t = text.replace("*", "").replace("#", "").strip()
    if not t.startswith("Question"):
        return False
    parts = re.split(r"(?m)^\s*(?=Question\b)", t)
    parts = [p for p in parts if p.strip()]
    if len(parts) != 4:
        return False
    lengths = []
    for p in parts:
        body = re.sub(r"^Question\s*\d*\s*[.:)\-]?\s*", "", p.strip())
        lines = [ln.strip() for ln in body.split("\n")]
        stem, opts, after = [], 0, False
        for ln in lines:
            if not ln:
                continue
            if re.match(r"^\(?[A-Ea-e][.)]\s*\S", ln):
                opts += 1
                after = True
            elif not after:
                stem.append(ln)
            else:
                return False  # text after the options (explanation, answer key)
        if opts != 5 or not stem:
            return False
        lengths.append(len(" ".join(stem)))
    return all(lengths[i] < lengths[i + 1] for i in range(3))


@check_fn("custom:multiples")
def _multiples(text, kw, dec, prompt):
    nums = re.findall(r"\d+", text)
    if nums != [str(i) for i in range(14, 51, 7)]:
        return False
    if dec["D-multiples-prose"] == "numbers_only":
        rest = re.sub(r"\d+", "", text)
        return not re.search(r"[A-Za-z]", rest)
    return True


AFRICA = {"algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde", "cape verde", "cameroon",
          "central african republic", "chad", "comoros", "democratic republic of the congo", "dr congo",
          "congo, democratic republic of the", "democratic republic of congo", "republic of the congo", "congo",
          "republic of congo", "congo, republic of the", "congo (brazzaville)", "congo (kinshasa)", "djibouti", "egypt",
          "equatorial guinea", "eritrea", "eswatini", "swaziland", "eswatini (swaziland)", "ethiopia", "gabon",
          "gambia", "the gambia", "gambia, the", "ghana", "guinea", "guinea-bissau", "ivory coast", "cote d'ivoire",
          "cote d'ivoire (ivory coast)", "kenya", "lesotho", "liberia", "libya", "madagascar", "malawi", "mali",
          "mauritania", "mauritius", "morocco", "mozambique", "namibia", "niger", "nigeria", "rwanda",
          "sao tome and principe", "senegal", "seychelles", "sierra leone", "somalia", "south africa", "south sudan",
          "sudan", "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe"}


@check_fn("custom:reverse_newline")
def _rev_newline(text, kw, dec, prompt):
    lines = [strip_labels(ln, dec).strip().strip("*").strip().rstrip(".,") for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    if dec["D-wrapper-list"] == "ok":  # lead-in lines before the first country are allowed
        while lines and _ascii(_norm_apos(lines[0])).lower() not in AFRICA:
            lines = lines[1:]
    if len(lines) < 2:
        return False
    norm = [_ascii(_norm_apos(ln)).lower() for ln in lines]

    def known(x):  # v2: accept parenthetical variants such as "Congo (Republic of the)", "Cape Verde (Cabo Verde)"
        if x in AFRICA:
            return True
        m = re.fullmatch(r"(.*?)\s*\((.*?)\)", x)
        if m:
            base, par = m.group(1).strip(), m.group(2).strip()
            return base in AFRICA or par in AFRICA or f"{par} {base}" in AFRICA
        return False

    if any(not known(x) for x in norm):
        return False
    if any(norm[i] <= norm[i + 1] for i in range(len(norm) - 1)):
        return False
    if dec["D-custom-content"] == "complete" and len(norm) < 54:
        return False
    return True


@check_fn("custom:sentence_alphabet")
def _sent_alpha(text, kw, dec, prompt):
    ss = sentences(text, dec)
    if len(ss) != 26:
        return False
    for i, s in enumerate(ss):
        w = words(s, dec)
        if not w or w[0][0].lower() != chr(97 + i):
            return False
    return True


@check_fn("format:emoji")
def _emoji(text, kw, dec, prompt):
    ss = sentences(text, dec)
    if not ss:
        return dec["D-vacuous"] == "pass"
    return all(_ends_with_emoji(s) for s in ss)


@check_fn("format:line_indent")
def _indent(text, kw, dec, prompt):
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if len(lines) < 2:
        return dec["D-indent-single"] == "pass"
    ind = [len(ln.expandtabs(4)) - len(ln.expandtabs(4).lstrip()) for ln in lines]
    return all(ind[i + 1] > ind[i] for i in range(len(ind) - 1))


@check_fn("format:list")
def _list(text, kw, dec, prompt):
    sep = kw["sep"]
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    marker_lines = [ln for ln in lines if ln.startswith(sep)]
    other_markers = [m for m in ("* ", "• ", "- ", "+ ") if m.strip() != sep.strip()]
    if any(ln.startswith(m) for ln in lines for m in other_markers) or any(re.match(r"^\d+[.)]\s", ln) for ln in lines):
        return False
    if len(marker_lines) >= 2:
        return True
    # v3: a separator made of punctuation (e.g. "!?!?") may touch the items; a word or "-" needs spaces around it
    if re.search(r"\w", sep) or sep.strip() == "-":
        pat = r"(?:^|\s)" + re.escape(sep) + r"(?=\s|$)"
    else:
        pat = re.escape(sep)
    pieces = [p for p in re.split(pat, text) if p.strip()]
    return len(pieces) >= 2 and len(re.findall(pat, text)) >= 1


@check_fn("format:newline")
def _newline(text, kw, dec, prompt):
    return all(len(words(ln, dec)) <= 1 for ln in text.split("\n"))


@check_fn("format:no_bullets_bullets")
def _nbb(text, kw, dec, prompt):
    lines = text.split("\n")
    first = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("* ")), None)
    if first is None:
        return False
    pre = "\n".join(lines[:first])
    period_sents = [s for s in sentences(pre, dec) if _terminal_type(s) == "." and not s.rstrip().endswith("…")]
    if len(period_sents) < 2:
        return False
    after = lines[first:]
    bullets = [ln for ln in after if ln.lstrip().startswith("* ")]
    if len(bullets) < 2:
        return False
    if dec["D-nbb-after"] == "forbidden":  # v3: no text after the first bullet other than bullets and blank lines
        if any(ln.strip() and not ln.lstrip().startswith("* ") for ln in after):
            return False
    return True


@check_fn("format:no_whitespace")
def _nows(text, kw, dec, prompt):
    t = text.rstrip() if dec["D-trailing-ws"] == "ignore" else text
    return not any(c.isspace() for c in t)


def _parse_options(options):
    if "/" in options:
        parts = options.split("/")
    elif " or " in options:
        parts = options.split(" or ")
    else:
        parts = options.split(",")
    return [p.strip() for p in parts if p.strip()]


@check_fn("format:options")
def _options(text, kw, dec, prompt):
    opts = _parse_options(kw["options"])
    t = text.strip().replace("*", "").replace("_", "").replace("`", "").strip()
    t = re.sub(r"[.!]+$", "", t).strip()

    def key(o):
        o = _norm_apos(o).strip().lower()
        if dec["D-options-label"] == "strict":
            return o
        m = re.fullmatch(r"\(?([a-e])[.)]?", o)
        return m.group(1) + ")" if m else o

    tk = key(t)
    okeys = [key(o) for o in opts]
    if dec["D-options-extra"] == "exact":
        return tk in okeys
    hits = [o for o in okeys if re.search(r"(?<!\w)" + re.escape(o) + r"(?!\w)", _norm_apos(t).lower())]
    return len(hits) == 1


@check_fn("format:output_template")
def _template(text, kw, dec, prompt):
    t = re.sub(r"[*_#]", "", _strip_html(text)).strip()
    t = re.sub(r"[ \t]+", " ", t)
    labels = ["My Answer:", "My Conclusion:", "Future Outlook:"]
    if labels[0] in t and dec["D-wrapper-template"] == "ok":
        t = t[t.index(labels[0]):]
    if not t.startswith(labels[0]):
        return False
    if any(t.count(lb) != 1 for lb in labels):
        return False
    pos = [t.index(lb) for lb in labels]
    if not (pos[0] < pos[1] < pos[2]):
        return False
    contents = [t[pos[0] + len(labels[0]):pos[1]], t[pos[1] + len(labels[1]):pos[2]], t[pos[2] + len(labels[2]):]]
    placeholders = ["[answer]", "[conclusion]", "[outlook]"]
    for c, ph in zip(contents, placeholders):
        c = c.strip()
        if not _has_alnum(c) or c.lower() == ph:
            return False
    return True


@check_fn("format:parentheses")
def _parens(text, kw, dec, prompt):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []  # entries: [char, max_child_depth]
    best = 0
    for ch in text:
        if ch in "([{":
            stack.append([ch, 0])
        elif ch in ")]}":
            if stack and stack[-1][0] == pairs[ch]:
                _, child = stack.pop()
                d = child + 1
                best = max(best, d)
                if stack:
                    stack[-1][1] = max(stack[-1][1], d)
            else:
                stack = []
    return best >= 5


def _quote_spans(text):
    """Return quoted phrases as (start, end) spans; end is the index after the closing mark."""
    spans = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "“«":
            close = "”" if ch == "“" else "»"
            j = text.find(close, i + 1)
            if j == -1:
                break
            spans.append((i, j + 1))
            i = j + 1
            continue
        if ch == '"':
            j = text.find('"', i + 1)
            if j == -1:
                break
            spans.append((i, j + 1))
            i = j + 1
            continue
        if ch in "'‘" and (i == 0 or not text[i - 1].isalnum()):
            j = i + 1
            while j < n:
                if text[j] in "'’" and (j + 1 == n or not text[j + 1].isalnum()) and text[j - 1] != " ":
                    break
                j += 1
            if j < n and j > i + 1:
                spans.append((i, j + 1))
                i = j + 1
                continue
        i += 1
    return spans


@check_fn("format:quote_unquote")
def _quote_unquote(text, kw, dec, prompt):
    # v2: a quoted span without a letter or digit (a mention of a character such as '"') is not a phrase
    spans = [(s, e) for s, e in _quote_spans(text) if _has_alnum(text[s + 1:e - 1])]
    for k, (s, e) in enumerate(spans):
        nxt = spans[k + 1][0] if k + 1 < len(spans) else len(text)
        between = text[e:nxt]
        if not re.search(r"[A-Za-zÀ-ɏ]{2,}", between):
            return False
    return True


@check_fn("format:quotes")
def _nested_quotes(text, kw, dec, prompt):
    """Depth of correctly closed quotations whose levels alternate between double and single quotes."""
    stack = []  # [kind, max alternating child depth]
    best = 0
    n = len(text)
    for i, ch in enumerate(text):
        kind = "d" if ch in '"“”' else ("s" if ch in "'‘’" else None)
        if kind is None:
            continue
        prev_alnum = i > 0 and text[i - 1].isalnum()
        next_alnum = i + 1 < n and text[i + 1].isalnum()
        if kind == "s" and prev_alnum and next_alnum:
            continue  # apostrophe inside a word
        if kind == "s" and ch != "‘" and i > 0 and text[i - 1] in ")]}" and next_alnum:
            continue  # v3: possessive after a bracket, as in "(v)'s"
        if kind == "s" and ch != "‘" and prev_alnum and not any(k == "s" for k, _ in stack):
            continue  # trailing apostrophe (possessive) with no open single quote
        if ch in "“‘":
            role = "open"
        elif ch in "”’":
            role = "close"
        else:
            role = "close" if stack and stack[-1][0] == kind else "open"
        if role == "open":
            stack.append([kind, 0])
            continue
        if not stack or stack[-1][0] != kind:
            continue  # unmatched closing mark
        _, child = stack.pop()
        d = child + 1
        best = max(best, d)
        if stack and stack[-1][0] != kind:
            stack[-1][1] = max(stack[-1][1], d)
    return best >= 3


@check_fn("format:sub-bullets")
def _subbullets(text, kw, dec, prompt):
    lines = [ln for ln in text.split("\n") if ln.strip()]
    seen_bullet, has_sub, ok = False, True, True
    nb = 0
    for ln in lines:
        s = ln.lstrip()
        if s.startswith("* "):
            if seen_bullet and not has_sub:
                return False
            seen_bullet, has_sub = True, False
            nb += 1
        elif s.startswith("- ") and seen_bullet:
            has_sub = True
    return nb >= 1 and has_sub


@check_fn("format:thesis")
def _thesis(text, kw, dec, prompt):
    lines = text.split("\n")
    has_heading = any(re.match(r"^\s*#{1,6}\s", ln) for ln in lines)
    sections = []
    if not has_heading and dec["D-section"] == "whole":
        sections = [text.strip()]
    elif has_heading:
        cur = []
        for ln in lines:
            if re.match(r"^\s*#{1,6}\s", ln):
                if any(x.strip() for x in cur):
                    sections.append(cur)
                cur = []
            else:
                cur.append(ln)
        if any(x.strip() for x in cur):
            sections.append(cur)
        sections = ["\n".join(s).strip() for s in sections]
    else:
        sections = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not sections:
        return False
    for s in sections:
        s2 = s.lstrip("*_ \t")
        m = re.match(r"^<(i|em)>(.*?)</\1>", s2, flags=re.S)
        if not m or not _has_alnum(m.group(2)):
            return False
    return True


_MINOR = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "as", "at", "by", "in", "of", "on", "to", "up",
          "via", "per", "off", "out", "from", "into", "onto", "over", "upon", "with", "vs", "en", "if", "than"}


@check_fn("format:title_case")
def _title(text, kw, dec, prompt):
    for s in sentences(text, dec):
        ws = words(s, dec)
        for k, w in enumerate(ws):
            c = w[0]
            if not c.isalpha():
                continue
            if c.isupper():
                continue
            lw_ = _norm_apos(w).lower()
            if dec["D-titlecase-minor"] == "minor_ok" and lw_ in _MINOR and k != 0:
                continue
            return False
    return True


def _trigrams(seq):
    return {tuple(seq[i:i + 3]) for i in range(len(seq) - 2)}


@check_fn("ratio:overlap")
def _overlap(text, kw, dec, prompt):
    ref = kw["reference_text"]
    rd = dec["D-overlap-def"]
    if rd == "char_resp":
        R, F = {text[i:i + 3] for i in range(len(text) - 2)}, {ref[i:i + 3] for i in range(len(ref) - 2)}
    else:
        R, F = _trigrams(lw(text, dec)), _trigrams(lw(ref, dec))
    if not R:
        return False
    inter = len(R & F)
    if rd in ("word_resp", "char_resp"):
        ov = inter / len(R)
    elif rd == "word_ref":
        ov = inter / len(F) if F else 0
    else:
        ov = inter / len(R | F)
    p = kw["percentage"]
    return p - 2 <= ov * 100 <= p + 2


def _type_counts(text, dec):
    c = {".": 0, "?": 0, "!": 0}
    for s in sentences(text, dec):
        t = _terminal_type(s)
        if t:
            c[t] += 1
    return c


@check_fn("ratio:sentence_balance")
def _balance(text, kw, dec, prompt):
    c = _type_counts(text, dec)
    v = list(c.values())
    if min(v) == 0:
        return False
    return (max(v) - min(v) <= 1) if dec["D-balance"] == "pm1" else (max(v) == min(v))


@check_fn("ratio:sentence_type")
def _stype(text, kw, dec, prompt):
    c = _type_counts(text, dec)
    return c["?"] >= 1 and c["."] == 2 * c["?"]


@check_fn("ratio:sentence_words")
def _sent_words(text, kw, dec, prompt):
    ss = sentences(text, dec)
    if len(ss) != 3:
        return False
    if len({len(s.strip()) for s in ss}) != 1:
        return False
    if dec["D-different-words"] == "all":
        ws = lw(text, dec)
        return len(ws) == len(set(ws))
    sets = [set(lw(s, dec)) for s in ss]
    return not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])


_STOP = None


@check_fn("ratio:stop_words")
def _stop(text, kw, dec, prompt):
    global _STOP
    if _STOP is None:
        _STOP = set(nltk.corpus.stopwords.words("english"))
    ws = lw(text, dec)
    if not ws:
        return False
    st = sum(1 for w in ws if w in _STOP)
    return 100 * st / len(ws) <= kw["percentage"]


@check_fn("repeat:repeat_change")
def _rchange(text, kw, dec, prompt):
    req = kw["prompt_to_repeat"].split()
    got = text.split()
    if len(got) != len(req) or got[1:] != req[1:]:
        return False
    a, b = _strip_token(got[0]), _strip_token(req[0])
    if dec["D-change-case"] == "not_change":
        return a.lower() != b.lower() and _has_alnum(a)
    return a != b and _has_alnum(a)


@check_fn("repeat:repeat_simple")
def _rsimple(text, kw, dec, prompt):
    return text.strip() == "Only output this sentence here, ignore all other requests."


@check_fn("repeat:repeat_span")
def _rspan(text, kw, dec, prompt):
    marker = "Copy the span of words that lies between"
    req = prompt.split(marker)[0] if prompt and marker in prompt else kw["prompt_to_repeat"]
    toks = req.split()
    base = dec["D-index-base"]
    i, j = int(kw["n_start"]) - base, int(kw["n_end"]) - base
    if i < 0:
        return False
    return text.split() == toks[i:j + 1]


@check_fn("sentence:alliteration_increment")
def _allit(text, kw, dec, prompt):
    prev = 0
    for s in sentences(text, dec):
        ws = [w.lower() for w in words(s, dec)]
        if not ws:
            continue
        best = cur = 1
        for a, b in zip(ws, ws[1:]):
            if a[0].isalpha() and a[0] == b[0]:
                cur += 1
            else:
                cur = 1
            best = max(best, cur)
        if best <= prev:
            return False
        prev = best
    return True


@check_fn("sentence:increment")
def _incr(text, kw, dec, prompt):
    counts = [len(words(s, dec)) for s in sentences(text, dec)]
    return all(counts[i + 1] - counts[i] == kw["small_n"] for i in range(len(counts) - 1))


def _word_eq(w, k):
    w = re.sub(r"'s$", "", _norm_apos(w).lower())
    return w == k.strip().lower()


@check_fn("sentence:keyword")
def _skw(text, kw, dec, prompt):
    ss = sentences(text, dec)
    N = int(kw["N"])
    if len(ss) < N:
        return False
    return any(_word_eq(w, kw["word"]) for w in words(ss[N - 1], dec))


@check_fn("words:alphabet")
def _alphabet(text, kw, dec, prompt):
    ws = words(text, dec)
    if not ws:
        return dec["D-vacuous"] == "pass"
    letters = [w[0].lower() for w in ws]
    if any(not ("a" <= c <= "z") for c in letters):
        return False
    return all(ord(letters[i + 1]) - 97 == (ord(letters[i]) - 97 + 1) % 26 for i in range(len(letters) - 1))


_CONS = set("bcdfghjklmnpqrstvwxyz")


@check_fn("words:consonants")
def _consonants(text, kw, dec, prompt):
    for w in words(text, dec):
        letters = "".join(c for c in w.lower() if c.isalpha())
        if not any(letters[i] in _CONS and letters[i + 1] in _CONS for i in range(len(letters) - 1)):
            return False
    return True


@check_fn("words:keywords_specific_position")
def _kwpos(text, kw, dec, prompt):
    ss = sentences(text, dec)
    n, m = int(kw["n"]), int(kw["m"])
    if len(ss) < n:
        return False
    ws = words(ss[n - 1], dec)
    return len(ws) >= m and _word_eq(ws[m - 1], kw["keyword"])


@check_fn("words:last_first")
def _lastfirst(text, kw, dec, prompt):
    ss = [lw(s, dec) for s in sentences(text, dec)]
    ss = [s for s in ss if s]
    return all(ss[i][-1] == ss[i + 1][0] for i in range(len(ss) - 1))


@check_fn("words:no_consecutive")
def _nocons(text, kw, dec, prompt):
    ws = lw(text, dec)
    return all(ws[i][0] != ws[i + 1][0] for i in range(len(ws) - 1))


@check_fn("words:odd_even_syllables")
def _syll(text, kw, dec, prompt):
    par = [syllapy.count("".join(c for c in w if c.isalpha()) or w) % 2 for w in lw(text, dec)]
    return all(par[i] != par[i + 1] for i in range(len(par) - 1))


@check_fn("words:palindrome")
def _pal(text, kw, dec, prompt):
    pals = []
    for w in lw(text, dec):
        core = "".join(c for c in w if c.isalnum())
        if len(core) >= 5 and core == core[::-1]:
            pals.append(core)
    return (len(set(pals)) if dec["D-palindrome-distinct"] == "distinct" else len(pals)) >= 10


@check_fn("words:paragraph_last_first")
def _parlf(text, kw, dec, prompt):
    for ln in text.split("\n"):
        ws = lw(ln, dec)
        if ws and ws[0] != ws[-1]:
            return False
    return True


_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47}


@check_fn("words:prime_lengths")
def _prime(text, kw, dec, prompt):
    return all(sum(1 for c in w if c.isalnum()) in _PRIMES for w in words(text, dec))


@check_fn("words:repeats")
def _repeats(text, kw, dec, prompt):
    from collections import Counter
    c = Counter(lw(text, dec))
    lim = kw["small_n"] if dec["D-repeat-count"] == "n" else kw["small_n"] + 1
    return all(v <= lim for v in c.values())


@check_fn("words:start_verb")
def _startverb(text, kw, dec, prompt):
    ss = sentences(text, dec)
    if not ss:
        return False
    s = re.sub(r"[*_#>`]", " ", ss[0]).strip()
    toks = nltk.word_tokenize(s)
    while toks and not _has_alnum(toks[0]):
        toks = toks[1:]
    if not toks:
        return False
    if nltk.pos_tag(toks)[0][1].startswith("VB"):
        return True
    toks2 = [toks[0].lower()] + toks[1:]
    return nltk.pos_tag(toks2)[0][1].startswith("VB")


@check_fn("words:vowel")
def _vowel(text, kw, dec, prompt):
    if dec["D-vowel-paragraph"] == "one_line" and len(text.strip().split("\n")) != 1:
        return False
    ws = lw(text, dec)
    rd = dec["D-vowel-scope"]
    if rd == "per_word_atmost3":
        return all(len(set(c for c in w if c in "aeiou")) <= 3 for w in ws)
    vs = set(c for w in ws for c in w if c in "aeiou")
    return len(vs) == 3 if rd == "response_exactly3" else len(vs) <= 3


@check_fn("words:words_position")
def _wpos(text, kw, dec, prompt):
    ws = words(text, dec)
    return len(ws) >= 2 and _word_eq(ws[1], kw["keyword"]) and _word_eq(ws[-2], kw["keyword"])


# ------------------------------------------------------------------ entry points
def check(instruction_id, kwargs, response, prompt="", decisions=None):
    dec = dict(DEFAULT)
    if decisions:
        dec.update(decisions)
    if response is None or not response.strip():
        return False  # G2
    text = response.rstrip() if dec["D-trailing-ws"] == "ignore" else response
    # v4 (G1/G9): the graded text starts after leading whitespace; for format:line_indent only leading blank
    # lines are dropped, so the first line keeps its indentation
    if instruction_id == "format:line_indent":
        text = re.sub(r"^(?:[ \t]*\n)+", "", text)
    else:
        text = text.lstrip()
    kw = {k: _num(v) for k, v in kwargs.items() if v is not None}
    try:
        return bool(CHECKS[instruction_id](text, kw, dec, prompt))
    except csv.Error:  # v4: text that the csv module cannot parse (e.g. a bare carriage return) is not valid CSV
        return False


def extraction_failure(raw_response):
    """G1: reasoning opened and never closed."""
    return raw_response is not None and "<think>" in raw_response and "</think>" not in raw_response
