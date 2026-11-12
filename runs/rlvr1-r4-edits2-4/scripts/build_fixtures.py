"""Build audit/fixtures.jsonl and audit/tests/expected_wrong.json from the step 3-4 results.

fixtures.jsonl: one line per labeled response (hand, metamorphic, content-free, fuzz), with the
required fields instruction_id, kwargs, response, label, plus id, source, thinking, label_source.
expected_wrong.json: fixture id -> {grader: reference} for every verdict that differs from the
label today (the tests mark these xfail(strict=True)), and {"skyrl_error": ref} for exceptions.
"""
import json
import sys
from pathlib import Path

A = Path("<W>/audit")
sys.path.insert(0, str(A / "lib"))

from contract_grader import DEFAULT_READINGS  # noqa: E402
from findings import check_candidates, fixture_ref, forbidden_ref, metamorphic_ref  # noqa: E402
from verdicts import fixture_id, replacement_with, verdicts  # noqa: E402

lines, wrong = {}, {}


def add(iid, kwargs, response, label, source, label_source, thinking=False, note="", refs=None, v=None):
    fid = fixture_id(iid, kwargs, response, thinking)
    if fid in lines:
        return
    v = v or verdicts(iid, kwargs, response, thinking)
    lines[fid] = {"id": fid, "instruction_id": iid, "kwargs": kwargs, "response": response, "label": label,
                  "source": source, "label_source": label_source, "thinking": thinking, "note": note}
    for g in ("skyrl", "gate", "replacement"):
        if v[g] is not None and v[g] != label:
            if g == "replacement":
                ref = (refs or {}).get(g) or "replacement limitation (unattributed)"
            else:
                ref = ((refs or {}).get(g) or decision_ref(iid, kwargs, response, thinking, v[g])
                       or "|".join(check_candidates(iid, g)) or f"unattributed:{g}")
            wrong.setdefault(fid, {})[g] = ref
    if v["skyrl_error"]:
        wrong.setdefault(fid, {})["skyrl_error"] = "G2"


def decision_ref(iid, kwargs, response, thinking, grader_verdict):
    if not response.strip() and grader_verdict == "pass":
        return "D-empty-response"
    hits = [e for e, r in DEFAULT_READINGS.items()
            if replacement_with(iid, kwargs, response, {e: "B" if r == "A" else "A"}, thinking) == grader_verdict]
    return "+".join(hits) if hits else None


# hand-written
for rec in json.loads((A / "work" / "fixture_verdicts.json").read_text(encoding="utf-8")):
    refs = {}
    for g in ("skyrl", "gate"):
        if rec[g] is not None and rec[g] != rec["label"]:
            named = [e for e in DEFAULT_READINGS if e in rec["note"]]
            alt_ok = [e for e in named if rec["replacement_alt"].get(e) == rec[g]]
            refs[g] = "+".join(alt_ok) if alt_ok else fixture_ref(rec["instruction_id"], g, rec["note"])
    add(rec["instruction_id"], rec["kwargs"], rec["response"], rec["label"], "hand", "contract",
        rec["thinking"], rec["note"], refs, v=rec)

# metamorphic
for rec in json.loads((A / "work" / "metamorphic_results.json").read_text(encoding="utf-8")):
    iid, kw = rec["instruction_id"], rec["kwargs"]
    add(iid, kw, rec["base"], "pass", "metamorphic-base", "contract",
        refs={g: metamorphic_ref(iid, g, "base") for g in ("skyrl", "gate")}, v=rec["base_verdicts"])
    for e in rec["edits"]:
        refs = {g: metamorphic_ref(iid, g, e["edit"]) for g in ("skyrl", "gate", "replacement")}
        add(iid, kw, e["response"], "pass", f"metamorphic:{e['edit']}", "contract", refs=refs, v=e["verdicts"])
    f = rec["forbidden"]
    refs = {g: forbidden_ref(iid, g) for g in ("skyrl", "gate", "replacement")}
    add(iid, kw, f["response"], "fail", "metamorphic:forbidden", "contract", refs=refs, v=f["verdicts"])

# content-free (one example row per check and kind where a grader passed)
cf = json.loads((A / "work" / "content_free.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(A / "lib"))
import harness  # noqa: E402

rows = harness.load_rows()
# Content-free lines whose replacement label is wrong: hand label, reason, refs per grader.
LABEL_OVERRIDES = {
    ("repeated", "change_case:english_lowercase"): (
        "pass", "lowercase English words; langdetect calls the text Afrikaans",
        {"skyrl": "F47", "replacement": "replacement limitation: langdetect"}),
}
makers = {"empty": lambda rec: "", "repeated": lambda rec: " ".join(["answer"] * 60), "restatement": lambda rec: rec["prompt"]}
for kind, per in cf["examples"].items():
    for iid, ex in per.items():
        response = makers[kind](rows[ex["uuid"]])
        v = verdicts(iid, ex["kwargs"], response)
        override = LABEL_OVERRIDES.get((kind, iid))
        if override:
            add(iid, ex["kwargs"], response, override[0], f"content-free:{kind}", "hand", note=ex["uuid"] + "; " + override[1],
                refs=override[2], v=v)
            continue
        add(iid, ex["kwargs"], response, v["replacement"], f"content-free:{kind}", "replacement", note=ex["uuid"], v=v)

# fuzz minimal reproducers
fz = json.loads((A / "work" / "fuzz.json").read_text(encoding="utf-8"))
for iid, res in fz.items():
    for key, m in res["minimal"].items():
        v = verdicts(iid, m["kwargs"] or {}, m["response"])
        add(iid, m["kwargs"] or {}, m["response"], v["replacement"], f"fuzz:{key}", "replacement", v=v)

with open(A / "fixtures.jsonl", "w", encoding="utf-8", newline="\n") as f:
    for rec in lines.values():
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
(A / "tests" / "expected_wrong.json").write_text(json.dumps(wrong, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
by_source = {}
for rec in lines.values():
    key = rec["source"].split(":")[0]
    by_source[key] = by_source.get(key, 0) + 1
print("fixtures", len(lines), by_source, "with a wrong verdict", len(wrong))
unattr = [(k, g, r) for k, d in wrong.items() for g, r in d.items() if r is None or str(r).startswith("unattributed")]
print("unattributed", len(unattr))
for u in unattr[:80]:
    print("  ", u, lines[u[0]]["source"], repr(lines[u[0]]["response"][:60]))
