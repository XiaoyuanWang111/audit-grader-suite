"""Grade the hand-written fixtures with all three graders and classify each wrong verdict.

Writes the hand fixtures into audit/fixtures.jsonl (replacing earlier `source: hand`
lines, keeping lines from other sources) and audit/tests/known_failures.json.

A wrong verdict is a decision when some combination of non-proposed readings (up to
three of the decision entries that can affect the check, or all of them at once) makes
the replacement give the grader's verdict; the entries are named. Otherwise it is a
finding.
"""

import hashlib
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)

import harness as h  # noqa: E402
import contract_grader as cg  # noqa: E402
from fixtures_src import FIXTURES  # noqa: E402

FIX_PATH = os.path.join(AUDIT, "fixtures.jsonl")
KNOWN = os.path.join(AUDIT, "tests", "known_failures.json")


def fixture_id(f):
    payload = json.dumps([f["iid"], f["kw"], f["response"], f.get("prompt", ""), bool(f.get("raw")),
                          bool(f.get("reasoning_model"))], ensure_ascii=False, sort_keys=True)
    return f["iid"] + ":" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def replacement_verdict(f, readings=cg.PROPOSED):
    if f.get("raw"):
        out = h.contract_grade(f["response"], [f["iid"]], [f["kw"]], f.get("prompt", ""),
                               bool(f.get("reasoning_model")), readings)
        return out["results"][0]
    return h.contract_check(f["response"], f["iid"], f["kw"], f.get("prompt", ""), readings)


def readings_with(names):
    changes = {cg.DECISIONS[n][0]: cg.DECISIONS[n][1] for n in names}
    return cg.Readings(**changes)


def explaining_decisions(f, target, also=()):
    """Smallest set of decision entries whose other readings give `target`, or None.

    `also` holds more (fixture, verdict) pairs that the same readings must reproduce,
    such as the unedited base of a metamorphic case and the grader's verdict on it, so
    that a reading that flips the verdict for an unrelated reason does not count.
    """
    relevant = sorted(n for n, checks in cg.AFFECTS.items() if f["iid"] in checks)

    def ok(names):
        r = readings_with(names)
        return replacement_verdict(f, r) == target and all(replacement_verdict(g, r) == v for g, v in also)

    for k in (1, 2, 3):
        for combo in itertools.combinations(relevant, k):
            if ok(combo):
                return list(combo)
    if relevant and ok(relevant):
        return relevant
    return None


def main():
    records = []
    known = {"skyrl": [], "tc": []}
    problems = 0
    for f in FIXTURES:
        fid = fixture_id(f)
        label = f["label"] == "pass"
        rep = replacement_verdict(f)
        if rep != label:
            problems += 1
            print("REPLACEMENT DISAGREES WITH LABEL:", fid, repr(f["response"][:60]), "label", f["label"])
        flips = [n for n in sorted(cg.AFFECTS) if f["iid"] in cg.AFFECTS[n]
                 and replacement_verdict(f, readings_with([n])) != rep]
        sky = h.skyrl_grade(f["response"], [f["iid"]], [f["kw"]])
        sky_v = bool(sky["results"][0]) and not sky["infra_error"]
        tc = h.tc_gate(f["response"], [f["iid"]], [f["kw"]])
        tc_v = tc["results"][0]
        rec = {
            "id": fid,
            "source": f.get("source", "hand"),
            "instruction_id": f["iid"],
            "kwargs": f["kw"],
            "response": f["response"],
            "label": f["label"],
            "note": f.get("note", ""),
            "prompt": f.get("prompt", ""),
            "raw": bool(f.get("raw")),
            "reasoning_model": bool(f.get("reasoning_model")),
            "decisions_that_flip_label": flips,
            "skyrl": "pass" if sky_v else "fail",
            "skyrl_error": sky["errors"][0],
            "tc": None if tc_v is None else ("pass" if tc_v else "fail"),
            "replacement": "pass" if rep else "fail",
        }
        for grader, verdict in (("skyrl", sky_v), ("tc", tc_v)):
            if verdict is None or verdict == label:
                rec[grader + "_class"] = None if verdict is None else "correct"
                continue
            if grader == "skyrl" and sky["errors"][0]:
                rec[grader + "_class"] = "finding (exception)"
            else:
                why = explaining_decisions(f, verdict)
                rec[grader + "_class"] = "finding" if why is None else "decision: " + ", ".join(why)
            known[grader].append(fid)
        records.append(rec)

    others = []
    if os.path.exists(FIX_PATH):
        with open(FIX_PATH, encoding="utf-8") as fh:
            others = [json.loads(line) for line in fh if line.strip()]
        others = [o for o in others if o.get("source") not in ("hand", "fuzz")]
    with open(FIX_PATH, "w", encoding="utf-8", newline="\n") as fh:
        for rec in records + others:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    old = {}
    if os.path.exists(KNOWN):
        with open(KNOWN, encoding="utf-8") as fh:
            old = json.load(fh)
    for key in known:
        old[key] = sorted(set(known[key]))
    with open(KNOWN, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(old, fh, indent=1, sort_keys=True)

    n = len(records)
    print(f"hand fixtures: {n}; replacement/label disagreements: {problems}")
    for grader in ("skyrl", "tc"):
        wrong = [r for r in records if r[grader + "_class"] not in (None, "correct")]
        fnd = [r for r in wrong if r[grader + "_class"].startswith("finding")]
        print(f"{grader}: wrong {len(wrong)} (findings {len(fnd)}, decisions {len(wrong) - len(fnd)})")
        for r in wrong:
            print(f"   {r[grader + '_class'][:60]:60s} {r['id']} {r['response'][:50]!r} label={r['label']}")
    exc = [r for r in records if r["skyrl_error"]]
    print(f"skyrl checker exceptions: {len(exc)}")
    for r in exc:
        print(f"   {r['id']} {r['response'][:40]!r}: {r['skyrl_error'][:80]}")


if __name__ == "__main__":
    main()
