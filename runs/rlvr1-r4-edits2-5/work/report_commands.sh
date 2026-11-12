#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export NLTK_DATA="<W>/case/deps/nltk_data"
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=../.venv/Scripts/python.exe
echo '== G1 ' '{"A": "pass", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check punctuation:no_comma null 'Okay the user wants a short answer so I will think about it' --reasoning 2>/dev/null
echo '== G2 ' '{"A": "fail", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check keywords:existence '{"keywords": ["tag"]}' 'Write the <think> tag before your notes.' 2>/dev/null
echo '== G3 ' '{"A": "some", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check length_constraints:nth_paragraph_first_word '{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}' $'History is long.\n\nHistory is fun.' --runs 30 2>/dev/null
echo '== G4 ' '{"A": "exception", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check last_word:last_word_answer '{"last_word": "hello"}' ' ' 2>/dev/null
echo '== D-empty ' '{"A": "1.0", "B": "failed", "C": "0.0"}'
$PY scripts/repro.py row eb817d5f-9f71-4bac-9f5e-9863c5e3957a '' 2>/dev/null
echo '== A-F1 ' '{"A": "fail", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check keywords:word_once '{"keyword": "fix"}' 'Fix it now and fix it well.' 2>/dev/null
echo '== A-F1 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check keywords:word_once '{"keyword": "fix"}' 'Let me fix the prefix.' 2>/dev/null
echo '== A-F2 ' '{"A": "fail", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check keywords:word_count_different_numbers '{"keyword": "box", "frequency": 2, "relation": "less than"}' 'A box and another box.' 2>/dev/null
echo '== A-F2 ' '{"A": "pass", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check keywords:word_count_different_numbers '{"keyword": "box", "frequency": 2, "relation": "less than"}' 'No crates here.' 2>/dev/null
echo '== A-F3 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check first_word:first_word_answer '{"first_word": "development"}' 'Development, as a concept, matters.' 2>/dev/null
echo '== A-F3 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check length_constraints:nth_paragraph_first_word '{"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"}' $'Cats are nice.\n\nIf: you like dogs, fine.' 2>/dev/null
echo '== A-F4 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check keywords:keyword_specific_position '{"keyword": "shot", "n": 2, "m": 3}' 'I went out. Then, the shot came.' 2>/dev/null
echo '== A-F4 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check keywords:keyword_specific_position '{"keyword": "repeat", "n": 1, "m": 1}' 'Repeat after me. Good.' 2>/dev/null
echo '== A-F5 ' '{"A": "fail", "B": "judge", "C": "pass"}'
$PY scripts/repro.py check count:count_unique null 'Apples, pears, plums.' 2>/dev/null
echo '== A-F6 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check count:counting_composition '{"n_sent": 3, "n_words": 2}' $'Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Parents watch. Time flies.' 2>/dev/null
echo '== A-F7 ' '{"A": "pass", "B": "judge", "C": "fail"}'
$PY scripts/repro.py check detectable_format:bigram_wrapping null '<<I am>> home' 2>/dev/null
echo '== A-F7 ' '{"A": "pass", "B": "judge", "C": "fail"}'
$PY scripts/repro.py check detectable_format:bigram_wrapping null Hello 2>/dev/null
echo '== A-F8 ' '{"A": "pass", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check detectable_format:constrained_response null 'My answer is yes. My answer is no.' 2>/dev/null
echo '== A-F9 ' '{"A": "pass", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check detectable_format:multiple_sections '{"num_sections": 2, "section_spliter": "SECTION"}' $'SECTION 1\nCats are great; see SECTION 2 for dogs.' 2>/dev/null
echo '== A-F10 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check detectable_format:number_bullet_lists '{"num_bullets": 2}' $'* Apples.\n* Bananas.\n\n---\n\nThat is all.' 2>/dev/null
echo '== A-F10 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check detectable_format:number_bullet_lists '{"num_bullets": 2}' $'*Note* the list:\n* Apples.\n* Bananas.' 2>/dev/null
echo '== A-F11 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check detectable_format:square_brackets null '[I] [like] [cats].' 2>/dev/null
echo '== A-F12 ' '{"A": "pass", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check keywords:no_adjacent_consecutive null '(apple) banana split.' 2>/dev/null
echo '== A-F12 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'Pick 1, 2 or 9' 2>/dev/null
echo '== A-F13 ' '{"A": "pass", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check keywords:palindrome null 'Cats run - dogs walk.' 2>/dev/null
echo '== A-F14 ' '{"A": "pass", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check detectable_content:postscript '{"postscript_marker": "P.S."}' 'Ship the parcel with U.P.S. today.' 2>/dev/null
echo '== A-F15 ' '{"A": "pass", "B": "judge", "C": "fail"}'
$PY scripts/repro.py check language:response_language '{"language": "fr"}' '12345 67890' 2>/dev/null
echo '== A-F16 ' '{"A": "pass", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' '***Cats*** are nice and dogs are loyal.' 2>/dev/null
echo '== A-F17 ' '{"A": "fail", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check first_word:first_word_sent '{"first_word": "peace"}' '1. Peace is good. Peace is calm.' 2>/dev/null
echo '== A-F18 ' '{"A": "pass", "B": "fail", "C": "fail"}'
$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is the best medicine. Laughter is our best medicine.' 2>/dev/null
echo '== A-F19 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check change_case:english_capital null 'I LIKE CATS AND DOGS VERY MUCH.' 2>/dev/null
echo '== A-F20 ' '{"A": "fail", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check length_constraints:number_sentences '{"num_sentences": 3, "relation": "at least"}' '我很好。你呢？他也很好。' 2>/dev/null
echo '== A-F21 ' '{"A": "fail", "B": "pass", "C": "pass"}'
$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' '<b>I</b> like it' 2>/dev/null
echo '== A-F22 ' '{"A": "fail", "B": "judge", "C": "pass"}'
$PY scripts/repro.py check count:count_unique null '**Every** word here appears once.' 2>/dev/null
echo '== B-F1 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is a best medicine. Laughter is our best medicine.' 2>/dev/null
echo '== B-F1 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is the best medicine. Laughter is the best medicine.' 2>/dev/null
echo '== B-F2 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' 'the the the end' 2>/dev/null
echo '== B-F2 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' 'Hello World' 2>/dev/null
echo '== B-F3 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'A big dog.' 2>/dev/null
echo '== B-F3 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'Tom ate ate cake.' 2>/dev/null
echo '== B-F4 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' $'Cats are nice.\n***\nDogs are loyal.' 2>/dev/null
echo '== B-F4 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' $'Cats are nice.\n\nDogs are loyal.' 2>/dev/null
echo '== B-F5 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check paragraphs:paragraphs '{}' $'Cats.\n***\nDogs.\n***\nBirds.' 2>/dev/null
echo '== B-F5 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check paragraphs:paragraphs2 '{}' $'Cats.\n\nDogs.\n\nBirds.' 2>/dev/null
echo '== B-F6 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check detectable_format:square_brackets null '[I] like cats.' 2>/dev/null
echo '== B-F7 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check count:counting_composition '{"n_sent": 3, "n_words": 2}' 'Birds sing. Cats sleep. Dogs run.' 2>/dev/null
echo '== B-F8 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check keywords:start_end null 'Hello world and hello.' 2>/dev/null
echo '== B-F9 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check startend:quotation null $'\'Hello there.\'' 2>/dev/null
echo '== B-F10 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check length_constraints:number_words '{"num_words": 5, "relation": "at least"}' 'Привет как дела у тебя' 2>/dev/null
echo '== B-F10 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check first_word:first_word_answer '{"first_word": "development"}' 'Привет development' 2>/dev/null
echo '== B-F11 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check length_constraints:number_sentences '{"num_sentences": 3, "relation": "at least"}' 'Dr. Smith runs. You walk.' 2>/dev/null
echo '== B-F12 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check keywords:palindrome null 'A man, a plan, a canal: Panama!' 2>/dev/null
echo '== B-F12 ' '{"A": "pass", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check keywords:palindrome null $'Cats run.\n\n---\n\nDogs walk.' 2>/dev/null
echo '== B-F13 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check detectable_format:number_highlighted_sections '{"num_highlights": 1}' $'Intro.\n\n* * *\n\nEnd.' 2>/dev/null
echo '== B-F14 ' '{"A": "fail", "B": "pass", "C": "fail"}'
$PY scripts/repro.py check detectable_format:title null $'<< >>\nIt was fine.' 2>/dev/null
echo '== B-F15 ' '{"A": "pass", "B": "fail", "C": "pass"}'
$PY scripts/repro.py check detectable_format:json_format null '```json {"answer": "Paris"} ```' 2>/dev/null
