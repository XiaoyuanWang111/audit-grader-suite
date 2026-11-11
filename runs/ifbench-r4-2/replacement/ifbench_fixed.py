"""Replacement IFBench grader built from audit/CONTRACTS.md.

check(iid, kwargs, response, prompt, opts) -> bool

Checks without a finding delegate to the grader's own checker class, so the
replacement differs from the grader only where a finding or a decision switch
applies. Two option profiles:

  FIX       every finding fixed; each decision set to the reading the grader uses
            (where the grader's behaviour is a reading at all)
  PROPOSED  every finding fixed; each implemented decision set to the proposed
            reading of CONTRACTS.md

Decision switches (opts keys) and the entry they implement:
  trim D-trim, sentence D-sentence, word D-word, keyword D-keyword-match,
  palindrome D-palindrome, repeats D-repeats, overlap D-overlap-def, vowel D-vowel,
  options D-options, plural D-plural, balance D-balance, section D-section,
  nbb D-nbb-order, stairs D-stairs-blank, csv_wrap D-csv-wrap, special D-special,
  complete D-custom-content, change_case D-change-case, simple_case D-simple-case,
  punct D-punct-set, number D-number, list_place D-list-placement,
  bullet D-bullet-syntax.
Not implemented (the grader's reading is kept in both profiles): D-conj-role,
D-pronoun-set, D-name-case, D-unique, D-emoji-position, D-japanese-words,
D-titlecase, D-paren-types, D-quote-chars, D-explanation, D-subbullet-indent,
D-sw-chars, D-sw-words (A in both), D-stopwords, D-index-base (A), D-alliteration
(A), D-consonant-y (A), D-syllables, D-verb, D-reverse-form, D-mcq-length,
D-vacuous (A), D-empty (A), D-whitespace (A), D-template-markup (A).
"""
import csv
import io
import re
import string
import sys
import unicodedata
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
import harness as H  # noqa: E402  (sets NLTK_DATA, blocks downloads)

import nltk  # noqa: E402
import syllapy  # noqa: E402

G_REG = H.G_REG.INSTRUCTION_DICT
ASCII_PUNCT = string.punctuation
_TR = str.maketrans("", "", ASCII_PUNCT)

FIX = dict(trim=False, sentence="punkt", word="grader", keyword="exact", palindrome="occurrences",
           repeats="n", overlap="char", vowel="le3", options="exact", plural=1, balance="equal",
           section="whole", nbb="strict", stairs="ignore", csv_wrap="strict", special="atleast",
           complete=True, change_case="sensitive", simple_case="insensitive", punct="six", number="grader",
           list_place="anywhere", bullet="loose")
PROPOSED = dict(trim=True, sentence="lines", word="g4", keyword="exact", palindrome="distinct",
                repeats="n", overlap="word", vowel="eq3", options="starts", plural=2, balance="within1",
                section="blocks", nbb="lenient", stairs="ignore", csv_wrap="fence", special="exact",
                complete=False, change_case="insensitive", simple_case="sensitive", punct="fifteen",
                number="split", list_place="line", bullet="space")


# ------------------------------------------------------------------ helpers
def _is_alnum(ch):
    return unicodedata.category(ch)[0] in ("L", "N")


def strip_edges(tok):
    i, j = 0, len(tok)
    while i < j and not _is_alnum(tok[i]):
        i += 1
    while j > i and not _is_alnum(tok[j - 1]):
        j -= 1
    return tok[i:j]


def g4_words(text):
    """G4: whitespace tokens, edge punctuation/symbols removed, empty dropped."""
    out = []
    for tok in text.replace("’", "'").split():
        w = strip_edges(tok)
        if w:
            out.append(w)
    return out


def fix_tokens(text, lower=True):
    """The grader's tokenization (ASCII punctuation removed) minus symbol-only tokens."""
    t = text.lower() if lower else text
    out = []
    for tok in t.translate(_TR).split():
        w = strip_edges(tok)
        if w:
            out.append(w)
    return out


def sentences(text, opts):
    if opts["sentence"] == "lines":
        out = []
        for line in text.split("\n"):
            if line.strip():
                out.extend(nltk.sent_tokenize(line.strip()))
        return out
    return nltk.sent_tokenize(text)


def count_words(text, opts):
    if opts["word"] == "g4":
        return len(g4_words(text))
    return len(nltk.tokenize.RegexpTokenizer(r"\w+").tokenize(text))


def _grader(iid, kwargs, response, prompt):
    inst = G_REG[iid](iid)
    filtered = {k: v for k, v in kwargs.items() if v is not None}
    inst.build_description(**filtered)
    args = inst.get_instruction_args()
    if args and "prompt" in args:
        inst.build_description(prompt=prompt)
    return inst.check_following(response)


def _kw_count(keyword, text, opts):
    pat = r"\b{}\b".format(re.escape(keyword))
    if opts["keyword"] == "inflect":
        pat = r"\b{}(?:s|es|ed|d|ing)?\b".format(re.escape(keyword))
    return len(re.findall(pat, text, flags=re.IGNORECASE))


# ------------------------------------------------------------------ checks
CHECKS = {}


def chk(iid):
    def deco(fn):
        CHECKS[iid] = fn
        return fn
    return deco


@chk("count:conjunctions")
def _conj(kw, r, p, o):
    conj = {"and", "but", "for", "nor", "or", "so", "yet"}
    found = {w.lower() for w in fix_tokens(r) if w.lower() in conj}
    return len(found) >= kw["small_n"]


@chk("count:keywords_multiple")
def _kwm(kw, r, p, o):
    for k, n in zip([kw[f"keyword{i}"] for i in range(1, 6)], [1, 2, 3, 5, 7]):
        if _kw_count(k.strip(), r, o) != n:
            return False
    return True


_NUM_SPLIT = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


@chk("count:numbers")
def _numbers(kw, r, p, o):
    text = r
    if o["number"] == "grader":
        # keep the grader's single-number reading of dates, times and fractions
        text = re.sub(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", r"\1\2\3", text)
        text = re.sub(r"\b(\d{1,2}):(\d{2})\b", r"\1\2", text)
        text = re.sub(r"\b(\d+)/(\d+)\b", r"\1\2", text)
    return len(_NUM_SPLIT.findall(text)) == kw["N"]


@chk("count:unique_word_count")
def _unique(kw, r, p, o):
    return len(set(fix_tokens(r))) >= kw["N"]


@chk("count:word_count_range")
def _wcr(kw, r, p, o):
    n = count_words(r, o)
    return kw["min_words"] <= n <= kw["max_words"]


@chk("ratio:stop_words")
def _stop(kw, r, p, o):
    if o["word"] == "g4":
        words = [w.lower() for w in g4_words(r)]
    else:
        words = [w.lower() for w in nltk.tokenize.RegexpTokenizer(r"\w+").tokenize(r)]
    if not words:
        return False
    sw = set(nltk.corpus.stopwords.words("english"))
    return 100 * sum(1 for w in words if w in sw) / len(words) <= kw["percentage"]


@chk("count:words_japanese")
def _jp(kw, r, p, o):
    n = kw["N"]
    jp = re.compile(r"[぀-ヿ一-鿿]")
    for i, tok in enumerate(r.split()):
        w = tok.strip(ASCII_PUNCT + " ")
        if (i + 1) % n == 0 and w and not jp.search(w):
            return False
    return True


@chk("count:punctuation")
def _punct(kw, r, p, o):
    if o["punct"] == "six":
        return _grader("count:punctuation", kw, r, p)
    t = r
    if not ("?!" in t or "!?" in t or "‽" in t):
        return False
    t2 = t.replace("?!", "", 1) if "?!" in t else t.replace("!?", "", 1)
    need = {
        "period": re.search(r"(?<!\.)\.(?!\.)", t2), "comma": "," in t2, "question": "?" in t2,
        "exclamation": "!" in t2, "colon": ":" in t2, "semicolon": ";" in t2,
        "apostrophe": re.search(r"['’]", t2), "quote": re.search(r"[\"“”]", t2),
        "hyphen": "-" in t2, "dash": re.search(r"[–—]|--", t2),
        "parens": "(" in t2 and ")" in t2, "brackets": "[" in t2 and "]" in t2,
        "braces": "{" in t2 and "}" in t2, "ellipsis": "..." in t2 or "…" in t2,
    }
    return all(bool(v) for v in need.values())


@chk("format:emoji")
def _emoji(kw, r, p, o):
    if o["sentence"] == "punkt":
        return _grader("format:emoji", kw, r, p)
    import emoji as E
    ss = sentences(r, o)
    for i, s in enumerate(ss):
        st = s.translate(_TR).strip()
        if not st:
            return False
        last = st[-1]
        second = st[-2] if len(st) > 1 else st[-1]
        if not E.is_emoji(last) and not E.is_emoji(second):
            if i < len(ss) - 1:
                nx = ss[i + 1].translate(_TR).strip()
                if not nx or not E.is_emoji(nx[0]):
                    return False
            else:
                return False
    return True


@chk("format:line_indent")
def _indent(kw, r, p, o):
    lines = r.split("\n")
    if o["stairs"] == "ignore":
        lines = [ln for ln in lines if ln.strip()]
    else:
        while lines and not lines[-1].strip():
            lines.pop()
    for a, b in zip(lines, lines[1:]):
        if not b.strip():
            return False
        ia = len(a) - len(a.lstrip())
        ib = len(b) - len(b.lstrip())
        if ib <= ia:
            return False
    return True


_BULLET = re.compile(r"^\s*(?:[*•]\s|-\s|\d+[.)]\s)")


@chk("format:list")
def _list(kw, r, p, o):
    sep = kw["sep"]
    items = 0
    for line in r.split("\n"):
        s = re.sub(r"^[*_]{2,3}(?=\S)", "", line.lstrip())  # bold wrapper around the marker
        if s.startswith(sep):
            items += 1
        elif sep != "-" and re.match(r"^(?:[*•]|-)\s", s):
            return False  # standard bullet points used
    if o.get("list_place", "line") == "anywhere":
        # D-list-placement B: SEP may also separate items inside a line; a hyphen
        # inside a word is never an item separator
        if sep == "-":
            inline = len(re.findall(r"(?<=\S)\s+-(?=\s)", r))
            items = items + inline
        else:
            items = r.count(sep)
    return items >= max(2, o["plural"])


@chk("format:newline")
def _newline(kw, r, p, o):
    for line in r.split("\n"):
        toks = fix_tokens(line)
        if len(toks) > 1:
            return False
    return len(fix_tokens(r)) > 0


_BULLET_MODE = {"mode": "space"}  # set per call from opts["bullet"] (D-bullet-syntax)


def _is_star_bullet(line):
    s = line.lstrip()
    if not s.startswith("*") or s.startswith("**") or len(s) < 2:
        return False
    return s[1] in " \t" if _BULLET_MODE["mode"] == "space" else not s[1].isspace() or s[1] in " \t"


def _is_dash_bullet(line):
    s = line.lstrip()
    if not s.startswith("-") or s.startswith("--") or len(s) < 2:
        return False
    return s[1] in " \t" if _BULLET_MODE["mode"] == "space" else True


@chk("format:no_bullets_bullets")
def _nbb(kw, r, p, o):
    lines = r.split("\n")
    period_sents = 0
    seen_bullets = 0
    for line in lines:
        if not line.strip():
            continue
        if _is_star_bullet(line):
            if period_sents >= 2:
                seen_bullets += 1
            elif seen_bullets == 0:
                return False
            continue
        if seen_bullets > 0:
            if o["nbb"] == "strict":
                return False
            continue
        if re.match(r"^\s*(?:[-•+]\s|\d+[.)]\s|[IVXLC]+\.\s|[A-Za-z][.)]\s|#)", line):
            continue  # outline items and headings are not the requested sentences
        for s in nltk.sent_tokenize(line.strip()):
            if s.rstrip(" \"'”)").endswith(".") and len(g4_words(s)) >= 2:
                period_sents += 1
    return seen_bullets >= 2


@chk("format:no_whitespace")
def _nows(kw, r, p, o):
    return not any(c.isspace() for c in r)


@chk("format:options")
def _options(kw, r, p, o):
    opts_text = kw["options"]
    text = r.replace("’", "'").replace("‘", "'")
    if o["options"] == "exact":
        if re.match(r"\W*[aA]\W*[bB]\W*[cC]\W*", opts_text) is not None:
            return text in [x.strip() for x in opts_text.split(",")]
        if "/" in opts_text:
            options = [x.strip() for x in opts_text.split("/")]
        elif "or" in opts_text:
            options = [x.strip() for x in opts_text.split("or")]
        else:
            options = [x.strip() for x in opts_text.split(",")]
        v = text.strip(ASCII_PUNCT + " ").lower()
        return any(x.strip(ASCII_PUNCT + " ").lower() == v for x in options)
    # proposed: starts with exactly one option, explanation allowed
    t = re.sub(r"^[\s*_#>`]+", "", text).strip()
    tl = t.lower()
    if re.match(r"\W*[aA]\W*[bB]\W*[cC]\W*", opts_text) is not None:
        m = re.match(r"^\(?([a-dA-D])(?:[).:]|\s|$)", t)
        return m is not None
    if "/" in opts_text:
        options = [x.strip().lower() for x in opts_text.split("/")]
    else:
        options = [x.strip().lower() for x in re.split(r"\bor\b", opts_text)]
    hits = [x for x in options if re.match(r"^" + re.escape(x) + r"(?![a-z'])", tl)]
    if len(hits) != 1:
        return False
    # restating the option list ("yes/no", "I know or I don't know") selects no single option
    for a in options:
        for b in options:
            if a != b and re.search(re.escape(a) + r"\s*(?:/|\bor\b|,)\s*" + re.escape(b) + r"(?![a-z'])", tl):
                return False
    return True


@chk("format:output_template")
def _template(kw, r, p, o):
    labels = ["My Answer:", "My Conclusion:", "Future Outlook:"]
    t = r.strip()
    plain = re.sub(r"[*_]{1,3}(My Answer:|My Conclusion:|Future Outlook:)[*_]{0,3}", r"\1", t)
    plain = re.sub(r"^#+\s*", "", plain, flags=re.M)
    if not plain.startswith("My Answer:"):
        return False
    pos = []
    for lab in labels:
        if plain.count(lab) != 1:
            return False
        pos.append(plain.index(lab))
    if pos != sorted(pos):
        return False
    bounds = pos + [len(plain)]
    for i, lab in enumerate(labels):
        body = plain[bounds[i] + len(lab):bounds[i + 1]].strip(" \n*_")
        if not body or re.fullmatch(r"\[(answer|conclusion|outlook)\]", body):
            return False
    return True


@chk("format:parentheses")
def _parens(kw, r, p, o):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []  # [char, max child depth]
    for ch in r:
        if ch in "([{":
            stack.append([ch, 0])
        elif ch in ")]}":
            if stack and stack[-1][0] == pairs[ch]:
                _, child = stack.pop()
                depth = child + 1
                if depth >= 5:
                    return True
                if stack:
                    stack[-1][1] = max(stack[-1][1], depth)
            # unmatched closer: ignored
    return False


def _quote_marks(text):
    """Yield (index, family, kind) for quote marks; kind in open/close/either.
    Apostrophes between letters (or after a letter, before a space, with no open
    single quote) are skipped by the caller's logic."""
    out = []
    n = len(text)
    for i, ch in enumerate(text):
        prev = text[i - 1] if i > 0 else " "
        nxt = text[i + 1] if i + 1 < n else " "
        if ch in "\"":
            out.append((i, "d", "either"))
        elif ch == "“":
            out.append((i, "d", "open"))
        elif ch == "”":
            out.append((i, "d", "close"))
        elif ch in "'‘’":
            if _is_alnum(prev) and _is_alnum(nxt):
                continue  # apostrophe inside a word
            if ch == "‘":
                out.append((i, "s", "open"))
            elif _is_alnum(prev) or prev in ".,!?;:":
                out.append((i, "s", "close_or_apos"))
            else:
                out.append((i, "s", "either"))  # closes an open single quote, else opens one
    return out


@chk("format:quotes")
def _quotes(kw, r, p, o):
    stack = []  # [family, child depth]
    for _, fam, kind in _quote_marks(r):
        top = stack[-1] if stack else None
        if kind in ("close", "close_or_apos", "either") and top is not None and top[0] == fam:
            stack.pop()
            depth = top[1] + 1
            if depth >= 3:
                return True
            if stack and stack[-1][0] != fam:
                stack[-1][1] = max(stack[-1][1], depth)
            continue
        if kind == "close_or_apos":
            continue  # an apostrophe after a word with no open single quote
        if kind in ("open", "either"):
            stack.append([fam, 0])
    return False


@chk("format:quote_unquote")
def _quote_unquote(kw, r, p, o):
    t = r.replace("'\"'", "")
    spans = []
    i, n = 0, len(t)
    open_map = {"\"": "\"", "“": "”", "«": "»"}
    while i < n:
        ch = t[i]
        if ch in open_map:
            j = t.find(open_map[ch], i + 1)
            if j == -1:
                break
            spans.append((i, j))
            i = j + 1
        else:
            i += 1
    for k, (a, b) in enumerate(spans):
        end = spans[k + 1][0] if k + 1 < len(spans) else n
        if not re.search(r"[^\W\d_]", t[b + 1:end]):
            return False
    return True


@chk("format:sub-bullets")
def _subbullets(kw, r, p, o):
    lines = r.split("\n")
    bullets = 0
    current_has_sub = None
    for line in lines:
        if _is_star_bullet(line):
            if current_has_sub is False:
                return False
            bullets += 1
            current_has_sub = False
        elif _is_dash_bullet(line) and current_has_sub is not None:
            current_has_sub = True
    if current_has_sub is False:
        return False
    return bullets >= o["plural"]


@chk("format:thesis")
def _thesis(kw, r, p, o):
    lines = r.strip().split("\n")
    heads = [i for i, ln in enumerate(lines)
             if re.match(r"^\s*#{1,6}\s", ln) or re.match(r"^\s*<h[1-6][^>]*>.*</h[1-6]>\s*$", ln)]
    if heads:
        bounds = heads + [len(lines)]
        sections = [lines[a + 1:b] for a, b in zip(bounds, bounds[1:])]
        if heads[0] > 0 and any(ln.strip() for ln in lines[:heads[0]]):
            sections.insert(0, lines[:heads[0]])
        if o["section"] == "whole":
            sections = sections[:1]
    else:
        text = "\n".join(lines)
        if o["section"] == "blocks":
            sections = [blk.split("\n") for blk in re.split(r"\n\s*\n", text) if blk.strip()]
        else:
            sections = [lines]
    sections = [s for s in sections if any(ln.strip() for ln in s)]
    if not sections:
        return False
    for sec in sections:
        body = "\n".join(sec).strip()
        # block wrappers and emphasis before the italic element are not text
        prev = None
        while prev != body:
            prev = body
            body = re.sub(r"^(?:<(?:html|body|main|header|p|div|blockquote|section|article|span|br)\b[^>]*>"
                          r"|[*_]{1,3}(?=<))\s*", "", body)
        m = re.match(r"^<(i|em)>(.*?)</\1>", body, flags=re.S)
        if not m or not re.search(r"[^\W\d_]", m.group(2)):
            return False
    return True


_MINOR = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "as", "at", "by", "in", "of",
          "off", "on", "per", "to", "up", "via", "from", "into", "onto", "over", "with", "upon", "than",
          "like", "near", "past", "till", "vs", "v", "en", "out"}


@chk("format:title_case")
def _title(kw, r, p, o):
    for tok in r.split():
        w = strip_edges(tok.replace("’", "'"))
        if not w or not w[0].isalpha():
            continue
        if w.lower() in _MINOR:
            continue
        if not w[0].isupper():
            return False
    return True


@chk("ratio:overlap")
def _overlap(kw, r, p, o):
    if o["overlap"] == "char":
        return _grader("ratio:overlap", kw, r, p)
    def tri(s):
        toks = [w.lower() for w in g4_words(s)]
        return set(zip(toks, toks[1:], toks[2:]))
    a, b = tri(r), tri(kw["reference_text"])
    if not a:
        return False
    v = 100 * len(a & b) / len(a)
    return kw["percentage"] - 2 <= v <= kw["percentage"] + 2


def _sent_types(r, o):
    ss = sentences(r, o)
    def term(s):
        s2 = s.rstrip(" \"'”’)*_")
        return s2[-1:] if s2 else ""
    ends = [term(s) for s in ss]
    return ends.count("."), ends.count("?"), ends.count("!"), len(ss)


@chk("ratio:sentence_type")
def _stype(kw, r, p, o):
    d, q, e, n = _sent_types(r, o)
    return q >= 1 and d == 2 * q


@chk("ratio:sentence_balance")
def _sbal(kw, r, p, o):
    d, q, e, n = _sent_types(r, o)
    if min(d, q, e) < 1:
        return False
    if o["balance"] == "equal":
        return d == q == e
    return max(d, q, e) - min(d, q, e) <= 1


@chk("ratio:sentence_words")
def _sw(kw, r, p, o):
    ss = sentences(r, o)
    if len(ss) != 3:
        return False
    if len({len(s.strip()) for s in ss}) != 1:
        return False
    words = fix_tokens(" ".join(ss))
    return len(words) == len(set(words))


@chk("repeat:repeat_change")
def _rchange(kw, r, p, o):
    req = kw["prompt_to_repeat"]
    a, b = req.split(), r.split()
    if not a or not b or a[1:] != b[1:]:
        return False
    if o["change_case"] == "insensitive":
        return a[0].lower() != b[0].lower()
    return a[0] != b[0]


@chk("repeat:repeat_simple")
def _rsimple(kw, r, p, o):
    target = "Only output this sentence here, ignore all other requests."
    if o["simple_case"] == "insensitive":
        return r.strip().lower() == target.lower()
    return r.strip() == target


@chk("repeat:repeat_span")
def _rspan(kw, r, p, o):
    words = kw["prompt_to_repeat"].split()
    expected = " ".join(words[int(kw["n_start"]):int(kw["n_end"]) + 1])
    return r.strip().lower() == expected.strip().lower()


@chk("sentence:alliteration_increment")
def _allit(kw, r, p, o):
    prev = -1
    for s in sentences(r, o):
        words = [w.lower() for w in g4_words(s)]
        best, run = (1 if words else 0), 1
        for x, y in zip(words, words[1:]):
            run = run + 1 if x[0] == y[0] else 1
            best = max(best, run)
        if best <= prev:
            return False
        prev = best
    return True


@chk("sentence:increment")
def _incr(kw, r, p, o):
    ss = sentences(r, o)
    if not ss:
        return False
    counts = [len(fix_tokens(s)) for s in ss]
    return all(b == a + kw["small_n"] for a, b in zip(counts, counts[1:]))


@chk("sentence:keyword")
def _skw(kw, r, p, o):
    ss = sentences(r, o)
    n = int(kw["N"])
    if len(ss) < n:
        return False
    return _kw_count(kw["word"], ss[n - 1], o) > 0


@chk("words:keywords_specific_position")
def _kwpos(kw, r, p, o):
    ss = sentences(r, o)
    n, m = int(kw["n"]), int(kw["m"])
    if len(ss) < n:
        return False
    if o["word"] == "g4":
        words = g4_words(ss[n - 1])
    else:
        words = [t for t in nltk.word_tokenize(ss[n - 1]) if any(c.isalnum() for c in t)]
    return len(words) >= m and words[m - 1].lower() == kw["keyword"].strip().lower()


@chk("words:last_first")
def _lastfirst(kw, r, p, o):
    ss = sentences(r, o)
    for a, b in zip(ss, ss[1:]):
        wa, wb = g4_words(a), g4_words(b)
        if not wa or not wb or wa[-1].lower() != wb[0].lower():
            return False
    return True


@chk("words:alphabet")
def _alpha(kw, r, p, o):
    words = fix_tokens(r)
    if not words:
        return False
    abc = string.ascii_lowercase
    cur = words[0][0]
    if cur not in abc:
        return False
    for w in words[1:]:
        cur = abc[(abc.index(cur) + 1) % 26]
        if w[0] != cur:
            return False
    return True


@chk("words:consonants")
def _cons(kw, r, p, o):
    cons = set("bcdfghjklmnpqrstvwxyz")
    for w in fix_tokens(r):
        if not any(a in cons and b in cons for a, b in zip(w, w[1:])):
            return False
    return True


@chk("words:no_consecutive")
def _nocons(kw, r, p, o):
    words = fix_tokens(r)
    return all(a[0] != b[0] for a, b in zip(words, words[1:]))


_SYL_OVERRIDE = {"duo": 2, "trio": 2, "neon": 2, "violin": 3, "crayon": 2, "naive": 2, "reuse": 2, "rodeo": 3,
                 "aorta": 3, "zoology": 4, "gradual": 3, "simile": 3, "apostrophe": 4, "coexist": 3,
                 "reenter": 3, "preexisting": 4}
_NT_ONE = {"don't": 1, "can't": 1, "won't": 1, "ain't": 1, "aren't": 1, "weren't": 1, "shan't": 1}


def syllables(word):
    w = word.lower().replace("’", "'")
    if w in _NT_ONE:
        return _NT_ONE[w]
    if w.endswith("n't") and len(w) > 3:
        return syllables(w[:-3]) + 1
    w2 = w.translate(_TR)
    if w2 in _SYL_OVERRIDE:
        return _SYL_OVERRIDE[w2]
    return syllapy.count(w2)


@chk("words:odd_even_syllables")
def _syl(kw, r, p, o):
    words = g4_words(r)
    par = [syllables(w) % 2 for w in words]
    return all(a != b for a, b in zip(par, par[1:]))


@chk("words:palindrome")
def _pal(kw, r, p, o):
    words = fix_tokens(r)
    pals = [w for w in words if w == w[::-1] and len(w) >= 5]
    if o["palindrome"] == "distinct":
        pals = set(pals)
    return len(pals) >= 10


@chk("words:paragraph_last_first")
def _para(kw, r, p, o):
    for line in r.split("\n"):
        words = [w.lower() for w in g4_words(line)]
        if words and words[0] != words[-1]:
            return False
    return True


_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97}


@chk("words:prime_lengths")
def _prime(kw, r, p, o):
    return all(len(w) in _PRIMES for w in fix_tokens(r, lower=False))


@chk("words:repeats")
def _repeats(kw, r, p, o):
    from collections import Counter
    lim = kw["small_n"] + (1 if o["repeats"] == "n+1" else 0)
    return all(c <= lim for c in Counter(fix_tokens(r)).values())


@chk("words:start_verb")
def _verb(kw, r, p, o):
    t = re.sub(r"^[\s#>*_`\"'“‘(\[-]+", "", r)
    t = re.sub(r"^\d+[.)]\s+", "", t)
    t = re.sub(r"[*_`]", "", t)  # markdown emphasis is not text
    toks = nltk.word_tokenize(t)
    return len(toks) > 0 and "VB" in nltk.pos_tag(toks)[0][1]


@chk("words:vowel")
def _vowel(kw, r, p, o):
    paras = r.strip().split("\n")
    if len(paras) != 1:
        return False
    v = {c for c in paras[0].lower() if c in "aeiou"}
    return len(v) <= 3 if o["vowel"] == "le3" else len(v) == 3


@chk("words:words_position")
def _wpos(kw, r, p, o):
    words = g4_words(r) if o["word"] == "g4" else [t for t in nltk.word_tokenize(r) if any(c.isalnum() for c in t)]
    k = kw["keyword"].strip().lower()
    return len(words) >= 2 and words[1].lower() == words[-2].lower() == k


@chk("custom:character_reverse")
def _crev(kw, r, p, o):
    t = r.strip()
    rev = t[::-1].lower()
    if "bald eagle" in t.lower() or "eagle" not in rev:
        return False
    return len(nltk.sent_tokenize(t[::-1])) == 1


@chk("custom:word_reverse")
def _wrev(kw, r, p, o):
    toks = r.strip().split()
    # one sentence: terminal punctuation may sit only on the first or last token
    if any(re.search(r"[.!?][\"')”]*$", t) for t in toks[1:-1]):
        return False
    return _grader("custom:word_reverse", kw, r, p)


def _csv_body(r, o):
    if o["csv_wrap"] == "fence":
        m = re.search(r"```[a-zA-Z]*\n(.*?)```", r, flags=re.S)
        if m:
            return m.group(1).strip("\n")
    return r


@chk("custom:csv_city")
def _csv_city(kw, r, p, o):
    return _grader("custom:csv_city", kw, _csv_body(r, o), p)


@chk("custom:csv_quotes")
def _csv_quotes(kw, r, p, o):
    body = _csv_body(r, o)
    header = body.split("\n")[0].strip()
    if not re.match(r'^(StudentID|"StudentID")\t *(Subject|"Subject")\t *(Grade|"Grade")\t *(Semester|"Semester")\t *(Score|"Score")$', header):
        return False
    data = list(csv.reader(io.StringIO(body.replace('"', '"""')), delimiter="\t"))
    if len(data) != 4:
        return False
    for row in data:
        if len(row) != 5:
            return False
        for f in row:
            s = f.strip()
            if len(s) < 2 or s[0] != '"' or s[-1] != '"':
                return False
    return True


@chk("custom:csv_special_character")
def _csv_special(kw, r, p, o):
    body = _csv_body(r, o)
    header = body.split("\n")[0].strip()
    if not re.match(r'^(ProductID|"ProductID"),[ \t]*(Category|"Category"),[ \t]*(Brand|"Brand"),[ \t]*(Price|"Price"),[ \t]*(Stock|"Stock")$', header):
        return False
    data = list(csv.reader(io.StringIO(body.replace('"', '"""'))))
    if len(data) != 15 or any(len(row) != 5 for row in data[1:]):
        return False
    special = sum(1 for row in data[1:] for f in row if re.match(r'".*[^\d\w\s].*"', f))
    return special == 1 if o["special"] == "exact" else special >= 1


_DIM = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


@chk("custom:date_format_list")
def _dates(kw, r, p, o):
    for d in r.strip().split(","):
        d = d.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return False
        y, m, dd = (int(x) for x in d.split("-"))
        if y < 1769 or y > 1821 or not 1 <= m <= 12 or not 1 <= dd <= _DIM[m]:
            return False
    return True


_CAPS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius",
         "Minsk", "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg",
         "Paris", "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
_CAP_ALIAS = {"Kiev": "Kyiv", "Berne": "Bern", "Luxembourg City": "Luxembourg"}


@chk("custom:european_capitals_sort")
def _caps(kw, r, p, o):
    t = unicodedata.normalize("NFKD", r).encode("ASCII", "ignore").decode("ASCII")
    items = [c.strip() for c in t.split(",") if c.strip()]
    items = [_CAP_ALIAS.get(c, c) for c in items]
    if o["complete"]:
        return items == _CAPS
    if not items or any(c not in _CAPS for c in items):
        return False
    idx = [_CAPS.index(c) for c in items]
    return idx == sorted(set(idx))


@chk("custom:mcq_count_length")
def _mcq(kw, r, p, o):
    if not r.startswith("Question"):
        return False
    qs = re.split(r"(?:^|\n+)(?:Question(?: \d+)?[.):;]?\s*)", r)
    qs = [q.strip() for q in qs if q.strip()]
    if len(qs) != 4:
        return False
    lens = []
    for q in qs:
        text, opts_n, done = "", 0, False
        for line in q.split("\n"):
            if re.match(r"^[A-Ea-e][.)]\s*\w+", line.strip()):
                opts_n += 1
                done = True
            elif not done:
                text += " " + line.strip()
        if opts_n != 5:
            return False
        lens.append(len(text.strip()))
    return all(a < b for a, b in zip(lens, lens[1:]))


_AFRICA = {"algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde", "cape verde",
           "cameroon", "central african republic", "chad", "comoros", "democratic republic of the congo",
           "dr congo", "drc", "congo", "republic of the congo", "congo-brazzaville", "congo-kinshasa", "djibouti",
           "egypt", "equatorial guinea", "eritrea", "eswatini", "swaziland", "ethiopia", "gabon", "gambia",
           "the gambia", "ghana", "guinea", "guinea-bissau", "ivory coast", "cote d'ivoire", "cote divoire",
           "kenya", "lesotho", "liberia", "libya", "madagascar", "malawi", "mali", "mauritania", "mauritius",
           "morocco", "mozambique", "namibia", "niger", "nigeria", "rwanda", "sao tome and principe",
           "senegal", "seychelles", "sierra leone", "somalia", "south africa", "south sudan", "sudan",
           "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe", "western sahara", "somaliland",
           "congo (brazzaville)", "congo (kinshasa)", "congo, democratic republic of the",
           "congo, republic of the"}


@chk("custom:reverse_newline")
def _africa(kw, r, p, o):
    lines = []
    for line in r.split("\n"):
        s = re.sub(r"^\s*(?:\d+[.)]|[*•-])\s*", "", line)
        s = s.strip(ASCII_PUNCT + " ")
        if s:
            lines.append(s)
    norm_all = [unicodedata.normalize("NFKD", ln).encode("ASCII", "ignore").decode("ASCII") for ln in lines]

    def _name(n):
        n = re.sub(r"\(.*?\)|\(.*$", "", n.replace("’", "'")).strip(ASCII_PUNCT + " ").lower()
        return n

    is_c = [_name(n) in _AFRICA for n in norm_all]
    if o["complete"]:
        start = next((i for i, ln in enumerate(lines) if "Zimbabwe" in ln), None)
    else:
        start = next((i for i, c in enumerate(is_c) if c), None)  # an intro line may precede the list
    if start is None:
        return False
    norm = norm_all[start:]
    if not all(is_c[start:]):
        return False
    if o["complete"] and len(norm) < 52:
        return False
    if len(norm) < 2:
        return False
    return norm == sorted(norm, reverse=True)


@chk("custom:sentence_alphabet")
def _salpha(kw, r, p, o):
    ss = sentences(r, o)
    if len(ss) != 26:
        return False
    for i, s in enumerate(ss):
        st = s.lstrip(ASCII_PUNCT + string.whitespace + "“‘*_#")
        if not st or st[0].lower() != chr(97 + i):
            return False
    return True


# ------------------------------------------------------------------ entry
def check(iid, kwargs, response, prompt="PROMPT", opts=None):
    o = dict(PROPOSED if opts is None else opts)
    r = response
    if r is None or not r.strip():
        return False  # G3 / D-empty A
    if o["trim"]:
        r = r.strip()
    _BULLET_MODE["mode"] = o.get("bullet", "space")
    fn = CHECKS.get(iid)
    if fn is None:
        return bool(_grader(iid, kwargs, r, prompt))
    return bool(fn({k: v for k, v in kwargs.items() if v is not None}, r, prompt, o))


def grade_row(row, response, opts=None, mode="strict"):
    out = []
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        if mode == "strict":
            out.append(check(iid, dict(kw), response, row["prompt"], opts))
        else:
            out.append(any(check(iid, dict(kw), c, row["prompt"], opts) for c in loose_variants(response)))
    return out


def loose_variants(response):
    lines = response.split("\n")
    first = "\n".join(lines[1:]).strip()
    last = "\n".join(lines[:-1]).strip()
    both = "\n".join(lines[1:-1]).strip()
    return [response, response.replace("*", ""), first, last, both,
            first.replace("*", ""), last.replace("*", ""), both.replace("*", "")]
