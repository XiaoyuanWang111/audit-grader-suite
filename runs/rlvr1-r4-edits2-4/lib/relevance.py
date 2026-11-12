"""Decision entries that each check's replacement implementation reads."""

UNIVERSAL = ["D-empty-response", "D-word-units", "D-word-cjk", "D-word-case"]
SENT = ["D-sentence-split"]
DIV = ["D-divider-form", "D-divider-edges", "D-divider-blank-lines"]
RELEVANT = {
    "change_case:capital_word_frequency": ["D-capital-word"],
    "change_case:english_capital": ["D-language-mixed"],
    "change_case:english_lowercase": ["D-language-mixed"],
    "combination:two_responses": ["D-two-different"],
    "copy:repeat_phrase": ["D-repeat-center", "D-repeat-original"],
    "count:count_unique": [],
    "count:counting_composition": DIV + SENT,
    "count:lowercase_counting": ["D-lowercase-count", "D-lowercase-scope"],
    "detectable_content:number_placeholders": ["D-placeholder"],
    "detectable_content:postscript": ["D-postscript-case", "D-postscript-position"],
    "detectable_format:bigram_wrapping": ["D-bigram-odd"],
    "detectable_format:constrained_response": ["D-constrained-extra"],
    "detectable_format:json_format": ["D-json-value"],
    "detectable_format:multiple_sections": ["D-section-case", "D-section-label", "D-sections-preamble"],
    "detectable_format:number_bullet_lists": ["D-bullet-markers"],
    "detectable_format:number_highlighted_sections": ["D-highlight-bold"],
    "detectable_format:sentence_hyphens": ["D-hyphens-single", "D-hyphens-spaces"] + SENT,
    "detectable_format:square_brackets": ["D-brackets-each"],
    "detectable_format:title": ["D-title-position"],
    "first_word:first_word_answer": [],
    "first_word:first_word_sent": SENT,
    "keywords:existence": ["D-keyword-inflection"],
    "keywords:forbidden_words": ["D-keyword-inflection"],
    "keywords:frequency": ["D-keyword-inflection"],
    "keywords:keyword_specific_position": SENT,
    "keywords:letter_frequency": ["D-letter-case"],
    "keywords:no_adjacent_consecutive": ["D-consecutive-order", "D-consecutive-script"],
    "keywords:palindrome": ["D-palindrome-unit", "D-palindrome-length"],
    "keywords:start_end": ["D-start-end-single"],
    "keywords:word_count_different_numbers": ["D-keyword-inflection", "D-word-count-exact"],
    "keywords:word_once": ["D-keyword-inflection"],
    "language:response_language": ["D-language-mixed"],
    "last_word:last_word_answer": [],
    "last_word:last_word_sent": SENT,
    "length_constraints:nth_paragraph_first_word": ["D-paragraph-blank-lines"],
    "length_constraints:number_paragraphs": DIV,
    "length_constraints:number_sentences": SENT,
    "length_constraints:number_words": [],
    "letters:letter_counting": ["D-letter-script"],
    "letters:letter_counting2": ["D-letter-case"],
    "paragraphs:paragraphs": DIV,
    "paragraphs:paragraphs2": ["D-paragraph-blank-lines"],
    "punctuation:no_comma": ["D-comma-chars"],
    "punctuation:punctuation_dot": ["D-dot-chars"],
    "punctuation:punctuation_exclamation": ["D-exclamation-chars"],
    "startend:end_checker": ["D-end-markup", "D-end-case"],
    "startend:quotation": ["D-quote-chars"],
}


def relevant(iid):
    return UNIVERSAL + RELEVANT.get(iid, [])
