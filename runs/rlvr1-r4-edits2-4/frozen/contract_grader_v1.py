"""Replacement grader: the contracts of audit/CONTRACTS.md, one switch per decision entry.

Reading "A" of every entry is the proposed reading (B for D-hyphens-single and
D-word-cjk, see DEFAULT_READINGS). Language checks use langdetect (seed 0) as an
approximation of "written in language X"; they are the only checks here that do
not follow from the contract text alone.
"""
from __future__ import annotations

import json
import unicodedata

import regex as re

DEFAULT_READINGS = {
    "D-empty-response": "A",
    "D-word-units": "A",
    "D-word-cjk": "B",  # open question; follows the reference (a CJK run is one word)
    "D-word-case": "A",
    "D-keyword-inflection": "A",
    "D-sentence-split": "A",
    "D-capital-word": "A",
    "D-language-mixed": "A",
    "D-two-different": "A",
    "D-repeat-center": "A",
    "D-repeat-original": "A",
    "D-lowercase-count": "A",
    "D-lowercase-scope": "A",
    "D-placeholder": "A",
    "D-postscript-case": "A",
    "D-postscript-position": "A",
    "D-bigram-odd": "A",
    "D-constrained-extra": "A",
    "D-json-value": "A",
    "D-section-case": "A",
    "D-section-label": "A",
    "D-sections-preamble": "A",
    "D-bullet-markers": "A",
    "D-highlight-bold": "A",
    "D-hyphens-single": "B",
    "D-hyphens-spaces": "A",
    "D-brackets-each": "A",
    "D-title-position": "A",
    "D-consecutive-order": "A",
    "D-palindrome-unit": "A",
    "D-palindrome-length": "A",
    "D-word-count-exact": "A",
    "D-paragraph-blank-lines": "A",
    "D-divider-form": "A",
    "D-divider-edges": "A",
    "D-divider-blank-lines": "A",
    "D-letter-case": "A",
    "D-letter-script": "A",
    "D-comma-chars": "A",
    "D-dot-chars": "A",
    "D-exclamation-chars": "A",
    "D-end-markup": "A",
    "D-end-case": "A",
    "D-quote-chars": "A",
    "D-start-end-single": "A",
}

WORD_CHARS = r"[\p{L}\p{N}\p{M}]"
WORD_A = re.compile(WORD_CHARS + r"+(?:['’\-]" + WORD_CHARS + r"+)*")
WORD_B = re.compile(WORD_CHARS + r"+")
CJK = re.compile(r"[\p{Han}\p{Hiragana}\p{Katakana}]")
COMMAS = {"A": ",，、،﹐", "B": ","}
DOTS = {"A": ".．。…", "B": "."}
EXCLAMATIONS = {"A": "!！¡‼❗❕", "B": "!"}
ABBREVIATIONS = {
    "e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "inc", "ltd", "co",
    "no", "fig", "approx", "dept", "est", "u.s", "u.k", "a.m", "p.m", "ph.d", "cf", "al",
}
THEMATIC_BREAK = re.compile(r"^\s*([*\-_])(?:\s*\1){2,}\s*$")
LIST_LABEL = re.compile(r"^(\s*)(?:\d{1,3}|[A-Za-z])[.)](\s+)", re.M)
CONSTRAINED = ("My answer is yes.", "My answer is no.", "My answer is maybe.")
HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*\s*/?>")


class ContractGrader:
    def __init__(self, readings: dict[str, str] | None = None):
        self.r = {**DEFAULT_READINGS, **(readings or {})}
        import langdetect
        from langdetect import DetectorFactory

        DetectorFactory.seed = 0
        self._langdetect = langdetect

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def extract(raw: str, thinking: bool) -> str | None:
        """Graded text; None is an extraction failure (a thinking response without </think>)."""
        if thinking:
            end = raw.rfind("</think>")
            if end < 0:
                return None
            return raw[end + len("</think>"):].strip()
        return raw.strip()

    def words(self, text: str) -> list[str]:
        pattern = WORD_A if self.r["D-word-units"] == "A" else WORD_B
        found = pattern.findall(text)
        if self.r["D-word-cjk"] == "A":
            out = []
            for w in found:
                if CJK.search(w):
                    out.extend(ch for ch in w if CJK.match(ch) or ch.isalnum())
                else:
                    out.append(w)
            return out
        return found

    def norm(self, word: str) -> str:
        word = word.replace("’", "'")
        return word.lower() if self.r["D-word-case"] == "A" else word

    def same_word(self, word: str, keyword: str) -> bool:
        a, b = self.norm(word), self.norm(keyword)
        if a == b:
            return True
        if self.r["D-keyword-inflection"] == "B":
            for suffix in ("s", "es", "ed", "d", "ing", "'s"):
                if a == b + suffix:
                    return True
        return False

    def count_keyword(self, text: str, keyword: str) -> int:
        return sum(1 for w in self.words(text) if self.same_word(w, keyword))

    def sentences(self, text: str) -> list[str]:
        # Protect list labels ("1. ", "a) ") at line starts.
        text = LIST_LABEL.sub(lambda m: m.group(1) + "\u0000" + m.group(2), text)
        units = text.split("\n") if self.r["D-sentence-split"] == "A" else [text.replace("\n", " ")]
        out: list[str] = []
        for unit in units:
            start = 0
            for m in re.finditer(r"[.!?。！？…]+[\"'”’)\]*_]*(?=\s|$)|[。！？]+", unit):
                end = m.end()
                piece = unit[start:end]
                tail_word = re.search(r"([\p{L}.]+)[.]$", unit[start:m.start() + 1])
                if m.group(0).startswith(".") and len(m.group(0).rstrip("\"'”’)]*_")) == 1 and tail_word:
                    token = tail_word.group(1).lower().rstrip(".")
                    if token in ABBREVIATIONS or (len(token) == 1 and token.isalpha()):
                        continue
                out.append(piece)
                start = end
            out.append(unit[start:])
        result = []
        for s in out:
            s = s.replace("\u0000", "").strip()
            if s and self.words(s):
                result.append(s)
        return result

    def blank_line_paragraphs(self, text: str) -> list[str] | None:
        if self.r["D-paragraph-blank-lines"] == "A":
            return [p for p in re.split(r"\n[ \t]*\n(?:[ \t]*\n)*", text) if p.strip()]
        parts = text.split("\n\n")
        if any(not p.strip() for p in parts[1:-1]):
            return None  # an empty paragraph between separators
        return [p for p in parts if p.strip()]

    def divider_paragraphs(self, text: str, form: str) -> list[str] | None:
        lines = text.split("\n")
        parts: list[list[str]] = [[]]
        for line in lines:
            stripped = line.strip()
            is_divider = stripped == form if self.r["D-divider-form"] == "A" else bool(THEMATIC_BREAK.match(line))
            if is_divider:
                parts.append([])
            else:
                parts[-1].append(line)
        blocks = ["\n".join(p) for p in parts]
        if self.r["D-divider-edges"] == "A":
            if any(not b.strip() for b in blocks):
                return None
        else:
            if any(not b.strip() for b in blocks[1:-1]):
                return None
            blocks = [b for b in blocks if b.strip()]
        if self.r["D-divider-blank-lines"] == "B":
            split: list[str] = []
            for b in blocks:
                split.extend(p for p in re.split(r"\n\s*\n", b) if p.strip())
            blocks = split
        return blocks

    @staticmethod
    def relation(count: int, relation: str, n: int) -> bool:
        if relation == "less than":
            return count < n
        if relation == "at least":
            return count >= n
        raise ValueError(f"unknown relation {relation!r}")

    def detect(self, text: str) -> str | None:
        try:
            return self._langdetect.detect(text)
        except Exception:
            return None

    def in_language(self, text: str, code: str) -> bool:
        """Reading A: the whole text and every sentence of 5+ words detect as the language
        (names, numbers, code and short phrases are allowed). Reading B: every sentence."""
        if self.detect(text) != code:
            return False
        min_words = 5 if self.r["D-language-mixed"] == "A" else 1
        saved = self.r["D-sentence-split"]
        self.r["D-sentence-split"] = "A"
        try:
            pieces = self.sentences(text)
        finally:
            self.r["D-sentence-split"] = saved
        for piece in pieces:
            if len(self.words(piece)) >= min_words and self.detect(piece) != code:
                return False
        return True

    # ------------------------------------------------------------------ entry point
    def check(self, iid: str, kwargs: dict | None, g: str | None) -> bool:
        if g is None:
            return False  # extraction failure
        kwargs = {k: v for k, v in (kwargs or {}).items() if v is not None}
        if not g.strip() and self.r["D-empty-response"] == "A":
            return False
        g = HTML_TAG.sub("", g)  # HTML tags are markup, not words
        fn = getattr(self, "c_" + iid.replace(":", "__"))
        return bool(fn(g, kwargs))

    # ------------------------------------------------------------------ checks
    def c_change_case__capital_word_frequency(self, g, kw):
        n = 0
        for w in self.words(g):
            letters = [c for c in w if c.isalpha()]
            cased = [c for c in letters if c.lower() != c.upper()]
            if not cased or any(not c.isupper() for c in cased):
                continue
            if self.r["D-capital-word"] == "B" and len(letters) < 2:
                continue
            n += 1
        return self.relation(n, kw["capital_relation"], kw["capital_frequency"])

    def c_change_case__english_capital(self, g, kw):
        if any(c.islower() for c in g):
            return False
        if not any(c.isalpha() for c in g):
            return False
        return self.in_language(g.lower(), "en")

    def c_change_case__english_lowercase(self, g, kw):
        if any(c.isupper() or c.istitle() for c in g):
            return False
        if not any(c.isalpha() for c in g):
            return False
        return self.in_language(g, "en")

    def c_combination__two_responses(self, g, kw):
        seps = list(re.finditer(r"(?<!\*)\*{6}(?!\*)", g))
        if len(seps) != 1:
            return False
        a, b = g[: seps[0].start()].strip(), g[seps[0].end():].strip()
        if not a or not b:
            return False
        if self.r["D-two-different"] == "A":
            return a != b
        na = " ".join(w.lower() for w in self.words(a))
        nb = " ".join(w.lower() for w in self.words(b))
        return na != nb

    def c_copy__repeat_phrase(self, g, kw):
        phrase = [self.norm(w) for w in WORD_A.findall(kw["phrase"])]
        k = len(phrase)
        n = kw["small_n"]
        center = {k // 2} if k % 2 else {k // 2 - 1, k // 2}
        if self.r["D-repeat-center"] == "B":
            center = set(range(1, k - 1))
        tokens = [self.norm(w) for w in WORD_A.findall(g)]
        variants = exact = bad = 0
        i = 0
        while i + k <= len(tokens):
            window = tokens[i:i + k]
            if window[0] == phrase[0] and window[-1] == phrase[-1]:
                diffs = [j for j in range(k) if window[j] != phrase[j]]
                if not diffs:
                    exact += 1
                elif len(diffs) == 1 and diffs[0] in center:
                    variants += 1
                else:
                    bad += 1
                i += k
            else:
                i += 1
        if self.r["D-repeat-original"] == "A":
            return variants == n and exact == 0 and bad == 0
        return variants == n and bad == 0

    def c_count__count_unique(self, g, kw):
        ws = [self.norm(w) for w in self.words(g)]
        return len(ws) == len(set(ws))

    def c_count__counting_composition(self, g, kw):
        form = "* * *"
        paras = self.divider_paragraphs(g, form)
        if paras is None or len(paras) != 3:
            return False
        for p in paras:
            ss = self.sentences(p.strip())
            if len(ss) != kw["n_sent"]:
                return False
            if any(len(self.words(s)) != kw["n_words"] for s in ss):
                return False
        return True

    def c_count__lowercase_counting(self, g, kw):
        n = kw["N"]
        ws = self.words(g)

        def is_lower(w):
            cased = [c for c in w if c.lower() != c.upper()]
            return bool(cased) and all(c.islower() for c in cased)

        lower_forms = [w for w in ws if is_lower(w)]
        if self.r["D-lowercase-scope"] == "B":
            return len(lower_forms) <= n
        counts: dict[str, int] = {}
        if self.r["D-lowercase-count"] == "A":
            for w in lower_forms:
                counts[w] = counts.get(w, 0) + 1
        else:
            seen = {w for w in lower_forms}
            for w in ws:
                if w.lower() in seen:
                    counts[w.lower()] = counts.get(w.lower(), 0) + 1
        return all(c <= n for c in counts.values())

    def c_detectable_content__number_placeholders(self, g, kw):
        n = 0
        for m in re.finditer(r"\[([^\[\]\n]*)\]", g):
            content = m.group(1).strip()
            if not content:
                continue
            if self.r["D-placeholder"] == "B":
                if g[m.end():m.end() + 1] == "(" or not re.search(r"\p{L}", content):
                    continue
            n += 1
        return n >= kw["num_placeholders"]

    def c_detectable_content__postscript(self, g, kw):
        marker = kw["postscript_marker"].strip()
        paras = [p for p in re.split(r"\n[ \t]*\n", g) if p.strip()]
        if not paras:
            return False

        def starts(p):
            body = re.sub(r"^[\s*_#>]+", "", p)
            if self.r["D-postscript-case"] == "B":
                return body.lower().startswith(marker.lower())
            return body.startswith(marker)

        if self.r["D-postscript-position"] == "A":
            return starts(paras[-1])
        return any(starts(p) for p in paras)

    def c_detectable_format__bigram_wrapping(self, g, kw):
        groups = list(re.finditer(r"<<([^<>]*)>>", g))
        outside = re.sub(r"<<([^<>]*)>>", " ", g)
        if self.words(outside) or not groups:
            return False
        sizes = [len(self.words(m.group(1))) for m in groups]
        total = sum(sizes)
        ones = sizes.count(1)
        if any(s not in (1, 2) for s in sizes):
            return False
        if self.r["D-bigram-odd"] == "A":
            return ones == 0 or (ones == 1 and total % 2 == 1)
        return ones == 0

    def c_detectable_format__constrained_response(self, g, kw):
        if self.r["D-constrained-extra"] == "B":
            return g.strip() in CONSTRAINED
        present = [o for o in CONSTRAINED if o in g]
        return len(present) == 1

    def c_detectable_format__json_format(self, g, kw):
        s = g.strip()
        m = re.match(r"^```[A-Za-z]*[ \t]*\n?(.*?)\n?[ \t]*```$", s, flags=re.S)
        if m:
            s = m.group(1).strip()

        def reject(_):
            raise ValueError("non-standard constant")

        try:
            value = json.loads(s, parse_constant=reject)
        except ValueError:
            return False
        if self.r["D-json-value"] == "A":
            return isinstance(value, (dict, list))
        return True

    def c_detectable_format__multiple_sections(self, g, kw):
        splitter = kw["section_spliter"].strip()
        flags = re.I if self.r["D-section-case"] == "A" else 0
        label = r"(?:\d+|[IVXLCivxlc]+|[A-Za-z])" if self.r["D-section-label"] == "A" else r"\d+"
        marker = re.compile(r"^[ \t]*[#*_>]*[ \t]*" + re.escape(splitter) + r"[ \t]+" + label + r"\b", flags | re.M)
        found = list(marker.finditer(g))
        if len(found) != kw["num_sections"]:
            return False
        pre = g[: found[0].start()].strip() if found else g
        if self.r["D-sections-preamble"] == "A" and pre and "\n" in pre.strip():
            return False
        for i, m in enumerate(found):
            end = found[i + 1].start() if i + 1 < len(found) else len(g)
            if not self.words(g[m.end():end]):
                return False
        return True

    def c_detectable_format__number_bullet_lists(self, g, kw):
        n = 0
        for line in g.split("\n"):
            if THEMATIC_BREAK.match(line):
                continue
            if self.r["D-bullet-markers"] == "A":
                if re.match(r"^\s*[*\-+][ \t]+\S", line):
                    n += 1
            elif re.match(r"^\*[ \t]+\S", line):
                n += 1
        return n == kw["num_bullets"]

    def c_detectable_format__number_highlighted_sections(self, g, kw):
        bold = re.compile(r"\*\*(?!\s)([^*\n]+?)(?<!\s)\*\*")
        n = len(bold.findall(g)) if self.r["D-highlight-bold"] == "A" else 0
        rest = bold.sub(" ", g)
        n += len(re.findall(r"(?<!\*)\*(?![\s*])([^*\n]+?)(?<![\s*])\*(?!\*)", rest))
        return n >= kw["num_highlights"]

    def c_detectable_format__sentence_hyphens(self, g, kw):
        s = g.strip()
        if self.r["D-hyphens-spaces"] == "B" and re.search(r"\s", s):
            return False
        if self.r["D-sentence-split"] == "A" and re.search(r"\S[ \t]*\n\s*\S", s):
            return False  # a line break between two non-empty lines is a sentence boundary
        joins = 0
        for m in re.finditer(r"[.!?]+[\"'”’)]*(?=.)", s, flags=re.S):
            nxt = s[m.end():m.end() + 2]
            if nxt[0] == "-":
                if len(nxt) > 1 and nxt[1].isspace():
                    return False
                joins += 1
                continue
            if nxt[0].isspace():
                tail = re.search(r"([\p{L}.]+)$", s[: m.start() + 1])
                token = tail.group(1).lower().rstrip(".") if tail else ""
                if token in ABBREVIATIONS or (len(token) == 1 and token.isalpha()):
                    continue
                return False  # two sentences separated by whitespace, not a hyphen
        if self.r["D-hyphens-single"] == "A" and joins == 0:
            return False
        return True

    def c_detectable_format__square_brackets(self, g, kw):
        groups = list(re.finditer(r"\[([^\[\]]*)\]", g))
        outside = re.sub(r"\[([^\[\]]*)\]", " ", g)
        if self.words(outside):
            return False
        if not groups:
            return False
        if self.r["D-brackets-each"] == "A":
            return all(len(self.words(m.group(1))) <= 1 for m in groups)
        return True

    def c_detectable_format__title(self, g, kw):
        m = re.search(r"<<([^<>\n]*\S[^<>\n]*)>>", g)
        if not m:
            return False
        if self.r["D-title-position"] == "B":
            return not self.words(g[: m.start()])
        return True

    def c_first_word__first_word_answer(self, g, kw):
        ws = self.words(g)
        return bool(ws) and self.same_word_exact(ws[0], kw["first_word"])

    def same_word_exact(self, word, target):
        return self.norm(word) == self.norm(target)

    def c_first_word__first_word_sent(self, g, kw):
        ss = self.sentences(g)
        return bool(ss) and all(self.same_word_exact(self.words(s)[0], kw["first_word"]) for s in ss)

    def c_keywords__existence(self, g, kw):
        return all(self.count_keyword(g, k) > 0 for k in kw["keywords"])

    def c_keywords__forbidden_words(self, g, kw):
        return all(self.count_keyword(g, k) == 0 for k in kw["forbidden_words"])

    def c_keywords__frequency(self, g, kw):
        return self.relation(self.count_keyword(g, kw["keyword"]), kw["relation"], kw["frequency"])

    def c_keywords__keyword_specific_position(self, g, kw):
        ss = self.sentences(g)
        n, m = kw["n"], kw["m"]
        if len(ss) < n:
            return False
        ws = self.words(ss[n - 1])
        return len(ws) >= m and self.same_word_exact(ws[m - 1], kw["keyword"])

    def c_keywords__letter_frequency(self, g, kw):
        letter = kw["letter"]
        if self.r["D-letter-case"] == "A":
            count = sum(1 for c in g if c.lower() == letter.lower())
        else:
            count = g.count(letter)
        return self.relation(count, kw["let_relation"], kw["let_frequency"])

    def c_keywords__no_adjacent_consecutive(self, g, kw):
        firsts = []
        for w in self.words(g):
            c = unicodedata.normalize("NFKD", w[0])[0].lower()
            firsts.append(c if "a" <= c <= "z" else None)
        for a, b in zip(firsts, firsts[1:]):
            if a is None or b is None:
                continue
            diff = ord(b) - ord(a)
            if diff == 1 or (self.r["D-consecutive-order"] == "A" and diff == -1):
                return False
        return True

    def c_keywords__palindrome(self, g, kw):
        min_len = 3 if self.r["D-palindrome-length"] == "A" else 1
        ws = [w for w in self.words(g)]
        for w in ws:
            core = "".join(c for c in w.lower() if c.isalnum())
            if len(core) >= min_len and core == core[::-1]:
                return True
            if self.r["D-palindrome-unit"] == "B":
                for size in range(max(min_len, 3), len(core)):
                    for i in range(len(core) - size + 1):
                        sub = core[i:i + size]
                        if sub == sub[::-1]:
                            return True
        lowered = ["".join(c for c in w.lower() if c.isalnum()) for w in ws]
        for i in range(len(lowered)):
            for j in range(i + 2, min(len(lowered), i + 12) + 1):
                joined = "".join(lowered[i:j])
                if len(joined) >= 5 and joined == joined[::-1]:
                    return True
        return False

    def c_keywords__start_end(self, g, kw):
        ws = self.words(g)
        if not ws:
            return False
        if len(ws) < 2 and self.r["D-start-end-single"] == "B":
            return False
        if not self.same_word_exact(ws[0], ws[-1]):
            return False
        return g.rstrip().endswith(ws[-1])

    def c_keywords__word_count_different_numbers(self, g, kw):
        count = self.count_keyword(g, kw["keyword"])
        if self.r["D-word-count-exact"] == "A":
            return count == kw["frequency"]
        return count >= kw["frequency"]

    def c_keywords__word_once(self, g, kw):
        return self.count_keyword(g, kw["keyword"]) >= 1

    def c_language__response_language(self, g, kw):
        return self.in_language(g, kw["language"])

    def c_last_word__last_word_answer(self, g, kw):
        ws = self.words(g)
        return bool(ws) and self.same_word_exact(ws[-1], kw["last_word"])

    def c_last_word__last_word_sent(self, g, kw):
        ss = self.sentences(g)
        return bool(ss) and all(self.same_word_exact(self.words(s)[-1], kw["last_word"]) for s in ss)

    def c_length_constraints__nth_paragraph_first_word(self, g, kw):
        paras = self.blank_line_paragraphs(g)
        if paras is None or len(paras) != kw["num_paragraphs"]:
            return False
        nth = kw["nth_paragraph"]
        if not 1 <= nth <= len(paras):
            return False
        ws = self.words(paras[nth - 1])
        return bool(ws) and self.same_word_exact(ws[0], kw["first_word"])

    def c_length_constraints__number_paragraphs(self, g, kw):
        paras = self.divider_paragraphs(g, "***")
        return paras is not None and len(paras) == kw["num_paragraphs"]

    def c_length_constraints__number_sentences(self, g, kw):
        return self.relation(len(self.sentences(g)), kw["relation"], kw["num_sentences"])

    def c_length_constraints__number_words(self, g, kw):
        return self.relation(len(self.words(g)), kw["relation"], kw["num_words"])

    def c_letters__letter_counting(self, g, kw):
        if self.r["D-letter-script"] == "A":
            count = sum(1 for c in g if c.isalpha())
        else:
            count = sum(1 for c in g if c.isascii() and c.isalpha())
        return self.relation(count, kw["relation"], kw["N"])

    def c_letters__letter_counting2(self, g, kw):
        return self.c_keywords__letter_frequency(g, kw)

    def c_paragraphs__paragraphs(self, g, kw):
        paras = self.divider_paragraphs(g, "***")
        return paras is not None and len(paras) == 2

    def c_paragraphs__paragraphs2(self, g, kw):
        paras = self.blank_line_paragraphs(g)
        return paras is not None and len(paras) == 2

    def c_punctuation__no_comma(self, g, kw):
        return not any(c in COMMAS[self.r["D-comma-chars"]] for c in g)

    def c_punctuation__punctuation_dot(self, g, kw):
        return not any(c in DOTS[self.r["D-dot-chars"]] for c in g)

    def c_punctuation__punctuation_exclamation(self, g, kw):
        return not any(c in EXCLAMATIONS[self.r["D-exclamation-chars"]] for c in g)

    def c_startend__end_checker(self, g, kw):
        phrase = kw["end_phrase"].strip()
        s = g.rstrip()
        if self.r["D-end-markup"] == "A":
            s = re.sub(r"[\s*_\"'”’]+$", "", s)
        if self.r["D-end-case"] == "B":
            s, phrase = s.lower(), phrase.lower()
        if not s.endswith(phrase):
            return False
        before = s[: len(s) - len(phrase)]
        return not before or not (before[-1].isalnum())

    def c_startend__quotation(self, g, kw):
        s = g.strip()
        if len(s) <= 2:
            return False
        if s[0] == '"' and s[-1] == '"':
            return True
        return self.r["D-quote-chars"] == "A" and s[0] == "“" and s[-1] == "”"
