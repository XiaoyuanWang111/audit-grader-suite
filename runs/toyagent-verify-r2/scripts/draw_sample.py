"""Step 6.1-6.3: draw, freeze and render the blinded review sample (round 1). The reviews themselves are not run.

Population: the 36 stored trials, one verdict each (check `answer-file`). Strata: the stored verifier verdict and the
replacement's proposed verdict disagree, or agree. Both strata are small, so the sample is all of each (a census);
the seed fixes the case ids and each reviewer's order.

Writes under audit/frozen/round1/:
- cases.jsonl     the frozen case list (what reviewers see, no source model and no verdict); its sha256 goes in ISSUE.md
- keys.jsonl      per case: trial, configuration, stratum, stored/rerun verifier verdicts, replacement verdicts
- strata.json     population and sample size per stratum, and the seed
- batch_A.md, batch_B.md   the same cases in two seeded orders
- show_case.py    helper that prints a case's exact files
- reviewer_prompt_A.txt, reviewer_prompt_B.txt   skill/references/reviewer-prompt.md with the placeholders filled

Usage: python -I audit/scripts/draw_sample.py   (needs audit/results/panel.json)
"""

import hashlib
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grader_runner as GR  # noqa: E402

SEED = 20261107
OUT = GR.AUDIT / "frozen" / "round1"
CHECK_NAME = "answer-file"
CHECK_TEXT = (
    "A trial passes when /workspace/out/answer.txt holds the correct count: the number of requests in the three log "
    "files whose status code is 500 to 599. Whitespace around the content, including a final newline, is ignored. "
    "A trial whose /workspace/out/answer.txt is missing or empty fails. (ToyOps README, scoring rule 1)")
REFERENCE = "The correct count is 41."


def render_bytes(b):
    """Exact text with escapes for every character that is not printable ASCII (newline shown as \\n)."""
    out = []
    for ch in b.decode("utf-8", "surrogateescape"):
        if 0xDC80 <= ord(ch) <= 0xDCFF:  # a byte that is not part of valid UTF-8
            out.append(f"\\x{ord(ch) - 0xDC00:02x}")
        elif ch == "\\":
            out.append("\\\\")
        elif " " <= ch <= "~":
            out.append(ch)
        else:
            out.append(ch.encode("unicode_escape").decode("ascii"))
    return "".join(out)


def frozen_state(trial_id):
    ws = GR.CASE / "trials" / trial_id / "workspace"
    files = []
    if ws.exists():
        for p in sorted(ws.rglob("*")):
            if p.is_file():
                b = p.read_bytes()
                files.append({"path": "/workspace/" + p.relative_to(ws).as_posix(), "bytes": len(b), "hex": b.hex(),
                              "escaped": render_bytes(b)})
    return files


def case_block(case):
    lines = [f"### CASE {case['case_id']}", "", f"REQUIREMENT TO JUDGE ({case['check']}): {case['check_text']}", "",
             f"REFERENCE ANSWER: {case['reference']}", "", "PROMPT (the task text the agent saw):",
             "<<<BEGIN PROMPT>>>", case["prompt"].rstrip("\n"), "<<<END PROMPT>>>", "",
             "RESPONSE (every file under /workspace when the trial ended; the read-only logs and empty directories "
             "are not stored):", "<<<BEGIN RESPONSE>>>"]
    if not case["files"]:
        lines.append("(no files)")
    for f in case["files"]:
        lines += [f"<<<BEGIN FILE {f['path']} ({f['bytes']} bytes)>>>", f["escaped"], "<<<END FILE>>>"]
    lines += ["<<<END RESPONSE>>>", ""]
    return "\n".join(lines)


HEADER = (
    "# Blinded review batch {name}: ToyOps count-server-errors, round 1\n\n"
    "Each case starts with `### CASE <id>`. The requirement and the reference answer follow, then the prompt between "
    "`<<<BEGIN PROMPT>>>` and `<<<END PROMPT>>>`, then the response between `<<<BEGIN RESPONSE>>>` and "
    "`<<<END RESPONSE>>>`. The response is the agent's final sandbox: each stored file sits between "
    "`<<<BEGIN FILE <path> (<n> bytes)>>>` and `<<<END FILE>>>`, written as exact text in which every character that "
    "is not printable ASCII is escaped (a newline is `\\n`, a backslash is `\\\\`), so leading and trailing "
    "whitespace stays visible. `(no files)` means the sandbox held no file besides the logs. The helper named in "
    "your instructions prints any case's files byte for byte.\n\n")

HELPER = '''"""Print the exact frozen files of one review case: python -I show_case.py CASE_ID"""
import json, pathlib, sys
cases = {json.loads(l)["case_id"]: json.loads(l)
         for l in (pathlib.Path(__file__).resolve().parent / "cases.jsonl").read_text(encoding="utf-8").splitlines()}
case = cases[sys.argv[1]]
if not case["files"]:
    print("(no files under /workspace besides the read-only logs)")
for f in case["files"]:
    b = bytes.fromhex(f["hex"])
    print(f"{f['path']}: {len(b)} bytes")
    print(f"  bytes: {b!r}")
'''


def reviewer_prompt(name):
    ref = (GR.ROOT / "skill" / "references" / "reviewer-prompt.md").read_text(encoding="utf-8")
    text = ref.split("```text\n", 1)[1].split("```", 1)[0]
    text = text.replace("<benchmark>", "ToyOps count-server-errors (an agent task graded by a verifier script)")
    text = text.replace("<batch path>", f"audit/frozen/round1/batch_{name}.md")
    text = text.replace("<output path>", f"audit/frozen/round1/reviews_{name}.jsonl")
    text = text.replace("<helper command>", "python -I audit/frozen/round1/show_case.py CASE_ID")
    text = text.replace(
        "ignore whether the content is correct, useful or well written unless the requirement is about that.",
        "ignore whether the content is correct, useful or well written unless the requirement is about that. Judge "
        "against the reference answer as given. Do not use your own knowledge of the facts. If the reference answer "
        "looks wrong, set verdict ambiguous and say why. The RESPONSE is the agent's final sandbox, the files the "
        "verifier could read; the helper prints each of its files.")
    return text


def main():
    panel = json.loads((GR.AUDIT / "results" / "panel.json").read_text(encoding="utf-8"))
    prompt = (GR.CASE / "task" / "instruction.md").read_text(encoding="utf-8")
    trials = panel["trials"]
    strata = {"disagree": [t for t in trials if t["grader"] != t["replacement"]],
              "agree": [t for t in trials if t["grader"] == t["replacement"]]}
    rng = random.Random(SEED)
    sample = [t for name in ("disagree", "agree") for t in strata[name]]  # census of both strata
    ids = rng.sample(range(1, 1000), len(sample))
    cases, keys = [], []
    for t, n in zip(sample, ids):
        cid = f"R1-{n:03d}"
        stratum = "disagree" if t in strata["disagree"] else "agree"
        cases.append({"case_id": cid, "check": CHECK_NAME, "check_text": CHECK_TEXT, "reference": REFERENCE,
                      "prompt": prompt, "files": frozen_state(t["trial_id"])})
        keys.append({"case_id": cid, "trial_id": t["trial_id"], "config": t["config"], "stratum": stratum,
                     "stored_verifier_exit": t["stored_exit"], "stored_verifier_output": t["stored_output"],
                     "rerun_verifier_exit": t["rerun_exit"], "grader_verdict": t["grader"],
                     "replacement_proposed": t["replacement"], "replacement_by_reading": t["replacement_by_reading"]})
    cases.sort(key=lambda c: c["case_id"])
    keys.sort(key=lambda k: k["case_id"])
    OUT.mkdir(parents=True, exist_ok=True)

    def dump(name, rows):
        (OUT / name).write_text("".join(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n" for r in rows),
                                encoding="utf-8", newline="\n")

    dump("cases.jsonl", cases)
    dump("keys.jsonl", keys)
    (OUT / "strata.json").write_text(json.dumps({
        "seed": SEED, "population": len(trials),
        "strata": {k: {"population": len(v), "sampled": len(v)} for k, v in strata.items()},
        "held_out": "all 36 trials: the replacement was frozen before the panel and not changed after it"},
        indent=1) + "\n", encoding="utf-8", newline="\n")
    for name, seed in (("A", SEED + 1), ("B", SEED + 2)):
        order = list(cases)
        random.Random(seed).shuffle(order)
        (OUT / f"batch_{name}.md").write_text(HEADER.format(name=name) + "\n".join(case_block(c) for c in order),
                                              encoding="utf-8", newline="\n")
        (OUT / f"reviewer_prompt_{name}.txt").write_text(reviewer_prompt(name), encoding="utf-8", newline="\n")
    (OUT / "show_case.py").write_text(HELPER, encoding="utf-8", newline="\n")
    for p in sorted(OUT.iterdir()):
        print(hashlib.sha256(p.read_bytes()).hexdigest(), p.relative_to(GR.AUDIT).as_posix())


if __name__ == "__main__":
    main()
