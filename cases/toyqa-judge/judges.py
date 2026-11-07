"""Judge back ends for offline runs of the ToyQA pipelines.

Both take the rendered judge prompt and the call number (1 for the first call, 2 for the retry) and return the
judge's reply text. Neither is part of the pipeline under audit.

RecordedJudge replays judge_replies.jsonl: the replies that the deployed judge model gave in the stored run, looked
up by the sha256 of the UTF-8 prompt and the call number. It covers exactly the prompts of the stored run and raises
LookupError for any other prompt.

FakeJudge is a deterministic stand-in for tests. It reads the gold target, the "also accepted" answers and the
predicted answer from the prompt, and replies "A" when the predicted answer contains the gold target or an accepted
answer (compared after removing accents, case, punctuation and the articles a, an, the), "C" when the predicted
answer is empty or says it does not know, and "B" otherwise. It does not model how the deployed judge handles hard
cases.
"""

import hashlib
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REFUSALS = ("not sure", "don't know", "do not know", "no idea", "cannot answer", "can't answer", "unsure")


def prompt_sha256(prompt):
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class RecordedJudge:
    def __init__(self, path=os.path.join(HERE, "judge_replies.jsonl")):
        self.replies = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    self.replies[(r["prompt_sha256"], r["call"])] = r["reply"]

    def __call__(self, prompt, call):
        key = (prompt_sha256(prompt), call)
        if key not in self.replies:
            raise LookupError(f"no recorded reply for prompt {key[0][:16]}... call {call}")
        return self.replies[key]


def _normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    words = re.sub(r"[^0-9a-z]+", " ", text).split()
    return " ".join(w for w in words if w not in ("a", "an", "the"))


class FakeJudge:
    def __call__(self, prompt, call):
        gold = re.search(r"^Gold target: (.*)$", prompt, re.M).group(1)
        m = re.search(r"\(also accepted: (.*)\)$", gold)
        answers = [gold[:m.start()].rstrip()] + m.group(1).split(", ") if m else [gold]
        predicted = prompt.split("<<<\n", 1)[1].rsplit("\n>>>", 1)[0]
        said = " " + _normalize(predicted) + " "
        if any(" " + _normalize(a) + " " in said for a in answers if _normalize(a)):
            return "A"
        if not predicted.strip() or any(r in predicted.casefold().replace("’", "'") for r in REFUSALS):
            return "C"
        return "B"
