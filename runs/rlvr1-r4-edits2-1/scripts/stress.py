"""Step 4 stress tests. Writes audit/results/stress_summary.json and prints tables.

(a) Content-free responses on all 11,817 rows: empty text, a lone period, repeated text, and a
    restatement of the instructions (the row's own prompt). Counts rows whose SkyRL reward is 1.0 and rows
    whose verifyit gate passes, and checker exceptions.
(b) Metamorphic edits: for every check, panel responses that all three graders pass are edited at the
    first and last word (bold, italics, HTML tag, typographic quotes, typographic apostrophe, punctuation
    after the word), or per line (numbered label, bullet, blank line between lines, trailing newline). An
    edit counts against a grader when the replacement's verdict stays pass and the grader's flips to fail.
(c) Fuzzing: random texts through every checker with each data row's kwargs; counts exceptions.
"""
import gzip
import json
import os
import random
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402
from analyze_panel import load_raw  # noqa: E402

RES = os.path.join(HERE, "..", "results")
rows = P.load_rows()


def content_free():
    out = {}
    variants = {
        "empty": lambda rec: "",
        "period": lambda rec: ".",
        "repeated": lambda rec: "ok " * 200,
        "restatement": lambda rec: rec["prompt"],
    }
    for name, make in variants.items():
        sk1 = gate1 = rp1 = 0
        sk_err = Counter()
        sk_pass_ids = Counter()
        gate_pass_ids = Counter()
        for rec in rows.values():
            text = make(rec)
            reward, sk, errs, _ = P.skyrl_grade(text, rec)
            for e in errs:
                if e:
                    sk_err[e.split(":")[0]] += 1
            if reward == 1.0 and not any(errs):
                sk1 += 1
            for iid, v in zip(rec["instruction_id_list"], sk):
                if v:
                    sk_pass_ids[iid] += 1
            gate, vi, verrs, _ = P.verifyit_gate(text, rec)
            gate1 += gate
            for iid, v in zip(rec["instruction_id_list"], vi):
                if v:
                    gate_pass_ids[iid] += 1
            rp1 += all(C.grade_text(text, rec["instruction_id_list"], rec["kwargs"]))
        out[name] = {"skyrl_reward1_rows": sk1, "gate_pass_rows": gate1, "replacement_pass_rows": rp1,
                     "skyrl_exceptions": dict(sk_err), "skyrl_passing_checks": dict(sk_pass_ids.most_common()),
                     "gate_passing_checks": dict(gate_pass_ids.most_common())}
        print(f"content-free {name}: SkyRL reward 1.0 on {sk1} rows, gate passes {gate1} rows, "
              f"replacement passes {rp1}; SkyRL exceptions {dict(sk_err)}")
        print("   SkyRL passing checks:", dict(sk_pass_ids.most_common(12)))
        print("   gate passing checks:", dict(gate_pass_ids.most_common(12)))
    return out


def _edit_word(text, which, fn):
    ms = C.word_matches(text, C.PROPOSED)
    if not ms:
        return None
    m = ms[0] if which == "first" else ms[-1]
    return text[: m.start()] + fn(m.group(0)) + text[m.end():]


WORD_EDITS = {
    "bold": lambda w: f"**{w}**",
    "italics": lambda w: f"*{w}*",
    "html": lambda w: f"<b>{w}</b>",
    "typographic_quotes": lambda w: f"“{w}”",
    "punct_after": lambda w: f"{w},",
}


def _apostrophe(text):
    i = text.find("'")
    return None if i < 0 else text[:i] + "’" + text[i + 1:]


LINE_EDITS = {
    "numbered": lambda t: "\n".join(f"{i + 1}. {ln}" if ln.strip() else ln for i, ln in enumerate(t.split("\n"))),
    "bullet": lambda t: "\n".join(f"- {ln}" if ln.strip() else ln for ln in t.split("\n")),
    "blank_line": lambda t: t.replace("\n", "\n\n"),
    "trailing_newline": lambda t: t + "\n",
    "typographic_apostrophe": _apostrophe,
}


def metamorphic(per_check=40, seed=0):
    raw = load_raw()
    with gzip.open(os.path.join(HERE, "..", "frozen", "panel_verdicts.jsonl.gz"), "rt", encoding="utf-8") as f:
        lines = [json.loads(x) for x in f]
    pools = defaultdict(list)
    for r in lines:
        if r["ext"]["repl_failure"]:
            continue
        for j, iid in enumerate(r["ids"]):
            if r["sk"][j] and r["rp"][j] and (r["vi"][j] in (True, None)):
                pools[iid].append((r["run"], r["uuid"], j))
    rng = random.Random(seed)
    flips = Counter()
    tried = Counter()
    examples = {}
    for iid, cands in sorted(pools.items()):
        rng.shuffle(cands)
        for run, uuid, j in cands[:per_check]:
            rec = rows[uuid]
            kw = rec["kwargs"][j] or {}
            text = P.final_answer_text(raw[(run, uuid)])
            edits = []
            for name, fn in WORD_EDITS.items():
                for which in ("first", "last"):
                    e = _edit_word(text, which, fn)
                    if e is not None:
                        edits.append((f"{name}@{which}", e))
            for name, fn in LINE_EDITS.items():
                e = fn(text)
                if e is not None and e != text:
                    edits.append((name, e))
            for name, e in edits:
                if not C.check(iid, kw, e):
                    continue  # the contract does not ignore this edit for this check
                tried[(iid, name)] += 1
                nv = P.nvidia_check(iid, kw, e)[0]
                vi = None if iid in P.SEMANTIC else P.verifyit_check(iid, kw, e)[0]
                if not nv:
                    flips[("nvidia", iid, name)] += 1
                    examples.setdefault(("nvidia", iid, name), (run, uuid, j))
                if vi is False:
                    flips[("verifyit", iid, name)] += 1
                    examples.setdefault(("verifyit", iid, name), (run, uuid, j))
    by_edit = defaultdict(Counter)
    for (g, iid, name), n in flips.items():
        by_edit[(g, name)][iid] += n
    print("\nMetamorphic flips (replacement still passes, grader flips to fail): grader, edit -> checks")
    for (g, name), c in sorted(by_edit.items()):
        tot = sum(c.values())
        print(f"{g:8s} {name:24s} {tot:4d}  " + ", ".join(f"{k.split(':')[1]}={v}" for k, v in c.most_common(8)))
    return {"flips": {f"{g}|{i}|{n}": v for (g, i, n), v in flips.items()},
            "tried": {f"{i}|{n}": v for (i, n), v in tried.items()},
            "examples": {f"{g}|{i}|{n}": ex for (g, i, n), ex in examples.items()}}


def fuzz(n_texts=300, seed=1):
    rng = random.Random(seed)
    alphabet = list("abcXYZ019 ,.!?-*_#[]<>\"'\n\t") + ["“", "”", "’", "。", "，",
                                                        "İ", "ß", "中", "д", "******", "***",
                                                        "P.S.", "SECTION 1", "<<", ">>", "```", "</think>", "<think>"]
    texts = ["", " ", "\n\n", "*", "-", "[]", "<<>>", "```", "İ"]
    for _ in range(n_texts):
        texts.append("".join(rng.choice(alphabet) for _ in range(rng.randint(1, 60))))
    by_id = {}
    for rec in rows.values():
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            by_id.setdefault(iid, []).append(kw)
    exc = Counter()
    exc_example = {}
    calls = 0
    for iid, kws in sorted(by_id.items()):
        for kw in kws[:5]:
            for t in texts:
                calls += 1
                ok, err = P.nvidia_check(iid, kw, t)
                if err:
                    k = ("nvidia", iid, err.split(":")[0])
                    exc[k] += 1
                    exc_example.setdefault(k, t)
                if iid not in P.SEMANTIC:
                    ok, err = P.verifyit_check(iid, kw, t)
                    if err:
                        k = ("verifyit", iid, err.split(":")[0])
                        exc[k] += 1
                        exc_example.setdefault(k, t)
                try:
                    C.check(iid, {k2: v for k2, v in (kw or {}).items() if v is not None}, t)
                except Exception as error:  # noqa: BLE001
                    k = ("replacement", iid, type(error).__name__)
                    exc[k] += 1
                    exc_example.setdefault(k, t)
    print(f"\nFuzz: {calls} (check, kwargs, text) cases per grader; exceptions:")
    for k, v in sorted(exc.items()):
        print(" ", k, v, "example:", repr(exc_example[k])[:60])
    return {"calls": calls, "exceptions": {"|".join(k): v for k, v in exc.items()},
            "examples": {"|".join(k): v for k, v in exc_example.items()}}


if __name__ == "__main__":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    out = {"content_free": content_free(), "metamorphic": metamorphic(), "fuzz": fuzz()}
    with open(os.path.join(RES, "stress_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
