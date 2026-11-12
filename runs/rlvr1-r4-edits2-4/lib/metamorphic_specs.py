"""Metamorphic specs: per check, a passing base response, the word the check reads, the edits
its contract ignores, and one edit its contract forbids (from audit/CONTRACTS.md)."""

AT, LT = "at least", "less than"
ALL = ["numbered", "bullet", "bold", "italic", "html", "typo_quotes", "punct_after", "blank_line", "trailing_newline"]
WORD_EDITS = ["bold", "italic", "html", "typo_quotes", "punct_after"]
LINE_EDITS = ["blank_line", "trailing_newline"]

# (iid, kwargs, base, target word, ignored edits, (forbidden find, forbidden replace))
SPECS = [
    ("change_case:capital_word_frequency", {"capital_relation": AT, "capital_frequency": 2}, "The NASA and ESA teams met.\nThey talked.", "NASA", ALL, ("NASA", "nasa")),
    ("change_case:english_capital", {}, "THE TEAM MET TODAY AND THEY TALKED ABOUT THE NEW PLAN FOR THE CITY.\nEVERYONE AGREED WITH THE IDEA.", "TEAM", ["numbered", "bullet", "bold", "italic", "typo_quotes", "punct_after"] + LINE_EDITS, ("TEAM", "team")),
    ("change_case:english_lowercase", {}, "the team met today and they talked about the new plan for the city.\neveryone agreed with the idea.", "team", ALL, ("team", "Team")),
    ("combination:two_responses", {}, "The capital of France is Paris.\n******\nParis is the capital of France.", "capital", ALL, ("Paris is the capital of France.", "The capital of France is Paris.")),
    ("copy:repeat_phrase", {"phrase": "Don't judge a book by cover", "small_n": 2}, "Don't judge the book by cover.\nDon't judge one book by cover.", "Don't", ALL + ["typo_apostrophe"], ("Don't judge one book", "Do not judge one book")),
    ("count:count_unique", {}, "Every cat sleeps\nDogs bark loudly", "cat", ALL, ("Dogs bark loudly", "Dogs bark every")),
    ("count:lowercase_counting", {"N": 2}, "The Cat Sat.\nA dog ran.", "dog", ALL, ("A dog ran.", "A dog ran ran ran.")),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name]\nMeet me at [address].", "Dear", ALL, ("[address]", "the station")),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\nP.S. Thanks for asking.", "P.S.", ["bold", "italic", "html"] + LINE_EDITS, ("P.S. Thanks", "Thanks")),
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>>\n<<with my>> <<cute dog>>", "am", ["bullet", "bold", "italic", "html", "typo_quotes", "punct_after"] + LINE_EDITS, ("<<cute dog>>", "cute dog")),
    ("detectable_format:constrained_response", {}, "My answer is yes.", "yes", ["trailing_newline"], ("yes.", "perhaps.")),
    ("detectable_format:json_format", {}, '{\n"a": 1,\n"b": "two"\n}', "two", LINE_EDITS, ('"two"\n}', '"two"\n')),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nThe cat sleeps.\nSECTION 2\nThe dog barks.", "SECTION 1", ["bold", "italic", "html"] + LINE_EDITS, ("SECTION 2\n", "")),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples are red\n* Pears are green", "Apples", WORD_EDITS + LINE_EDITS, ("* Pears are green", "* Pears are green\n* Plums are blue")),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* text.\nThat is *urgent* too.", "text", ALL, ("*urgent*", "urgent")),
    ("detectable_format:sentence_hyphens", {}, "Sunrise.-Birdsong.-Walks.", "Sunrise", ["bold", "italic", "html", "typo_quotes", "trailing_newline"], (".-Birdsong", ". Birdsong")),
    ("detectable_format:square_brackets", {}, "[The] [sun] [is] [bright]\n[Birds] [sing]", "[sun]", ["bullet", "bold", "italic", "html", "typo_quotes", "punct_after"] + LINE_EDITS, ("[sing]", "sing")),
    ("detectable_format:title", {}, "<<Ode to Rain>>\nThe rain falls softly.", "rain", ALL, ("<<Ode to Rain>>", "Ode to Rain")),
    ("first_word:first_word_answer", {"first_word": "rain"}, "Rain falls softly today.\nClouds gather.", "Rain", ["bullet"] + WORD_EDITS + LINE_EDITS, ("Rain falls", "Snow falls")),
    ("first_word:first_word_sent", {"first_word": "rain"}, "Rain falls today.\nRain cools the air.", "Rain", ALL, ("Rain cools", "Wind cools")),
    ("keywords:existence", {"keywords": ["art", "home"]}, "Art makes a house a home.\nWe love it.", "home", ALL, ("a home", "a house")),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "sound"]}, "The rules are fair.\nWe follow them.", "rules", ALL, ("rules", "law")),
    ("keywords:frequency", {"keyword": "cat", "relation": AT, "frequency": 2}, "A cat sat.\nAnother cat ran.", "cat", ALL, ("Another cat", "Another dog")),
    ("keywords:keyword_specific_position", {"keyword": "river", "n": 2, "m": 3}, "We walked far.\nThen the river appeared.", "river", ALL, ("Then the river", "The river")),
    ("keywords:letter_frequency", {"letter": "z", "let_relation": AT, "let_frequency": 2}, "Zebras graze.\nThey rest.", "Zebras", ALL, ("graze", "eat")),
    ("keywords:no_adjacent_consecutive", {}, "Zebras graze quietly near water.\nKids play.", "Zebras", ALL, ("Kids play", "Kids like")),
    ("keywords:palindrome", {}, "We saw the racecar today.\nIt was red.", "racecar", ALL, ("racecar", "racecars")),
    ("keywords:start_end", {}, "Rain falls today\nand we wait for rain", "Rain", ["bullet"] + WORD_EDITS + LINE_EDITS, ("for rain", "for rain.")),
    ("keywords:word_count_different_numbers", {"keyword": "tree", "relation": AT, "frequency": 2}, "A tree grew.\nAnother tree fell.", "tree", ALL, ("Another tree fell.", "Another tree fell near a tree.")),
    ("keywords:word_once", {"keyword": "river"}, "The river flows.\nIt is calm.", "river", ALL, ("The river", "The stream")),
    ("language:response_language", {"language": "fr"}, "Le temps est très beau aujourd'hui et nous allons au parc.\nNous jouons avec nos amis toute la journée.", "temps", ALL + ["typo_apostrophe"], ("Nous jouons avec nos amis toute la journée.", "We play with our friends all day long in the park.")),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We pushed hard.\nWe reached the limit.", "limit", ALL, ("the limit.", "the limit today.")),
    ("last_word:last_word_sent", {"last_word": "limit"}, "We reached the limit.\nThey hit the limit.", "limit", ALL, ("They hit the limit.", "They hit the wall.")),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered over town.\n\nRain fell all night.", "Rain", ["bullet"] + WORD_EDITS + LINE_EDITS, ("Rain fell", "Snow fell")),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph here.\n***\nSecond paragraph here.", "Second", WORD_EDITS + LINE_EDITS, ("\n***\n", "\n\n")),
    ("length_constraints:number_sentences", {"relation": AT, "num_sentences": 2}, "The cat sleeps.\nThe dog barks.", "cat", ALL, ("sleeps.\nThe dog barks.", "sleeps and the dog barks.")),
    ("length_constraints:number_words", {"relation": AT, "num_words": 6}, "The cat doesn't sleep all day.\nThe dog barks.", "cat", ALL + ["typo_apostrophe"], ("The cat doesn't sleep all day.\n", "")),
    ("letters:letter_counting", {"relation": AT, "N": 3}, "Hello there.\nGood day.", "Hello", ALL, ("Hello there.\nGood day.", "Hi")),
    ("letters:letter_counting2", {"letter": "z", "let_relation": AT, "let_frequency": 2}, "Zebras graze.\nThey rest.", "Zebras", ALL, ("graze", "eat")),
    ("paragraphs:paragraphs", {}, "First paragraph here.\n***\nSecond paragraph here.", "Second", WORD_EDITS + LINE_EDITS, ("\n***\n", "\n\n")),
    ("paragraphs:paragraphs2", {}, "First paragraph here.\n\nSecond paragraph here.", "Second", ALL, ("\n\nSecond", " Second")),
    ("punctuation:no_comma", {}, "No commas here.\nNone at all.", "commas", ALL, ("No commas", "No, commas")),
    ("punctuation:punctuation_dot", {}, "No dots here\nNone at all", "dots", ["bullet"] + WORD_EDITS + LINE_EDITS, ("None at all", "None at all.")),
    ("punctuation:punctuation_exclamation", {}, "Calm words here.\nNothing loud.", "words", ALL, ("Nothing loud.", "Nothing loud!")),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the plan.\nAny other questions?", "plan", ALL, ("Any other questions?", "Any other questions? Bye.")),
    ("startend:quotation", {}, '"The cat sleeps.\nThe dog barks."', "cat", WORD_EDITS + LINE_EDITS, ('barks."', "barks.")),
]


def apply_edit(text: str, target: str, edit: str) -> str:
    import re

    lines = text.split("\n")
    if edit == "numbered":
        return "\n".join(f"{i + 1}. {line}" if line.strip() else line for i, line in enumerate(lines))
    if edit == "bullet":
        return "\n".join(f"- {line}" if line.strip() else line for line in lines)
    if edit == "blank_line":
        return "\n\n".join(lines)
    if edit == "trailing_newline":
        return text + "\n"
    if edit == "typo_apostrophe":
        return text.replace("'", "’")
    index = text.find(target)
    if index < 0:
        raise ValueError(f"target {target!r} not in {text!r}")
    end = index + len(target)
    wrap = {
        "bold": ("**", "**"),
        "italic": ("*", "*"),
        "html": ("<b>", "</b>"),
        "typo_quotes": ("“", "”"),
        "punct_after": ("", ";"),
    }[edit]
    return text[:index] + wrap[0] + target + wrap[1] + text[end:]
