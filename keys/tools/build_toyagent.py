"""Write cases/toyagent-verify: the sandbox logs, expected.json, and the stored trials. Private: part of the keys.

The verifier exit codes stored in each trial's result.json are filled in afterwards by check_toyagent.py --record,
which runs the case's own verify.sh on each trial snapshot.
"""

import gzip
import io
import json
import os
import random
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(HERE, "..", "..", "cases", "toyagent-verify"))
LOGS = os.path.join(CASE, "task", "environment", "logs")

PATHS = [
    "/",
    "/index.html",
    "/api/orders",
    "/api/orders/17",
    "/api/cart",
    "/login",
    "/static/app.js",
    "/static/style.css",
    "/img/logo.png",
    "/api/search?q=lamp",
    "/checkout",
    "/api/health",
]
OK_STATUS = [200, 200, 200, 200, 201, 204, 301, 304, 403, 404]
ERR_STATUS = [500, 502, 503, 504]


def line(rng, day, status, size=None, path=None, request=None):
    ip = f"10.0.{rng.randint(0, 9)}.{rng.randint(2, 250)}"
    hh, mm, ss = rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)
    method = "POST" if (path or "").startswith("/api/orders") and rng.random() < 0.5 else "GET"
    req = request or f"{method} {path or rng.choice(PATHS)} HTTP/1.1"
    if size is None:
        size = rng.choice([0, 13, 88, 342, 1460, 2326, 7020, 18432]) if status < 500 else rng.choice([0, 91, 167])
        if status in (204, 304):
            size = 0
    return f'{ip} - - [{day:02d}/Oct/2026:{hh:02d}:{mm:02d}:{ss:02d} +0000] "{req}" {status} {size}'


def make_file(rng, day, n_lines, n_err, special):
    """n_lines lines, n_err of them 5xx; special is a list of extra fixed lines inserted at random places."""
    rows = []
    for i in range(n_lines - len(special)):
        status = rng.choice(ERR_STATUS) if i < n_err else rng.choice(OK_STATUS)
        rows.append(line(rng, day, status))
    rows += special
    rng.shuffle(rows)
    return "\n".join(rows) + "\n"


def build_logs():
    rng = random.Random(7)
    if os.path.isdir(LOGS):
        shutil.rmtree(LOGS)
    os.makedirs(LOGS)
    # access.log: 20 server errors; two 2xx lines whose size field starts with 5 followed by two digits
    cur = make_file(rng, 6, 40, 20, [line(rng, 6, 200, 5120), line(rng, 6, 200, 512)])
    # access.log.1: 17 server errors, one of them on a request line with a raw space in the path
    prev = make_file(rng, 5, 40, 16, [line(rng, 5, 503, 167, request="GET /api/search?q=red shoes HTTP/1.1")])
    # access.log.2.gz: 4 server errors; two 2xx lines with sizes 5xx and 59000
    old = make_file(rng, 4, 30, 4, [line(rng, 4, 200, 580), line(rng, 4, 200, 59000)])
    with open(os.path.join(LOGS, "access.log"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cur)
    with open(os.path.join(LOGS, "access.log.1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(prev)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(old.encode("utf-8"))
    with open(os.path.join(LOGS, "access.log.2.gz"), "wb") as f:
        f.write(buf.getvalue())
    return cur, prev, old


def counts(cur, prev, old):
    def status_count(text):
        return sum(1 for l in text.splitlines() if 500 <= int(re.search(r'" (\d{3}) \S+$', l).group(1)) <= 599)

    def awk9(text):
        return sum(1 for l in text.splitlines() if len(l.split()) >= 9 and l.split()[8].startswith("5"))

    def naive(text):
        return sum(1 for l in text.splitlines() if re.search(r" 5[0-9][0-9]", l))

    return {
        "correct": status_count(cur) + status_count(prev) + status_count(old),
        "no_gz": status_count(cur) + status_count(prev),
        "awk_field9": awk9(cur) + awk9(prev) + awk9(old),
        "awk_field9_no_gz": awk9(cur) + awk9(prev),
        "naive_grep": naive(cur) + naive(prev) + naive(old),
        "naive_grep_no_gz": naive(cur) + naive(prev),
    }


CONFIGS = ["agentx+falcon-70b", "agentx+merlin-32b", "agentx+osprey-14b", "agentx+kestrel-8b"]

# trial id -> (config index, agent_status, agent_error, steps, {relative path: content})
SCRIPT = "zcat -f /workspace/logs/access.log* | awk '{print $9}' | grep -c '^5'\n"
TRIALS = {
    "t01": (0, "completed", None, 9, {"out/answer.txt": "41\n"}),
    "t02": (0, "completed", None, 7, {"out/answer.txt": "41\n"}),
    "t03": (0, "completed", None, 11, {"out/answer.txt": "41\n", "tmp/count.py": "import gzip, re\n"}),
    "t04": (0, "completed", None, 6, {"out/answer.txt": "41"}),
    "t05": (0, "timeout", "agent exceeded 600 s wall time", 40, {"out/answer.txt": "41\n"}),
    "t06": (0, "completed", None, 8, {"out/answer.txt": "41\n"}),
    "t07": (0, "completed", None, 5, {"out/answer.txt": "40\n", "out/count.sh": SCRIPT}),
    "t08": (0, "completed", None, 10, {"out/answer.txt": "41\n"}),
    "t09": (0, "completed", None, 9, {"out/answer.txt": "41 server errors\n"}),
    "t10": (1, "completed", None, 12, {"out/answer.txt": "41\n"}),
    "t11": (1, "completed", None, 6, {"out/answer.txt": "37\n"}),
    "t12": (1, "completed", None, 8, {"answer.txt": "41\n"}),
    "t13": (1, "completed", None, 14, {"out/answer.txt": "41\n"}),
    "t14": (1, "error", "context length exceeded", 23, {"tmp/notes.txt": "access.log: 20\naccess.log.1: 17\n"}),
    "t15": (1, "timeout", "agent exceeded 600 s wall time", 38, {"out/answer.txt": "41\n"}),
    "t16": (1, "completed", None, 9, {"out/answer.txt": "41\n"}),
    "t17": (1, "completed", None, 11, {"out/answer.txt": "Total 5xx: 41\n"}),
    "t18": (1, "completed", None, 7, {"out/answer.txt": "41\n"}),
    "t19": (2, "completed", None, 5, {"out/answer.txt": "37\n"}),
    "t20": (2, "completed", None, 13, {"out/answer.txt": "41\n"}),
    "t21": (2, "error", "tool call failed: shell exited with status 137", 4, {}),
    "t22": (2, "completed", None, 6, {"out/answer.txt": "37\n"}),
    "t23": (2, "completed", None, 7, {"answer.txt": "37\n"}),
    "t24": (2, "completed", None, 5, {"out/answer.txt": "45\n"}),
    "t25": (2, "completed", None, 15, {"out/answer.txt": "41\n"}),
    "t26": (2, "completed", None, 9, {"out/answer.txt": ""}),
    "t27": (2, "completed", None, 6, {"out/answer.txt": "40\n", "out/count.sh": SCRIPT}),
    "t28": (3, "completed", None, 4, {"out/answer.txt": "37\n"}),
    "t29": (3, "timeout", "agent exceeded 600 s wall time", 40, {"tmp/scratch.txt": "trying zcat\n"}),
    "t30": (3, "completed", None, 6, {"out/answer.txt": "36\n"}),
    "t31": (3, "completed", None, 5, {"out/answer.txt": "45\n"}),
    "t32": (3, "completed", None, 12, {"out/answer.txt": "41\n"}),
    "t33": (3, "completed", None, 3, {"out/answer.txt": "0\n"}),
    "t34": (3, "completed", None, 5, {"out/answer.txt": "37\n"}),
    "t35": (3, "completed", None, 9, {"answer.txt": "41\n"}),
    "t36": (3, "completed", None, 4, {"out/answer.txt": "37\n"}),
}


def build_trials():
    root = os.path.join(CASE, "trials")
    if os.path.isdir(root):
        shutil.rmtree(root)
    for tid, (ci, status, err, steps, files) in TRIALS.items():
        d = os.path.join(root, tid)
        os.makedirs(os.path.join(d, "workspace"))
        for rel, content in files.items():
            p = os.path.join(d, "workspace", *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
        result = {
            "trial_id": tid,
            "task": "count-server-errors",
            "config": CONFIGS[ci],
            "agent_status": status,
            "agent_error": err,
            "agent_steps": steps,
            "verifier_exit_code": None,
            "verifier_output": None,
        }
        with open(os.path.join(d, "result.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(result, indent=2) + "\n")


def main():
    cur, prev, old = build_logs()
    c = counts(cur, prev, old)
    print("counts:", c)
    tests = os.path.join(CASE, "task", "tests")
    os.makedirs(tests, exist_ok=True)
    with open(os.path.join(tests, "expected.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"server_error_count": c["correct"]}) + "\n")
    build_trials()
    print(f"wrote logs, expected.json and {len(TRIALS)} trials")


if __name__ == "__main__":
    main()
