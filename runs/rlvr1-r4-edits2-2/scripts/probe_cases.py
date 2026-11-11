"""First probes of suspected defects, before the fixture suite existed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness  # noqa: E402

harness.setup()
CASES = [
    ("change_case:english_capital", {}, "THE CAT SAT ON THE MAT AND LOOKED AT THE BIRDS IN THE GARDEN."),
    ("change_case:english_capital", {}, "HELLO WORLD"),
    ("change_case:english_capital", {}, "ПРИВЕТ МИР КАК ДЕЛА"),
    ("change_case:english_lowercase", {}, "bonjour je suis tres content de vous voir aujourd hui"),
    ("keywords:no_adjacent_consecutive", {}, "apple banana"),
    ("keywords:no_adjacent_consecutive", {}, "the the"),
    ("keywords:no_adjacent_consecutive", {}, "Step 1 2 done"),
    ("keywords:no_adjacent_consecutive", {}, '"apple" banana'),
    ("detectable_format:square_brackets", {}, "[Hello] world"),
    ("detectable_format:square_brackets", {}, "[Hello], [world]."),
    ("detectable_format:sentence_hyphens", {}, "I like tea.-You like coffee."),
    ("detectable_format:sentence_hyphens", {}, "Tea is well-known.-Coffee is too."),
    ("count:lowercase_counting", {"N": 2}, "the cat sat"),
    ("count:lowercase_counting", {"N": 2}, "Hello World"),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each moment to the fullest. Live each life to the fullest."),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each day to the fullest. Live each day to the fullest."),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 3},
     "Live each day to the fullest. Live each day to the fullest. Live each hour to the fullest."),
    ("keywords:word_once", {"keyword": "beer"}, "beer and more beer"),
    ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "less than"}, "a box and a box"),
    ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "less than"}, "no boxes"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n***\nTwo.\n***\nThree."),
    ("paragraphs:paragraphs", {}, "One.\n***\nTwo.\n***\nThree."),
    ("paragraphs:paragraphs2", {}, "One.\n\nTwo.\n\nThree."),
    ("keywords:start_end", {}, "Hello there my friend hello."),
    ("startend:quotation", {}, "'single quoted'"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"},
     "SECTION 1\nA.\nSECTION 2\nB.\nSECTION 3\nC."),
    ("detectable_format:constrained_response", {}, "My answer is yes. My answer is no."),
    ("detectable_format:constrained_response", {}, "My answer is yes. Because it is."),
    ("first_word:first_word_answer", {"first_word": "development"}, "**Development** matters."),
    ("first_word:first_word_answer", {"first_word": "development"}, "Development, as a field, matters."),
    ("keywords:palindrome", {}, "This - that"),
    ("keywords:palindrome", {}, "Level up."),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Text here.\n\nP.P.S. later"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Text, see P.S. below, more text."),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Text.\n\n**P.S.** Thanks."),
    ("length_constraints:number_sentences", {"num_sentences": 2, "relation": "at least"}, "One. Two."),
    ("last_word:last_word_answer", {"last_word": "end"}, ""),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"},
     "**Fuel** is good.\n\nSecond."),
]
for iid, kw, text in CASES:
    n = harness.skyrl_constraint(iid, kw, text)
    v = harness.verifyit_constraint(iid, kw, text)
    print(f"{iid:45s} {text[:50]!r:55s} nvidia={n[0]!s:5} {n[1] or ''} | verifyit={v[0]!s:5} {v[1][:60]}")
