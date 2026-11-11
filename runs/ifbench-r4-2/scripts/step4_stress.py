"""Step 4 stress tests: content-free responses, fuzzing, metamorphic edits.

Writes audit/out/step4_content_free.tsv, audit/out/step4_fuzz.tsv,
audit/out/step4_metamorphic.tsv and prints summaries.
"""
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit" / "replacement"))
import harness as H  # noqa: E402
import ifbench_fixed as RF  # noqa: E402

ROWS = H.load_rows()
OUT = W / "audit" / "out"


def verdicts(row, resp):
    g, ge = H.grade_row(row, resp, "grader", "strict")
    gl, gle = H.grade_row(row, resp, "grader", "loose")
    r, re_ = H.grade_row(row, resp, "reference", "strict")
    try:
        x = RF.grade_row(row, resp, RF.PROPOSED)
        xe = None
    except Exception as e:  # noqa: BLE001
        x, xe = None, f"{type(e).__name__}: {e}"
    return (g, ge), (gl, gle), (r, re_), (x, xe)


# ------------------------------------------------------------ content-free
INSTR_SENT = re.compile(r"[^.?!]*$")


def content_free_variants(row):
    p = row["prompt"]
    return {
        "empty": "",
        "space": " ",
        "repeat_word": " ".join(["the"] * 60),
        "repeat_sentence": " ".join(["This is a sentence."] * 20),
        "restate_prompt": p,
        "single_char": "a",
    }


def run_content_free():
    passes = defaultdict(Counter)  # (variant, impl) -> Counter(iid)
    totals = Counter()
    for row in ROWS:
        for name, resp in content_free_variants(row).items():
            (g, _), (gl, _), (r, _), (x, _) = verdicts(row, resp)
            for i, iid in enumerate(row["instruction_id_list"]):
                totals[(name, iid)] += 1
                for impl, v in (("grader", g), ("grader_loose", gl), ("reference", r), ("replacement", x)):
                    if v and v[i]:
                        passes[(name, impl)][iid] += 1
    with open(OUT / "step4_content_free.tsv", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("variant\timpl\tiid\tpassed\tinstances\n")
        for (name, impl), cnt in sorted(passes.items()):
            for iid, n in sorted(cnt.items()):
                fh.write(f"{name}\t{impl}\t{iid}\t{n}\t{totals[(name, iid)]}\n")
    print("== content-free: checks passed (instances passed / instances)")
    for name in ["empty", "space", "single_char", "repeat_word", "repeat_sentence", "restate_prompt"]:
        for impl in ("grader", "grader_loose", "reference", "replacement"):
            cnt = passes.get((name, impl), Counter())
            print(f"{name:16s} {impl:13s} {sum(cnt.values()):4d} instances, {len(cnt):2d} checks: "
                  + ", ".join(f"{k}({v})" for k, v in sorted(cnt.items())))


# ------------------------------------------------------------ fuzz
ALPH = list("abcdeABCDE xyz") + list("0123456789") + list(".,;:!?'\"()[]{}*-_#/\\|<>@&%$~`^=+") + \
    ["\n", "\t", "  ", "—", "’", "“", "”", " ", "\U0001F600", "日本", "?!", "...",
     "<i>", "</i>", "<em>", "</em>", "* ", "- ", "\n* ", "\n  - ", "Question 1: ", "A) ", "My Answer:", "\"\"",
     "\t\t", ",,", "Zimbabwe\n", "́", "﻿", "\r\n"]


def rand_text(rng):
    n = rng.randint(0, 80)
    return "".join(rng.choice(ALPH) for _ in range(n))


def run_fuzz(per_row=40, seed=10060):
    rng = random.Random(seed)
    exc = defaultdict(Counter)  # impl -> Counter(iid or msg)
    examples = {}
    calls = 0
    for row in ROWS:
        for _ in range(per_row):
            resp = rand_text(rng)
            calls += 1
            (g, ge), (gl, gle), (r, re_), (x, xe) = verdicts(row, resp)
            for impl, err in (("grader", ge), ("grader_loose", gle), ("reference", re_), ("replacement", xe)):
                if err:
                    key = (",".join(row["instruction_id_list"]), err.split(":")[0])
                    exc[impl][key] += 1
                    examples.setdefault((impl, key), (row["key"], resp, err))
    with open(OUT / "step4_fuzz.tsv", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("impl\tiids\terror\tcount\texample_key\texample_response_json\texample_error\n")
        for impl, cnt in exc.items():
            for (iids, et), n in cnt.most_common():
                k, resp, err = examples[(impl, (iids, et))]
                fh.write(f"{impl}\t{iids}\t{et}\t{n}\t{k}\t{json.dumps(resp, ensure_ascii=False)}\t{err[:120]}\n")
    print(f"== fuzz: {calls} responses (seed {seed}, {per_row} per row)")
    for impl in ("grader", "grader_loose", "reference", "replacement"):
        cnt = exc.get(impl, Counter())
        print(f"{impl:13s} exceptions={sum(cnt.values())} " + "; ".join(f"{a}:{b}={n}" for (a, b), n in cnt.most_common()))


# ------------------------------------------------------------ metamorphic
def load_greedy():
    out = []
    for folder in sorted((W / "case" / "panel").iterdir()):
        if not folder.is_dir():
            continue
        f = folder / "greedy.jsonl"
        for line in open(f, encoding="utf-8"):
            rec = json.loads(line)
            out.append((folder.name, rec))
    return out


IGNORED = {
    "curly_apostrophe": lambda s: re.sub(r"(?<=[A-Za-z])'(?=[A-Za-z])", "’", s),
    "double_space": lambda s: re.sub(r"(?<=\S) (?=\S)", "  ", s),
    "trailing_newline": lambda s: s + "\n",
}
# checks whose contract the edit does change (excluded from the invariance count)
EXEMPT = {
    "double_space": {"format:no_whitespace", "format:line_indent", "repeat:repeat_simple", "ratio:sentence_words",
                     "custom:csv_quotes", "custom:csv_city", "custom:csv_special_character",
                     "format:output_template", "format:options", "custom:character_reverse",
                     "custom:reverse_newline", "custom:european_capitals_sort"},
    "trailing_newline": set(),
    "curly_apostrophe": {"count:punctuation"},
}


def run_metamorphic():
    data = load_greedy()
    rows = {r["key"]: r for r in ROWS}
    flips = defaultdict(Counter)
    totals = Counter()
    examples = {}
    for tname, fn in IGNORED.items():
        for folder, rec in data:
            row = rows[str(rec["key"])]
            resp = rec["response"]
            new = fn(resp)
            if new == resp:
                continue
            for impl in ("grader", "replacement"):
                if impl == "grader":
                    a, _ = H.grade_row(row, resp, "grader", "strict")
                    b, _ = H.grade_row(row, new, "grader", "strict")
                else:
                    a = RF.grade_row(row, resp, RF.PROPOSED)
                    b = RF.grade_row(row, new, RF.PROPOSED)
                if a is None or b is None:
                    continue
                for i, iid in enumerate(row["instruction_id_list"]):
                    if iid in EXEMPT[tname]:
                        continue
                    if impl == "grader":
                        totals[(tname, iid)] += 1
                    if a[i] != b[i]:
                        flips[(tname, impl)][iid] += 1
                        examples.setdefault((tname, impl, iid), (folder, rec["key"]))
    with open(OUT / "step4_metamorphic.tsv", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("edit\timpl\tiid\tflips\tinstances_changed\texample_folder\texample_key\n")
        for (tname, impl), cnt in sorted(flips.items()):
            for iid, n in cnt.most_common():
                f, k = examples[(tname, impl, iid)]
                fh.write(f"{tname}\t{impl}\t{iid}\t{n}\t{totals[(tname, iid)]}\t{f}\t{k}\n")
    print("== metamorphic (greedy runs, edits the contract ignores): verdict flips")
    for tname in IGNORED:
        for impl in ("grader", "replacement"):
            cnt = flips.get((tname, impl), Counter())
            print(f"{tname:16s} {impl:12s} flips={sum(cnt.values())} " + ", ".join(f"{k}({v})" for k, v in cnt.most_common()))


def mutate(rng, s):
    ops = rng.randint(1, 3)
    for _ in range(ops):
        k = rng.random()
        pos = rng.randint(0, len(s)) if s else 0
        if k < 0.4:
            s = s[:pos] + rng.choice(ALPH) + s[pos:]
        elif k < 0.7 and s:
            end = min(len(s), pos + rng.randint(1, 20))
            s = s[:pos] + s[end:]
        else:
            lines = s.split(chr(10))
            i = rng.randrange(len(lines))
            lines.insert(i, lines[i])
            s = chr(10).join(lines)
    return s


def run_mutation_fuzz(seed=10061, per=3):
    rng = random.Random(seed)
    rows = {r["key"]: r for r in ROWS}
    exc = defaultdict(Counter)
    examples = {}
    calls = 0
    for folder, rec in load_greedy():
        row = rows[str(rec["key"])]
        for _ in range(per):
            resp = mutate(rng, rec["response"] or "")
            calls += 1
            (g, ge), (gl, gle), (r, re_), (x, xe) = verdicts(row, resp)
            for impl, err in (("grader", ge), ("grader_loose", gle), ("reference", re_), ("replacement", xe)):
                if err:
                    key = (",".join(row["instruction_id_list"]), err.split(":")[0])
                    exc[impl][key] += 1
                    examples.setdefault((impl, key), (folder, row["key"], resp, err))
    TAB, NL = chr(9), chr(10)
    with open(OUT / "step4_mutation_fuzz.tsv", "w", newline=NL, encoding="utf-8") as fh:
        fh.write(TAB.join(["impl", "iids", "error", "count", "example_folder", "example_key",
                           "example_response_json", "example_error"]) + NL)
        for impl, cnt in exc.items():
            for (iids, et), n in cnt.most_common():
                f, k, resp, err = examples[(impl, (iids, et))]
                fh.write(TAB.join([impl, iids, et, str(n), f, str(k), json.dumps(resp, ensure_ascii=False),
                                   err[:120]]) + NL)
    print(f"== mutation fuzz: {calls} mutated greedy responses (seed {seed})")
    for impl in ("grader", "grader_loose", "reference", "replacement"):
        cnt = exc.get(impl, Counter())
        print(f"{impl:13s} exceptions={sum(cnt.values())} " + "; ".join(f"{a}:{b}={n}" for (a, b), n in cnt.most_common()))


if __name__ == "__main__":
    which = sys.argv[1:] or ["content_free", "fuzz", "metamorphic", "mutation"]
    if "content_free" in which:
        run_content_free()
    if "fuzz" in which:
        run_fuzz()
    if "metamorphic" in which:
        run_metamorphic()
    if "mutation" in which:
        run_mutation_fuzz()
