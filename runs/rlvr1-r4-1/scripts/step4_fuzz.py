"""Step 4: fuzz both graders' checks for exceptions.

Generates N random texts (seed recorded) from a token mix: English words, digits, punctuation,
markdown symbols, brackets, quotes, CJK and Cyrillic letters, emoji, whitespace runs, newlines,
reasoning markers, and empty or whitespace-only texts. Each text is graded by every check of
both graders with the kwargs of the first data constraint of each id. Exceptions are counted per
check and exception type. Counts depend on the generator; they are not rates.

Usage: python audit/scripts/step4_fuzz.py [N] [seed]
"""
import collections
import json
import pathlib
import random
import sys
import traceback

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
import harness  # noqa: E402
from verifyit.modes.ifeval import CONSTRAINTS  # noqa: E402

TOKENS = (
    ["the", "cat", "Level", "NASA", "data", "policy", "village", "act", "garden", "If", "P.S.", "p.s.", "P.P.S",
     "SECTION", "Section", "1", "2", "3.5", "-5", "well-known", "it's", "I", "a", "racecar", "Any", "other",
     "questions?", "limit", "peace"]
    + [".", ",", "!", "?", ";", ":", "-", "--", "—", "...", "…", "，", "。", "！", "、", "(", ")", "[", "]", "[]",
       "<<", ">>", "<<a b>>", "*", "**", "***", "******", "* * *", "#", "##", "`", "```", "```json", "{", "}",
       '"', "'", "“", "”", "_", "|", "/", "\\"]
    + ["你好", "世界", "привет", "мир", "😀", "é", "İ", "ß", "ﬁ", "​", " "]
    + [" ", "  ", "\t", "\n", "\n\n", "\n\n\n", "\r\n", " \n "]
    + ["<think>", "</think>", "<thinking>", "<|eot_id|>"]
)


def gen(rng):
    k = rng.random()
    if k < 0.03:
        return ""
    if k < 0.06:
        return rng.choice([" ", "\n", "\n\n", "\t \n"])
    n = rng.randint(1, 60)
    out = []
    for _ in range(n):
        t = rng.choice(TOKENS)
        out.append(t)
        if rng.random() < 0.6:
            out.append(" ")
    return "".join(out)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261111
    rng = random.Random(seed)
    rows = harness.load_rows()
    kw_by_id = {}
    for row in rows:
        rec = harness.record_of(row)
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            if iid not in kw_by_id:
                kw_by_id[iid] = {k: v for k, v in (kw or {}).items() if v is not None}
    texts = [gen(rng) for _ in range(n)]
    nv_exc = collections.Counter()
    vi_exc = collections.Counter()
    nv_none = collections.Counter()
    examples = {}
    for text in texts:
        for iid, kw in sorted(kw_by_id.items()):
            if iid == "length_constraints:nth_paragraph_first_word":
                kw = {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"}
            try:
                ins = harness.build_instruction(iid, kw)
                v = ins.check_following(text)
                if not isinstance(v, bool):
                    nv_none[(iid, type(v).__name__)] += 1
            except Exception as e:  # noqa: BLE001
                key = (iid, type(e).__name__)
                nv_exc[key] += 1
                examples.setdefault("nvidia " + repr(key), repr(text[:80]))
            if iid in CONSTRAINTS:
                try:
                    CONSTRAINTS[iid](text, kw)
                except Exception as e:  # noqa: BLE001
                    key = (iid, type(e).__name__)
                    vi_exc[key] += 1
                    examples.setdefault("verifyit " + repr(key), repr(text[:80]))
    out = {
        "n_texts": n, "seed": seed, "checks_per_text": len(kw_by_id),
        "nvidia_exceptions": {f"{a} {b}": c for (a, b), c in nv_exc.items()},
        "nvidia_non_bool_returns": {f"{a} {b}": c for (a, b), c in nv_none.items()},
        "verifyit_exceptions": {f"{a} {b}": c for (a, b), c in vi_exc.items()},
        "examples": examples,
    }
    (W / "audit" / "out" / "step4_fuzz.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
