"""Replacement grader written from audit/CONTRACTS.md (not from either grader's code).

Every check takes the graded text (or None for an extraction failure) and the constraint's
kwargs and returns True/False. Each decision entry D-<topic> has a switch with the values
"proposed" (the contract's proposed reading) and "alt" (the other reading in the decision table).

    r = Replacement()                       # proposed readings
    r = Replacement(**{"D-keyword-substring": "alt"})
    r.check("keywords:existence", {"keywords": ["dog"]}, "My dog.")

`NVIDIA_SIDE` records which value of each switch NVIDIA's reference code is closest to; the
configuration `Replacement.fixes_only()` uses those values, so that its differences from NVIDIA's
verdicts are defect fixes, not changes of reading.
"""

from __future__ import annotations

import json
import re
import unicodedata

import regex

PROPOSED = "proposed"
ALT = "alt"

# Decision entries with a switch (CONTRACTS.md v2).
DECISIONS = (
    "D-think-nonthinking", "D-word", "D-word-cjk", "D-keyword-case", "D-keyword-substring",
    "D-sentence-lines", "D-first-last-markup", "D-allcaps-short", "D-case-scope", "D-english-mixed",
    "D-two-sep", "D-two-different", "D-repeat-center", "D-repeat-copies", "D-unique-case",
    "D-lowercase-scope", "D-placeholder", "D-postscript-case", "D-postscript-dot", "D-postscript-end",
    "D-bigram-odd", "D-constrained-extra", "D-json-scalar", "D-sections-case", "D-sections-number",
    "D-sections-preamble", "D-bullet-markers", "D-bullet-nested", "D-highlight-bold",
    "D-hyphens-single", "D-brackets-per-word", "D-title-position", "D-palindrome-min",
    "D-consecutive-order", "D-start-markup", "D-start-end-single", "D-appear-n-times",
    "D-letter-case", "D-letter-unit", "D-language-mixed", "D-paragraph-blank", "D-divider-line",
    "D-comma-variants", "D-dot-variants", "D-exclamation-variants", "D-end-trailing", "D-end-case",
    "D-quote-curly", "D-hyphen-dash", "D-two-sep-edge", "D-consecutive-script", "D-postscript-line",
)

# Which reading NVIDIA's checker code is closest to ("mixed" notes in CONTRACTS.md / AUDIT.md).
NVIDIA_SIDE = {
    "D-think-nonthinking": ALT, "D-word": ALT, "D-word-cjk": ALT, "D-keyword-case": PROPOSED,
    "D-keyword-substring": ALT, "D-sentence-lines": ALT, "D-first-last-markup": ALT,
    "D-allcaps-short": PROPOSED, "D-case-scope": PROPOSED, "D-english-mixed": PROPOSED,
    "D-two-sep": ALT, "D-two-different": PROPOSED, "D-repeat-center": PROPOSED, "D-repeat-copies": ALT,
    "D-unique-case": ALT, "D-lowercase-scope": ALT, "D-placeholder": PROPOSED,
    "D-postscript-case": PROPOSED, "D-postscript-dot": ALT, "D-postscript-end": ALT,
    "D-bigram-odd": PROPOSED, "D-constrained-extra": ALT, "D-json-scalar": PROPOSED,
    "D-sections-case": PROPOSED, "D-sections-number": ALT, "D-sections-preamble": PROPOSED,
    "D-bullet-markers": PROPOSED, "D-bullet-nested": PROPOSED, "D-highlight-bold": PROPOSED,
    "D-hyphens-single": PROPOSED, "D-brackets-per-word": PROPOSED, "D-title-position": PROPOSED,
    "D-palindrome-min": ALT, "D-consecutive-order": ALT, "D-start-markup": ALT,
    "D-start-end-single": ALT, "D-appear-n-times": ALT, "D-letter-case": PROPOSED,
    "D-letter-unit": PROPOSED, "D-language-mixed": PROPOSED, "D-paragraph-blank": ALT,
    "D-divider-line": ALT, "D-comma-variants": ALT, "D-dot-variants": ALT,
    "D-exclamation-variants": ALT, "D-end-trailing": ALT, "D-end-case": ALT, "D-quote-curly": ALT,
    "D-hyphen-dash": PROPOSED, "D-two-sep-edge": ALT, "D-consecutive-script": PROPOSED, "D-postscript-line": ALT,
}

# --- tokenization -----------------------------------------------------------------------

_CJK = r"\p{Han}\p{Hiragana}\p{Katakana}"
_WORDCHAR = r"[\p{L}\p{N}\p{M}--[" + _CJK + r"]]"
WORD_PROPOSED = regex.compile(r"[" + _CJK + r"]|" + _WORDCHAR + r"+(?:['’\-]" + _WORDCHAR + r"+)*", regex.V1)
WORD_ALT_JOIN = regex.compile(r"[" + _CJK + r"]|" + _WORDCHAR + r"+", regex.V1)  # split at ' and -
WORD_CJK_RUN = regex.compile(r"[\p{L}\p{N}\p{M}]+(?:['’\-][\p{L}\p{N}\p{M}]+)*", regex.V1)
WORD_ALT_BOTH = regex.compile(r"[\p{L}\p{N}\p{M}]+", regex.V1)
WORDCHAR_RE = regex.compile(r"[\p{L}\p{N}\p{M}]", regex.V1)

MARKUP_CHARS = set("*_#`~>")
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "vs", "etc", "e.g", "i.e", "u.s", "u.k",
    "a.m", "p.m", "no", "fig", "inc", "ltd", "co", "approx", "dept", "est", "vol", "cf", "al",
}
LIST_MARKER = re.compile(r"^\s*(?:#{1,6}\s+|>\s*|[*+\-]\s+|\d+[.)]\s+|[a-zA-Z][.)]\s+(?=\S))")
TERMINAL = re.compile(r"[.!?。！？]+[\"'”’)\]]*")


class Replacement:
    def __init__(self, **switches: str) -> None:
        self.s = {d: PROPOSED for d in DECISIONS}
        for key, value in switches.items():
            if key not in self.s or value not in (PROPOSED, ALT):
                raise ValueError(f"unknown switch {key}={value}")
            self.s[key] = value

    @classmethod
    def fixes_only(cls) -> "Replacement":
        return cls(**NVIDIA_SIDE)

    def alt(self, decision: str) -> bool:
        return self.s[decision] == ALT

    # --- G1 extraction ---------------------------------------------------------------
    def graded_text(self, raw: str, thinking: bool) -> str | None:
        """G1. None is an extraction failure."""
        if "</think>" in raw:
            return raw[raw.rfind("</think>") + len("</think>"):]
        if thinking:
            return None
        if self.alt("D-think-nonthinking"):
            return None if "<think>" in raw else raw
        if raw.lstrip().startswith("<think>"):
            return None
        return raw

    # --- G3 words ----------------------------------------------------------------------
    def words(self, text: str) -> list[str]:
        if self.alt("D-word") and self.alt("D-word-cjk"):
            return WORD_ALT_BOTH.findall(text)
        if self.alt("D-word"):
            return WORD_ALT_JOIN.findall(text) if not self.alt("D-word-cjk") else WORD_ALT_BOTH.findall(text)
        if self.alt("D-word-cjk"):
            return WORD_CJK_RUN.findall(text)
        return WORD_PROPOSED.findall(text)

    def kw_words(self, text: str) -> list[str]:
        """Words for keyword matching: G3 with the D-word switch, CJK one char per word."""
        return WORD_ALT_JOIN.findall(text) if self.alt("D-word") else WORD_PROPOSED.findall(text)

    def _eq(self, a: str, b: str) -> bool:
        return a == b if self.alt("D-keyword-case") else a.casefold() == b.casefold()

    # --- G4 keyword counting -------------------------------------------------------------
    def keyword_count(self, text: str, keyword: str) -> int:
        keyword = keyword.strip()
        if self.alt("D-keyword-substring"):
            flags = 0 if self.alt("D-keyword-case") else re.IGNORECASE
            return len(re.findall(re.escape(keyword), text, flags))
        kws = self.kw_words(keyword)
        if not kws:
            return 0
        tw = self.kw_words(text)
        k = len(kws)
        count = 0
        i = 0
        while i + k <= len(tw):
            if all(self._eq(tw[i + j], kws[j]) for j in range(k)):
                count += 1
                i += k
            else:
                i += 1
        return count

    # --- G5 sentences --------------------------------------------------------------------
    def _split_line(self, line: str) -> list[str]:
        out = []
        start = 0
        for m in TERMINAL.finditer(line):
            end = m.end()
            if end < len(line) and not line[end].isspace():
                continue  # 3.14, file.txt, a.m
            before = line[start:m.start()]
            last = before.split()[-1].lower() if before.split() else ""
            last = last.lstrip("(\"'“")
            if m.group(0) == "." and last.rstrip(".") in ABBREVIATIONS:
                continue
            if m.group(0) == "." and len(last) == 1 and last.isalpha():
                continue  # an initial such as "J."
            out.append(line[start:end])
            start = end
        out.append(line[start:])
        return out

    def sentences(self, text: str) -> list[str]:
        if self.alt("D-sentence-lines"):
            lines = [" ".join(LIST_MARKER.sub("", l) for l in text.splitlines())]
        else:
            lines = [LIST_MARKER.sub("", l) for l in text.splitlines()]
        out = []
        for line in lines:
            for seg in self._split_line(line):
                if WORDCHAR_RE.search(seg):
                    out.append(seg.strip())
        return out

    # --- G6 first / last word -------------------------------------------------------------
    def first_word(self, text: str) -> str | None:
        if self.alt("D-first-last-markup"):
            toks = text.split()
            if not toks:
                return None
            tok = toks[0]
            tok = tok.rstrip("".join(c for c in set(tok) if unicodedata.category(c).startswith("P") and c not in MARKUP_CHARS))
            return tok
        w = self.words(text)
        return w[0] if w else None

    def last_word(self, text: str) -> str | None:
        if self.alt("D-first-last-markup"):
            toks = text.split()
            if not toks:
                return None
            tok = toks[-1]
            while tok and unicodedata.category(tok[-1]).startswith("P") and tok[-1] not in MARKUP_CHARS:
                tok = tok[:-1]
            return tok
        w = self.words(text)
        return w[-1] if w else None

    # --- paragraphs ------------------------------------------------------------------------
    def blank_paragraphs(self, text: str) -> list[str] | None:
        """Paragraphs separated by blank lines; None when an empty paragraph sits between two."""
        if self.alt("D-paragraph-blank"):
            parts = text.strip().split("\n\n")
            if any(not p.strip() for p in parts):
                return None
            return parts if text.strip() else []
        return [p for p in re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", text.strip()) if p.strip()]

    def divider_parts(self, text: str, divider_line: str) -> list[str] | None:
        """Parts between divider lines; None when a part between two dividers is empty."""
        if self.alt("D-divider-line") and divider_line == "***":
            parts = re.split(r"\*\*\*", text)
        else:
            parts = re.split(r"(?m)^[ \t]*" + re.escape(divider_line) + r"[ \t]*$", text)
        while parts and not self.words(parts[0]):
            parts = parts[1:]
        while parts and not self.words(parts[-1]):
            parts = parts[:-1]
        if any(not self.words(p) for p in parts):
            return None
        return parts

    # --- language ----------------------------------------------------------------------------
    @staticmethod
    def _strip_code(text: str) -> str:
        text = re.sub(r"```.*?(```|$)", " ", text, flags=re.S)
        text = re.sub(r"`[^`\n]*`", " ", text)
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        return text

    def lang_ok(self, text: str, code: str, mixed_switch: str) -> bool:
        import langdetect
        from langdetect import DetectorFactory

        DetectorFactory.seed = 0
        body = self._strip_code(text)
        if not any(c.isalpha() for c in body):
            return False
        try:
            if langdetect.detect(body) != code:
                return False
        except langdetect.LangDetectException:
            return False
        if self.alt(mixed_switch):
            for line in body.splitlines():
                if len(self.words(line)) >= 5:
                    try:
                        if langdetect.detect(line) != code:
                            return False
                    except langdetect.LangDetectException:
                        return False
        return True

    @staticmethod
    def _rel(actual: int, relation: str, n: int) -> bool:
        if relation == "less than":
            return actual < n
        if relation == "at least":
            return actual >= n
        if relation == "at most":
            return actual <= n
        if relation in ("exactly", "equal"):
            return actual == n
        raise ValueError(relation)

    # --- the checks ----------------------------------------------------------------------------
    def check(self, iid: str, kw: dict | None, text: str | None, prompt: str | None = None) -> bool:
        if text is None:
            return False
        kw = {k: v for k, v in (kw or {}).items() if v is not None}
        fn = getattr(self, "c_" + iid.replace(":", "__"))
        return bool(fn(text, kw))

    def c_change_case__capital_word_frequency(self, t, kw):
        n = 0
        for w in self.words(t):
            cased = [c for c in w if c.isupper() or c.islower()]
            if cased and all(c.isupper() for c in cased):
                if self.alt("D-allcaps-short") and len(cased) < 2:
                    continue
                n += 1
        return self._rel(n, kw["capital_relation"], kw["capital_frequency"])

    def _case_body(self, t):
        return self._strip_code(t) if self.alt("D-case-scope") else t

    def c_change_case__english_capital(self, t, kw):
        if any(c.islower() for c in self._case_body(t)):
            return False
        return self.lang_ok(t.lower(), "en", "D-english-mixed")

    def c_change_case__english_lowercase(self, t, kw):
        body = self._case_body(t)
        if any(c.isupper() or unicodedata.category(c) == "Lt" for c in body):
            return False
        return self.lang_ok(t, "en", "D-english-mixed")

    def c_combination__two_responses(self, t, kw):
        runs = list(re.finditer(r"\*+", t))
        if self.alt("D-two-sep"):
            seps = [m for m in runs if len(m.group(0)) >= 6]
        else:
            seps = [m for m in runs if len(m.group(0)) == 6]
        if self.alt("D-two-sep-edge"):  # separators with no response before or after them are ignored
            seps = [m for m in seps if self.words(t[: m.start()]) and self.words(t[m.end():])]
        if len(seps) != 1:
            return False
        a, b = t[: seps[0].start()], t[seps[0].end():]
        if not self.words(a) or not self.words(b):
            return False
        if self.alt("D-two-different"):
            norm = lambda s: " ".join(w.casefold() for w in self.words(s))
            return norm(a) != norm(b)
        return a.strip() != b.strip()

    def c_copy__repeat_phrase(self, t, kw):
        fold = (lambda w: w) if self.alt("D-keyword-case") else str.casefold
        phrase = [fold(w) for w in self.kw_words(kw["phrase"])]
        k = len(phrase)
        tw = [fold(w) for w in self.kw_words(t)]
        if self.alt("D-repeat-center"):
            centers = {k // 2} if k % 2 else {k // 2 - 1, k // 2}
        else:
            centers = set(range(1, k - 1))
        variants = copies = 0
        i = 0
        while i + k <= len(tw):
            window = tw[i:i + k]
            diffs = [j for j in range(k) if window[j] != phrase[j]]
            if not diffs:
                copies += 1
                i += k
            elif len(diffs) == 1 and diffs[0] in centers:
                variants += 1
                i += k
            else:
                i += 1
        if self.alt("D-repeat-copies") and copies:
            return False
        return variants == kw["small_n"]

    def c_count__count_unique(self, t, kw):
        ws = self.words(t)
        if not self.alt("D-unique-case"):
            ws = [w.casefold() for w in ws]
        return len(ws) == len(set(ws))

    def c_count__counting_composition(self, t, kw):
        parts = self.divider_parts(t, "* * *")
        if parts is None or len(parts) != 3:
            return False
        for p in parts:
            ss = self.sentences(p)
            if len(ss) != kw["n_sent"]:
                return False
            if any(len(self.words(s)) != kw["n_words"] for s in ss):
                return False
        return True

    def c_count__lowercase_counting(self, t, kw):
        low = []
        for w in self.words(t):
            cased = [c for c in w if c.isupper() or c.islower()]
            if cased and all(c.islower() for c in cased):
                low.append(w)
        if self.alt("D-lowercase-scope"):
            return len(low) <= kw["N"]
        counts = {}
        for w in low:
            counts[w] = counts.get(w, 0) + 1
        return all(v <= kw["N"] for v in counts.values())

    def c_detectable_content__number_placeholders(self, t, kw):
        n = 0
        for m in re.finditer(r"\[([^\[\]\n]*)\]", t):
            content = m.group(1)
            if not content.strip():
                continue
            if self.alt("D-placeholder"):
                if t[m.end():m.end() + 1] == "(" or content.strip().isdigit():
                    continue
            n += 1
        return n >= kw["num_placeholders"]

    def c_detectable_content__postscript(self, t, kw):
        marker = kw["postscript_marker"]
        base = marker.rstrip(".")
        dot = r"\." if (marker.endswith(".") and self.alt("D-postscript-dot")) else r"\.?"
        if self.alt("D-postscript-line"):
            # the marker starts a line, or follows the end of a sentence or a dash, then whitespace
            lead = r"(?:^[ \t]*|(?<=[.!?:;–—\-][ \t]))(?:[*_\[(\"'“‘]+[ \t]*)?"
        else:
            lead = r"^[ \t]*(?:[*_>#\[(\"'“‘]+[ \t]*)?"
        pat = lead + re.escape(base) + dot + r"(?![A-Za-z])"
        flags = re.MULTILINE | (0 if self.alt("D-postscript-case") else re.IGNORECASE)
        hits = list(re.finditer(pat, t.strip(), flags))
        if not hits:
            return False
        if self.alt("D-postscript-end"):
            return True
        body = t.strip()
        last = hits[-1].start()
        return not re.search(r"\n[ \t]*\n\s*\S", body[last:])

    def c_detectable_format__bigram_wrapping(self, t, kw):
        groups = re.findall(r"<<(.*?)>>", t, flags=re.S)
        outside = re.sub(r"<<.*?>>", " ", t, flags=re.S)
        if self.words(outside):
            return False
        sizes = [len(self.words(g)) for g in groups]
        if any(s == 0 or s > 2 for s in sizes):
            return False
        singles = sizes.count(1)
        if self.alt("D-bigram-odd"):
            return singles == 0
        return singles == 0 or (singles == 1 and sum(sizes) % 2 == 1)

    OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")

    def c_detectable_format__constrained_response(self, t, kw):
        if self.alt("D-constrained-extra"):
            return sum(1 for o in self.OPTIONS if o in t) == 1
        return t.strip() in self.OPTIONS

    def c_detectable_format__json_format(self, t, kw):
        s = t.strip()
        m = re.fullmatch(r"```[A-Za-z0-9_+-]*[ \t]*\n?(.*?)\n?[ \t]*```", s, flags=re.S)
        if m:
            s = m.group(1).strip()

        def bad_constant(name):
            raise ValueError(name)

        try:
            value = json.loads(s, parse_constant=bad_constant)
        except ValueError:
            return False
        if self.alt("D-json-scalar"):
            return isinstance(value, (dict, list))
        return True

    def c_detectable_format__multiple_sections(self, t, kw):
        spl = kw["section_spliter"].strip()
        flags = re.MULTILINE | (re.IGNORECASE if self.alt("D-sections-case") else 0)
        pat = re.compile(r"^[ \t]*[\"'“\[(]?[ \t]*(?:#{1,6}[ \t]*)?(?:[*_]{1,3})?" + re.escape(spl) + r"[ \t]+(\d+)\b", flags)
        ms = list(pat.finditer(t))
        n = kw["num_sections"]
        if len(ms) != n:
            return False
        if not self.alt("D-sections-number"):
            if [int(m.group(1)) for m in ms] != list(range(1, n + 1)):
                return False
        if self.alt("D-sections-preamble") and ms and self.words(t[: ms[0].start()]):
            return False
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
            if not self.words(t[m.end():end]):
                return False
        return True

    def c_detectable_format__number_bullet_lists(self, t, kw):
        marks = "*" if self.alt("D-bullet-markers") else "*+\\-"
        n = 0
        for line in t.splitlines():
            if re.fullmatch(r"\s*([*\-_]\s*){3,}", line):
                continue  # horizontal rule
            m = re.match(r"^(\s*)[" + marks + r"]\s+\S", line)
            if m:
                if self.alt("D-bullet-nested") and m.group(1):
                    continue
                n += 1
        return n == kw["num_bullets"]

    def c_detectable_format__number_highlighted_sections(self, t, kw):
        n = 0
        for line in t.splitlines():
            line = re.sub(r"^\s*[*+\-]\s+", "", line)  # a bullet marker is not emphasis
            bold = list(re.finditer(r"\*\*(?=\S)([^*\n]*?\S)\*\*", line))
            if not self.alt("D-highlight-bold"):
                n += len(bold)
            rest = re.sub(r"\*\*(?=\S)([^*\n]*?\S)\*\*", " ", line)
            n += len(re.findall(r"(?<!\*)\*(?=\S)([^*\n]*?\S)\*(?!\*)", rest))
        return n >= kw["num_highlights"]

    def c_detectable_format__sentence_hyphens(self, t, kw):
        s = t.strip()
        if not self.words(s):
            return not self.alt("D-hyphens-single")  # no sentences: nothing to connect
        connections = 0
        if not self.alt("D-sentence-lines"):
            if "\n" in s:
                return False
        dashes = "-\u2010\u2011\u2012\u2013\u2014\u2015" if self.alt("D-hyphen-dash") else "-\u2010\u2011"
        if re.search(r"\s[" + dashes + r"]|[" + dashes + r"]\s", s):
            return False  # clauses joined by a dash with a space: spaces between sentences
        if not self.alt("D-hyphen-dash") and re.search("[\u2012\u2013\u2014\u2015]", s):
            return False  # an en or em dash is not a hyphen
        for m in TERMINAL.finditer(s):
            end = m.end()
            if end >= len(s):
                continue
            nxt = s[end]
            if nxt in dashes:
                if end + 1 < len(s) and not s[end + 1].isspace():
                    connections += 1
                    continue
                return False
            if nxt.isspace():
                before = s[:m.start()].split()
                last = before[-1].lower() if before else ""
                if m.group(0) == "." and (last.rstrip(".") in ABBREVIATIONS or (len(last) == 1 and last.isalpha())):
                    continue
                return False
        if self.alt("D-hyphens-single") and connections == 0:
            return False
        return True

    def c_detectable_format__square_brackets(self, t, kw):
        spans = re.findall(r"\[([^\[\]]*)\]", t)
        outside = re.sub(r"\[[^\[\]]*\]", " ", t)
        if self.words(outside):
            return False
        if not self.alt("D-brackets-per-word"):
            if any(len(self.words(sp)) > 1 for sp in spans):
                return False
        return True

    def c_detectable_format__title(self, t, kw):
        if self.alt("D-title-position"):
            lines = [l for l in t.strip().splitlines() if l.strip()]
            t = lines[0] if lines else ""
        return any(m.strip() for m in re.findall(r"<<([^<>\n]*?)>>", t))

    def c_first_word__first_word_answer(self, t, kw):
        w = self.first_word(t)
        return w is not None and w.casefold() == kw["first_word"].casefold()

    def c_first_word__first_word_sent(self, t, kw):
        for s in self.sentences(t):
            w = self.first_word(s)
            if w is None or w.casefold() != kw["first_word"].casefold():
                return False
        return True

    def c_keywords__existence(self, t, kw):
        return all(self.keyword_count(t, k) >= 1 for k in kw["keywords"])

    def c_keywords__forbidden_words(self, t, kw):
        return all(self.keyword_count(t, k) == 0 for k in kw["forbidden_words"])

    def c_keywords__frequency(self, t, kw):
        return self._rel(self.keyword_count(t, kw["keyword"]), kw["relation"], kw["frequency"])

    def c_keywords__keyword_specific_position(self, t, kw):
        ss = self.sentences(t)
        n, m = kw["n"], kw["m"]
        if len(ss) < n:
            return False
        ws = self.words(ss[n - 1])
        if len(ws) < m:
            return False
        return self._eq(ws[m - 1], kw["keyword"].strip())

    def _letter_count(self, t, letter):
        if self.alt("D-letter-case"):
            return t.count(letter)
        return sum(1 for c in t if c.lower() == letter.lower())

    def c_keywords__letter_frequency(self, t, kw):
        return self._rel(self._letter_count(t, kw["letter"]), kw["let_relation"], kw["let_frequency"])

    c_letters__letter_counting2 = c_keywords__letter_frequency

    def c_keywords__no_adjacent_consecutive(self, t, kw):
        firsts = []
        for w in self.words(t):
            c = w[0].lower()
            if len(c) == 1 and "a" <= c <= "z":
                firsts.append(("latin", c))
            elif len(c) == 1 and "\u0430" <= c <= "\u044f" and not self.alt("D-consecutive-script"):
                firsts.append(("cyrillic", c))
            elif len(c) == 1 and "\u03b1" <= c <= "\u03c9" and c != "\u03c2" and not self.alt("D-consecutive-script"):
                firsts.append(("greek", c))
            else:
                firsts.append(None)
        for a, b in zip(firsts, firsts[1:]):
            if a is None or b is None or a[0] != b[0]:
                continue
            a, b = a[1], b[1]
            d = ord(b) - ord(a)
            if d == 1 or (d == -1 and not self.alt("D-consecutive-order")):
                return False
        return True

    def c_keywords__palindrome(self, t, kw):
        minimum = 1 if self.alt("D-palindrome-min") else 3
        ws = ["".join(c for c in w.casefold() if c.isalnum()) for w in self.words(t)]
        ws = [w for w in ws if w]
        for i in range(len(ws)):
            s = ""
            for j in range(i, min(i + 10, len(ws))):
                s += ws[j]
                if len(s) >= minimum and s == s[::-1]:
                    return True
        return False

    def c_keywords__start_end(self, t, kw):
        s = t.strip()
        if not s or not WORDCHAR_RE.match(s[-1]):
            return False
        if self.alt("D-start-markup") and not WORDCHAR_RE.match(s[0]):
            return False
        ws = self.words(s)
        if not ws:
            return False
        if self.alt("D-start-end-single") and len(ws) < 2:
            return False
        return ws[0].casefold() == ws[-1].casefold()

    def c_keywords__word_count_different_numbers(self, t, kw):
        c = self.keyword_count(t, kw["keyword"])
        return c >= kw["frequency"] if self.alt("D-appear-n-times") else c == kw["frequency"]

    def c_keywords__word_once(self, t, kw):
        return self.keyword_count(t, kw["keyword"]) >= 1

    def c_language__response_language(self, t, kw):
        return self.lang_ok(t, kw["language"], "D-language-mixed")

    def c_last_word__last_word_answer(self, t, kw):
        w = self.last_word(t)
        return w is not None and w.casefold() == kw["last_word"].casefold()

    def c_last_word__last_word_sent(self, t, kw):
        for s in self.sentences(t):
            w = self.last_word(s)
            if w is None or w.casefold() != kw["last_word"].casefold():
                return False
        return True

    def c_length_constraints__nth_paragraph_first_word(self, t, kw):
        ps = self.blank_paragraphs(t)
        if ps is None or len(ps) != kw["num_paragraphs"]:
            return False
        nth = kw["nth_paragraph"]
        if nth < 1 or nth > len(ps):
            return False
        w = self.first_word(ps[nth - 1])
        return w is not None and w.casefold() == kw["first_word"].casefold()

    def c_length_constraints__number_paragraphs(self, t, kw):
        parts = self.divider_parts(t, "***")
        return parts is not None and len(parts) == kw["num_paragraphs"]

    def c_length_constraints__number_sentences(self, t, kw):
        return self._rel(len(self.sentences(t)), kw["relation"], kw["num_sentences"])

    def c_length_constraints__number_words(self, t, kw):
        return self._rel(len(self.words(t)), kw["relation"], kw["num_words"])

    def c_letters__letter_counting(self, t, kw):
        n = len(self.words(t)) if self.alt("D-letter-unit") else sum(1 for c in t if c.isalpha())
        return self._rel(n, kw["relation"], kw["N"])

    def c_paragraphs__paragraphs(self, t, kw):
        parts = self.divider_parts(t, "***")
        return parts is not None and len(parts) == 2

    def c_paragraphs__paragraphs2(self, t, kw):
        ps = self.blank_paragraphs(t)
        return ps is not None and len(ps) == 2

    COMMAS = {",", "，", "、", "،", "﹐", "﹑", "､"}
    DOTS = {".", "．", "…", "․", "‥"}
    EXCLAMATIONS = {"!", "！", "¡", "‼"}

    def c_punctuation__no_comma(self, t, kw):
        chars = {","} if self.alt("D-comma-variants") else self.COMMAS
        return not any(c in chars for c in t)

    def c_punctuation__punctuation_dot(self, t, kw):
        chars = {"."} if self.alt("D-dot-variants") else self.DOTS
        return not any(c in chars for c in t)

    def c_punctuation__punctuation_exclamation(self, t, kw):
        chars = {"!"} if self.alt("D-exclamation-variants") else self.EXCLAMATIONS
        return not any(c in chars for c in t)

    def c_startend__end_checker(self, t, kw):
        phrase = kw["end_phrase"].strip()
        s = t.rstrip()
        tail = r"\s*$" if self.alt("D-end-trailing") else r"[^\w]*$"
        flags = re.IGNORECASE if self.alt("D-end-case") else 0
        m = re.search(re.escape(phrase) + tail, s, flags)
        if not m:
            return False
        before = s[: m.start()]
        return not (before and WORDCHAR_RE.match(before[-1]))

    def c_startend__quotation(self, t, kw):
        s = t.strip()
        if len(s) < 2:
            return False
        if self.alt("D-quote-curly"):
            return s[0] == '"' and s[-1] == '"'
        return s[0] in '"“' and s[-1] in '"”'
