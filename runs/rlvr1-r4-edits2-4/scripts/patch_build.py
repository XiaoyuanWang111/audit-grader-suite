from pathlib import Path
p = Path("<W>/audit/scripts/build_fixtures.py")
s = p.read_text(encoding="utf-8")
reps = [
 ('from findings import fixture_ref, forbidden_ref, metamorphic_ref  # noqa: E402',
  'from findings import check_candidates, fixture_ref, forbidden_ref, metamorphic_ref  # noqa: E402'),
 ('''            ref = (refs or {}).get(g) or decision_ref(iid, kwargs, response, thinking, v[g]) or f"unattributed:{g}"''',
  '''            ref = ((refs or {}).get(g) or decision_ref(iid, kwargs, response, thinking, v[g])
                   or "|".join(check_candidates(iid, g)) or f"unattributed:{g}")'''),
 ('''    add(iid, kw, rec["base"], "pass", "metamorphic-base", "contract", v=rec["base_verdicts"])''',
  '''    add(iid, kw, rec["base"], "pass", "metamorphic-base", "contract",
        refs={g: metamorphic_ref(iid, g, "base") for g in ("skyrl", "gate")}, v=rec["base_verdicts"])'''),
 ('''        v = verdicts(iid, ex["kwargs"], response)
        add(iid, ex["kwargs"], response, v["replacement"], f"content-free:{kind}", "replacement", note=ex["uuid"], v=v)''',
  '''        v = verdicts(iid, ex["kwargs"], response)
        override = LABEL_OVERRIDES.get((kind, iid))
        if override:
            add(iid, ex["kwargs"], response, override[0], f"content-free:{kind}", "hand", note=ex["uuid"] + "; " + override[1],
                refs=override[2], v=v)
            continue
        add(iid, ex["kwargs"], response, v["replacement"], f"content-free:{kind}", "replacement", note=ex["uuid"], v=v)'''),
 ('''makers = {''',
  '''# Content-free lines whose replacement label is wrong: hand label, reason, refs per grader.
LABEL_OVERRIDES = {
    ("repeated", "change_case:english_lowercase"): (
        "pass", "lowercase English words; langdetect calls the text Afrikaans",
        {"skyrl": "F47", "replacement": "replacement limitation: langdetect"}),
}
makers = {'''),
]
for a, b in reps:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
