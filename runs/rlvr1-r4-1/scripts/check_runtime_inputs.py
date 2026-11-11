"""Code-level runtime inputs of grader 1 (SkyRL / NVIDIA checkers).

1. Which NLTK resources the checkers load, and from where.
2. Whether building any of the 28,219 constraints with the row's kwargs consumes
   Python's global random state (a randomized parameter would make the verdict
   depend on the RNG).
3. Whether the built parameters equal the kwargs (no silent defaulting).
"""
import json
import os
import pathlib
import random
import sys

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "case" / "reference"))

from skyrl_gym.envs.nemotron_ultra.instruction_following import _ensure_nltk_data, build_instruction  # noqa: E402
import nltk  # noqa: E402

DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"


def main():
    print("NLTK_DATA", os.environ.get("NLTK_DATA"))
    _ensure_nltk_data()
    print("punkt_tab:", nltk.data.find("tokenizers/punkt_tab"))
    try:
        print("punkt (pickle):", nltk.data.find("tokenizers/punkt"))
    except LookupError:
        print("punkt (pickle): not installed")
    from verifiable_instructions import instructions_util
    tok = instructions_util._get_sentence_tokenizer()
    print("count_sentences tokenizer:", type(tok).__module__, type(tok).__name__)
    print("count_sentences('A b. C d.') =", instructions_util.count_sentences("A b. C d."))

    rows = [json.loads(l) for l in DATA.open(encoding="utf-8")]
    consumed = {}
    mismatched = {}
    errors = {}
    for row in rows:
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            kw = {k: v for k, v in (kw or {}).items() if v is not None}
            random.seed(12345)
            before = random.getstate()
            try:
                ins = build_instruction(iid, kw)
            except Exception as e:  # noqa: BLE001
                errors[iid] = errors.get(iid, 0) + 1
                continue
            if random.getstate() != before:
                consumed[iid] = consumed.get(iid, 0) + 1
            args = ins.get_instruction_args() or {}
            norm = {k: (sorted(v) if isinstance(v, list) else v) for k, v in args.items()}
            want = {k: (sorted(v) if isinstance(v, list) else v) for k, v in kw.items()}
            if iid == "length_constraints:nth_paragraph_first_word":
                want = {**want, "first_word": want["first_word"].lower()}
            if norm != want:
                mismatched.setdefault(iid, []).append((kw, args))
    print("constructions that consumed the RNG:", consumed or "none")
    print("construction errors:", errors or "none")
    print("built args differing from kwargs:", {k: len(v) for k, v in mismatched.items()} or "none")
    for k, v in mismatched.items():
        print("  e.g.", k, v[0])


if __name__ == "__main__":
    main()
