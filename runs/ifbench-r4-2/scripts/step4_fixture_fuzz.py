"""Mutation fuzz seeded with the fixture responses (structured inputs such as
CSV, MCQ blocks and templates that random text rarely reaches).
Writes audit/out/step4_fixture_fuzz.tsv."""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit" / "tests"))
sys.path.insert(0, str(W / "audit" / "replacement"))
import harness as H  # noqa: E402
import ifbench_fixed as RF  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402
from step4_stress import mutate  # noqa: E402

rng = random.Random(10062)
PER = 50
exc = defaultdict(Counter)
examples = {}
calls = 0
for f in FIXTURES:
    for _ in range(PER):
        resp = mutate(rng, f["response"])
        calls += 1
        for impl in ("grader", "reference", "replacement"):
            if impl == "replacement":
                try:
                    RF.check(f["check"], f["kwargs"], resp, opts=RF.PROPOSED)
                    err = None
                except Exception as e:  # noqa: BLE001
                    err = f"{type(e).__name__}: {e}"
            else:
                v = H.check_one(f["check"], f["kwargs"], resp, which=impl)
                err = v[4:] if isinstance(v, str) else None
            if err:
                key = (f["check"], err.split(":")[0])
                exc[impl][key] += 1
                examples.setdefault((impl, key), (f["id"], resp, err))
TAB, NL = chr(9), chr(10)
with open(W / "audit" / "out" / "step4_fixture_fuzz.tsv", "w", newline=NL, encoding="utf-8") as fh:
    fh.write(TAB.join(["impl", "check", "error", "count", "seed_fixture", "example_response_json", "error_text"]) + NL)
    for impl, cnt in exc.items():
        for (chk, et), n in cnt.most_common():
            fid, resp, err = examples[(impl, (chk, et))]
            fh.write(TAB.join([impl, chk, et, str(n), fid, json.dumps(resp, ensure_ascii=False), err[:120]]) + NL)
print(f"fixture-seeded mutation fuzz: {calls} responses (seed 10062, {PER} per fixture)")
for impl in ("grader", "reference", "replacement"):
    cnt = exc.get(impl, Counter())
    print(f"{impl:12s} exceptions={sum(cnt.values())} " + "; ".join(f"{a}:{b}={n}" for (a, b), n in cnt.most_common()))
