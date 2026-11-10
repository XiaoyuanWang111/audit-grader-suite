"""Shim: reference class names backed by the replacement grader."""
import ifbench_contract as _rep

LAST = {}


class Instruction:
    def __init__(self, instruction_id):
        self.id = instruction_id


class _Base:
    IID = None

    def __init__(self, instruction_id):
        self.id = instruction_id
        self._kw = {}

    def build_description(self, **kwargs):
        self._kw = {k: v for k, v in kwargs.items() if v is not None}
        return ''

    def get_instruction_args(self):
        return dict(self._kw)

    def get_instruction_args_keys(self):
        return list(self._kw)

    def check_following(self, value):
        LAST['iid'] = self.IID
        LAST['kwargs'] = dict(self._kw)
        LAST['value'] = value
        return _rep.check(self.IID, self._kw, '', value)


class WordCountRangeChecker(_Base):
    IID = 'count:word_count_range'


class UniqueWordCountChecker(_Base):
    IID = 'count:unique_word_count'


class StopWordPercentageChecker(_Base):
    IID = 'ratio:stop_words'


class SentTypeRatioChecker(_Base):
    IID = 'ratio:sentence_type'


class SentBalanceChecker(_Base):
    IID = 'ratio:sentence_balance'


class ConjunctionCountChecker(_Base):
    IID = 'count:conjunctions'


class PersonNameCountChecker(_Base):
    IID = 'count:person_names'


class NGramOverlapChecker(_Base):
    IID = 'ratio:overlap'


class NumbersCountChecker(_Base):
    IID = 'count:numbers'


class AlphabetLoopChecker(_Base):
    IID = 'words:alphabet'


class SingleVowelParagraphChecker(_Base):
    IID = 'words:vowel'


class ConsonantClusterChecker(_Base):
    IID = 'words:consonants'


class IncrementingAlliterationChecker(_Base):
    IID = 'sentence:alliteration_increment'


class PalindromeChecker(_Base):
    IID = 'words:palindrome'


class PunctuationCoverChecker(_Base):
    IID = 'count:punctuation'


class NestedParenthesesChecker(_Base):
    IID = 'format:parentheses'


class NestedQuotesChecker(_Base):
    IID = 'format:quotes'


class PrimeLengthsChecker(_Base):
    IID = 'words:prime_lengths'


class OptionsResponseChecker(_Base):
    IID = 'format:options'


class NewLineWordsChecker(_Base):
    IID = 'format:newline'


class EmojiSentenceChecker(_Base):
    IID = 'format:emoji'


class CharacterCountUniqueWordsChecker(_Base):
    IID = 'ratio:sentence_words'


class NthWordJapaneseChecker(_Base):
    IID = 'count:words_japanese'


class StartWithVerbChecker(_Base):
    IID = 'words:start_verb'


class LimitedWordRepeatChecker(_Base):
    IID = 'words:repeats'


class IncludeKeywordChecker(_Base):
    IID = 'sentence:keyword'


class PronounCountChecker(_Base):
    IID = 'count:pronouns'


class AlternateParitySyllablesChecker(_Base):
    IID = 'words:odd_even_syllables'


class LastWordFirstNextChecker(_Base):
    IID = 'words:last_first'


class ParagraphLastFirstWordMatchChecker(_Base):
    IID = 'words:paragraph_last_first'


class IncrementingWordCountChecker(_Base):
    IID = 'sentence:increment'


class NoConsecutiveFirstLetterChecker(_Base):
    IID = 'words:no_consecutive'


class IndentStairsChecker(_Base):
    IID = 'format:line_indent'


class QuoteExplanationChecker(_Base):
    IID = 'format:quote_unquote'


class SpecialBulletPointsChecker(_Base):
    IID = 'format:list'


class ItalicsThesisChecker(_Base):
    IID = 'format:thesis'


class SubBulletPointsChecker(_Base):
    IID = 'format:sub-bullets'


class SomeBulletPointsChecker(_Base):
    IID = 'format:no_bullets_bullets'


class PrintMultiplesChecker(_Base):
    IID = 'custom:multiples'


class MultipleChoiceQuestionsChecker(_Base):
    IID = 'custom:mcq_count_length'


class ReverseNewlineChecker(_Base):
    IID = 'custom:reverse_newline'


class WordReverseOrderChecker(_Base):
    IID = 'custom:word_reverse'


class CharacterReverseOrderChecker(_Base):
    IID = 'custom:character_reverse'


class SentenceAlphabetChecker(_Base):
    IID = 'custom:sentence_alphabet'


class EuropeanCapitalsSortChecker(_Base):
    IID = 'custom:european_capitals_sort'


class CityCSVChecker(_Base):
    IID = 'custom:csv_city'


class SpecialCharacterCSVChecker(_Base):
    IID = 'custom:csv_special_character'


class QuotesCSVChecker(_Base):
    IID = 'custom:csv_quotes'


class DateFormatListChecker(_Base):
    IID = 'custom:date_format_list'


class KeywordsMultipleChecker(_Base):
    IID = 'count:keywords_multiple'


class KeywordSpecificPositionChecker(_Base):
    IID = 'words:keywords_specific_position'


class WordsPositionChecker(_Base):
    IID = 'words:words_position'


class RepeatChangeChecker(_Base):
    IID = 'repeat:repeat_change'


class RepeatSimpleChecker(_Base):
    IID = 'repeat:repeat_simple'


class RepeatSpanChecker(_Base):
    IID = 'repeat:repeat_span'


class TitleCaseChecker(_Base):
    IID = 'format:title_case'


class OutputTemplateChecker(_Base):
    IID = 'format:output_template'


class NoWhitespaceChecker(_Base):
    IID = 'format:no_whitespace'


