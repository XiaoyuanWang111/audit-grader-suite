"""Property and metamorphic generators: each strategy draws (instruction_id, kwargs, response, label)
whose label follows from the contract by construction (proposed readings; constructions avoid the
decision entries unless the property says otherwise)."""
from __future__ import annotations

import string

from hypothesis import strategies as st

LOWER = "abcdefghijklmnopqrstuvwxyz"
# filler words: lowercase ASCII, 4-7 letters, never palindromes, never containing the keywords used
_word = st.text(alphabet=LOWER, min_size=4, max_size=7).filter(lambda w: w != w[::-1])


def _filler(n_min=3, n_max=12, avoid=()):
    return st.lists(
        _word.filter(lambda w: not any(a in w or w in a for a in avoid)), min_size=n_min, max_size=n_max
    )


@st.composite
def keyword_frequency(draw):
    """P3: exactly c whole-word lowercase occurrences of the keyword; relation from the data."""
    kw = "monitor"
    words = draw(_filler(avoid=(kw,)))
    c = draw(st.integers(0, 4))
    for _ in range(c):
        words.insert(draw(st.integers(0, len(words))), kw)
    rel = draw(st.sampled_from(["at least", "less than"]))
    f = draw(st.integers(1, 3))
    label = (c >= f) if rel == "at least" else (c < f)
    return "keywords:frequency", {"keyword": kw, "frequency": f, "relation": rel}, " ".join(words) + ".", label


@st.composite
def word_count_exact(draw):
    """P4: exactly f occurrences; the prompt says 'should appear f times' (pass under both readings)."""
    kw = "skin"
    words = draw(_filler(avoid=(kw,)))
    f = draw(st.integers(1, 3))
    for _ in range(f):
        words.insert(draw(st.integers(0, len(words))), kw)
    rel = draw(st.sampled_from(["at least", "less than"]))
    return "keywords:word_count_different_numbers", {"keyword": kw, "frequency": f, "relation": rel}, " ".join(words) + ".", True


@st.composite
def number_words(draw):
    """P5: n words (Latin or Cyrillic letters), relation and threshold around n."""
    alphabet = draw(st.sampled_from([LOWER, "абвгдежзиклмнопрстуф"]))
    words = draw(st.lists(st.text(alphabet=alphabet, min_size=2, max_size=6), min_size=1, max_size=15))
    n = len(words)
    rel = draw(st.sampled_from(["at least", "less than"]))
    k = draw(st.integers(max(1, n - 1), n + 1))
    label = (n >= k) if rel == "at least" else (n < k)
    return "length_constraints:number_words", {"num_words": k, "relation": rel}, " ".join(words) + ".", label


@st.composite
def divider_paragraphs(draw):
    """P6: k paragraphs separated by a *** line with blank lines around it."""
    k = draw(st.integers(1, 5))
    paras = [" ".join(draw(_filler(2, 6))).capitalize() + "." for _ in range(k)]
    sep = draw(st.sampled_from(["\n***\n", "\n\n***\n\n"]))
    return "length_constraints:number_paragraphs", {"num_paragraphs": k}, sep.join(paras), True


@st.composite
def nth_paragraph(draw):
    """P7: k blank-line paragraphs; paragraph i starts with the word, followed by punctuation."""
    k = draw(st.integers(1, 4))
    i = draw(st.integers(1, k))
    w = "crash"
    paras = [" ".join(draw(_filler(2, 6, avoid=(w,)))) + "." for _ in range(k)]
    punct = draw(st.sampled_from(["", ",", ":", ";", "!", "?", "."]))
    paras[i - 1] = w.capitalize() + punct + " " + paras[i - 1]
    kw = {"num_paragraphs": k, "nth_paragraph": i, "first_word": w}
    return "length_constraints:nth_paragraph_first_word", kw, "\n\n".join(paras), True


@st.composite
def sentence_count(draw):
    """P8: n sentences of plain words, each ending with . ! or ?"""
    n = draw(st.integers(1, 6))
    ss = []
    for _ in range(n):
        ss.append(" ".join(draw(_filler(2, 5))).capitalize() + draw(st.sampled_from([".", "!", "?"])))
    rel = draw(st.sampled_from(["at least", "less than"]))
    k = draw(st.integers(max(1, n - 1), n + 1))
    label = (n >= k) if rel == "at least" else (n < k)
    return "length_constraints:number_sentences", {"num_sentences": k, "relation": rel}, " ".join(ss), label


@st.composite
def bullet_no_palindrome(draw):
    """P9: markdown bullets of non-palindromic words: no palindrome (fail)."""
    lines = ["- " + " ".join(draw(_filler(1, 3))) for _ in range(draw(st.integers(1, 4)))]
    return "keywords:palindrome", None, "\n".join(lines), False


@st.composite
def first_word_sent(draw):
    """P10: every sentence starts with the word, optionally followed by punctuation."""
    w = "peace"
    n = draw(st.integers(1, 4))
    ss = []
    for _ in range(n):
        punct = draw(st.sampled_from(["", ","]))
        ss.append(w.capitalize() + punct + " " + " ".join(draw(_filler(1, 4, avoid=(w,)))) + ".")
    return "first_word:first_word_sent", {"first_word": w}, " ".join(ss), True


@st.composite
def end_checker(draw):
    """P11: text then the phrase; the phrase either starts a new word (pass) or extends a word (fail)."""
    phrase = "Any other questions?"
    body = " ".join(draw(_filler(1, 5)))
    joined = draw(st.booleans())
    if joined:
        return "startend:end_checker", {"end_phrase": phrase}, body + phrase.lower(), False
    return "startend:end_checker", {"end_phrase": phrase}, body + ". " + phrase, True


@st.composite
def start_end(draw):
    """P14: same first and last word; optionally a trailing period (fail)."""
    w = draw(_word)
    mid = " ".join(draw(_filler(1, 5, avoid=(w,))))
    dot = draw(st.booleans())
    return "keywords:start_end", None, f"{w.capitalize()} {mid} {w}" + ("." if dot else ""), not dot


@st.composite
def repeat_phrase(draw):
    """P15: n variants of the phrase, each replacing the center word with another word."""
    phrase = "The early bird catches the worm"
    words = phrase.split()
    n = draw(st.integers(2, 3))
    reps = []
    for _ in range(n):
        new = draw(_word.filter(lambda w: w not in ("catches", "bird", "early", "worm", "the")))
        v = list(words)
        v[3] = new
        reps.append(" ".join(v) + ".")
    return "copy:repeat_phrase", {"phrase": phrase, "small_n": n}, " ".join(reps), True


@st.composite
def count_unique(draw):
    """P16: distinct lowercase words in sentences: unique (pass) whatever the punctuation."""
    ws = draw(st.lists(_word, min_size=2, max_size=10, unique=True))
    parts = []
    for i, w in enumerate(ws):
        parts.append(w + (draw(st.sampled_from(["", ".", ",", "!"])) if i < len(ws) - 1 else "."))
    return "count:count_unique", None, " ".join(parts), True


PROPERTIES = {
    "P3-keyword-frequency": keyword_frequency,
    "P4-word-count-exact": word_count_exact,
    "P5-number-words": number_words,
    "P6-divider-paragraphs": divider_paragraphs,
    "P7-nth-paragraph-punct": nth_paragraph,
    "P8-sentence-count": sentence_count,
    "P9-bullets-no-palindrome": bullet_no_palindrome,
    "P10-first-word-sent": first_word_sent,
    "P11-end-phrase-word": end_checker,
    "P14-start-end": start_end,
    "P15-repeat-phrase": repeat_phrase,
    "P16-count-unique": count_unique,
}

# Metamorphic edit (P2): leading and trailing whitespace the contract ignores (G2).
PAD = ("  \n", "\n\n\n\n")
