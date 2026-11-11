"""Step 6.1 to 6.3: draw, freeze and render the blinded-review sample from the step 5 panel.

Usage: python -B audit/scripts/draw_sample.py [SEED]

Population: the 36 stored trial verdicts. Strata: whether the current grader (stored verifier_exit_code) and the
replacement (proposed readings) disagree. Both strata are small, so the sample takes every case (a census).
Writes to audit/frozen/keys/ (auditor only, never shown to reviewers):
    round1_case_list.json  case ids with stratum, seed and stratum sizes (its sha256 is the freeze record)
    round1_keys.json       case id -> trial, configuration, verdicts
and under audit/frozen/round1/ (the reviewers' material):
    cases.json             case id -> frozen graded state (files under /workspace); read by the helper
    batch_A.md, batch_B.md the two reviewers' batches, same cases in different orders
    logs_decompressed.txt  the three input logs as the agent saw them, decompressed, for checking the reference
    show_case.py           helper that prints a case's exact files
    reviewer_prompt_A.txt, reviewer_prompt_B.txt   skill/references/reviewer-prompt.md filled in
"""

import gzip
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

import harness  # noqa: E402

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261111
OUT = os.path.join(harness.AUDIT, "frozen", "round1")
PANEL = os.path.join(harness.AUDIT, "panel", "panel_verdicts.json")
TRIALS = os.path.join(harness.CASE, "trials")

REQUIREMENT = (
    "The agent must count the requests in the three access logs (access.log, access.log.1 and the gzip-compressed "
    "access.log.2.gz) whose HTTP status code is 500 to 599, where the status code is the field right after the "
    "quoted request, and write the count as a decimal integer to /workspace/out/answer.txt. Scoring rule: the "
    "trial passes when /workspace/out/answer.txt holds the correct count. Whitespace around the content, "
    "including a final newline, is ignored. A trial whose /workspace/out/answer.txt is missing or empty fails. "
    "Reference answer (the count stored by the task): 41."
)

INSTRUCTION_FILE = os.path.join(harness.CASE, "task", "instruction.md")


def snapshot(trial):
    files = {}
    ws = os.path.join(TRIALS, trial, "workspace")
    if os.path.isdir(ws):
        for root, dirs, names in os.walk(ws):
            dirs.sort()
            for n in sorted(names):
                p = os.path.join(root, n)
                rel = "/workspace/" + os.path.relpath(p, ws).replace(os.sep, "/")
                with open(p, "rb") as f:
                    files[rel] = f.read()
    return files


def render_state(files):
    if not files:
        return ["(No files under /workspace at the end of the trial, apart from the read-only /workspace/logs.)"]
    lines = []
    for path, data in files.items():
        lines.append(f"File {path}: {len(data)} bytes; exact bytes as a Python literal: {data!r}")
        lines.append(f"<<<BEGIN FILE {path}>>>")
        lines.append(data.decode("utf-8", "replace") + "<<<END FILE>>>")
    return lines


def main():
    with open(PANEL, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    rng = random.Random(SEED)
    ids = rng.sample(range(0x1000, 0x10000), len(rows))
    cases, keys = {}, {}
    strata = {"disagree": [], "agree": []}
    for row, num in zip(rows, ids):
        cid = f"C{num:04X}"
        cur = "pass" if row["stored_exit"] == 0 else "fail"
        rep = "pass" if row["replacement_exit"] == 0 else "fail"
        stratum = "disagree" if cur != rep else "agree"
        strata[stratum].append(cid)
        files = snapshot(row["trial"])
        cases[cid] = {path: data.decode("latin-1") for path, data in files.items()}
        keys[cid] = {"trial": row["trial"], "config": row["config"], "agent_status": row["agent_status"],
                     "stratum": stratum, "current": cur, "replacement": rep,
                     "flips": {d: ("pass" if c == 0 else "fail") for d, c in row["flip_exit"].items()}}
    # Census: every case of both strata. Batch order: seeded shuffle for A, a second shuffle for B.
    order_a = sorted(cases)
    rng.shuffle(order_a)
    order_b = list(order_a)
    while order_b == order_a or order_b == order_a[::-1]:
        rng.shuffle(order_b)
    case_list = {"seed": SEED, "population": {k: len(v) for k, v in strata.items()},
                 "sample": {k: len(v) for k, v in strata.items()},
                 "cases": [{"case_id": c, "stratum": keys[c]["stratum"]} for c in sorted(cases)]}
    os.makedirs(OUT, exist_ok=True)

    def dump(name, obj):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, sort_keys=True)
            f.write("\n")

    keys_dir = os.path.join(harness.AUDIT, "frozen", "keys")
    os.makedirs(keys_dir, exist_ok=True)
    for name, obj in (("round1_case_list.json", case_list), ("round1_keys.json", keys)):
        with open(os.path.join(keys_dir, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, sort_keys=True)
            f.write("\n")
    dump("cases.json", {"encoding": "file bytes as latin-1 code points", "cases": cases})

    with open(INSTRUCTION_FILE, encoding="utf-8") as f:
        instruction = f.read().strip()
    for label, order in (("A", order_a), ("B", order_b)):
        out = [
            f"# Review batch {label}: ToyOps count-server-errors, {len(order)} cases",
            "",
            "Each case starts with a line `=== CASE <id> ===` and ends with `=== END CASE <id> ===`. It gives the "
            "requirement to judge, the task prompt the agent saw, and the RESPONSE: every file the agent left under "
            "/workspace when the trial ended (the read-only input logs are not repeated). Each file is shown twice: "
            "once as a Python bytes literal, which makes every invisible character visible, and once as text "
            "between `<<<BEGIN FILE path>>>` and `<<<END FILE>>>`, which sit directly against the first and last "
            "byte so that leading and trailing whitespace stays visible. A file that is not listed did not exist. "
            "The input logs, decompressed, are in logs_decompressed.txt next to this file.",
            "",
        ]
        for cid in order:
            out += [f"=== CASE {cid} ===", "REQUIREMENT TO JUDGE: " + REQUIREMENT, "",
                    "PROMPT (the agent's task text):", "<<<BEGIN PROMPT>>>", instruction, "<<<END PROMPT>>>", "",
                    "RESPONSE (final files under /workspace):"]
            out += render_state({p: d.encode("latin-1") for p, d in cases[cid].items()})
            out += [f"=== END CASE {cid} ===", ""]
        with open(os.path.join(OUT, f"batch_{label}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out))

    with open(os.path.join(OUT, "logs_decompressed.txt"), "w", encoding="utf-8", newline="\n") as f:
        for name in ("access.log", "access.log.1", "access.log.2.gz"):
            p = os.path.join(harness.LOGS, name)
            opener = gzip.open if name.endswith(".gz") else open
            with opener(p, "rb") as g:
                text = g.read().decode("utf-8")
            f.write(f"##### /workspace/logs/{name}" + (" (shown decompressed)" if name.endswith(".gz") else "")
                    + "\n" + text)

    with open(os.path.join(harness.ROOT, "skill", "references", "reviewer-prompt.md"), encoding="utf-8") as f:
        template = f.read().split("```text\n", 1)[1].split("\n```", 1)[0]
    reference_rule = (" Judge against the reference answer as given. Do not use your own knowledge of the facts. "
                      "If the reference answer looks wrong, set verdict ambiguous and say why.")
    for label in ("A", "B"):
        text = template.replace("<benchmark>", "ToyOps count-server-errors")
        text = text.replace("<batch path>", f"audit/frozen/round1/batch_{label}.md")
        text = text.replace("<output path>", f"audit/frozen/round1/reviews_{label}.jsonl")
        text = text.replace("<helper command>", "python -I audit/frozen/round1/show_case.py <case_id>")
        text = text.replace("unless the requirement is about that.",
                            "unless the requirement is about that." + reference_rule)
        text = text.replace("read only your batch file, the helper above, and the full-response files your batch "
                            "names.", "read only your batch file, the helper above, and the full-response files "
                            "your batch names (here: logs_decompressed.txt).")
        with open(os.path.join(OUT, f"reviewer_prompt_{label}.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    print(json.dumps(case_list["population"]), "cases:", len(cases))


if __name__ == "__main__":
    main()
