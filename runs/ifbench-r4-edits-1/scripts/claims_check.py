"""Recompute a few numbers quoted in audit/AUDIT.md.

1. Which grader checkers call NLTK-data-backed functions (sentence tokenizer,
   word tokenizer, tagger, stop words, \\w+ counters in instructions_util).
2. Verdicts that loose grading adds over strict, and how many of them the
   replacement (contract) fails.
"""
import ast
import json

import common

src = (common.CASE / "grader" / "IFBench" / "instructions.py").read_text(encoding="utf-8")
tree = ast.parse(src)
reg = {}
for line in (common.CASE / "grader" / "IFBench" / "instructions_registry.py").read_text(encoding="utf-8").splitlines():
    if "instructions." in line and ":" in line:
        k = line.split('"')[1]
        reg[line.split("instructions.")[1].strip().rstrip(",")] = k
NEEDLES = ("split_into_sentences", "word_tokenize", "pos_tag", "count_stopwords", "_word_tokens_without_punctuation")
uses = []
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name in reg:
        body = ast.get_source_segment(src, node)
        cf = body[body.find("def check_following"):]
        if any(n in cf for n in NEEDLES):
            uses.append(reg[node.name])
print(len(uses), "checks use NLTK data (punkt, tagger or stopwords):", sorted(uses))

add = add_fail = 0
for f in (common.W / "audit" / "work" / "panel").glob("*.jsonl"):
    for line in f.read_text(encoding="utf-8").splitlines():
        for c in json.loads(line)["checks"]:
            if c["gl"] is True and c["gs"] is not True:
                add += 1
                add_fail += c["rep"] is not True
print("loose-only passes:", add, "of which the replacement fails:", add_fail, f"({add_fail / add:.1%})")
