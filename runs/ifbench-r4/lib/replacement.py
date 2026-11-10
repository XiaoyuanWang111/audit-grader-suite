"""Replacement grader (X) built from audit/contracts.md.

X fixes every finding that a change to a checker can fix, and has one switch per
decision entry it implements. With the default switches (`AS_IS`), each decision
follows the grader's current reading, so X minus G measures the findings alone; with
`PROPOSED`, every implemented decision follows the contract's proposed reading.
Checks without a finding delegate to the reference checker (which equals the grader's
checker for them, see the diff in ISSUE.md).

    check(iid, kwargs, text, prompt="", sw=None) -> bool

G1 (extraction failure) and G4 (empty text) are applied by the caller / here.
"""
import contextlib
import datetime
import re
import string
import unicodedata

import ifbaudit as A
from ifbench import instructions as R_inst
from ifbench import instructions_util as R_util

nltk = A.nltk
emoji = R_inst.emoji

# ---------------- switches ----------------
AS_IS = {
    "D-trim": False,              # P: ignore surrounding whitespace (no_whitespace, options)
    "D-sentence": False,          # P: line breaks also end sentences
    "D-punct-set": False,         # P: 11 marks incl. ' " - ( )
    "D-this-sentence": False,     # P: repeat_simple wants the preceding sentence
    "D-options-exact": False,     # P: letter options accept case, (b), b, b) text
    "D-nbb-order": False,         # P: text after the bullets allowed
    "D-palindrome-distinct": False,  # P: distinct palindromes
    "D-vowel-paragraph": False,   # P: paragraph form not graded
    "D-japanese-digits": False,   # P: a numeral at an Nth position fails
    "D-csv-wrapper": False,       # P: code fence / prose around the CSV block allowed
    "D-list-sep": False,          # P: one inline separator between two items suffices
    "D-word": False,              # P: punctuation-only tokens are not words (consonants, prime lengths, repeats, no_consecutive, alphabet)
    "D-keyword-form": False,      # A: inflections count (not implemented: both settings whole-word)
    "D-verb": False,              # P: a gerund/participle subject ("Running is fun") is not a verb start
    "D-explanation": False,       # P: unquoted words must follow each quote before the next quote or sentence end
    "D-section": False,           # P: without headings, blank-line blocks are sections; A: the whole text is one section
    "D-template-repeat": False,   # P: the template appears once; A: repeated filled templates allowed
}
PROPOSED = {k: True for k in AS_IS}
PROPOSED["D-keyword-form"] = False

PUNCT = string.punctuation
WORD_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")


def words_g5(text):
    """Words per contract G5: runs of letters/digits joined by apostrophes or hyphens."""
    return WORD_RE.findall(text)


def _sw(sw):
    d = dict(AS_IS)
    if sw:
        d.update(sw)
    return d


# ---------------- sentence splitting (D-sentence) ----------------
_orig_split = R_util.split_into_sentences


def _split_lines_then_punkt(text):
    out = []
    for line in text.split("\n"):
        if line.strip():
            out.extend(_orig_split(line))
    return out


@contextlib.contextmanager
def sentence_mode(by_lines):
    if not by_lines:
        yield _orig_split
        return
    R_util.split_into_sentences = _split_lines_then_punkt
    try:
        yield _split_lines_then_punkt
    finally:
        R_util.split_into_sentences = _orig_split


def _ref(iid, kwargs, text, prompt):
    return A.check_R(iid, kwargs, text, prompt)


# ---------------- fixed checkers ----------------

def conjunctions(kw, text, sw):
    found = {w.strip(PUNCT + " ").lower() for w in text.split()}
    return len(found & {"and", "but", "for", "nor", "or", "so", "yet"}) >= kw["small_n"]


def numbers(kw, text, sw):
    text = re.sub(r"(?<=\d)-(?=\d)", " ", text)
    text = text.translate(str.maketrans("", "", PUNCT))
    return len(re.findall(r"\d+", text)) == kw["N"]


def word_count_range(kw, text, sw):
    return kw["min_words"] <= len(words_g5(text)) <= kw["max_words"]


def words_japanese(kw, text, sw):
    n = kw["N"]
    toks = [t.strip(PUNCT + " ") for t in text.split()]
    toks = [t for t in toks if any(ch.isalnum() for ch in t)]
    jp = re.compile(r"[぀-ヿ一-鿿]")
    for i, t in enumerate(toks):
        if (i + 1) % n == 0:
            if t.isdigit() and not sw["D-japanese-digits"]:
                continue
            if not jp.search(t):
                return False
    return True


_FORWARD_WORDS = {"the", "is", "of", "and", "to", "in", "it", "answer", "national", "symbol", "bald", "eagle", "animal", "this"}


def character_reverse(kw, text, sw):
    rev = text[::-1].lower()
    if "bald eagle" not in re.sub(r"\s+", " ", rev.translate(str.maketrans("", "", PUNCT))):
        return False
    fwd = {w.lower() for w in words_g5(text)}
    return not (fwd & _FORWARD_WORDS)


def date_format_list(kw, text, sw):
    for d in text.strip().split(","):
        d = d.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return False
        y, m, dd = (int(x) for x in d.split("-"))
        if y < 1769 or y > 1821:
            return False
        try:
            datetime.date(y, m, dd)
        except ValueError:
            return False
    return True


CAPITALS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius",
            "Minsk", "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg",
            "Paris", "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]


def _ascii(t):
    return unicodedata.normalize("NFKD", t).encode("ASCII", "ignore").decode("ASCII")


def european_capitals(kw, text, sw):
    caps = [c.strip() for c in _ascii(text).split(",") if c.strip()]
    caps = ["Kyiv" if c in ("Kiev", "Kyiv") else c for c in caps]
    return caps == CAPITALS


def mcq(kw, text, sw):
    if not text.startswith("Question"):
        return False
    qs = re.split(r"(?:^|\n)\s*Question(?:\s*\d+)?\s*[\.\):;]?\s*", text)
    qs = [q.strip() for q in qs if q.strip()]
    if len(qs) != 4:
        return False
    lens = []
    for q in qs:
        qt, nopt, done = "", 0, False
        for line in q.split("\n"):
            if re.match(r"^[A-Ea-e][\.|\)]\s*\w+", line.strip()):
                nopt += 1
                done = True
            elif not done:
                qt += " " + line.strip()
        if nopt != 5:
            return False
        lens.append(len(qt.strip()))
    return all(lens[i] < lens[i + 1] for i in range(3))


_AFRICA_ALIASES = {
    "cabo verde": "cabo verde", "cape verde": "cabo verde",
    "ivory coast": "ivory coast", "cote d'ivoire": "ivory coast", "cote divoire": "ivory coast",
    "eswatini": "eswatini", "swaziland": "eswatini", "eswatini (swaziland)": "eswatini",
    "congo": "congo", "republic of the congo": "congo", "congo, republic of the": "congo", "congo-brazzaville": "congo",
    "democratic republic of the congo": "drc", "dr congo": "drc", "drc": "drc", "congo, democratic republic of the": "drc",
    "congo-kinshasa": "drc", "gambia": "gambia", "the gambia": "gambia",
    "sao tome and principe": "sao tome and principe",
}
_AFRICA = ["algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde", "cameroon",
           "central african republic", "chad", "comoros", "congo", "drc", "djibouti", "egypt", "equatorial guinea",
           "eritrea", "eswatini", "ethiopia", "gabon", "gambia", "ghana", "guinea", "guinea-bissau", "ivory coast",
           "kenya", "lesotho", "liberia", "libya", "madagascar", "malawi", "mali", "mauritania", "mauritius",
           "morocco", "mozambique", "namibia", "niger", "nigeria", "rwanda", "sao tome and principe", "senegal",
           "seychelles", "sierra leone", "somalia", "south africa", "south sudan", "sudan", "tanzania", "togo",
           "tunisia", "uganda", "zambia", "zimbabwe"]


def reverse_newline(kw, text, sw):
    lines = [_ascii(l).strip(PUNCT + " ").replace("’", "'") for l in text.split("\n")]
    lines = [re.sub(r"^\d+[\.\)]\s*", "", l).strip() for l in lines if l.strip(PUNCT + " ")]
    names = []
    for l in lines:
        low = l.lower()
        key = _AFRICA_ALIASES.get(low, low)
        if key not in _AFRICA:
            if "democratic" in low and "congo" in low:
                key = "drc"
            elif "kinshasa" in low:
                key = "drc"
            elif low.startswith("congo") or low.startswith("republic of the congo"):
                key = "congo"
            elif "verde" in low:
                key = "cabo verde"
            elif "ivoire" in low or "ivory" in low:
                key = "ivory coast"
            elif "eswatini" in low or "swaziland" in low:
                key = "eswatini"
            elif "gambia" in low:
                key = "gambia"
        if key in _AFRICA:
            names.append((l, key))
    if {k for _, k in names} != set(_AFRICA):
        return False
    shown = [l for l, _ in names]
    return shown == sorted(shown, reverse=True)


def sentence_alphabet(kw, text, sw):
    return _ref("custom:sentence_alphabet", kw, text, "")


def _ends_with_emoji(s):
    s = s.translate(str.maketrans("", "", PUNCT)).strip()
    if not s:
        return False
    found = emoji.emoji_list(s)
    if not found:
        return False
    tail = s[found[-1]["match_end"]:]
    return tail.strip("️‍ ") == ""


def _starts_with_emoji(s):
    s = s.translate(str.maketrans("", "", PUNCT)).strip()
    found = emoji.emoji_list(s)
    return bool(found) and found[0]["match_start"] == 0


def emoji_sentences(kw, text, sw, split):
    sents = split(text)
    for i, s in enumerate(sents):
        if not s.translate(str.maketrans("", "", PUNCT)).strip():
            return False
        if _ends_with_emoji(s):
            continue
        if i < len(sents) - 1 and _starts_with_emoji(sents[i + 1]):
            continue
        return False
    return True


def line_indent(kw, text, sw):
    lines = [l.expandtabs(4) for l in text.split("\n") if l.strip()]
    ind = [len(l) - len(l.lstrip()) for l in lines]
    return all(ind[i + 1] > ind[i] for i in range(len(ind) - 1))


def special_list(kw, text, sw):
    sep = kw["sep"]
    if sep == "-":  # a hyphen inside a word is not a marker; at a line start or between spaces it is
        pat = r"^[ \t]*-|(?<=\s)-(?=\s)"
    else:
        pat = re.escape(sep)
    n = len(re.findall(pat, text, flags=re.M))
    if sw["D-list-sep"]:
        items = [x for x in re.split(pat, text, flags=re.M) if x.strip()]
        return n >= 1 and len(items) >= 2
    return n >= 2


def no_bullets_bullets(kw, text, sw, split):
    lines = [l for l in text.split("\n") if l.strip()]
    period_sents, bullets, seen_bullet = 0, 0, False
    for l in lines:
        s = l.strip()
        if re.match(r"^\*[ \t]", s):
            if period_sents < 2:
                return False
            seen_bullet = True
            bullets += 1
        elif not seen_bullet:
            period_sents += sum(1 for x in split(s) if x.rstrip().endswith("."))
        elif not sw["D-nbb-order"]:
            return False
    return bullets >= 2


_TEMPLATE = ["My Answer:", "My Conclusion:", "Future Outlook:"]


def output_template(kw, text, sw):
    pos = []
    for lab in _TEMPLATE:
        c = text.count(lab)
        if c == 0 or (c > 1 and sw["D-template-repeat"]):
            return False
        pos.append(text.index(lab))
    if not pos[0] < pos[1] < pos[2]:
        return False
    parts = [text[pos[0] + len(_TEMPLATE[0]):pos[1]], text[pos[1] + len(_TEMPLATE[1]):pos[2]],
             text[pos[2] + len(_TEMPLATE[2]):]]
    for part, ph in zip(parts, ["[answer]", "[conclusion]", "[outlook]"]):
        body = part.strip(" \n*_#")
        if not body or body.lower() == ph:
            return False
    return True


def quote_unquote(kw, text, sw):
    t = text.replace("“", '"').replace("”", '"')
    if not _ref("format:quote_unquote", kw, t, ""):
        return False
    if not sw["D-explanation"]:
        return True
    for m in re.finditer(r'"[^"\n]*"', t):
        after = re.split(r'["\n]|[.!?](?:\s|$)', t[m.end():], maxsplit=1)[0]
        if not re.search(r"[^\W\d_]", after):
            return False
    return True


def quotes(kw, text, sw):
    if _ref("format:quotes", kw, text, ""):
        return True
    t = re.sub(r"(?<=\w)’(?=\w)", "", text)  # curly apostrophes inside words are not quote marks
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return _ref("format:quotes", kw, t, "")


def sub_bullets(kw, text, sw):
    lines = [l for l in text.split("\n") if l.strip()]
    bullets = 0
    pending = False
    for l in lines:
        s = l.strip()
        if re.match(r"^\*[ \t]", s):
            if pending:
                return False
            bullets += 1
            pending = True
        elif re.match(r"^-[ \t]", s) and bullets:
            pending = False
    return bullets >= 1 and not pending


def thesis(kw, text, sw):
    lines = text.split("\n")
    if any(l.lstrip().startswith("#") for l in lines):
        sections, cur = [], []
        for l in lines:
            if l.lstrip().startswith("#"):
                if cur:
                    sections.append(cur)
                cur = []
            else:
                cur.append(l)
        sections.append(cur)
        sections = ["\n".join(s).strip() for s in sections]
    elif sw["D-section"]:
        sections = [s.strip() for s in re.split(r"\n\s*\n", text)]
    else:
        sections = [text.strip()]
    sections = [s for s in sections if s]
    if not sections:
        return False
    for s in sections:
        m = re.match(r"^(?:\*\*)?<(i|em)>(.*?)</\1>", s, flags=re.S)
        if not m or not m.group(2).strip():
            return False
    return True


_MINOR = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "as", "at", "by", "in", "of", "off",
          "on", "per", "to", "up", "via", "from", "into", "onto", "over", "with", "upon", "than", "vs"}


def title_case(kw, text, sw):
    first = True
    for line in text.split("\n"):
        first = True
        for w in words_g5(line):
            if not w[0].isalpha():
                first = False
                continue
            if w[0].islower() and not (w.lower() in _MINOR and not first):
                return False
            first = False
    return True


def overlap(kw, text, sw):
    def tri(t):
        w = [x.lower() for x in words_g5(t)]
        return set(zip(w, w[1:], w[2:]))
    a, b = tri(text), tri(kw["reference_text"])
    if not a:
        return False
    return kw["percentage"] - 2 <= 100 * len(a & b) / len(a) <= kw["percentage"] + 2


def sentence_balance(kw, text, sw, split):
    s = split(text)
    d = sum(x.endswith(".") for x in s)
    q = sum(x.endswith("?") for x in s)
    e = sum(x.endswith("!") for x in s)
    return d == q == e and d > 0


def sentence_type(kw, text, sw, split):
    s = split(text)
    d = sum(x.endswith(".") for x in s)
    q = sum(x.endswith("?") for x in s)
    return q >= 1 and d == 2 * q


def repeat_change(kw, text, sw):
    p = kw["prompt_to_repeat"].split()
    v = text.split()
    if not v or v[0].lower() == p[0].lower():
        return False
    return " ".join(p[1:]) == " ".join(v[1:])


def repeat_simple(kw, text, sw, prompt):
    if not sw["D-this-sentence"]:
        return _ref("repeat:repeat_simple", kw, text, prompt)
    k = prompt.find("Only output this sentence here")
    before = _orig_split(prompt[:k].strip()) if k > 0 else []
    return bool(before) and text.strip().lower() == before[-1].strip().lower()


def alliteration(kw, text, sw, split):
    prev = -1
    for s in split(text):
        ws = [w.lower() for w in words_g5(s)]
        best, run = (1 if ws else 0), 1
        for i in range(1, len(ws)):
            run = run + 1 if ws[i][0] == ws[i - 1][0] else 1
            best = max(best, run)
        if best <= prev:
            return False
        prev = best
    return True


def kw_specific_position(kw, text, sw, split):
    s = split(text)
    if len(s) < kw["n"]:
        return False
    ws = words_g5(s[kw["n"] - 1])
    return len(ws) >= kw["m"] and ws[kw["m"] - 1].lower() == kw["keyword"].lower()


def last_first(kw, text, sw, split):
    s = split(text)
    for i in range(len(s) - 1):
        a, b = words_g5(s[i]), words_g5(s[i + 1])
        if not a or not b or a[-1].lower() != b[0].lower():
            return False
    return True


def paragraph_last_first(kw, text, sw):
    for p in text.split("\n"):
        ws = words_g5(p)
        if ws and ws[0].lower() != ws[-1].lower():
            return False
    return True


def start_verb(kw, text, sw):
    head = re.sub(r"[*_`#>]+", "", text).lstrip(" \t\n\"'")
    toks = nltk.word_tokenize(head)
    if not toks:
        return False
    tags = nltk.pos_tag(toks)
    if tags[0][1] in ("NNS", "NNPS"):  # imperatives are never plural nouns ("Lights flicker")
        return False
    if "VB" in tags[0][1]:
        if sw["D-verb"] and tags[0][1] in ("VBG", "VBN") and any(t.startswith("VB") or t == "MD" for _, t in tags[1:3]):
            return False
        return True
    framed = nltk.pos_tag(["You", "should", toks[0].lower()] + toks[1:])[2][1]
    if not framed.startswith("VB") or len(toks) < 2:
        return False
    nxt = tags[1:3]
    if not any(c.isalnum() for c in nxt[0][0]):
        return False
    return not any(t.startswith("VB") or t == "MD" for _, t in nxt)


def words_position(kw, text, sw):
    ws = words_g5(text)
    return len(ws) >= 2 and ws[1].lower() == ws[-2].lower() == kw["keyword"].lower()


def sentence_words(kw, text, sw, split):
    s = split(text)
    if len(s) != 3:
        return False
    if len({len(x.strip()) for x in s}) != 1:
        return False
    ws = [w.lower() for w in words_g5(text)]
    return len(ws) == len(set(ws))


def repeat_span(kw, text, sw):
    return _ref("repeat:repeat_span", kw, text, "")


def keywords_multiple(kw, text, sw):
    return _ref("count:keywords_multiple", kw, text, "")


# ---------------- decision-only switches on otherwise unchanged checks ----------------

def no_whitespace(kw, text, sw):
    t = text.strip() if sw["D-trim"] else text
    return not any(c.isspace() for c in t)


def options(kw, text, sw):
    t = text.strip() if sw["D-trim"] else text
    if not sw["D-options-exact"]:
        return A.check_G("format:options", kw, t)
    opts = kw["options"]
    t2 = t.strip(" *_").rstrip(".").strip().lower()
    if re.match(r"\W*[aA]\W*[bB]\W*[cC]\W*", opts):
        return re.fullmatch(r"\(?([a-d])\)?(?:[\s.:]+.*)?", t2, flags=re.S) is not None and len(t2) < 120
    return A.check_G("format:options", kw, t)


def punctuation(kw, text, sw):
    if not A.check_G("count:punctuation", kw, text):
        return False
    if not sw["D-punct-set"]:
        return True
    return ("'" in text or "’" in text) and ('"' in text or "“" in text) and ("-" in text or "–" in text or "—" in text) \
        and "(" in text and ")" in text


def palindrome(kw, text, sw):
    if not sw["D-palindrome-distinct"]:
        return A.check_G("words:palindrome", kw, text)
    ws = text.translate(str.maketrans("", "", PUNCT)).lower().split()
    return len({w for w in ws if w == w[::-1] and len(w) >= 5}) >= 10


def vowel(kw, text, sw):
    if not sw["D-vowel-paragraph"]:
        return A.check_G("words:vowel", kw, text)
    return len({c for c in text.lower() if c in "aeiou"}) <= 3


def _csv_block(text):
    m = re.search(r"```[^\n]*\n(.*?)```", text, flags=re.S)
    if m:
        return m.group(1).strip("\n")
    return text


def csv_check(iid):
    def f(kw, text, sw):
        t = _csv_block(text) if sw["D-csv-wrapper"] else text
        try:
            return A.check_G(iid, kw, t)
        except IndexError:  # csv_quotes indexes an empty field; an empty field is not quoted
            return False
    return f


def _drop_nonwords(text):
    return " ".join(t for t in text.split() if any(ch.isalnum() for ch in t))


def word_switch(iid):
    def f(kw, text, sw):
        if sw["D-word"]:
            text = "\n".join(_drop_nonwords(l) for l in text.split("\n"))
        return A.check_G(iid, kw, text)
    return f


SIMPLE = {
    "count:conjunctions": conjunctions,
    "count:keywords_multiple": keywords_multiple,
    "count:numbers": numbers,
    "count:word_count_range": word_count_range,
    "count:words_japanese": words_japanese,
    "count:punctuation": punctuation,
    "custom:character_reverse": character_reverse,
    "custom:date_format_list": date_format_list,
    "custom:european_capitals_sort": european_capitals,
    "custom:mcq_count_length": mcq,
    "custom:reverse_newline": reverse_newline,
    "custom:sentence_alphabet": sentence_alphabet,
    "custom:csv_city": csv_check("custom:csv_city"),
    "custom:csv_quotes": csv_check("custom:csv_quotes"),
    "custom:csv_special_character": csv_check("custom:csv_special_character"),
    "format:line_indent": line_indent,
    "format:list": special_list,
    "format:output_template": output_template,
    "format:quote_unquote": quote_unquote,
    "format:quotes": quotes,
    "format:sub-bullets": sub_bullets,
    "format:thesis": thesis,
    "format:title_case": title_case,
    "format:no_whitespace": no_whitespace,
    "format:options": options,
    "ratio:overlap": overlap,
    "repeat:repeat_change": repeat_change,
    "repeat:repeat_span": repeat_span,
    "words:paragraph_last_first": paragraph_last_first,
    "words:start_verb": start_verb,
    "words:words_position": words_position,
    "words:palindrome": palindrome,
    "words:vowel": vowel,
    "words:consonants": word_switch("words:consonants"),
    "words:prime_lengths": word_switch("words:prime_lengths"),
    "words:repeats": word_switch("words:repeats"),
    "words:no_consecutive": word_switch("words:no_consecutive"),
    "words:alphabet": word_switch("words:alphabet"),
}
SENTENCE = {
    "format:emoji": emoji_sentences,
    "format:no_bullets_bullets": no_bullets_bullets,
    "ratio:sentence_balance": sentence_balance,
    "ratio:sentence_type": sentence_type,
    "ratio:sentence_words": sentence_words,
    "sentence:alliteration_increment": alliteration,
    "words:keywords_specific_position": kw_specific_position,
    "words:last_first": last_first,
}
# checks that use sentences internally and have no finding: delegate under the sentence mode
SENTENCE_DELEGATE = {"sentence:keyword", "sentence:increment", "custom:sentence_alphabet", "custom:word_reverse"}

FIXED = set(SIMPLE) | set(SENTENCE)


def check(iid, kwargs, text, prompt="", sw=None):
    s = _sw(sw)
    if not (text and text.strip()):
        return False
    kw = A.nonnull(dict(kwargs))
    if iid == "repeat:repeat_simple":
        return repeat_simple(kw, text, s, prompt)
    with sentence_mode(s["D-sentence"]) as split:
        if iid in SENTENCE:
            return bool(SENTENCE[iid](kw, text, s, split))
        if iid in SIMPLE:
            return bool(SIMPLE[iid](kw, text, s))
        return _ref(iid, kw, text, prompt)
