"""Fixtures added after the review labels were read (2026-11-10), for three defects found while
explaining review cases and the panel residuals. Labels come from audit/CONTRACT.md (version 2)
under every reading, as in fixtures_data.py. `replacement` names a replacement error where the
replacement grader (not changed in this round) gets the label wrong.

Fixture id = check + first 8 hex of sha256 over the kwargs and the response, as in fixtures_data.py.
"""
import hashlib
import json
from dataclasses import dataclass, field

from fixtures_data import ROWS


@dataclass
class PostFx:
    check: str
    label: str
    response: str
    key: str
    note: str
    grader: str = ""
    reference: str = ""
    replacement: str = ""
    kwargs: dict = field(default_factory=dict)
    prompt: str = ""
    id: str = ""


THIRTEEN_A = "Alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike."
THIRTEEN_B = "November oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu."

POST = [
    # Two sentences of 2 and 3 words (difference 1, the prompt asks for 5): fail under every reading.
    # The grader's sentence splitter does not end a sentence at ".</i>", sees one sentence, and passes it
    # under D-vacuous B.
    PostFx("sentence:increment", "fail", "<i>Cats sleep.</i> Dogs run fast.", "190",
           "a period followed by an HTML closing tag", grader="F-sentence-html-tags", reference="F-sentence-html-tags"),
    # 26 words, the prompt asks for 24 to 28: pass. `\w+` also counts the tag names "p" (4 more words).
    PostFx("count:word_count_range", "pass", f"<p>{THIRTEEN_A}</p>\n<p>{THIRTEEN_B}</p>", "43",
           "HTML paragraph tags around 26 words", grader="F-wordcount-html-tags", reference="F-wordcount-html-tags"),
    # Each sentence ends with an emoji; the first is the US flag (two regional-indicator characters).
    PostFx("format:emoji", "pass", "I love this country. \U0001F1FA\U0001F1F8 It is my home. \U0001F389", "65",
           "a flag emoji after the first sentence", grader="F-emoji-flag", reference="F-emoji-flag",
           replacement="REPL-emoji-flag"),
    # The first quoted phrase is followed only by "=" and the next quoted phrase: no explanation. The
    # grader checks only that two quotation marks are not adjacent and that the text does not end
    # with one.
    PostFx("format:quote_unquote", "fail", '"Those" = "Diese" is the German word for those.', "116",
           "a separator symbol between two quoted phrases", grader="F-quote-separator", reference="F-quote-separator"),
]

for f in POST:
    row = ROWS[f.key]
    f.kwargs = dict(row["kwargs"][row["instruction_id_list"].index(f.check)])
    f.prompt = row["prompt"]
    h = hashlib.sha256(json.dumps({"kwargs": f.kwargs, "response": f.response}, sort_keys=True,
                                  ensure_ascii=False).encode("utf-8")).hexdigest()[:8]
    f.id = f"{f.check}-{h}"
