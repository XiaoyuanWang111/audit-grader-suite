"""Metamorphic transforms that the contract ignores, with the checks where each must keep a verdict.

Applied to every passing fixture (contract label True) of an allowed check; the grader's verdict
must stay True. Used by audit/scripts/step4_properties.py and audit/tests/test_properties.py.
"""
import re

ALL_BUT_COPY_CSV = lambda c: not (c.startswith("custom:csv") or c.startswith("repeat:"))  # noqa: E731
WORD_CHECKS = {
    "count:conjunctions", "count:keywords_multiple", "count:person_names", "count:pronouns",
    "count:unique_word_count", "count:word_count_range", "count:words_japanese", "sentence:increment",
    "sentence:keyword", "sentence:alliteration_increment", "words:alphabet", "words:consonants",
    "words:keywords_specific_position", "words:last_first", "words:no_consecutive",
    "words:odd_even_syllables", "words:palindrome", "words:paragraph_last_first", "words:prime_lengths",
    "words:repeats", "words:start_verb", "words:vowel", "words:words_position", "ratio:stop_words",
    "format:title_case", "format:newline",
}


def trailing_newline(s):
    return s + "\n"


def curly_quotes(s):
    """Straight double quotes to typographic pairs, apostrophes inside words to U+2019."""
    out, open_q = [], True
    for ch in s:
        if ch == '"':
            out.append("“" if open_q else "”")
            open_q = not open_q
        else:
            out.append(ch)
    s = "".join(out)
    return re.sub(r"(?<=\w)'(?=\w)", "’", s)


def bold_first_word(s):
    m = re.search(r"[A-Za-z][A-Za-z']*", s)
    if not m:
        return s
    return s[:m.start()] + "**" + m.group(0) + "**" + s[m.end():]


def comma_after_first_word(s):
    """Insert a comma after the first word when it is followed by a space (punctuation after a word)."""
    m = re.search(r"^(\W*[A-Za-z][A-Za-z']*)( )", s)
    if not m:
        return s
    return s[:m.end(1)] + "," + s[m.end(1):]


def emdash_between_words(s):
    """Insert ' —' after the second word of the first line that has three or more words."""
    lines = s.split("\n")
    for i, line in enumerate(lines):
        parts = line.split(" ")
        if len([p for p in parts if re.search(r"[A-Za-z]", p)]) >= 3:
            parts.insert(2, "—")
            lines[i] = " ".join(parts)
            return "\n".join(lines)
    return s


TRANSFORMS = {
    # name: (function, predicate on check id: is the contract verdict invariant under this edit?)
    "trailing_newline": (trailing_newline, lambda c: True),
    "curly_quotes": (curly_quotes, ALL_BUT_COPY_CSV),
    "bold_first_word": (bold_first_word, lambda c: c in WORD_CHECKS - {"format:title_case"}),
    "emdash_between_words": (emdash_between_words, lambda c: c in WORD_CHECKS - {
        "words:paragraph_last_first", "words:words_position", "words:keywords_specific_position",
        "words:last_first", "sentence:alliteration_increment"}),
}
