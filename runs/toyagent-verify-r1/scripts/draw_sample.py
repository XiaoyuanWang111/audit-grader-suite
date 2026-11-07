"""Step 6.1-6.3: draw, freeze and render the blinded-review sample (round 1).

Population: the 36 stored trial verdicts, in two strata by whether the stored
verdict (verify.sh) and the replacement (proposed readings) disagree. Round 1
takes every trial of both strata (a census; 36 cases), plus calibration
fixtures with unambiguous labels and decision fixtures, which stay out of the
error rate. Opaque case ids and the two reviewers' orders come from SEED.

Writes into audit/frozen/round1/:
  cases.json        the case list (case id, source, stratum); its sha256 is the freeze
  key.json          per case: source trial, source model, grader verdicts (never shown to reviewers)
and the reviewer packet into audit/frozen/round1/packet/:
  responses.json    per case: the frozen graded state (every stored file under /workspace)
  batch_A.md, batch_B.md   rendered cases, two orders
  show_case.py      helper that prints a case's exact files
  reviewer_prompt_A.md, reviewer_prompt_B.md

    python -I audit/scripts/draw_sample.py audit/panel/panel_results.json
"""

import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(AUDIT, "tests"), os.path.join(AUDIT, "replacement")]

import common  # noqa: E402
import fixtures  # noqa: E402

SEED = 20261107
OUT = os.path.join(AUDIT, "frozen", "round1")

CALIBRATION = ["empty-workspace", "wrong-path-root-41", "answer-is-directory", "spaces-around",
               "decimal-point", "info-sep-1c-after", "text-prefix", "tab-crlf"]
DECISION = ["leading-zero", "plus-sign", "nbsp-after", "utf8-bom"]

REQUIREMENT_NAME = "answer"
REQUIREMENT_TEXT = (
    "The trial passes when /workspace/out/answer.txt holds the correct count: the number of requests in the "
    "three log files whose status code is 500 to 599. Whitespace around the content, including a final "
    "newline, is ignored. A trial whose /workspace/out/answer.txt is missing or empty fails. "
    "(ToyOps README, scoring rule 1.)")
REFERENCE_ANSWER = "41"


def stored_files(tid):
    ws = os.path.join(common.TRIALS_DIR, tid, "workspace")
    files = {}
    for root, _d, names in os.walk(ws):
        for name in names:
            p = os.path.join(root, name)
            with open(p, "rb") as f:
                files[os.path.relpath(p, ws).replace(os.sep, "/")] = f.read()
    return files


def render_file(rel, data):
    if data is None:
        return [f"FILE /workspace/{rel}: a directory (no content)"]
    lines = [f"FILE /workspace/{rel}: {len(data)} bytes"]
    if len(data) > 400:
        lines.append("(longer than 400 bytes: print it with the helper)")
        return lines
    lines.append(f"BYTES (Python repr): {data!r}")
    # The end marker follows the last byte directly, so a final newline puts it on its own line.
    lines.append("<<<BEGIN FILE>>>\n" + data.decode("utf-8", "backslashreplace") + "<<<END FILE>>>")
    return lines


def render_case(cid, files, prompt):
    out = [f"## CASE {cid}", "", f"REQUIREMENT TO JUDGE ({REQUIREMENT_NAME}): {REQUIREMENT_TEXT}", "",
           "PROMPT (the task text the agent saw):", "<<<BEGIN PROMPT>>>\n" + prompt + "<<<END PROMPT>>>", "",
           f"REFERENCE ANSWER (the correct count): {REFERENCE_ANSWER}", "",
           "RESPONSE: the final sandbox, every file under /workspace except the read-only /workspace/logs "
           f"({len(files)} file(s); empty directories are not stored):", ""]
    if not files:
        out.append("(no files)")
    for rel in sorted(files):
        out += render_file(rel, files[rel])
        out.append("")
    out.append(f"END OF CASE {cid}")
    out.append("")
    return out


def main(argv):
    common.require_pins("before draw")
    with open(argv[0], encoding="utf-8") as f:
        panel = json.load(f)
    rng = random.Random(SEED)
    trials = panel["trials"]
    strata = {"disagree": [t for t in trials if t["grader"] != t["replacement"]],
              "agree": [t for t in trials if t["grader"] == t["replacement"]]}
    population = {k: len(v) for k, v in strata.items()}
    picked = []
    for name, ts in strata.items():
        for t in ts:  # census of both strata
            picked.append(("trial", t["trial_id"], name))
    fx_by_name = {fx["name"]: fx for fx in fixtures.VERIFIER_FIXTURES}
    for name in CALIBRATION:
        picked.append(("fixture", fx_by_name[name]["id"], "calibration"))
    for name in DECISION:
        picked.append(("fixture", fx_by_name[name]["id"], "decision"))
    ids = rng.sample(range(1000, 10000), len(picked))
    order = list(range(len(picked)))
    rng.shuffle(order)
    cases = []
    for k in order:
        src, ref, stratum = picked[k]
        cases.append({"case_id": f"C{ids[k]}", "source": src, "ref": ref, "stratum": stratum})
    responses, key = {}, {}
    tmap = {t["trial_id"]: t for t in trials}
    for c in cases:
        if c["source"] == "trial":
            files = stored_files(c["ref"])
            t = tmap[c["ref"]]
            key[c["case_id"]] = {"trial_id": c["ref"], "source_model": t["config"], "agent_status": t["agent_status"],
                                 "grader_verdict": t["grader"], "stored_exit": t["stored_exit"],
                                 "replacement_verdict": t["replacement"], "stratum": c["stratum"]}
        else:
            fx = next(f for f in fixtures.VERIFIER_FIXTURES if f["id"] == c["ref"])
            files = fx["files"]
            key[c["case_id"]] = {"fixture_id": fx["id"], "fixture_name": fx["name"], "label": fx["label"],
                                 "decision": fx["decision"]["entries"] if fx["decision"] else None,
                                 "stratum": c["stratum"]}
        responses[c["case_id"]] = {rel: (None if b is None else b.hex()) for rel, b in files.items()}
    packet = os.path.join(OUT, "packet")
    os.makedirs(packet, exist_ok=True)
    with open(os.path.join(common.CASE, "task", "instruction.md"), encoding="utf-8", newline="") as f:
        prompt = f.read()

    def dump(name, obj):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, sort_keys=False)
            f.write("\n")

    dump("cases.json", {"round": 1, "seed": SEED, "population": population,
                        "sampled": {k: sum(1 for c in cases if c["stratum"] == k) for k in
                                    ("disagree", "agree", "calibration", "decision")},
                        "cases": cases})
    dump("key.json", key)
    with open(os.path.join(packet, "responses.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(responses, f, indent=1)
        f.write("\n")
    order_b = list(cases)
    random.Random(SEED + 1).shuffle(order_b)
    for label, seq in (("A", cases), ("B", order_b)):
        lines = [f"# Review batch {label}: ToyOps count-server-errors, round 1", "",
                 "Each case starts with a line `## CASE <id>` and ends with `END OF CASE <id>`. A case gives the "
                 "requirement to judge, the reference answer, and the response: every file the trial left under "
                 "/workspace. Each file's bytes are shown as a Python bytes repr and again between the lines "
                 "<<<BEGIN FILE>>> and <<<END FILE>>>, so leading and trailing whitespace and control characters "
                 "are visible; the text between the markers is exact except that bytes that are not UTF-8 are "
                 "shown as \\x escapes. A directory has no content. The helper prints any case's files exactly.",
                 "", f"Cases in this batch: {len(seq)}.", ""]
        for c in seq:
            files = {rel: (None if h is None else bytes.fromhex(h)) for rel, h in responses[c["case_id"]].items()}
            lines += render_case(c["case_id"], files, prompt)
        with open(os.path.join(packet, f"batch_{label}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
        with open(os.path.join(common.ROOT, "skill", "references", "reviewer-prompt.md"), encoding="utf-8") as f:
            ref = f.read()
        body = ref.split("```text\n", 1)[1].split("```", 1)[0]
        body = (body.replace("<benchmark>", "ToyOps count-server-errors (an agent task graded by a verifier script)")
                    .replace("<batch path>", f"audit/frozen/round1/packet/batch_{label}.md")
                    .replace("<output path>", f"audit/frozen/round1/reviews/reviewer_{label}.jsonl")
                    .replace("<helper command>", "python -I audit/frozen/round1/packet/show_case.py CASE_ID"))
        added = ("unless the requirement is about that. Judge against the reference answer as given. Do not use "
                 "your own knowledge of the facts. If the reference answer looks wrong, set verdict ambiguous and "
                 "say why. The RESPONSE is the final state the agent left in its sandbox, every file under "
                 "/workspace; judge the requirement on that state.")
        assert body.count("unless the requirement is about that.") == 1
        body = body.replace("unless the requirement is about that.", added)
        with open(os.path.join(packet, f"reviewer_prompt_{label}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    helper = '''"""Print a case's exact response files: python -I show_case.py CASE_ID"""
import json, os, sys
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.json"), encoding="utf-8"))
files = d[sys.argv[1]]
if not files:
    print("(no files under /workspace)")
for rel in sorted(files):
    if files[rel] is None:
        print(f"/workspace/{rel}: directory")
        continue
    b = bytes.fromhex(files[rel])
    print(f"/workspace/{rel}: {len(b)} bytes")
    print("  hex:  " + b.hex(" "))
    print("  repr: " + repr(b))
'''
    with open(os.path.join(packet, "show_case.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(helper)
    common.require_pins("after draw")
    h = hashlib.sha256(open(os.path.join(OUT, "cases.json"), "rb").read()).hexdigest()
    print("population", population, "cases", len(cases), "cases.json sha256", h)


if __name__ == "__main__":
    main(sys.argv[1:])
