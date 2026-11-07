"""Private checks for cases/toyagent-verify. Part of the keys; never give this to an auditor.

    python check_toyagent.py --record   runs task/tests/verify.sh on every trial snapshot and stores the exit code
                                        and output in the trial's result.json (as the harness did)
    python check_toyagent.py            checks everything and prints the tables used in the key

Oracle: the TASK.md scoring rule with one switch per planted defect and one per reading of the ambiguity.
  A1  a missing answer file ends the verifier with exit status 0
  A2  when out/answer.txt is missing, the verifier grades /workspace/answer.txt instead
  A3  score_trials.py counts a trial whose verifier did not run (exit code null) as passed
  reading "strict": the answer file must hold only the integer; "lenient": a file that states the count in words
  around the number passes (operationalized for the key as: its last run of digits is the count)
"""

import sys as _sys

_sys.dont_write_bytecode = True
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(HERE, "..", "..", "cases", "toyagent-verify"))
TESTS = os.path.join(CASE, "task", "tests")
TRIALS = os.path.join(CASE, "trials")
PY = sys.executable
BASH = shutil.which("bash")
ALL_ON = {"A1": True, "A2": True, "A3": True}
ALL_OFF = {"A1": False, "A2": False, "A3": False}
with open(os.path.join(TESTS, "expected.json"), encoding="utf-8") as _expected:
    EXPECTED = json.load(_expected)["server_error_count"]


def run_verifier(workspace):
    env = dict(
        os.environ,
        WORKSPACE=workspace.replace("\\", "/"),
        TESTS_DIR=TESTS.replace("\\", "/"),
        PYTHON=PY.replace("\\", "/"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    p = subprocess.run(
        [BASH, os.path.join(TESTS, "verify.sh").replace("\\", "/")], env=env, capture_output=True, text=True
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def o_exit(workspace, sw, reading="strict"):
    """Oracle verifier exit status (0 pass, 1 fail)."""
    answer = os.path.join(workspace, "out", "answer.txt")
    if not os.path.isfile(answer) and sw["A2"] and os.path.isfile(os.path.join(workspace, "answer.txt")):
        answer = os.path.join(workspace, "answer.txt")
    if not os.path.isfile(answer):
        return 0 if sw["A1"] else 1
    text = read(answer).strip()
    if reading == "strict":
        return 0 if re.fullmatch(r"[0-9]+", text) and int(text) == EXPECTED else 1
    runs = re.findall(r"[0-9]+", text)
    return 0 if runs and int(runs[-1]) == EXPECTED else 1


def o_reward(exit_code, sw):
    if exit_code is None:
        return 1.0 if sw["A3"] else 0.0
    return 1.0 if exit_code == 0 else 0.0


def load_trials():
    out = []
    for tid in sorted(os.listdir(TRIALS)):
        with open(os.path.join(TRIALS, tid, "result.json"), encoding="utf-8") as f:
            out.append((tid, json.load(f)))
    return out


def record():
    for tid, result in load_trials():
        code, output = run_verifier(os.path.join(TRIALS, tid, "workspace"))
        result["verifier_exit_code"] = code
        result["verifier_output"] = output
        with open(os.path.join(TRIALS, tid, "result.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(result, indent=2) + "\n")
        print(tid, code, output)


def score_table(results, sw):
    by = {}
    for r in results:
        by.setdefault(r["config"], []).append(o_reward(r["verifier_exit_code"], sw))
    return {c: (len(v), int(sum(v)), round(100.0 * sum(v) / len(v), 1)) for c, v in sorted(by.items())}


def run_score(trials_dir):
    p = subprocess.run([PY, "-B", os.path.join(CASE, "score_trials.py"), trials_dir], capture_output=True, text=True)
    table = {}
    for line in p.stdout.splitlines()[1:]:
        c, n, k, s = line.split()
        table[c] = (int(n), int(k), float(s))
    return table, p.stdout


def main():
    if "--record" in sys.argv:
        record()
        return 0
    print("bash:", BASH)
    ok = True
    trials = load_trials()
    results = [r for _, r in trials]

    # 1. the recorded exit codes are what verify.sh gives on each snapshot, and what the oracle (all on) gives
    for tid, r in trials:
        ws = os.path.join(TRIALS, tid, "workspace")
        code, _ = run_verifier(ws)
        if code != r["verifier_exit_code"] or code != o_exit(ws, ALL_ON):
            ok = False
            print("MISMATCH", tid, code, r["verifier_exit_code"], o_exit(ws, ALL_ON))
    g_table, g_out = run_score(TRIALS)
    if g_table != score_table(results, ALL_ON):
        ok = False
        print("MISMATCH score table", g_table, score_table(results, ALL_ON))
    print("panel equality checks:", "OK" if ok else "FAILED")
    print(g_out)

    # 2. contract verdicts
    rows = []
    for tid, r in trials:
        ws = os.path.join(TRIALS, tid, "workspace")
        files = sorted(
            os.path.relpath(os.path.join(dp, f), ws).replace("\\", "/") for dp, _, fs in os.walk(ws) for f in fs
        )
        rows.append(
            {
                "id": tid,
                "config": r["config"],
                "agent": r["agent_status"],
                "files": files,
                "grader": r["verifier_exit_code"],
                "strict": o_exit(ws, ALL_OFF, "strict"),
                "lenient": o_exit(ws, ALL_OFF, "lenient"),
                "answer": (
                    read(os.path.join(ws, "out", "answer.txt"))
                    if os.path.isfile(os.path.join(ws, "out", "answer.txt"))
                    else None
                ),
            }
        )
    for row in rows:
        print(
            f"  {row['id']} {row['config']:<20} agent={row['agent']:<9} files={row['files']} "
            f"answer={row['answer']!r} verifier_exit={row['grader']} "
            f"contract_strict={row['strict']} lenient={row['lenient']}"
        )
    n = len(rows)
    gp = sum(r["grader"] == 0 for r in rows)
    cs = sum(r["strict"] == 0 for r in rows)
    cl = sum(r["lenient"] == 0 for r in rows)
    print(
        f"\npasses: verifier {gp}/{n} ({100.0 * gp / n:.1f}%), contract strict {cs}/{n} ({100.0 * cs / n:.1f}%), "
        f"contract lenient {cl}/{n} ({100.0 * cl / n:.1f}%)"
    )

    def table(key):
        by = {}
        for r in rows:
            by.setdefault(r["config"], []).append(r[key] == 0)
        return {c: f"{sum(v)}/{len(v)} = {100.0 * sum(v) / len(v):.1f}" for c, v in sorted(by.items())}

    print("per config: verifier", table("grader"))
    print("            contract strict", table("strict"))
    print("            contract lenient", table("lenient"))
    print("\nper-defect verdict changes (verifier vs verifier with only that defect removed):")
    for d in ["A1", "A2"]:
        ch = [
            tid
            for tid, r in trials
            if o_exit(os.path.join(TRIALS, tid, "workspace"), ALL_ON)
            != o_exit(os.path.join(TRIALS, tid, "workspace"), dict(ALL_ON, **{d: False}))
        ]
        print(f"  {d}: {len(ch)}/{n} {ch}")
    print(
        f"  A3: trials with a null exit code in the panel: {[t for t, r in trials if r['verifier_exit_code'] is None]}"
    )
    print(
        f"  D-extra-text: verdicts that depend on the reading: {[r['id'] for r in rows if r['strict'] != r['lenient']]}"
    )
    print(
        "  trap (agent error or timeout, contract pass): "
        f"{[r['id'] for r in rows if r['agent'] != 'completed' and r['strict'] == 0]}"
    )
    print(
        "  agent error or timeout, no answer file: "
        f"{[r['id'] for r in rows if r['agent'] != 'completed' and r['answer'] is None]}"
    )
    print(f"  empty answer file: {[r['id'] for r in rows if r['answer'] == '']}")

    # 3. counterexamples
    print("\ncounterexamples:")
    cases = {
        "CE-A1 empty sandbox": {},
        "CE-A1 only scratch files": {"tmp/notes.txt": "20 + 17\n"},
        "CE-A2 legacy path": {"answer.txt": f"{EXPECTED}\n"},
        "CE-A2 both paths": {"answer.txt": f"{EXPECTED}\n", "out/answer.txt": "37\n"},
        "CE-D words around": {"out/answer.txt": f"{EXPECTED} requests\n"},
        "CE-T correct": {"out/answer.txt": f"{EXPECTED}\n"},
        "near: empty file": {"out/answer.txt": ""},
        "near: no newline": {"out/answer.txt": f"{EXPECTED}"},
        "near: CRLF": {"out/answer.txt": f"{EXPECTED}\r\n"},
        "near: leading zero": {"out/answer.txt": f"0{EXPECTED}\n"},
        "near: plus sign": {"out/answer.txt": f"+{EXPECTED}\n"},
        "near: two lines": {"out/answer.txt": f"{EXPECTED}\n{EXPECTED}\n"},
        "near: answer is a directory": {"out/answer.txt/x": "41\n"},
    }
    for name, files in cases.items():
        with tempfile.TemporaryDirectory() as td:
            for rel, content in files.items():
                p = os.path.join(td, *rel.split("/"))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(content)
            code, out = run_verifier(td)
            o = o_exit(td, ALL_ON)
            if code != o:
                ok = False
                print("  MISMATCH", name, code, o)
            print(
                f"  {name:<28} verify.sh exit={code} ({out!r}) contract strict={o_exit(td, ALL_OFF)} "
                f"lenient={o_exit(td, ALL_OFF, 'lenient')}"
            )
    with tempfile.TemporaryDirectory() as td:
        for tid, code in [("x1", 0), ("x2", 1), ("x3", None), ("x4", 2)]:
            os.makedirs(os.path.join(td, tid))
            with open(os.path.join(td, tid, "result.json"), "w", encoding="utf-8") as f:
                json.dump({"trial_id": tid, "config": "ce", "verifier_exit_code": code}, f)
        t, out = run_score(td)
        print(
            f"  CE-A3 exit codes 0, 1, null, 2 -> score_trials.py {t['ce']}; contract "
            f"{sum(o_reward(c, ALL_OFF) for c in (0, 1, None, 2))} of 4 pass"
        )
        if t["ce"][1] != 2:
            ok = False

    # 4. fuzz the verifier
    rng = random.Random(20261106)
    contents = [
        f"{EXPECTED}",
        f"{EXPECTED}\n",
        f" {EXPECTED} \n",
        "37\n",
        "",
        "\n",
        f"{EXPECTED}.0\n",
        f"{EXPECTED} requests\n",
        f"answer: {EXPECTED}",
        "4 1\n",
        f"{EXPECTED}\n\n",
        f"\t{EXPECTED}\t",
        "٤١\n",
        "0x29\n",
        f"{EXPECTED}\x00",
        "-41\n",
    ]
    bad = 0
    count = 0
    for _ in range(120):
        files = {}
        if rng.random() < 0.8:
            files["out/answer.txt"] = rng.choice(contents)
        if rng.random() < 0.3:
            files["answer.txt"] = rng.choice(contents)
        if rng.random() < 0.2:
            files["tmp/x.txt"] = "scratch\n"
        with tempfile.TemporaryDirectory() as td:
            for rel, content in files.items():
                p = os.path.join(td, *rel.split("/"))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(content)
            code, _ = run_verifier(td)
            count += 1
            if code != o_exit(td, ALL_ON):
                bad += 1
                print("  FUZZ MISMATCH", files, code, o_exit(td, ALL_ON))
    print(f"\nfuzz {count}: verify.sh/oracle mismatches {bad}")
    if bad:
        ok = False
    print("\nALL CHECKS", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
