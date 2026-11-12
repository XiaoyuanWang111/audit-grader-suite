"""Step 4: fuzzing (exceptions per grader and check) and content-free responses on every data row.

Writes audit/out/fuzz.json, audit/out/content_free.json and audit/fixtures_generated_fuzz_cf.jsonl.
"""
import collections
import json
import random
import sys
import time

sys.path.insert(0, "<W>/audit")
import harness as h  # noqa: E402

W = "<W>"
A = f"{W}/audit"
SEED = 20261112

ALPHABET = (
    list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") * 3
    + list(" " * 20 + "\n" * 6 + "\t")
    + list(".,!?;:'\"-*_#`~>[](){}<>|/\\@&%$+=")
    + list("。，！？、“”‘’…—–·")
    + list("中文日本語한국어привет") + ["\u0301", "\u200b", "\U0001F600", "İ", "ß", "ǅ"]
)
TOKENS = ["***", "******", "* * *", "<<", ">>", "P.S.", "P.P.S", "SECTION 1", "Section 2", "\n\n", "</think>",
          "<think>", "```json\n", "\n```", "My answer is yes.", "Any other questions?", "- ", "* ", "1. "]


def rand_text(rng):
    n = rng.choice([0, 1, 2, 3, 5, 8, 13, 21, 40, 80, 120])
    out = []
    for _ in range(n):
        out.append(rng.choice(TOKENS) if rng.random() < 0.08 else rng.choice(ALPHABET))
    return "".join(out)


def data_rows():
    rows = []
    for line in open(f"{W}/case/data/rlvr1_instruction_following.jsonl", encoding="utf-8"):
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        rows.append((rec, row["prompt"][0]["content"]))
    return rows


def fuzz(rows, n_texts=1500):
    kwargs_by_id = collections.defaultdict(list)
    for rec, _ in rows:
        for i, k in zip(rec["instruction_id_list"], rec["kwargs"]):
            if len(kwargs_by_id[i]) < 2 and k not in kwargs_by_id[i]:
                kwargs_by_id[i].append(k)
    rng = random.Random(SEED)
    texts = [rand_text(rng) for _ in range(n_texts)] + ["", " ", "\n", "\n\n", "*", "-", "."]
    exc = collections.Counter()
    smallest = {}
    disagree = collections.Counter()
    total = collections.Counter()
    for t in texts:
        for iid, kws in kwargs_by_id.items():
            for kw in kws:
                total[iid] += 1
                random.seed(SEED)
                nv, nv_err = h.nv_check(iid, kw, t)
                vg, vg_err = h.vg_check(iid, kw, t)
                try:
                    r = h.R.check(iid, kw, t)
                    r_err = None
                except Exception as error:  # noqa: BLE001
                    r, r_err = None, f"{type(error).__name__}: {error}"
                for g, err in (("NV", nv_err), ("VG", vg_err), ("R", r_err)):
                    if err:
                        key = (g, iid, err.split(":")[0])
                        exc[key] += 1
                        if key not in smallest or len(t) < len(smallest[key]["response"]):
                            smallest[key] = {"response": t, "kwargs": kw, "error": err[:200]}
                if r is not None:
                    if not nv_err and bool(nv) != r:
                        disagree[("NV", iid)] += 1
                    if vg is not None and not vg_err and bool(vg) != r:
                        disagree[("VG", iid)] += 1
    # VS on a subsample (subprocess-free path; it is slower)
    vs_exc = collections.Counter()
    vs_small = {}
    for t in texts[:300]:
        for iid, kws in kwargs_by_id.items():
            kw = kws[0]
            random.seed(SEED)
            v, err = h.vs_check(iid, kw, t)
            if err:
                key = ("VS", iid, err.split(":")[0] + ":" + err.split("'error_type': ")[-1][:40])
                vs_exc[key] += 1
                if key not in vs_small or len(t) < len(vs_small[key]["response"]):
                    vs_small[key] = {"response": t, "kwargs": kw, "error": err[:300]}
    return {
        "n_texts": len(texts),
        "checks_per_text": sum(len(v) for v in kwargs_by_id.values()),
        "exceptions": {"|".join(k): v for k, v in sorted(exc.items())},
        "smallest": {"|".join(k): v for k, v in smallest.items()},
        "vs_texts": 300,
        "vs_exceptions": {"|".join(k): v for k, v in sorted(vs_exc.items())},
        "vs_smallest": {"|".join(k): v for k, v in vs_small.items()},
        "disagree_with_R": {"|".join(k): v for k, v in sorted(disagree.items())},
        "total_per_check": dict(total),
    }


def content_free(rows):
    responses = {
        "empty": lambda p: "",
        "whitespace": lambda p: " \n\t ",
        "repeated_word": lambda p: ("the " * 200).strip(),
        "repeated_sentence": lambda p: ("Hello world. " * 30).strip(),
        "restate_prompt": lambda p: p,
    }
    out = {}
    for name, make in responses.items():
        per_check = collections.defaultdict(lambda: collections.Counter())
        row_reward = collections.Counter()
        for rec, prompt in rows:
            raw = make(prompt)
            random.seed(SEED)
            nv = h.nv_row(raw, rec)
            vg = h.vg_row(raw, rec)
            r = h.r_row(raw, rec, False)
            row_reward["NV_reward1"] += nv["reward"] == 1.0
            row_reward["NV_infra"] += nv["outcome"] == "infra_error"
            row_reward["VG_gate_pass"] += vg["gate_pass"]
            row_reward["R_reward1"] += r["reward"] == 1.0
            row_reward["rows"] += 1
            for j, iid in enumerate(rec["instruction_id_list"]):
                c = per_check[iid]
                c["n"] += 1
                c["NV"] += bool(nv["results"][j]) and not nv["errors"][j]
                c["NV_err"] += bool(nv["errors"][j])
                if vg["results"][j] is not None:
                    c["VG_n"] += 1
                    c["VG"] += bool(vg["results"][j])
                c["R"] += bool(r["results"][j])
        out[name] = {"rows": dict(row_reward), "per_check": {k: dict(v) for k, v in sorted(per_check.items())}}
        print(name, dict(row_reward), flush=True)
    return out


def main():
    rows = data_rows()
    t0 = time.time()
    cf = content_free(rows)
    json.dump(cf, open(f"{A}/out/content_free.json", "w", encoding="utf-8"), indent=1)
    print("content-free done", round(time.time() - t0), flush=True)
    fz = fuzz(rows)
    json.dump(fz, open(f"{A}/out/fuzz.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("fuzz done", round(time.time() - t0), flush=True)
    gen = []
    for key, v in list(fz["smallest"].items()) + list(fz["vs_smallest"].items()):
        g, iid = key.split("|")[0], key.split("|")[1]
        label = "pass" if h.R.check(iid, v["kwargs"], v["response"]) else "fail"
        gen.append({"source": f"fuzz exception {key}", "grader": g, "instruction_id": iid, "kwargs": v["kwargs"],
                    "response": v["response"], "label": label})
    with open(f"{A}/fixtures_generated_fuzz.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in gen:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
