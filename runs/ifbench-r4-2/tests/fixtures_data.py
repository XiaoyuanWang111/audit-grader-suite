"""Labeled fixtures for the IFBench checks.

Every label comes from audit/CONTRACTS.md (proposed readings). Fields:
  check     instruction id
  kwargs    checker kwargs, with the types `datasets` produces (floats for N etc.)
  response  the graded text
  label     contract verdict under the proposed readings (True = pass)
  dec       decision entries whose non-proposed readings, taken together, flip the
            label; empty = the contract is unambiguous for this response
  finding   finding id when the fixture reproduces a defect (filled for the
            smallest repro of each finding)
  note      why the label is what it is
The fixture id is check + first 8 hex of sha256(check, kwargs, response).
"""
import hashlib
import json

FIXTURES = []


def fx(check, kwargs, response, label, dec=(), finding=None, note="", prompt=""):
    h = hashlib.sha256(json.dumps([check, kwargs, response], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]
    FIXTURES.append(dict(id=f"{check}:{h}", check=check, kwargs=kwargs, response=response, label=label,
                         dec=list(dec), finding=finding, note=note, prompt=prompt))


# ---------------------------------------------------------------- count
C = "count:conjunctions"
fx(C, {"small_n": 3.0}, "I came and I saw, but I left, so it ended.", True, note="and, but, so")
fx(C, {"small_n": 3.0}, "I came and I saw and I left.", False, note="only and")
fx(C, {"small_n": 3.0}, "And and, AND but.", False, finding="F-conj-case",
   note="2 distinct conjunctions (and, but); case and punctuation variants are the same word")
fx(C, {"small_n": 2.0}, "Pick tea or coffee, for example.", True, dec=["D-conj-role"],
   note="or + for; 'for example' is a preposition use, counted under D-conj-role A")

C = "count:keywords_multiple"
KW = {"keyword1": "door", "keyword2": "bread", "keyword3": "blue", "keyword4": "lamp", "keyword5": "river"}
base = ("The door was open. Bread and more bread. Blue sky, blue sea, blue eyes. "
        "Lamp one, lamp two, lamp three, lamp four, lamp five. "
        "River, river, river, river, river, river, river.")
fx(C, KW, base, True, note="exact counts 1,2,3,5,7")
fx(C, KW, base.replace("river, river.", "river."), False, note="river six times")
fx(C, KW, base + " We stayed indoors near the doorway.", True, finding="F-kw-substring",
   note="'indoors' and 'doorway' are other words, not the keyword door")
fx(C, KW, base + " Two doors.", True, dec=["D-keyword-match"],
   note="'doors' is an inflection; counts only under D-keyword-match B")

C = "count:numbers"
fx(C, {"N": 2.0}, "I have 2 cats and 3 dogs.", True)
fx(C, {"N": 2.0}, "I have 2 cats, 3 dogs and 4 fish.", False)
fx(C, {"N": 2.0}, "Delivery takes 3-5 days.", True, finding="F-numbers-merge",
   note="a range 3-5 is two numbers under every reading")
fx(C, {"N": 3.0}, "Pick 1,2,3 now.", True, finding="F-numbers-merge", note="list 1,2,3 is three numbers")
fx(C, {"N": 2.0}, "I have two cats, 3 dogs and 4 birds.", True, dec=["D-number"],
   note="number words count only under D-number B")

C = "count:person_names"
fx(C, {"N": 3.0}, "Emma met Liam and Noah.", True)
fx(C, {"N": 3.0}, "Emma met Liam.", False)
fx(C, {"N": 2.0}, "Emma, Emma and Emma.", False, note="one distinct name")
fx(C, {"N": 3.0}, "emma met liam and noah.", False, dec=["D-name-case"])

C = "count:pronouns"
fx(C, {"N": 5.0}, "I told her she and they would help me.", True, note="I, her, she, they, me")
fx(C, {"N": 5.0}, "The cat sat on the mat.", False)
fx(C, {"N": 5.0}, "This plan says that all of those rules apply to each case.", False, dec=["D-pronoun-set"],
   note="only 'all' stands for a noun; this/those/each are determiners, that a conjunction (count under C)")

C = "count:punctuation"
full = ("Wait?! Here's the plan: we go (quickly) [now] {really}; then \"rest\" - a well-earned break — "
        "or not... Done. Right, yes? Yes!")
fx(C, {}, full, True, note="all 15 marks plus ?!")
fx(C, {}, "Hello, world.", False)
fx(C, {}, "Wait?! Yes, really; done: ok. Why? Now!", False, dec=["D-punct-set"],
   note="no apostrophe, quotes, hyphen, dash, brackets, ellipsis; passes only under D-punct-set C")

C = "count:unique_word_count"
fx(C, {"N": 5.0}, "One two three four five.", True)
fx(C, {"N": 5.0}, "One two three four.", False)
fx(C, {"N": 3.0}, "“Alpha” alpha alpha, Alpha. beta", False, finding="F-word-symbols",
   note="2 distinct words; curly quotes are not part of a word")
fx(C, {"N": 4.0}, "red — green — blue", False, finding="F-word-symbols",
   note="3 words; an em dash is not a word")
fx(C, {"N": 5.0}, "a a b c d e", True, dec=["D-unique"], note="5 distinct types; 4 hapaxes")

C = "count:word_count_range"
fx(C, {"min_words": 5.0, "max_words": 7.0}, "This sentence has exactly six words.", True)
fx(C, {"min_words": 5.0, "max_words": 7.0}, "Too short here.", False)
fx(C, {"min_words": 5.0, "max_words": 7.0}, "One two three four five six seven.", True, note="boundary 7")
fx(C, {"min_words": 5.0, "max_words": 7.0}, "One two three four five six seven eight.", False, note="8")
fx(C, {"min_words": 6.0, "max_words": 8.0}, "Don't stop, it's well-known.", False, dec=["D-word"],
   note="4 words under G4, 7 regex runs under D-word B")

C = "count:words_japanese"
fx(C, {"N": 3.0}, "I like 寿司 very much 本当に and you.", True)
fx(C, {"N": 3.0}, "I like sushi very much indeed.", False)
fx(C, {"N": 3.0}, "I like 2 very much 本当に.", False, finding="F-japanese-digits",
   note="word 3 is the numeral 2, not Japanese")
fx(C, {"N": 3.0}, "Hi there.", True, dec=["D-vacuous"], note="fewer than N words")

# ---------------------------------------------------------------- format
C = "format:emoji"
fx(C, {}, "I love sunny days \U0001F600. They make me happy \U0001F31E!", True)
fx(C, {}, "I love sunny days. They make me happy \U0001F31E!", False)
fx(C, {}, "Sunny days \U0001F600\nHeading\nThey make me happy \U0001F31E.", False, dec=["D-sentence"],
   note="the line 'Heading' is a sentence without an emoji under D-sentence A")

C = "format:line_indent"
fx(C, {}, "a\n  b\n    c", True)
fx(C, {}, "a\n  b\n  c", False)
fx(C, {}, "a\n\tb\n\t\tc", True, finding="F-indent-tabs", note="tab indentation is indentation")
fx(C, {}, "a\n\n\n  b", True, dec=["D-stairs-blank"], note="two blank lines in a row")

C = "format:list"
fx(C, {"sep": "!?!?"}, "!?!? apples\n!?!? pears", True)
fx(C, {"sep": "!?!?"}, "* apples\n* pears", False)
fx(C, {"sep": "-"}, "A well-known and long-term plan.", False, finding="F-list-anywhere",
   note="no list at all; two hyphens inside words")
fx(C, {"sep": "SEPARATOR"}, "Use SEPARATOR or SEPARATOR as you like.", False, finding="F-list-anywhere",
   note="no list items; the marker never starts a line")
fx(C, {"sep": "!?!?"}, "!?!? apples", False, dec=["D-plural"], note="one item")
fx(C, {"sep": "!?!?"}, "apples !?!? pears !?!? plums", False, dec=["D-list-placement"],
   note="the marker separates items inside one line")

C = "format:newline"
fx(C, {}, "Hello\nworld\nagain.", True)
fx(C, {}, "Hello world\nagain.", False)
fx(C, {}, "Hello world\n \nagain", False, finding="F-newline-blank",
   note="two words share line 1; the whitespace-only line holds no word")

C = "format:no_bullets_bullets"
fx(C, {}, "First sentence here. Second sentence here.\n* item one\n* item two", True)
fx(C, {}, "* item one\n* item two", False)
fx(C, {}, "Hello there\nHow are you\n* item one\n* item two", False, finding="F-nbb-period",
   note="no sentence ends in a period")
fx(C, {}, "First sentence here. Second one here.\n*item one\n*item two", False, dec=["D-bullet-syntax"],
   note="no space after the bullet marker")
fx(C, {}, "**Intro**\nFirst sentence here. Second one here.\n* item one\n* item two", True, finding="F-nbb-bold",
   note="a bold heading is not a bullet")
fx(C, {}, "I. Intro\nII. Body\n* item one\n* item two", False, finding="F-nbb-period",
   note="outline numerals are not sentences ending in a period")
fx(C, {}, "First sentence. Second sentence.\n\n* item one\n\n* item two", True, finding="F-nbb-blank",
   note="blank lines between bullets are not text")
fx(C, {}, "First sentence. Second sentence.\n* item one\n* item two\n", True, finding="F-nbb-blank",
   note="trailing newline")
fx(C, {}, "First sentence. Second sentence.\n* item one\n* item two\nA closing sentence.", True,
   dec=["D-nbb-order"], note="text after the bullets")

C = "format:no_whitespace"
fx(C, {}, "Yes,allsetsareclasses.", True)
fx(C, {}, "Yes, all sets", False)
fx(C, {}, "Yes,allsets.\n", True, dec=["D-trim"], note="trailing newline only")
fx(C, {}, "a b", False, dec=["D-whitespace"], note="no-break space")

C = "format:options"
fx(C, {"options": "yes/no/maybe"}, "Yes.", True)
fx(C, {"options": "yes/no/maybe"}, "Perhaps.", False)
fx(C, {"options": "yes/no/maybe"}, "Yes, because games teach.", True, dec=["D-options"])
fx(C, {"options": "yes/no/maybe"}, "Yes\n", True, dec=["D-trim"], note="trailing newline")
fx(C, {"options": "I know or I don't know"}, "I don’t know.", True, finding="F-options-apostrophe",
   note="typographic apostrophe; the same option")
fx(C, {"options": "a), b), c), d)"}, "c)", True)
fx(C, {"options": "a), b), c), d)"}, "C)", True, dec=["D-options"], note="letter case")
fx(C, {"options": "a), b), c), d)"}, "c", True, dec=["D-options"], note="bare letter")

C = "format:output_template"
fx(C, {}, "My Answer: It is large. My Conclusion: So it matters. Future Outlook: It grows.", True)
fx(C, {}, "Answer: It is large. Conclusion: It matters.", False)
fx(C, {}, "Future Outlook: It grows. My Conclusion: So it matters. My Answer: It is large.", False,
   finding="F-template-presence", note="labels out of order")
fx(C, {}, "Sure, here it is.\nMy Answer: It is large. My Conclusion: So it matters. Future Outlook: It grows.", False,
   finding="F-template-presence", note="text before the template")
fx(C, {}, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", False,
   finding="F-template-presence", note="placeholders not filled")
fx(C, {}, "**My Answer:** It is large. **My Conclusion:** So it matters. **Future Outlook:** It grows.", True,
   dec=["D-template-markup"])

C = "format:parentheses"
fx(C, {}, "(a [b {c (d [e] d) c} b] a)", True)
fx(C, {}, "(a [b] a)", False)
fx(C, {}, "(((((x)", False, finding="F-paren-unclosed", note="four openers never close")
fx(C, {}, "(((((x)))))", True, dec=["D-paren-types"])

C = "format:quote_unquote"
fx(C, {}, "\"Carpe diem\" means seize the day.", True)
fx(C, {}, "He said \"carpe diem\"", False)
fx(C, {}, "\"alpha\", \"beta\" are words.", False, finding="F-quote-unquote",
   note="'alpha' is followed only by a comma")
fx(C, {}, "“Carpe diem” “seize the day”", False, finding="F-quote-unquote",
   note="curly quotes; no explanation at all")
fx(C, {}, "\"x\" here.", True, dec=["D-explanation"])

C = "format:quotes"
fx(C, {}, "\"She said 'He told me \"run\" today' loudly\" end.", True)
fx(C, {}, "\"Only one level.\"", False)
fx(C, {}, "\"It's\" he said \"and that's all\"", False, finding="F-quotes-apostrophe",
   note="no nesting; the apostrophes are not quote marks")
fx(C, {}, "“She said ‘He told me “run” today’ loudly” end.", True,
   finding="F-quotes-apostrophe", note="curly quotes, three levels")

C = "format:sub-bullets"
fx(C, {}, "* Point one\n  - detail\n* Point two\n  - detail", True)
fx(C, {}, "* Point one\n* Point two", False)
fx(C, {}, "A plain paragraph without any list.", False, finding="F-subbullets",
   note="no bullet points at all")
fx(C, {}, "* A well-known point\n* Another long-term point", False, finding="F-subbullets",
   note="hyphens inside words are not sub-bullets")
fx(C, {}, "**Intro**\n* Point one\n  - detail\n* Point two\n  - detail", True, finding="F-subbullets",
   note="bold text is not a bullet")
fx(C, {}, "* Point one\n- detail\n* Point two\n- detail", True, dec=["D-subbullet-indent"])
fx(C, {}, "* Point one\n  - detail", False, dec=["D-plural"], note="one bullet")

C = "format:thesis"
fx(C, {}, "<i>Cats are great pets.</i> They purr and cuddle.", True)
fx(C, {}, "Cats are great pets. They purr.", False)
fx(C, {}, "<p><i>Cats are great pets.</i></p> They purr.", True, note="HTML paragraph wrapper")
fx(C, {}, "Cats are great pets. They purr, and <i>dogs bark</i> loudly.", False, finding="F-thesis-anywhere",
   note="the only italics are mid-paragraph; no section begins with them")
fx(C, {}, "<i>Thesis one.</i> Text.\n\nSecond paragraph without a thesis.", False, dec=["D-section"])

C = "format:title_case"
fx(C, {}, "The Lord Of The Rings Is A Great Book", True)
fx(C, {}, "the lord of the rings is great", False)
fx(C, {}, "The Lord of the Rings Is a Great Book", True, finding="F-titlecase-minor",
   note="minor words may be lowercase")
fx(C, {}, "Don't Stop Believing", True, finding="F-titlecase-minor", note="contraction")
fx(C, {}, "THE END IS NEAR", True, dec=["D-titlecase"])

# ---------------------------------------------------------------- ratio
C = "ratio:overlap"
REF = "the quick brown fox jumps over the lazy dog"
fx(C, {"percentage": 100.0, "reference_text": REF}, REF, True)
fx(C, {"percentage": 50.0, "reference_text": REF}, REF, False)
fx(C, {"percentage": 29.0, "reference_text": REF}, "the quick brown fox runs under a sleepy cat", True,
   dec=["D-overlap-def"], note="2 of 7 word trigrams = 28.6%")

C = "ratio:sentence_balance"
fx(C, {}, "I like tea. Do you? Wow!", True)
fx(C, {}, "I like tea. I like coffee.", False)
fx(C, {}, "I like tea\nI like coffee", False, finding="F-ratio-zero",
   note="two statements, no question, no exclamation")
fx(C, {}, "I like tea. I like milk. Do you? Wow!", True, dec=["D-balance"])

C = "ratio:sentence_type"
fx(C, {}, "I like tea. I like milk. Do you?", True)
fx(C, {}, "I like tea. Do you?", False)
fx(C, {}, "Wow! Amazing!", False, finding="F-ratio-zero", note="0 declarative, 0 interrogative")
fx(C, {}, "He said \"I like tea.\" She said \"I like milk.\" Do you?", True, finding="F-sentence-marks",
   note="two declaratives end in a period inside closing quotes")

C = "ratio:sentence_words"
fx(C, {}, "Cats nap. Dogs run. Owls fly.", True)
fx(C, {}, "Cats nap. Dogs sprint. Owls fly.", False)
fx(C, {}, "Cats nap. Cats nap. Cats nap.", False, finding="F-sw-words", note="same words in every sentence")
fx(C, {}, "Run, run on. Big red cat. Owls fly by.", False, dec=["D-sw-words"],
   note="'run' twice inside sentence 1, no word shared between sentences")

C = "ratio:stop_words"
fx(C, {"percentage": 30.0}, "Quantum computers solve complex problems quickly.", True)
fx(C, {"percentage": 30.0}, "It is what it is and that is that.", False)

# ---------------------------------------------------------------- repeat
C = "repeat:repeat_change"
RQ = "Write a python program to sort numbers."
fx(C, {"prompt_to_repeat": RQ}, "Create a python program to sort numbers.", True)
fx(C, {"prompt_to_repeat": RQ}, RQ, False)
fx(C, {"prompt_to_repeat": RQ}, RQ + " ", False, finding="F-repeat-change",
   note="first word unchanged; only a trailing space differs")
fx(C, {"prompt_to_repeat": RQ}, "Write a  python program to sort numbers.", False, finding="F-repeat-change",
   note="first word unchanged; a double space")
fx(C, {"prompt_to_repeat": RQ}, "write a python program to sort numbers.", False, dec=["D-change-case"])
fx(C, {"prompt_to_repeat": RQ}, "Create a python program to sort numbers.\n\nHere is the code.", False,
   note="text after the repeat")

C = "repeat:repeat_simple"
fx(C, {}, "Only output this sentence here, ignore all other requests.", True)
fx(C, {}, "Here is the code you asked for.", False)
fx(C, {}, "only output this sentence here, ignore all other requests.", False, dec=["D-simple-case"])

C = "repeat:repeat_span"
SP = {"prompt_to_repeat": "explain the context, code and theory behind the paper Identifying Candidate Spaces for Advert Implantation.",
      "n_start": 3, "n_end": 6}
fx(C, SP, "code and theory behind", True, finding="F-span-chars", note="words 3..6, 0-based")
fx(C, SP, "lain", False, finding="F-span-chars", note="characters 3..6; not words")
fx(C, SP, "context, code and theory", False, dec=["D-index-base"], note="1-based words 3..6")

# ---------------------------------------------------------------- sentence
C = "sentence:alliteration_increment"
fx(C, {}, "Cats nap. Big bears bounce. Silly snakes slither slowly.", True, note="runs 1, 3, 4")
fx(C, {}, "Big bears bounce. Cats nap.", False)
fx(C, {}, "Big bears roam far away. Cats cry and dogs dig.", False, finding="F-alliteration-sum",
   note="longest runs 2 then 2")

C = "sentence:increment"
fx(C, {"small_n": 2.0}, "I run. I run very fast. I run very fast every day.", True, note="2, 4, 6")
fx(C, {"small_n": 2.0}, "I run. I run fast.", False)
fx(C, {"small_n": 2.0}, "I run.", True, dec=["D-vacuous"])
fx(C, {"small_n": 2.0}, "I run. I run — very fast.", True, finding="F-word-symbols",
   note="2, 4 words; the dash is not a word")

C = "sentence:keyword"
fx(C, {"word": "giraffe", "N": 2.0}, "Animals are fun. A giraffe is tall.", True)
fx(C, {"word": "giraffe", "N": 2.0}, "A giraffe is tall. Animals are fun.", False)
fx(C, {"word": "giraffe", "N": 2.0}, "Animals are fun. Giraffes are tall.", False, dec=["D-keyword-match"])

# ---------------------------------------------------------------- words
C = "words:alphabet"
fx(C, {}, "Big cats dance elegantly.", True)
fx(C, {}, "Big dogs dance.", False)
fx(C, {}, "Yak zebra apple.", True, note="Z loops to A")

C = "words:consonants"
fx(C, {}, "Strong black crabs.", True)
fx(C, {}, "I like a cat.", False)
fx(C, {}, "Try my sky.", True, dec=["D-consonant-y"])
fx(C, {}, "Strong — black crabs.", True, finding="F-word-symbols", note="the dash is not a word")

C = "words:keywords_specific_position"
fx(C, {"keyword": "giggle", "n": 2, "m": 3}, "Hi there. We all giggle now.", True)
fx(C, {"keyword": "giggle", "n": 2, "m": 3}, "Hi there. We giggle all now.", False)
fx(C, {"keyword": "giggle", "n": 2, "m": 3}, "Hi there. Don't giggle now.", False, dec=["D-word"],
   note="word 3 is 'now' under G4; 'giggle' when don't splits in two")

C = "words:last_first"
fx(C, {}, "I love tea. Tea is warm. Warm days are nice.", True)
fx(C, {}, "I love tea. Coffee is warm.", False)
fx(C, {}, "One sentence only.", True, dec=["D-vacuous"])
fx(C, {}, "I love tea. Tea. Tea is warm.", True, finding="F-lastfirst-punct",
   note="a one-word sentence keeps its period in the grader")
fx(C, {}, "I love “tea.” Tea is warm.", True, note="closing curly quote after the last word")

C = "words:no_consecutive"
fx(C, {}, "Big cats dance happily.", True)
fx(C, {}, "Big bears dance.", False)
fx(C, {}, "Big, Bold cats.", False, note="b, b")

C = "words:odd_even_syllables"
fx(C, {}, "Cat happy dog water.", True, note="1,2,1,2")
fx(C, {}, "Cat dog happy.", False, note="1,1")
fx(C, {}, "Duo cat happy dog.", True, finding="F-syllables", note="duo has 2 syllables: 2,1,2,1")
fx(C, {}, "Trio happy.", False, finding="F-syllables", note="trio has 2 syllables: 2,2")
fx(C, {}, "It isn't hot.", True, finding="F-syllables", note="it 1, isn't 2, hot 1")

C = "words:palindrome"
P10 = "level radar civic refer rotor kayak madam racecar stats tenet"
fx(C, {}, P10, True)
fx(C, {}, " ".join(P10.split()[:9]), False)
fx(C, {}, " ".join(["level"] * 10), False, dec=["D-palindrome"], note="one palindrome ten times")

C = "words:paragraph_last_first"
fx(C, {}, "Time heals all wounds in time.\nLove conquers all with love.", True)
fx(C, {}, "Time heals all wounds.\nLove conquers all.", False)
fx(C, {}, "Time, they say, heals wounds over time.", True, finding="F-para-punct",
   note="first word Time, last word time")

C = "words:prime_lengths"
fx(C, {}, "We are not big at all.", True)
fx(C, {}, "I am here.", False)
fx(C, {}, "We are — not big.", True, finding="F-word-symbols", note="the dash is not a word")

C = "words:repeats"
fx(C, {"small_n": 2.0}, "the cat and the dog", True)
fx(C, {"small_n": 2.0}, "the cat the dog the end", False, dec=["D-repeats"])
fx(C, {"small_n": 2.0}, "red — green — blue — pink", True, finding="F-word-symbols",
   note="the dash is not a word")

C = "words:start_verb"
fx(C, {}, "Imagine a world of peace.", True)
fx(C, {}, "The world is big.", False)
fx(C, {}, "**Imagine** a world of peace.", True, finding="F-start-verb-markup",
   note="first word after markup is the verb Imagine")
fx(C, {}, "# Imagine a world of peace\nIt is calm.", True, finding="F-start-verb-markup",
   note="heading marker before the verb")
fx(C, {}, "Discover the truth.", True, finding="F-start-verb-tagger", note="imperative verb tagged IN")
fx(C, {}, "Craft a story.", True, finding="F-start-verb-tagger", note="imperative verb tagged NNP")

C = "words:vowel"
fx(C, {}, "Cats sit on mats.", True, note="a, i, o")
fx(C, {}, "Education is useful.", False)
fx(C, {}, "Cats can nap at a bar.", False, dec=["D-vowel"], note="only a")
fx(C, {}, "Cats sit\non mats.", False, note="two paragraphs/lines")

C = "words:words_position"
fx(C, {"keyword": "despite"}, "Go despite the rain, go on despite it.", True)
fx(C, {"keyword": "despite"}, "Go on despite rain.", False)
fx(C, {"keyword": "despite"}, "Yes, despite the rain we went despite it.", True, finding="F-words-position",
   note="word 2 and the second-to-last word are 'despite'")

# ---------------------------------------------------------------- custom
C = "custom:character_reverse"
fx(C, {}, ".elgae dlab ehT", True)
fx(C, {}, "The bald eagle.", False)
fx(C, {}, "The bald eagle. Reversed: elgae dlab ehT", False, finding="F-reverse-substring",
   note="a forward sentence plus a partial reversal")

C = "custom:word_reverse"
fx(C, {}, "eagle. bald the is animal national The", True)
fx(C, {}, "The national animal is the bald eagle.", False)
fx(C, {}, "Eagle bald the is animal national the. I hope this helps you today.", False,
   finding="F-reverse-substring", note="second sentence is in forward order")

CSV_HDR = "ID,Country,City,Year,Count"
rows7 = [f"{i},France,Paris,{2000 + i},{i * 3}" for i in range(1, 8)]
C = "custom:csv_city"
fx(C, {}, "\n".join([CSV_HDR] + rows7), True)
fx(C, {}, "\n".join([CSV_HDR] + rows7[:6]), False)
fx(C, {}, "```csv\n" + "\n".join([CSV_HDR] + rows7) + "\n```", True, dec=["D-csv-wrap"])

C = "custom:csv_quotes"
QH = '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"'
qrows = ['"1"\t"Math"\t"A"\t"Fall"\t"95"', '"2"\t"Art"\t"B"\t"Fall"\t"88"', '"3"\t"Bio"\t"A"\t"Spring"\t"91"']
fx(C, {}, "\n".join([QH] + qrows), True)
fx(C, {}, "StudentID\tSubject\tGrade\tSemester\tScore\n1\tMath\tA\tFall\t95\n2\tArt\tB\tFall\t88\n3\tBio\tA\tSpring\t91", False)
fx(C, {}, "\n".join([QH, '"1"\t\t"A"\t"Fall"\t"95"'] + qrows[1:]), False, finding="F-exception",
   note="an empty unquoted field")

C = "custom:csv_special_character"
SH = "ProductID,Category,Brand,Price,Stock"
srows = [f"{i},Tools,Acme,{10 + i}.00,{i * 5}" for i in range(1, 15)]
sp = list(srows)
sp[0] = '1,Tools,"Smith & Co",11.00,5'
fx(C, {}, "\n".join([SH] + sp), True)
fx(C, {}, "\n".join([SH] + srows), False)
bad = list(sp)
bad[4] = "5,Tools,Acme"
fx(C, {}, "\n".join([SH] + bad), False, finding="F-csv-special-rows", note="row 5 has 3 fields")
two = list(sp)
two[1] = '2,Tools,"B&B",12.00,10'
fx(C, {}, "\n".join([SH] + two), False, dec=["D-special"], note="two special quoted fields")

C = "custom:date_format_list"
fx(C, {}, "1796-04-12, 1805-12-02, 1815-06-18", True)
fx(C, {}, "April 12, 1796", False)
fx(C, {}, "1805-00-00, 1815-06-18", False, finding="F-date-zero", note="month 00 and day 00")

C = "custom:european_capitals_sort"
CAPS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius",
        "Minsk", "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg",
        "Paris", "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
fx(C, {}, ", ".join(CAPS), True, finding="F-capitals-kyiv", note="complete list including Kyiv (50.45 N)")
fx(C, {}, ", ".join(sorted(CAPS)), False, note="alphabetical, not by latitude")
fx(C, {}, ", ".join(c for c in CAPS if c != "Kyiv"), True, dec=["D-custom-content"],
   note="sorted, all above 45 N, Kyiv missing (complete only under B)")

C = "custom:mcq_count_length"


def mcq(labels):
    stems = ["Who painted it?", "Which artist painted Guernica?", "Which movement did Salvador Dali belong to?",
             "Which artist is best known for the drip painting technique of the 1940s and 1950s?"]
    out = []
    for lab, s in zip(labels, stems):
        out.append(f"{lab} {s}\nA) Picasso\nB) Monet\nC) Dali\nD) Pollock\nE) Warhol")
    return "\n\n".join(out)


fx(C, {}, mcq([f"Question {i}:" for i in range(1, 5)]), True)
fx(C, {}, mcq([f"Question {i}:" for i in range(1, 4)]), False, note="three questions")
fx(C, {}, mcq(["Question:"] * 4), True, finding="F-mcq-label", note="label 'Question' without a number")

C = "custom:multiples"
fx(C, {}, "14, 21, 28, 35, 42, 49", True)
fx(C, {}, "7, 14, 21, 28, 35, 42, 49", False)

AFRICA = sorted(["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
                 "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo",
                 "Republic of the Congo", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia",
                 "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia",
                 "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique",
                 "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles",
                 "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia",
                 "Uganda", "Zambia", "Zimbabwe"], reverse=True)
C = "custom:reverse_newline"
fx(C, {}, "\n".join(AFRICA), True)
fx(C, {}, "\n".join(sorted(AFRICA)), False)
fake = ["Zimbabwe"] + [f"Y{chr(122 - i // 26)}{chr(122 - i % 26)}" for i in range(51)]
fx(C, {}, "\n".join(fake), False, finding="F-africa-content", note="51 invented names after Zimbabwe")
fx(C, {}, "\n".join(f"{i}. {c}" for i, c in enumerate(AFRICA, 1)), True, finding="F-africa-content",
   note="numbered list, correct order")
fx(C, {}, "Zimbabwe\nZambia\nUganda", True, dec=["D-custom-content"], note="incomplete but ordered")

C = "custom:sentence_alphabet"
ALPHA = ["Ants", "Bears", "Cats", "Dogs", "Eels", "Foxes", "Geese", "Hens", "Ibises", "Jays", "Koalas", "Lions",
         "Moles", "Newts", "Owls", "Pigs", "Quails", "Rats", "Seals", "Toads", "Urchins", "Voles", "Wasps", "Xerus",
         "Yaks", "Zebras"]
story = " ".join(f"{a} came to the party." for a in ALPHA)
fx(C, {}, story, True)
fx(C, {}, " ".join(f"{a} came to the party." for a in ALPHA[:25]), False, note="25 sentences")
story_q = " ".join((f"\"{a} came to the party,\" said the host." if a == "Moles" else f"{a} came to the party.")
                   for a in ALPHA)
fx(C, {}, story_q, True, finding="F-alphabet-quote", note="sentence 13 opens with a quotation mark")
