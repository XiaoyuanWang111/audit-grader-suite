"""Print every fixture's verdict from each grader and flag where `wrong` differs from the run."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402


def verdicts(fx):
    out = {}
    out["nvidia"] = P.nvidia_check(fx["check"], fx["kwargs"], fx["response"])[0]
    if "verifyit" not in fx["na"]:
        out["verifyit"] = P.verifyit_check(fx["check"], fx["kwargs"], fx["response"])[0]
    out["replacement"] = C.check(fx["check"], fx["kwargs"], fx["response"])
    return out


bad = 0
for fx in FIXTURES:
    v = verdicts(fx)
    actual_wrong = {g for g, ok in v.items() if ok != fx["label"]}
    flag = "" if actual_wrong == fx["wrong"] else f"   <-- predicted wrong={sorted(fx['wrong'])}"
    if flag:
        bad += 1
    if flag or "-v" in sys.argv:
        print(f"{fx['id']} label={fx['label']} {fx['kind']} {fx['ref']} verdicts={v} wrong={sorted(actual_wrong)}{flag}")
print(f"{len(FIXTURES)} fixtures, {bad} with a different wrong-set than predicted")
