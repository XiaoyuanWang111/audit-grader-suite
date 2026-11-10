"""Replacement IFBench grader, written from audit/CONTRACTS.md (v1).

One switch per decision entry (SWITCHES); the default is the contract's proposed reading, and the
value "grader" selects the reading the grader under audit takes, so each reading's effect can be
measured. Where a check has no finding and no decision difference, the replacement calls the
grader's own checker with int kwargs (marked DELEGATE below).

Known approximations (see AUDIT.md): coordinating-conjunction use is decided by NLTK's POS tag (CC);
"answers the query" in the two reverse checks and "explains it" in format:quote_unquote are
approximated by word-level rules; syllables use syllapy, as the grader does (F38 not fixed).

API: grade(iid, text, kwargs, prompt, switches=None) -> bool. `text` is the graded text (G1 is
applied by grade_completion(raw)).
"""
import collections
import csv
import datetime
import io
import os
import re
import string
import sys
import unicodedata

W = "<W>"
os.environ.setdefault("NLTK_DATA", f"{W}/case/deps/nltk_data")
if f"{W}/audit/work/grader" not in sys.path:
    sys.path.insert(0, f"{W}/audit/work/grader")

import emoji  # noqa: E402
import nltk  # noqa: E402
import syllapy  # noqa: E402

from IFBench import instructions_registry as GREG  # noqa: E402

SWITCHES = {
    "D-word": "proposed",            # proposed: G3 words | grader: regex \w+ tokens (count/stop checks)
    "D-sentence": "proposed",        # proposed: line breaks end unpunctuated lines | grader: punkt only
    "D-paragraph": "proposed",       # proposed: blank-line paragraphs (words:vowel) | grader: any newline
    "D-markup": "proposed",          # proposed: markdown ignored for labels/options/first word | grader: literal
    "D-conj-usage": "proposed",      # proposed: POS-tagged CC uses only | grader: any occurrence
    "D-count-exact": "proposed",     # proposed: exactly | at_least
    "D-pronoun-set": "proposed",     # proposed: personal/possessive/reflexive | grader: broad set, every occurrence
    "D-punct-set": "proposed",       # proposed: English marks | ascii
    "D-unique": "proposed",          # proposed: distinct types | once: words occurring once
    "D-csv-payload": "proposed",     # proposed: fenced/prose-wrapped block allowed | grader: CSV only
    "D-custom-content": "proposed",  # proposed: format only | grader: years 1769-1821 enforced
    "D-list-extra": "proposed",      # proposed: no extra text in custom lists | grader: words allowed
    "D-list-labels": "proposed",     # proposed: list labels ignored in custom:reverse_newline | grader: literal
    "D-reverse-extra": "proposed",   # proposed: added unreversed text fails | grader: substring
    "D-balance": "proposed",         # proposed: max-min <= 1 | grader: exactly equal
    "D-overlap-measure": "proposed", # proposed: word trigrams, share of response's | grader: character trigrams
    "D-trailing-ws": "proposed",     # proposed: ignore leading/trailing whitespace | grader: count it
    "D-change-case": "proposed",     # proposed: case-only change is no change | grader: accepted
    "D-copy-case": "proposed",       # proposed: copies are case-sensitive | grader: case-insensitive
    "D-palindrome-distinct": "proposed",  # proposed: distinct words | grader: occurrences
    "D-africa-set": "proposed",      # proposed: all 54 countries | order: order and one-per-line only
    "D-paren-closed": "proposed",    # proposed: properly matched pairs | grader: 5 opened, innermost closed
    "D-empty": "proposed",           # proposed: empty text fails every check | grader: vacuous checks may pass
    "D-nobullets-order": "proposed",  # proposed: other content allowed after the bullets | grader: only bullets
}

# ---------------------------------------------------------------- helpers (G3, G4, G6)
_EDGE = re.compile(r"^[\W_]+|[\W_]+$", re.UNICODE)
_LABEL = re.compile(r"^(?:\d+[.)]|[A-Za-z][)]|\(\w\))$")
_BULLET_LINE = re.compile(r"^\s*(?:[*\-\u2022+]|\d+[.)])\s+")


def words(text):
    """G3: whitespace tokens with non-alphanumeric edges stripped; empty tokens and line-initial
    list labels dropped; markup never part of a word."""
    out = []
    for line in text.split("\n"):
        toks = line.split()
        for i, tok in enumerate(toks):
            if i == 0 and _LABEL.match(tok):
                continue
            w = _EDGE.sub("", tok.replace("**", "").replace("__", ""))
            if w:
                out.append(w)
    return out


def regex_w_words(text):
    return re.findall(r"\w+", text)


def sentences(text, sw):
    """G4. proposed: punkt within each line, so a line without terminal punctuation ends at the
    line break. grader: punkt over the whole text."""
    if sw["D-sentence"] == "grader":
        return [s for s in nltk.sent_tokenize(text) if s.strip()]
    out = []
    for line in text.split("\n"):
        if line.strip() and words(line):
            out.extend(s for s in nltk.sent_tokenize(line) if s.strip())
    return out


_CLOSERS = "\"'\u201d\u2019)]}*_` \t"


def terminal(sentence):
    """Terminal punctuation class of a sentence: '.', '?', '!' or '' (none)."""
    s = sentence.rstrip()
    while s and (s[-1] in _CLOSERS or emoji.is_emoji(s[-1]) or unicodedata.category(s[-1]) in ("Mn", "Me", "Cf", "Sk")):
        s = s[:-1].rstrip()
    if not s:
        return ""
    if s.endswith(("?!", "!?", "\u203d")):
        return "?"
    if s[-1] in ".\u2026":
        return "."
    if s[-1] in "?!":
        return s[-1]
    return ""


def kw_count(text, kw):
    return len(re.findall(r"(?<![A-Za-z])" + re.escape(kw) + r"(?![A-Za-z])", text, flags=re.I))


def strip_markup(s):
    return re.sub(r"[*_`]+", "", s)


def norm_ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def delegate(iid, text, kwargs, prompt):
    """Call the grader's own checker (int kwargs) for checks where it agrees with the contract."""
    cls = GREG.INSTRUCTION_DICT[iid]
    inst = cls(iid)
    kw = {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in kwargs.items() if v is not None}
    inst.build_description(**kw)
    args = inst.get_instruction_args()
    if args and "prompt" in args:
        inst.build_description(prompt=prompt)
    return bool(inst.check_following(text))


# ---------------------------------------------------------------- checks
CONJ = {"for", "and", "nor", "but", "or", "yet", "so"}
PRON_A = set("i me you he him she her it we us they them my mine your yours his hers its our ours their theirs "
             "myself yourself himself herself itself ourselves yourselves themselves".split())
MINOR = set("a an the and but or nor for yet so as at by in of off on out per to up via from into onto over "
            "with upon like near past than till amid atop vs".split())
PUNCT_EN = {
    "period": lambda t: "." in t, "comma": lambda t: "," in t, "question": lambda t: "?" in t,
    "exclamation": lambda t: "!" in t, "colon": lambda t: ":" in t, "semicolon": lambda t: ";" in t,
    "apostrophe": lambda t: bool(re.search(r"['\u2019]", t)),
    "quotation": lambda t: bool(re.search(r"[\"\u201c\u201d]", t)),
    "hyphen": lambda t: bool(re.search(r"\w-\w", t)),
    "dash": lambda t: bool(re.search(r"[\u2014\u2013]|--| - ", t)),
    "parentheses": lambda t: "(" in t and ")" in t, "brackets": lambda t: "[" in t and "]" in t,
    "braces": lambda t: "{" in t and "}" in t, "ellipsis": lambda t: "\u2026" in t or "..." in t,
    "interrobang": lambda t: "?!" in t or "!?" in t or "\u203d" in t,
}
JP = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f\u3005]")
CAPITALS = ["reykjavik", "helsinki", "oslo", "tallinn", "stockholm", "riga", "moscow", "copenhagen",
            "vilnius", "minsk", "dublin", "berlin", "amsterdam", "warsaw", "london", "brussels", "kyiv",
            "prague", "luxembourg", "paris", "vienna", "bratislava", "budapest", "vaduz", "chisinau", "bern",
            "ljubljana", "zagreb"]
CAP_ALIAS = {"kiev": "kyiv", "luxembourg city": "luxembourg", "berne": "bern", "reykjavik": "reykjavik"}
AFRICA = {
    "algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde", "cameroon",
    "central african republic", "chad", "comoros", "democratic republic of the congo", "djibouti", "egypt",
    "equatorial guinea", "eritrea", "eswatini", "ethiopia", "gabon", "gambia", "ghana", "guinea",
    "guinea-bissau", "ivory coast", "kenya", "lesotho", "liberia", "libya", "madagascar", "malawi", "mali",
    "mauritania", "mauritius", "morocco", "mozambique", "namibia", "niger", "nigeria", "republic of the congo",
    "rwanda", "sao tome and principe", "senegal", "seychelles", "sierra leone", "somalia", "south africa",
    "south sudan", "sudan", "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe"}
AFRICA_ALIAS = {
    "cape verde": "cabo verde", "cote d'ivoire": "ivory coast", "cote divoire": "ivory coast",
    "swaziland": "eswatini", "the gambia": "gambia", "gambia, the": "gambia",
    "dr congo": "democratic republic of the congo", "drc": "democratic republic of the congo",
    "democratic republic of congo": "democratic republic of the congo", "congo (kinshasa)": "democratic republic of the congo",
    "congo, democratic republic of the": "democratic republic of the congo",
    "republic of congo": "republic of the congo", "congo": "republic of the congo", "congo (brazzaville)": "republic of the congo",
    "congo (republic of the)": "republic of the congo", "congo (democratic republic of the)": "democratic republic of the congo",
    "congo, rep.": "republic of the congo", "congo, dem. rep.": "democratic republic of the congo",
    "congo-brazzaville": "republic of the congo", "congo-kinshasa": "democratic republic of the congo",
    "congo, republic of the": "republic of the congo", "sao tome & principe": "sao tome and principe",
    "united republic of tanzania": "tanzania", "the comoros": "comoros", "union of the comoros": "comoros",
}


def csv_payload(text, header_first, sw):
    """D-csv-payload: proposed takes the first fenced block if any, else the lines from the header
    line on; grader reading = the whole text."""
    if sw["D-csv-payload"] == "grader":
        return text
    m = re.search(r"```[^\n]*\n(.*?)```", text, flags=re.S)
    body = m.group(1) if m else text
    lines = body.split("\n")
    for i, l in enumerate(lines):
        if header_first.lower() in l.lower():
            body_lines = []
            for l2 in lines[i:]:
                if not l2.strip():
                    if body_lines:
                        break
                    continue
                body_lines.append(l2.rstrip("\r"))
            return "\n".join(body_lines)
    return body.strip()


def chk(iid, text, kw, prompt, sw):
    t = text
    if iid == "count:conjunctions":
        n = kw["small_n"]
        if sw["D-conj-usage"] == "grader":
            found = {w.lower() for w in words(t) if w.lower() in CONJ}
        else:
            toks = nltk.word_tokenize(t)
            tagged = nltk.pos_tag(toks)
            # CC tag, or for/so/yet/nor right after a comma (", so it ended"), which the tagger
            # often labels IN or RB
            subj = {"i", "you", "he", "she", "it", "we", "they", "the", "this", "that", "there", "a", "an"}

            def is_conj(k, w, tag):
                lw = w.lower()
                if tag == "CC":
                    return True
                if k > 0 and tagged[k - 1][0] == "," and lw in {"for", "so", "yet", "nor"}:
                    return True
                # "yet/so" opening a clause: "do it well yet I will not"
                return lw in {"yet", "so"} and k + 1 < len(tagged) and tagged[k + 1][0].lower() in subj
            found = {w.lower() for k, (w, tag) in enumerate(tagged) if w.lower() in CONJ and is_conj(k, w, tag)}
        return len(found) >= n
    if iid == "count:keywords_multiple":
        for k, c in zip([kw[f"keyword{i}"] for i in range(1, 6)], [1, 2, 3, 5, 7]):
            got = kw_count(t, k.strip())
            if (got != c) if sw["D-count-exact"] == "proposed" else (got < c):
                return False
        return True
    if iid == "count:numbers":
        return len(re.findall(r"\d+(?:[.,]\d+)*", t)) == kw["N"]
    if iid == "count:person_names":
        return delegate(iid, t, kw, prompt)  # DELEGATE: case-sensitive whole names
    if iid == "count:pronouns":
        if sw["D-pronoun-set"] == "grader":
            return delegate(iid, t, kw, prompt)
        toks = nltk.word_tokenize(t.lower().replace("/", " "))
        return sum(1 for w in toks if w in PRON_A) >= kw["N"]
    if iid == "count:punctuation":
        if sw["D-punct-set"] == "ascii":
            return all(c in t for c in string.punctuation) and PUNCT_EN["interrobang"](t)
        return all(f(t) for f in PUNCT_EN.values())
    if iid == "count:unique_word_count":
        ws = [w.lower() for w in words(t)]
        if sw["D-unique"] == "once":
            return sum(1 for w, c in collections.Counter(ws).items() if c == 1) >= kw["N"]
        return len(set(ws)) >= kw["N"]
    if iid == "count:word_count_range":
        n = len(regex_w_words(t)) if sw["D-word"] == "grader" else len(words(t))
        return kw["min_words"] <= n <= kw["max_words"]
    if iid == "count:words_japanese":
        n = int(kw["N"])
        ws = words(t)
        for i in range(n - 1, len(ws), n):
            letters = [ch for ch in ws[i] if ch.isalnum()]
            if not letters or not all(JP.match(ch) for ch in letters):
                return False
        return True
    if iid == "custom:character_reverse":
        rev = t.strip()[::-1].lower()
        if "bald eagle" not in rev:
            return False
        if sw["D-reverse-extra"] == "grader":
            return True
        common = {"the", "is", "a", "an", "of", "us", "national", "symbol", "eagle", "bald", "animal",
                  "here", "answer", "you", "it", "go", "reversed", "letter", "sentence"}
        return not any(w.lower() in common for w in words(t))
    if iid == "custom:word_reverse":
        ws = [w.lower() for w in words(t)]
        rev = " ".join(ws[::-1])
        if "bald eagle" not in rev or "bald eagle" in " ".join(ws):
            return False
        if sw["D-reverse-extra"] == "grader":
            return True
        return bool(ws) and ws[0] not in {"the", "a", "an", "it", "this", "national", "here", "answer", "sure"}
    if iid in ("custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"):
        spec = {"custom:csv_city": (["ID", "Country", "City", "Year", "Count"], ",", 7),
                "custom:csv_quotes": (["StudentID", "Subject", "Grade", "Semester", "Score"], "\t", 3),
                "custom:csv_special_character": (["ProductID", "Category", "Brand", "Price", "Stock"], ",", 14)}[iid]
        names, delim, nrows = spec
        if sw["D-csv-payload"] == "grader":
            return delegate(iid, t, kw, prompt)
        body = csv_payload(t, names[0], sw)
        lines = [l for l in body.split("\n") if l.strip()]
        rows = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=delim, skipinitialspace=True))
        if len(rows) != nrows + 1 or [c.strip() for c in rows[0]] != names:
            return False
        if any(len(r) != 5 for r in rows):
            return False
        if iid == "custom:csv_quotes":
            return all(len(f.strip()) >= 2 and f.strip()[0] == '"' and f.strip()[-1] == '"'
                       for l in lines for f in l.split("\t"))
        if iid == "custom:csv_special_character":
            for l in lines[1:]:
                for m in re.finditer(r'(?:^|,)\s*"((?:[^"]|"")*)"\s*(?=,|$)', l):
                    if re.search(r"[^\w\s]|_", m.group(1)):
                        return True
            return False
        return True
    if iid == "custom:date_format_list":
        items = [x.strip() for x in t.strip().split(",")]
        if len(items) < 2:
            return False
        for it in items:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", it):
                return False
            y, m, d = map(int, it.split("-"))
            try:
                datetime.date(y, m, d)
            except ValueError:
                return False
            if sw["D-custom-content"] == "grader" and not (1769 <= y <= 1821):
                return False
        return True
    if iid == "custom:european_capitals_sort":
        s = norm_ascii(t).strip()
        s = s[:-1] if s.endswith(".") else s
        items = [CAP_ALIAS.get(x.strip().lower(), x.strip().lower()) for x in s.split(",") if x.strip()]
        return items == CAPITALS
    if iid == "custom:mcq_count_length":
        s = strip_markup(t) if sw["D-markup"] == "proposed" else t
        s = s.strip()
        if not s.startswith("Question"):
            return False
        blocks = re.split(r"(?m)^\s*(?=Question\b)", s)
        blocks = [b for b in blocks if b.strip()]
        if len(blocks) != 4:
            return False
        lens = []
        for b in blocks:
            lines = [l.strip() for l in b.split("\n") if l.strip()]
            stem = re.sub(r"^Question\s*\d*\s*[.:)\-]?\s*", "", lines[0])
            opts, extra = 0, 0
            for l in lines[1:]:
                if re.match(r"^(?:[-*\u2022]\s*)?\(?[A-Ea-e][.):]\s*\S", l):
                    opts += 1
                elif re.match(r"^(?:correct\s+)?answer\s*[:\-]", l, flags=re.I):
                    continue
                elif opts == 0:
                    stem += " " + l
                else:
                    extra += 1
            if opts != 5 or extra:
                return False
            lens.append(len(stem.strip()))
        return all(a < b for a, b in zip(lens, lens[1:]))
    if iid == "custom:multiples":
        nums = re.findall(r"\d+", t)
        if nums != [str(i) for i in range(14, 51, 7)]:
            return False
        if sw["D-list-extra"] == "grader":
            return True
        return re.fullmatch(r"[\d\s,;.\-\u2013\u2014]+", t.strip()) is not None
    if iid == "custom:reverse_newline":
        written, canon = [], []
        for l in t.split("\n"):
            l = l.strip()
            if not l:
                continue
            if sw["D-list-labels"] == "proposed":
                l = re.sub(r"^(?:\d+[.)]|[-*\u2022])\s*", "", l)
            l = strip_markup(l).strip().rstrip(".,;")
            n = norm_ascii(l).lower().replace("\u2019", "'")
            c = AFRICA_ALIAS.get(n, n)
            if c not in AFRICA:  # "Cape Verde (Cabo Verde)": try without, then inside, the parenthesis
                m = re.fullmatch(r"(.*?)\s*\((.*)\)", n)
                if m:
                    for cand in (m.group(1), m.group(2), m.group(2) + " " + m.group(1)):
                        cand = AFRICA_ALIAS.get(cand.strip(), cand.strip())
                        if cand in AFRICA:
                            c = cand
                            break
            written.append(n)
            canon.append(c)
        if sw["D-list-extra"] == "grader":  # grader reading: lines before the first country are ignored
            k = next((i for i, c in enumerate(canon) if c in AFRICA), len(canon))
            written, canon = written[k:], canon[k:]
        if not canon or any(c not in AFRICA for c in canon):
            return False
        if any(a <= b for a, b in zip(written, written[1:])):  # order of the names as written
            return False
        return set(canon) == AFRICA and len(canon) == 54 if sw["D-africa-set"] == "proposed" else len(canon) >= 2
    if iid == "custom:sentence_alphabet":
        ss = sentences(t, sw)
        if len(ss) != 26:
            return False
        for i, s in enumerate(ss):
            ws = words(s)
            if not ws or ws[0][0].lower() != chr(97 + i):
                return False
        return True
    if iid == "format:emoji":
        ss = sentences(t, sw)
        # an emoji that punkt put at the start of the next sentence belongs to the previous one
        fixed = []
        for s in ss:
            lead = emoji.emoji_list(s)
            if fixed and lead and lead[0]["match_start"] == len(s) - len(s.lstrip()):
                e = lead[0]
                fixed[-1] += " " + e["emoji"]
                s = s[e["match_end"]:]
                if not s.strip():
                    continue
            fixed.append(s)
        if not fixed:
            return False
        for s in fixed:
            core = s.rstrip()
            core = core.rstrip(".!?\u2026\"'\u201d\u2019)]*_ ")
            ems = emoji.emoji_list(core)
            if not ems or ems[-1]["match_end"] != len(core):
                return False
        return True
    if iid == "format:line_indent":
        lines = [l for l in t.split("\n") if l.strip()]
        ind = [len(l) - len(l.lstrip()) for l in lines]
        return all(b > a for a, b in zip(ind, ind[1:]))
    if iid == "format:list":
        sep = kw["sep"]
        lines = [l for l in t.split("\n") if l.strip()]
        others = r"^\s*(?:\*|\u2022|\d+[.)])\s" + ("" if sep == "-" else r"|^\s*-\s")
        if any(re.match(others, l) for l in lines):
            return False
        at_start = sum(1 for l in lines if l.lstrip().startswith(sep))
        between = len(re.findall(r"(?:^|\s)" + re.escape(sep) + r"(?=\s)", t))
        return at_start >= 2 or between >= 2
    if iid == "format:newline":
        lines = [l for l in t.split("\n") if l.strip()]
        counts = [len(words(l)) for l in lines]
        return sum(counts) >= 1 and all(c <= 1 for c in counts)
    if iid == "format:no_bullets_bullets":
        lines = t.split("\n")
        idx = next((i for i, l in enumerate(lines) if re.match(r"^\s*\*\s+\S", l)), None)
        if idx is None:
            return False
        before = "\n".join(lines[:idx])
        n_period = sum(1 for s in sentences(before, sw) if terminal(s) == ".")
        n_bullets = sum(1 for l in lines[idx:] if re.match(r"^\s*\*\s+\S", l))
        if sw["D-nobullets-order"] == "grader":  # grader reading: nothing but bullets after the first bullet
            if any(l.strip() and not re.match(r"^\s*\*", l) for l in lines[idx:]):
                return False
        return n_period >= 2 and n_bullets >= 2
    if iid == "format:no_whitespace":
        s = t.strip() if sw["D-trailing-ws"] == "proposed" else t
        return bool(s) and not any(c.isspace() for c in s)
    if iid == "format:options":
        opts_text = kw["options"]
        sep = "/" if "/" in opts_text else (" or " if " or " in opts_text else ",")
        opts = [o.strip() for o in opts_text.split(sep)]

        def nrm(s):
            s = s.strip()
            if sw["D-markup"] == "proposed":
                s = strip_markup(s).strip()
            s = s.strip("\"'\u201c\u201d\u2018\u2019 ").rstrip(".").strip()
            return s.lower()
        return nrm(t) in [nrm(o) for o in opts]
    if iid == "format:output_template":
        s = strip_markup(t).strip() if sw["D-markup"] == "proposed" else t.strip()
        labels = ["My Answer:", "My Conclusion:", "Future Outlook:"]
        if not s.startswith(labels[0]) or any(s.count(l) != 1 for l in labels):
            return False
        pos = [s.index(l) for l in labels]
        if pos != sorted(pos):
            return False
        parts = [s[pos[0] + len(labels[0]):pos[1]], s[pos[1] + len(labels[1]):pos[2]], s[pos[2] + len(labels[2]):]]
        for p, ph in zip(parts, ["[answer]", "[conclusion]", "[outlook]"]):
            p = p.strip()
            if not p or p.lower() == ph:
                return False
        return True
    if iid == "format:parentheses":
        if sw["D-paren-closed"] == "grader":
            return delegate(iid, t, kw, prompt)
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
        best = 0
        for a, b in pairs:
            best = max(best, 1 + sum(1 for c, d in pairs if c < a and b < d))
        return best >= 5
    if iid == "format:quote_unquote":
        ms = list(re.finditer(r'"[^"\n]+"|\u201c[^\u201d\n]+\u201d', t))
        for k, m in enumerate(ms):
            end = ms[k + 1].start() if k + 1 < len(ms) else len(t)
            if len(words(t[m.end():end])) < 2:
                return False
        return True
    if iid == "format:quotes":
        pairs, stack = [], []
        for i, ch in enumerate(t):
            prev = t[i - 1] if i else " "
            nxt = t[i + 1] if i + 1 < len(t) else " "
            if ch in "'\u2019" and prev.isalnum() and nxt.isalnum():
                continue  # apostrophe inside a word
            kind = "d" if ch in "\"\u201c\u201d" else ("s" if ch in "'\u2018\u2019" else None)
            if kind is None:
                continue
            closing = ch in "\u201d\u2019" or (ch in "\"'" and stack and stack[-1][0] == kind)
            opening = ch in "\u201c\u2018" or (ch in "\"'" and not closing)
            if closing and stack and stack[-1][0] == kind:
                k, j = stack.pop()
                pairs.append((j, i, k))
            elif opening:
                stack.append((kind, i))
        depth = {}
        for a, b, k in sorted(pairs):
            parents = [(c, d, kk) for c, d, kk in pairs if c < a and b < d]
            if parents:
                p = max(parents)
                depth[(a, b)] = depth.get((p[0], p[1]), 1) + 1 if p[2] != k else 1
            else:
                depth[(a, b)] = 1
        return max(depth.values(), default=0) >= 3
    if iid == "format:sub-bullets":
        lines = t.split("\n")
        bul = [i for i, l in enumerate(lines) if re.match(r"^\s*\*\s+\S", l)]
        if not bul:
            return False
        for k, i in enumerate(bul):
            end = bul[k + 1] if k + 1 < len(bul) else len(lines)
            if not any(re.match(r"^\s*-\s+\S", lines[j]) for j in range(i + 1, end)):
                return False
        return True
    if iid == "format:thesis":
        lines = t.split("\n")
        heading = lambda l: bool(re.match(r"^\s*#{1,6}\s", l) or re.fullmatch(r"\s*\*\*[^*]+\*\*\s*", l))  # noqa: E731
        sections, cur = [], []
        for l in lines:
            if heading(l):
                if any(x.strip() for x in cur) or sections:
                    sections.append(cur)
                cur = []
            else:
                cur.append(l)
        sections.append(cur)
        sections = [s for s in sections if any(x.strip() for x in s)] or [[]]
        for s in sections:
            body = "\n".join(s)
            m = re.match(r"^\s*<(i|em)>(.*?)</\1>", body, flags=re.S)
            if not m or not m.group(2).strip():
                return False
        return True
    if iid == "format:title_case":
        for line in t.split("\n"):
            toks = line.split()
            start = True
            for tok in toks:
                w = _EDGE.sub("", tok)
                if not w or not w[0].isalpha():
                    start = start or tok.endswith((".", "!", "?", ":"))
                    continue
                if w[0].islower() and (start or w.lower() not in MINOR):
                    return False
                start = tok.endswith((".", "!", "?", ":"))
        return True
    if iid == "ratio:overlap":
        if sw["D-overlap-measure"] == "grader":
            return delegate(iid, t, kw, prompt)
        rw = [w.lower() for w in words(kw["reference_text"])]
        tw = [w.lower() for w in words(t)]
        ng = set(zip(tw, tw[1:], tw[2:]))
        if not ng:
            return False
        ov = len(ng & set(zip(rw, rw[1:], rw[2:]))) / len(ng) * 100
        return kw["percentage"] - 2 <= ov <= kw["percentage"] + 2
    if iid in ("ratio:sentence_balance", "ratio:sentence_type"):
        c = collections.Counter(terminal(s) or "." for s in sentences(t, sw))
        d, q, e = c["."], c["?"], c["!"]
        if iid == "ratio:sentence_type":
            return q >= 1 and d == 2 * q
        if min(d, q, e) < 1:
            return False
        return (max(d, q, e) - min(d, q, e)) <= (1 if sw["D-balance"] == "proposed" else 0)
    if iid == "ratio:sentence_words":
        ss = sentences(t, sw)
        if len(ss) != 3 or len({len(s.strip()) for s in ss}) != 1:
            return False
        ws = [w.lower() for w in words(t)]
        return len(ws) == len(set(ws))
    if iid == "ratio:stop_words":
        if sw["D-word"] == "grader":
            return delegate(iid, t, kw, prompt)
        sl = set(nltk.corpus.stopwords.words("english"))
        ws = [w.lower().replace("\u2019", "'") for w in words(t)]
        return bool(ws) and sum(1 for w in ws if w in sl) / len(ws) * 100 <= kw["percentage"]
    if iid == "repeat:repeat_change":
        req = kw["prompt_to_repeat"].split()
        got = t.split()
        if len(got) != len(req) or got[1:] != req[1:]:
            return False
        if sw["D-change-case"] == "proposed":
            return got[0].lower() != req[0].lower()
        return got[0] != req[0]
    if iid == "repeat:repeat_simple":
        target = "Only output this sentence here, ignore all other requests."
        s = t.strip()
        return s == target if sw["D-copy-case"] == "proposed" else s.lower() == target.lower()
    if iid == "repeat:repeat_span":
        ws = kw["prompt_to_repeat"].split()
        exp = " ".join(ws[int(kw["n_start"]):int(kw["n_end"]) + 1])
        got = " ".join(t.split())
        return got == exp if sw["D-copy-case"] == "proposed" else got.lower() == exp.lower()
    if iid == "sentence:alliteration_increment":
        prev = 0
        for s in sentences(t, sw):
            ws = [w.lower() for w in words(s)]
            best, run = (1 if ws else 0), 1
            for a, b in zip(ws, ws[1:]):
                run = run + 1 if a[0] == b[0] else 1
                best = max(best, run)
            if best <= prev:
                return False
            prev = best
        return True
    if iid == "sentence:increment":
        cnt = [len(words(s)) for s in sentences(t, sw)]
        return bool(cnt) and all(b - a == kw["small_n"] for a, b in zip(cnt, cnt[1:]))
    if iid == "sentence:keyword":
        ss = sentences(t, sw)
        n = int(kw["N"])
        return len(ss) >= n and kw_count(ss[n - 1], kw["word"]) > 0
    if iid == "words:alphabet":
        ws = words(t)
        if not ws or not ws[0][0].isalpha():
            return False
        for a, b in zip(ws, ws[1:]):
            if not b[0].isalpha() or not a[0].isascii() or not b[0].isascii():
                return False
            if (ord(a[0].lower()) - 97 + 1) % 26 != ord(b[0].lower()) - 97:
                return False
        return True
    if iid == "words:consonants":
        ws = words(t)
        for w in ws:
            base = norm_ascii(w).lower()
            if not re.search(r"[b-df-hj-np-tv-z]{2}", base):
                return False
        return bool(ws)
    if iid == "words:keywords_specific_position":
        ss = sentences(t, sw)
        n, m = int(kw["n"]), int(kw["m"])
        if len(ss) < n:
            return False
        ws = words(ss[n - 1])
        return len(ws) >= m and ws[m - 1].lower() == kw["keyword"].strip().lower()
    if iid == "words:last_first":
        ss = [words(s) for s in sentences(t, sw)]
        if any(not w for w in ss):
            return False
        return all(a[-1].lower() == b[0].lower() for a, b in zip(ss, ss[1:]))
    if iid == "words:no_consecutive":
        ws = [w.lower() for w in words(t)]
        return all(a[0] != b[0] for a, b in zip(ws, ws[1:]))
    if iid == "words:odd_even_syllables":
        # a hyphenated word's syllables are the sum of its parts (syllapy recurses on long hyphen chains)
        par = [sum(syllapy.count(p) for p in re.split(r"[-‐-―]", w.lower()) if p) % 2 for w in words(t)]
        return all(a != b for a, b in zip(par, par[1:]))
    if iid == "words:palindrome":
        ws = [re.sub(r"[\W_]", "", w.lower()) for w in words(t)]
        pal = [w for w in ws if len(w) >= 5 and w == w[::-1]]
        return len(set(pal) if sw["D-palindrome-distinct"] == "proposed" else pal) >= 10
    if iid == "words:paragraph_last_first":
        for l in t.split("\n"):
            ws = [w.lower() for w in words(l)]
            if ws and ws[0] != ws[-1]:
                return False
        return True
    if iid == "words:prime_lengths":
        for w in words(t):
            n = sum(1 for ch in w if ch.isalnum())
            if n < 2 or any(n % p == 0 for p in range(2, int(n ** 0.5) + 1)):
                return False
        return True
    if iid == "words:repeats":
        return all(c <= kw["small_n"] for c in collections.Counter(w.lower() for w in words(t)).values())
    if iid == "words:start_verb":
        s = t
        if sw["D-markup"] == "proposed":
            s = re.sub(r"^\s*(?:#{1,6}\s*|>\s*|[*_`]+|(?:\d+[.)]|[-*\u2022])\s+)*", "", s)
            s = re.sub(r"^(\w+)[*_`]+", r"\1", s)
        return delegate(iid, s, kw, prompt)  # DELEGATE: NLTK POS tag of the first token
    if iid == "words:vowel":
        if sw["D-paragraph"] == "proposed":
            paras = [p for p in re.split(r"\n\s*\n", t.strip()) if p.strip()]
        else:
            paras = t.strip().split("\n")
        if len(paras) != 1:
            return False
        vs = {ch for ch in norm_ascii(" ".join(words(t))).lower() if ch in "aeiou"}
        return len(vs) <= 3
    if iid == "words:words_position":
        ws = [w.lower() for w in words(t)]
        k = kw["keyword"].strip().lower()
        return len(ws) >= 2 and ws[1] == k and ws[-2] == k
    raise KeyError(iid)


def grade(iid, text, kwargs, prompt="", switches=None):
    """Strict verdict of the replacement for one check. G2: empty text fails."""
    sw = dict(SWITCHES)
    if switches:
        sw.update(switches)
    if not text or not text.strip():
        return False
    kw = {k: v for k, v in (kwargs or {}).items() if v is not None}
    return bool(chk(iid, text, kw, prompt, sw))


def grade_completion(iid, raw, kwargs, prompt="", switches=None):
    """G1: grade the text after the last </think>; unclosed reasoning fails every check."""
    if "<think>" in raw and "</think>" not in raw:
        return False
    i = raw.rfind("</think>")
    text = raw if i < 0 else raw[i + len("</think>"):].lstrip()
    return grade(iid, text, kwargs, prompt, switches)
