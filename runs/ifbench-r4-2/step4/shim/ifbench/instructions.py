import os as _os
import sys as _sys
from pathlib import Path as _P

_W = _P(__file__).resolve().parents[4]
exec(compile(open(_W / "audit/frozen/code/reference/IFBench/ifbench/instructions.py", encoding="utf-8").read(),
             "ref_instructions.py", "exec"))

_TARGET = _os.environ.get("IFB_TARGET", "reference")

# class name -> instruction id (the grader's registry uses the same names)
_NAME_TO_ID = {
    "WordCountRangeChecker": "count:word_count_range", "UniqueWordCountChecker": "count:unique_word_count",
    "StopWordPercentageChecker": "ratio:stop_words", "SentTypeRatioChecker": "ratio:sentence_type",
    "SentBalanceChecker": "ratio:sentence_balance", "ConjunctionCountChecker": "count:conjunctions",
    "PersonNameCountChecker": "count:person_names", "NGramOverlapChecker": "ratio:overlap",
    "NumbersCountChecker": "count:numbers", "AlphabetLoopChecker": "words:alphabet",
    "SingleVowelParagraphChecker": "words:vowel", "ConsonantClusterChecker": "words:consonants",
    "IncrementingAlliterationChecker": "sentence:alliteration_increment", "PalindromeChecker": "words:palindrome",
    "PunctuationCoverChecker": "count:punctuation", "NestedParenthesesChecker": "format:parentheses",
    "NestedQuotesChecker": "format:quotes", "PrimeLengthsChecker": "words:prime_lengths",
    "OptionsResponseChecker": "format:options", "NewLineWordsChecker": "format:newline",
    "EmojiSentenceChecker": "format:emoji", "CharacterCountUniqueWordsChecker": "ratio:sentence_words",
    "NthWordJapaneseChecker": "count:words_japanese", "StartWithVerbChecker": "words:start_verb",
    "LimitedWordRepeatChecker": "words:repeats", "IncludeKeywordChecker": "sentence:keyword",
    "PronounCountChecker": "count:pronouns", "AlternateParitySyllablesChecker": "words:odd_even_syllables",
    "LastWordFirstNextChecker": "words:last_first", "ParagraphLastFirstWordMatchChecker": "words:paragraph_last_first",
    "IncrementingWordCountChecker": "sentence:increment", "NoConsecutiveFirstLetterChecker": "words:no_consecutive",
    "IndentStairsChecker": "format:line_indent", "QuoteExplanationChecker": "format:quote_unquote",
    "SpecialBulletPointsChecker": "format:list", "ItalicsThesisChecker": "format:thesis",
    "SubBulletPointsChecker": "format:sub-bullets", "SomeBulletPointsChecker": "format:no_bullets_bullets",
    "PrintMultiplesChecker": "custom:multiples", "MultipleChoiceQuestionsChecker": "custom:mcq_count_length",
    "ReverseNewlineChecker": "custom:reverse_newline", "WordReverseOrderChecker": "custom:word_reverse",
    "CharacterReverseOrderChecker": "custom:character_reverse", "SentenceAlphabetChecker": "custom:sentence_alphabet",
    "EuropeanCapitalsSortChecker": "custom:european_capitals_sort", "CityCSVChecker": "custom:csv_city",
    "SpecialCharacterCSVChecker": "custom:csv_special_character", "QuotesCSVChecker": "custom:csv_quotes",
    "DateFormatListChecker": "custom:date_format_list", "KeywordsMultipleChecker": "count:keywords_multiple",
    "KeywordSpecificPositionChecker": "words:keywords_specific_position", "WordsPositionChecker": "words:words_position",
    "RepeatChangeChecker": "repeat:repeat_change", "RepeatSimpleChecker": "repeat:repeat_simple",
    "RepeatSpanChecker": "repeat:repeat_span", "TitleCaseChecker": "format:title_case",
    "OutputTemplateChecker": "format:output_template", "NoWhitespaceChecker": "format:no_whitespace",
}


def _target_impl():
    _sys.path.insert(0, str(_W / "audit" / "frozen" / "code" / "grader"))
    _sys.path.insert(0, str(_W / "audit" / "replacement"))
    _sys.path.insert(0, str(_W / "audit" / "scripts"))
    if _TARGET == "grader":
        from IFBench import instructions_registry as greg  # the grader package, not the shim
        return greg.INSTRUCTION_DICT, None
    import ifbench_fixed as rf
    return None, rf


if _TARGET != "reference":
    def _make(cls_name, iid):
        ref_cls = globals()[cls_name]

        def check_following(self, value):
            kwargs = {k: v for k, v in (self.get_instruction_args() or {}).items() if v is not None}
            greg, rf = _target_impl()
            if greg is not None:
                inst = greg[iid](iid)
                inst.build_description(**kwargs)
                return inst.check_following(value)
            return rf.check(iid, kwargs, value, prompt="PROMPT", opts=rf.PROPOSED)

        return type(cls_name, (ref_cls,), {"check_following": check_following})

    for _name, _iid in _NAME_TO_ID.items():
        if _name in globals():
            globals()[_name] = _make(_name, _iid)
