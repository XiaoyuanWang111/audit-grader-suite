"""Probe environment-dependent behaviors of the NVIDIA checkers (sentence tokenizer, langdetect)."""
import os
import sys
import traceback

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "case", "reference"))
from skyrl_gym.envs.nemotron_ultra.instruction_following import grade_instruction_following, build_instruction  # noqa: E402
from skyrl_gym.envs.nemotron_ultra.instruction_following import _ensure_nltk_data  # noqa: E402
from verifiable_instructions import instructions_util  # noqa: E402

_ensure_nltk_data()
try:
    print("count_sentences:", instructions_util.count_sentences("One. Two. Three."))
except Exception as e:  # noqa: BLE001
    print("count_sentences raised:", type(e).__name__, str(e)[:300])
r = {"instruction_id_list": ["length_constraints:number_sentences"], "kwargs": [{"num_sentences": 2, "relation": "at least"}]}
print("number_sentences reward:", grade_instruction_following("One. Two. Three.", r))
import nltk  # noqa: E402
print("word_tokenize:", nltk.word_tokenize("Hello, world. Don't stop."))
import langdetect  # noqa: E402
from langdetect import DetectorFactory  # noqa: E402
DetectorFactory.seed = 0
samples = [
    "THIS IS A SHORT ANSWER IN ENGLISH WRITTEN ENTIRELY IN CAPITAL LETTERS.",
    "HELLO WORLD",
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG.",
    "this is a short answer in english written entirely in lowercase letters.",
    "",
]
for s in samples:
    try:
        print(repr(s[:40]), langdetect.detect(s))
    except Exception as e:  # noqa: BLE001
        print(repr(s[:40]), "raised", type(e).__name__, e)
