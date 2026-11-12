"""Findings register: id -> (graders, checks, title). Used by the tests and the report.

"skyrl" is the SkyRL reward (NVIDIA's checkers), "gate" the task-curation gate (verifyit).
"""

FINDINGS = {
    "F1": ("skyrl", ["keywords:existence", "keywords:frequency", "keywords:word_once", "keywords:word_count_different_numbers"], "A keyword is matched as a substring of other words (art in start, cat in catalog, river in riverbank)."),
    "F2": ("skyrl,gate", ["keywords:word_once"], "Requires exactly one occurrence; the text \"Include keyword X\" sets no upper bound."),
    "F3": ("skyrl,gate", ["keywords:word_count_different_numbers"], "Applies the kwargs relation that the prompt never shows; with \"less than N\", exactly N occurrences fail and zero pass."),
    "F4": ("skyrl", ["copy:repeat_phrase"], "Only the last repetition's change count is checked, so an unchanged copy followed by one variant passes."),
    "F5": ("skyrl", ["copy:repeat_phrase"], "Repetitions are found by a regex on raw text, so markup, quotes, punctuation or a typographic apostrophe on the phrase's first word hide a repetition."),
    "F6": ("gate", ["copy:repeat_phrase"], "Counts unchanged copies of the phrase (at least small_n): an untransformed repetition passes and every transformed one fails."),
    "F7": ("skyrl", ["count:count_unique"], "Punctuation and markup tokens count as words, so two commas are a repeated word."),
    "F8": ("skyrl", ["count:counting_composition"], "Splits paragraphs on *** although the instruction gives * * *, and counts punctuation tokens as words; no response that follows the instruction passes."),
    "F9": ("gate", ["count:counting_composition"], "Checks only that the first n_sent sentences have at least n_words words; ignores the paragraphs and the exact counts."),
    "F10": ("gate", ["count:lowercase_counting"], "Relation inverted: passes when there are at least N lowercase words; the text says at most N times."),
    "F11": ("gate", ["keywords:no_adjacent_consecutive"], "Checks that no two adjacent words are identical, a different requirement from consecutive first letters."),
    "F12": ("gate", ["change_case:english_capital", "change_case:english_lowercase"], "No check that the response is in English."),
    "F13": ("gate", ["detectable_format:square_brackets"], "Passes when any one bracketed span exists."),
    "F14": ("gate", ["detectable_format:sentence_hyphens"], "Sentences separated by spaces pass when each holds a hyphen and no space."),
    "F15": ("skyrl", ["detectable_format:sentence_hyphens"], "A hyphen inside a sentence (a hyphenated word, hyphens between words) fails the response."),
    "F16": ("gate", ["length_constraints:number_paragraphs"], "Counts blank-line paragraphs and ignores the *** divider that the instruction asks for."),
    "F17": ("gate", ["paragraphs:paragraphs", "paragraphs:paragraphs2"], "Passes at two or more paragraphs instead of exactly two; paragraphs:paragraphs also accepts blank lines instead of the divider."),
    "F18": ("skyrl", ["length_constraints:number_paragraphs", "paragraphs:paragraphs"], "*** anywhere in a line (bold italics, an inline mention of the divider) splits paragraphs."),
    "F19": ("skyrl", ["detectable_format:multiple_sections"], "Passes at n or more sections; the text says the response must have n sections."),
    "F20": ("skyrl,gate", ["detectable_format:multiple_sections"], "A mention of the splitter inside a sentence (See SECTION 2 below) counts as a section marker."),
    "F21": ("skyrl", ["detectable_format:number_bullet_lists"], "A line that starts with * and a non-asterisk (italic text) or with - (horizontal rule, negative number) counts as a bullet."),
    "F22": ("skyrl,gate", ["detectable_format:number_bullet_lists"], "A * * * divider line counts as a bullet."),
    "F23": ("skyrl,gate", ["detectable_format:number_highlighted_sections"], "Text between two multiplication signs or bullet markers counts as a highlight; the gate also counts * * (whitespace)."),
    "F24": ("skyrl", ["detectable_format:constrained_response"], "A response that contains two different options passes."),
    "F25": ("skyrl,gate", ["detectable_format:json_format"], "NaN and Infinity, which are not JSON, pass."),
    "F26": ("gate", ["detectable_format:json_format"], "An uppercase (```JSON) or one-line fence fails although the instruction allows markdown ticks."),
    "F27": ("skyrl,gate", ["detectable_content:number_placeholders"], "Empty brackets [] (SkyRL) and whitespace-only brackets [ ] (both) count as placeholders."),
    "F28": ("skyrl", ["detectable_content:postscript"], "The marker matches anywhere in a line: a mention inside a sentence, or P.P.S. for P.S., passes."),
    "F29": ("gate", ["detectable_content:postscript"], "Markup before the marker (**P.S.**) fails."),
    "F30": ("gate", ["detectable_format:title"], "A whitespace-only title << >> passes."),
    "F31": ("skyrl,gate", ["startend:end_checker"], "No word boundary before the phrase: \"Many other questions?\" ends with the phrase."),
    "F32": ("gate", ["startend:quotation"], "Single quotation marks pass, even a lone '."),
    "F33": ("skyrl,gate", ["combination:two_responses"], "A run of seven or more asterisks counts as the six-asterisk separator."),
    "F34": ("skyrl", ["first_word:first_word_answer", "first_word:first_word_sent", "length_constraints:nth_paragraph_first_word", "keywords:start_end"], "The first whitespace token keeps punctuation and markup (Development, **Rain** “Rain” - Rain 1.) and is compared whole."),
    "F35": ("skyrl", ["keywords:start_end"], "Tokens need not be words: a punctuation-only response (! !) passes."),
    "F36": ("skyrl", ["keywords:palindrome"], "Any one-character token passes, including *, - and —; punctuation, quotes, HTML tags or a capital letter on a palindrome fail it."),
    "F37": ("skyrl", ["keywords:no_adjacent_consecutive"], "Compares first characters of whitespace tokens: quotes and markup hide consecutive letters, and consecutive digits (1 2) fail."),
    "F38": ("skyrl", ["keywords:keyword_specific_position"], "Punctuation and markup tokens count as words, which shifts word positions."),
    "F39": ("skyrl", ["detectable_format:square_brackets"], "Punctuation or markup outside a bracketed word ([bright]. **[sun]**) fails the response."),
    "F40": ("skyrl", ["detectable_format:bigram_wrapping"], "An unwrapped final word is ignored and a one-word response passes; punctuation after >> or a bullet marker fails."),
    "F41": ("skyrl", ["language:response_language", "change_case:english_capital", "change_case:english_lowercase"], "A langdetect exception (text without letters, such as 12345 or an empty answer) counts as a pass."),
    "F42": ("gate", ["length_constraints:number_words", "first_word:first_word_answer", "first_word:first_word_sent", "last_word:last_word_answer", "last_word:last_word_sent", "keywords:start_end", "keywords:keyword_specific_position", "keywords:palindrome", "change_case:capital_word_frequency", "length_constraints:nth_paragraph_first_word"], "Word tokenizer [A-Za-z0-9'-]+: non-ASCII words are not words (Cyrillic, CJK, İ), a bare - or --- is a word, and HTML tag names are words."),
    "F43": ("gate", ["length_constraints:number_sentences", "first_word:first_word_sent", "last_word:last_word_sent", "keywords:keyword_specific_position"], "Sentence splitter on whitespace after . ! ?: a list label (1.) is a sentence and an abbreviation (Dr.) ends one."),
    "F44": ("gate", ["keywords:start_end"], "Punctuation after the last word passes (\"not even punctuation\")."),
    "F45": ("skyrl", ["last_word:last_word_answer"], "A trailing punctuation token (language —) becomes the last word and fails the response."),
    "F46": ("skyrl", ["count:lowercase_counting"], "Counts only ASCII words matching [a-z]+: lowercase words in other scripts are ignored, and HTML tag names count as lowercase words."),
    "F47": ("skyrl", ["language:response_language", "change_case:english_capital", "change_case:english_lowercase"], "One langdetect call on the whole text decides the language: a full sentence in another language passes when the rest dominates, and repetitive or upper-case English can be detected as another language."),
    "F48": ("skyrl,gate", ["length_constraints:number_sentences", "first_word:first_word_sent", "last_word:last_word_sent", "keywords:keyword_specific_position"], "CJK sentence ends (。！？) are not sentence boundaries: a Chinese answer of many sentences counts as one."),
    "G1": ("skyrl,gate", ["graded text"], "A thinking-mode response whose reasoning never closes is graded as if the reasoning were the answer."),
    "G2": ("skyrl", ["session"], "A checker exception (IndexError on an empty answer to last_word_answer) makes the row an INFRA_ERROR \"Verifier configuration failed\" with reward 0."),
    "G3": ("skyrl", ["length_constraints:nth_paragraph_first_word"], "77 rows ask for paragraph num+1 of num paragraphs; the checker redraws the paragraph index from the unseeded global random state, so the verdict is random and can be a pass."),
    "G4": ("skyrl", ["dependencies"], "NLTK punkt_tab is downloaded at run time when missing, with no hash; the data is not pinned by the code."),
    "G5": ("skyrl", ["session"], "NemotronTaskSession requires route task_session; all 11,817 rows carry route skyrl_gym (unverified: the routing code is not in the case)."),
}

# (instruction id, grader, substring of the fixture note) -> reference, for hand-written fixtures
FIXTURE_REFS = [
    ("change_case:english_capital", "gate", "not English", "F12"),
    ("change_case:english_lowercase", "gate", "not English", "F12"),
    ("combination:two_responses", "*", "seven asterisks", "F33"),
    ("copy:repeat_phrase", "gate", "", "F6"),
    ("copy:repeat_phrase", "skyrl", "one unchanged copy", "F4"),
    ("copy:repeat_phrase", "skyrl", "typographic apostrophe", "F5"),
    ("count:count_unique", "skyrl", "punctuation is not a word", "F7"),
    ("count:counting_composition", "skyrl", "", "F8"),
    ("count:counting_composition", "gate", "", "F9"),
    ("count:lowercase_counting", "gate", "", "F10"),
    ("detectable_content:number_placeholders", "*", "", "F27"),
    ("detectable_content:postscript", "skyrl", "mention inside", "F28"),
    ("detectable_content:postscript", "skyrl", "P.P.S. is not", "F28"),
    ("detectable_content:postscript", "gate", "bold marker", "F29"),
    ("detectable_format:bigram_wrapping", "skyrl", "", "F40"),
    ("detectable_format:constrained_response", "skyrl", "two options", "F24"),
    ("detectable_format:json_format", "*", "NaN", "F25"),
    ("detectable_format:json_format", "gate", "fence", "F26"),
    ("detectable_format:multiple_sections", "skyrl", "three sections", "F19"),
    ("detectable_format:multiple_sections", "*", "mention inside", "F20"),
    ("detectable_format:number_bullet_lists", "skyrl", "italic", "F21"),
    ("detectable_format:number_bullet_lists", "skyrl", "horizontal rule", "F21"),
    ("detectable_format:number_bullet_lists", "skyrl", "negative number", "F21"),
    ("detectable_format:number_bullet_lists", "*", "* * * divider", "F22"),
    ("detectable_format:number_highlighted_sections", "*", "", "F23"),
    ("detectable_format:sentence_hyphens", "gate", "space between sentences", "F14"),
    ("detectable_format:sentence_hyphens", "skyrl", "", "F15"),
    ("detectable_format:sentence_hyphens", "gate", "hyphenated word", "D-hyphens-spaces"),
    ("detectable_format:square_brackets", "gate", "one word bracketed", "F13"),
    ("detectable_format:square_brackets", "skyrl", "", "F39"),
    ("detectable_format:title", "gate", "blank title", "F30"),
    ("first_word:first_word_answer", "skyrl", "", "F34"),
    ("first_word:first_word_sent", "skyrl", "comma", "F34"),
    ("keywords:existence", "skyrl", "inside start", "F1"),
    ("keywords:frequency", "skyrl", "", "F1"),
    ("keywords:keyword_specific_position", "skyrl", "comma", "F38"),
    ("keywords:no_adjacent_consecutive", "gate", "", "F11"),
    ("keywords:no_adjacent_consecutive", "skyrl", "quoted", "F37"),
    ("keywords:no_adjacent_consecutive", "skyrl", "digits", "F37"),
    ("keywords:palindrome", "skyrl", "", "F36"),
    ("keywords:palindrome", "gate", "horizontal rule", "F42"),
    ("keywords:start_end", "gate", "period after", "F44"),
    ("keywords:start_end", "skyrl", "bold first word", "F34"),
    ("keywords:start_end", "skyrl", "no words", "F35"),
    ("keywords:word_count_different_numbers", "*", "hidden relation", "F3"),
    ("keywords:word_once", "*", "keyword twice", "F2"),
    ("keywords:word_once", "skyrl", "riverbank", "F1"),
    ("language:response_language", "skyrl", "no language", "F41"),
    ("length_constraints:nth_paragraph_first_word", "skyrl", "nth beyond num", "G3"),
    ("length_constraints:nth_paragraph_first_word", "skyrl", "", "F34"),
    ("length_constraints:number_paragraphs", "gate", "", "F16"),
    ("length_constraints:number_paragraphs", "skyrl", "bold italics", "F18"),
    ("length_constraints:number_sentences", "gate", "abbreviation", "F43"),
    ("length_constraints:number_words", "gate", "Cyrillic", "F42"),
    ("paragraphs:paragraphs", "gate", "", "F17"),
    ("paragraphs:paragraphs2", "gate", "", "F17"),
    ("startend:end_checker", "*", "longer word", "F31"),
    ("startend:quotation", "gate", "single quotation", "F32"),
    ("keywords:word_once", "*", "thinking:", "G1"),
    ("punctuation:no_comma", "*", "thinking:", "G1"),
]

# (instruction id, grader, edit) -> reference, for metamorphic flips; edit "*" matches any
METAMORPHIC_REFS = [
    ("detectable_format:bigram_wrapping", "replacement", "html", "replacement limitation: an HTML tag before >> is not removed"),
    ("copy:repeat_phrase", "skyrl", "*", "F5"),
    ("copy:repeat_phrase", "gate", "*", "F6"),
    ("length_constraints:number_paragraphs", "gate", "*", "F16"),
    ("count:count_unique", "skyrl", "*", "F7"),
    ("count:lowercase_counting", "skyrl", "html", "F46"),
    ("detectable_content:postscript", "gate", "*", "F29"),
    ("detectable_format:bigram_wrapping", "skyrl", "*", "F40"),
    ("detectable_format:square_brackets", "skyrl", "*", "F39"),
    ("first_word:first_word_answer", "skyrl", "*", "F34"),
    ("first_word:first_word_sent", "skyrl", "*", "F34"),
    ("length_constraints:nth_paragraph_first_word", "skyrl", "blank_line", "D-paragraph-blank-lines"),
    ("length_constraints:nth_paragraph_first_word", "skyrl", "*", "F34"),
    ("keywords:start_end", "skyrl", "*", "F34"),
    ("keywords:keyword_specific_position", "skyrl", "*", "F38"),
    ("keywords:palindrome", "skyrl", "*", "F36"),
    ("last_word:last_word_answer", "skyrl", "html", "F45"),
    ("last_word:last_word_sent", "skyrl", "*", "F34"),
    ("paragraphs:paragraphs2", "skyrl", "blank_line", "D-paragraph-blank-lines"),
    ("*", "gate", "html", "F42"),
    ("*", "gate", "bullet", "F42"),
    ("*", "gate", "numbered", "F43"),
]

FORBIDDEN_REFS = [
    ("language:response_language", "replacement", "replacement limitation: whole-text langdetect misses one foreign sentence"),
    ("count:count_unique", "skyrl", "D-word-case"),
    ("count:lowercase_counting", "gate", "F10"),
    ("detectable_format:square_brackets", "gate", "F13"),
    ("keywords:no_adjacent_consecutive", "gate", "F11"),
    ("keywords:start_end", "gate", "F44"),
    ("keywords:word_count_different_numbers", "*", "D-word-count-exact"),
    ("language:response_language", "skyrl", "F47"),
    ("length_constraints:number_paragraphs", "gate", "F16"),
    ("paragraphs:paragraphs", "gate", "F17"),
]


def _match(table, iid, grader, text):
    for t_iid, t_grader, key, ref in table:
        if t_iid in (iid, "*") and t_grader in (grader, "*") and (key == "*" or key in text):
            return ref
    return None


def fixture_ref(iid, grader, note):
    return _match(FIXTURE_REFS, iid, grader, note)


def metamorphic_ref(iid, grader, edit):
    for t_iid, t_grader, t_edit, ref in METAMORPHIC_REFS:
        if t_iid in (iid, "*") and t_grader in (grader, "*") and t_edit in (edit, "*"):
            return ref
    return None


def forbidden_ref(iid, grader):
    for t_iid, t_grader, ref in FORBIDDEN_REFS:
        if t_iid == iid and t_grader in (grader, "*"):
            return ref
    return None


def check_candidates(iid, grader):
    """Findings registered for this check and grader (fallback attribution)."""
    return [fid for fid, (graders, checks, _) in FINDINGS.items() if grader in graders.split(",") and iid in checks]
