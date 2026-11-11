"""Reproduce a fixture's verdicts: SkyRL checker, task-curation (verifyit) check, contract.

Usage (from W, with NLTK_DATA and PYTHONDONTWRITEBYTECODE set as in case/TASK.md):
  .venv/Scripts/python.exe audit/repro.py <fixture id>          # e.g. keywords:word_once:c67fb421612a
  .venv/Scripts/python.exe audit/repro.py --check <id> '<kwargs json>' '<text>'
  .venv/Scripts/python.exe audit/repro.py --extraction <unclosed-thinking|literal-think-tag|closed-thinking>
  .venv/Scripts/python.exe audit/repro.py --nth-rng
  .venv/Scripts/python.exe audit/repro.py --empty-last-word

Prints one line: skyrl=<verdict> verifyit=<verdict or not-gated> contract=<verdict>.
"""
import json
import logging
import pathlib
import random
import sys

logging.disable(logging.CRITICAL)
W = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(W / "audit"))
sys.path.insert(0, str(W / "audit" / "tests"))
import harness  # noqa: E402
import replacement as rp  # noqa: E402
from fixtures import EXTRACTION, all_fixtures  # noqa: E402


def show(check, kwargs, text):
    sk = harness.skyrl_check(check, kwargs, text)
    vi = "not-gated" if check in harness.SEMANTIC else harness.curation_check(check, kwargs, text)
    ct = rp.check_constraint(check, kwargs, text)
    print(f"check={check} kwargs={json.dumps(kwargs, ensure_ascii=False)} text={json.dumps(text, ensure_ascii=False)}")
    print(f"skyrl={sk} verifyit={vi} contract={ct}")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    if a[0] == "--check":
        show(a[1], json.loads(a[2]), a[3])
    elif a[0] == "--extraction":
        for suffix, reasoning, raw, record, label, note in EXTRACTION:
            if suffix == a[1]:
                sk, _, _, sk_text = harness.skyrl_grade(raw, record)
                gate, _, _ = harness.curation_gate(raw, record)
                ct = rp.grade_row(rp.graded_text(raw, reasoning), record)[0]
                print(f"raw={json.dumps(raw)} reasoning_model={reasoning} record={json.dumps(record)}")
                print(f"graded_text_by_graders={json.dumps(sk_text)}")
                print(f"skyrl_reward={sk} gate_passed={gate} contract_reward={ct}")
    elif a[0] == "--nth-rng":
        kw = {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}
        text = "Intro text.\n\nHistory matters."
        verdicts = []
        for seed in range(10):
            random.seed(seed)
            verdicts.append(harness.skyrl_check("length_constraints:nth_paragraph_first_word", kw, text))
        print(f"kwargs={json.dumps(kw)} text={json.dumps(text)}")
        print("skyrl verdicts for random.seed(0..9):", verdicts,
              "verifyit=", harness.curation_check("length_constraints:nth_paragraph_first_word", kw, text),
              "contract=", rp.check_constraint("length_constraints:nth_paragraph_first_word", kw, text))
    elif a[0] == "--empty-last-word":
        record = {"instruction_id_list": ["last_word:last_word_answer"], "kwargs": [{"last_word": "limit"}]}
        reward, results, errors, _ = harness.skyrl_grade("", record)
        print(f"skyrl_reward={reward} results={results} instruction_errors={errors}")
    else:
        fx = {f["id"]: f for f in all_fixtures()}[a[0]]
        show(fx["check"], fx["kwargs"], fx["text"])


if __name__ == "__main__":
    main()
