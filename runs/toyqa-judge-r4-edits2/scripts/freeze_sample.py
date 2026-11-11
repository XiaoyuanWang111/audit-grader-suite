"""Step 6.1-6.3: draw, freeze and render the blinded-review sample. The review itself (6.4-6.5) is not run here.

Usage (from W):  python -B audit/scripts/freeze_sample.py
Needs audit/panel/labels.jsonl (python -B audit/scripts/panel.py). Writes audit/frozen/:
  cases.jsonl        the case list (case_id, stratum, question_id, response row sha256), sorted by case_id
  keys.jsonl         per case: source response id and model, finish_reason, verdicts of every grader (not for reviewers)
  responses/<id>.txt the exact response of each case
  batch_A.md, batch_B.md   the same cases in two different orders, for reviewers A and B
  reviewer_prompt.md the reviewer prompt from skill/references/reviewer-prompt.md with this run's values
  show_case.py       the helper that prints a case's exact response
  SHA256SUMS         sha256 of every frozen file
Strata: whether the replacement (X) and the grader under audit (G) disagree. The population is the 48 stored
verdicts; every case of both strata is drawn (a census), so the seed only fixes the opaque ids and batch orders.
"""
import hashlib
import json
import random
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import AUDIT, CASE, load_jsonl, questions, responses  # noqa: E402

SEED = 20261111
FROZEN = AUDIT / "frozen"
CHECK_NAME = "ToyQA answer grade"
CHECK_TEXT = (
    "Give the response the label it deserves under these rules. "
    "(1) The answer is the text after the last </think> in the response, or the whole response if it has no "
    "</think>, with leading and trailing whitespace removed. A response that contains <think> but no </think> has "
    "reasoning that never closed and gets extraction_failure. "
    "(2) The grader shows the judge only the first 300 characters of the answer. "
    "(3) correct: the answer gives the reference answer, or an answer listed as also accepted, and nothing in it "
    "contradicts the reference answer. incorrect: the answer gives an answer that is not the reference answer, or "
    "says something that contradicts it. not_attempted: the answer gives no answer, for example because it says it "
    "does not know, and it does not guess. Differences in capitalization, punctuation, accents or articles (a, an, "
    "the) do not matter. The answer does not need to repeat the question.")
LABELS = "correct, incorrect, not_attempted, extraction_failure"
HEADER = (
    "# ToyQA blinded review, batch {name}\n\n"
    "Each case starts with a line `=== CASE <id> ===`. It gives the requirement to judge, the question, the "
    "reference answer with any other accepted answers, the prompt the answering model saw between `<<<PROMPT BEGIN>>>` "
    "and `<<<PROMPT END>>>`, and the model's response between `<<<RESPONSE BEGIN>>>` and `<<<RESPONSE END>>>`. "
    "The markers stand on their own lines; everything between them, including leading and trailing whitespace and "
    "blank lines, is the exact text. The response is also in `audit/frozen/responses/<id>.txt`, and "
    "`python -B audit/frozen/show_case.py <id>` prints it exactly (add `--repr` to see escapes). "
    "Labels: {labels}, or ambiguous.\n\n")

SHOW_CASE = '''"""Print a frozen case's exact response.  Usage: python -B audit/frozen/show_case.py CASE_ID [--repr]"""
import pathlib
import sys

p = pathlib.Path(__file__).resolve().parent / "responses" / (sys.argv[1] + ".txt")
text = p.read_bytes().decode("utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(f"{len(text)} characters")
print("<<<RESPONSE BEGIN>>>")
print(repr(text) if "--repr" in sys.argv else text)
print("<<<RESPONSE END>>>")
'''


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    qs = questions()
    resp = {r["id"]: r for r in responses()}
    raw = {}
    for line in (CASE / "responses.jsonl").read_bytes().split(b"\n"):
        if line.strip():
            raw[json.loads(line.decode("utf-8"))["id"]] = sha(line)
    labels = {r["id"]: r for r in load_jsonl(AUDIT / "panel" / "labels.jsonl")}
    prompt_tpl = (CASE / "prompt_template.txt").read_text(encoding="utf-8")

    strata = {"disagree": [], "agree": []}
    for rid, row in labels.items():
        strata["disagree" if row["G"] != row["X"] else "agree"].append(rid)
    rnd = random.Random(SEED)
    drawn = {s: sorted(rnd.sample(sorted(ids), len(ids))) for s, ids in strata.items()}  # census

    case_of = {}
    for rid in labels:
        cid = "T" + sha(f"{SEED}:{rid}".encode())[:6]
        case_of[rid] = cid
    assert len(set(case_of.values())) == len(case_of)

    (FROZEN / "responses").mkdir(parents=True, exist_ok=True)
    cases, keys = [], []
    for s, ids in drawn.items():
        for rid in ids:
            r, row, cid = resp[rid], labels[rid], case_of[rid]
            cases.append({"case_id": cid, "stratum": s, "question_id": r["question_id"],
                          "response_sha256": raw[rid]})
            keys.append({"case_id": cid, "response_id": rid, "model": r["model"], "question_id": r["question_id"],
                         "finish_reason": r["finish_reason"], "stratum": s, "G": row["G"], "R": row["R"],
                         "X": row["X"], "X_full": row["X_full"]})
            (FROZEN / "responses" / f"{cid}.txt").write_bytes(r["response"].encode("utf-8"))
    cases.sort(key=lambda c: c["case_id"])
    keys.sort(key=lambda c: c["case_id"])

    def write_jsonl(name, rows):
        with open(FROZEN / name, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_jsonl("cases.jsonl", cases)
    write_jsonl("keys.jsonl", keys)

    def render(case):
        q = qs[case["question_id"]]
        ref = q["gold"] + (f" (also accepted: {', '.join(q['aliases'])})" if q["aliases"] else "")
        text = (FROZEN / "responses" / f"{case['case_id']}.txt").read_bytes().decode("utf-8")
        return (f"=== CASE {case['case_id']} ===\n"
                f"REQUIREMENT TO JUDGE: {CHECK_NAME}. {CHECK_TEXT}\n"
                f"QUESTION: {q['question']}\n"
                f"REFERENCE ANSWER: {ref}\n"
                f"PROMPT THE MODEL SAW:\n<<<PROMPT BEGIN>>>\n{prompt_tpl.replace('{question}', q['question'])}"
                f"<<<PROMPT END>>>\n"
                f"RESPONSE ({len(text)} characters; full file responses/{case['case_id']}.txt):\n"
                f"<<<RESPONSE BEGIN>>>\n{text}\n<<<RESPONSE END>>>\n\n")

    orders = {}
    for name, seed in (("A", SEED + 1), ("B", SEED + 2)):
        order = list(cases)
        random.Random(seed).shuffle(order)
        orders[name] = [c["case_id"] for c in order]
        with open(FROZEN / f"batch_{name}.md", "w", encoding="utf-8", newline="\n") as f:
            f.write(HEADER.format(name=name, labels=LABELS))
            for c in order:
                f.write(render(c))
    assert orders["A"] != orders["B"]

    ref_prompt = (W_SKILL := AUDIT.parent / "skill" / "references" / "reviewer-prompt.md").read_text(encoding="utf-8")
    block = ref_prompt.split("```text\n", 1)[1].split("\n```", 1)[0]
    block = (block.replace("<benchmark>", "ToyQA 1.0, a short-answer factual QA benchmark graded by an LLM judge")
             .replace("<helper command>", "python -B audit/frozen/show_case.py CASE_ID")
             .replace('ignore whether the content is correct, useful or well written unless the requirement is about '
                      'that.', 'ignore whether the content is correct, useful or well written unless the requirement '
                      'is about that. Judge against the reference answer as given. Do not use your own knowledge of '
                      'the facts. If the reference answer looks wrong, set verdict ambiguous and say why.')
             .replace('"verdict" ("pass", "fail" or "ambiguous"), "lean" ("pass" or "fail")',
                      '"verdict" ("correct", "incorrect", "not_attempted", "extraction_failure" or "ambiguous"), '
                      '"lean" ("correct", "incorrect", "not_attempted" or "extraction_failure")'))
    assert "Judge against the reference answer" in block and '"lean" ("correct"' in block, "prompt template changed"
    with open(FROZEN / "reviewer_prompt.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Reviewer prompt for this sample\n\nAdapted from `{W_SKILL.relative_to(AUDIT.parent).as_posix()}`. "
                "Reviewer A gets `<batch path>` = `audit/frozen/batch_A.md` and `<output path>` = "
                "`audit/frozen/reviews/review_A.jsonl`; reviewer B gets `batch_B.md` and `review_B.jsonl`.\n\n"
                "```text\n" + block + "\n```\n")
    (FROZEN / "show_case.py").write_text(SHOW_CASE, encoding="utf-8", newline="\n")

    files = sorted(p for p in FROZEN.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    with open(FROZEN / "SHA256SUMS", "w", encoding="utf-8", newline="\n") as f:
        for p in files:
            f.write(f"{sha(p.read_bytes())}  {p.relative_to(FROZEN).as_posix()}\n")
    print("strata (population = drawn):", {s: len(v) for s, v in drawn.items()})
    print("cases.jsonl sha256:", sha((FROZEN / "cases.jsonl").read_bytes()))
    print("keys.jsonl sha256:", sha((FROZEN / "keys.jsonl").read_bytes()))
    for name in ("batch_A.md", "batch_B.md", "reviewer_prompt.md", "show_case.py"):
        print(f"{name} sha256:", sha((FROZEN / name).read_bytes()))
    print("SHA256SUMS sha256:", sha((FROZEN / "SHA256SUMS").read_bytes()), f"({len(files)} files)")


if __name__ == "__main__":
    main()
