from pathlib import Path
p = Path("<W>/audit/scripts/build_fixtures.py")
s = p.read_text(encoding="utf-8")
reps = [
 ('''            ref = ((refs or {}).get(g) or decision_ref(iid, kwargs, response, thinking, v[g])
                   or "|".join(check_candidates(iid, g)) or f"unattributed:{g}")''',
  '''            if g == "replacement":
                ref = (refs or {}).get(g) or "replacement limitation (unattributed)"
            else:
                ref = ((refs or {}).get(g) or decision_ref(iid, kwargs, response, thinking, v[g])
                       or "|".join(check_candidates(iid, g)) or f"unattributed:{g}")'''),
 ('''        refs = {g: metamorphic_ref(iid, g, e["edit"]) for g in ("skyrl", "gate")}''',
  '''        refs = {g: metamorphic_ref(iid, g, e["edit"]) for g in ("skyrl", "gate", "replacement")}'''),
 ('''    refs = {g: forbidden_ref(iid, g) for g in ("skyrl", "gate")}''',
  '''    refs = {g: forbidden_ref(iid, g) for g in ("skyrl", "gate", "replacement")}'''),
]
for a, b in reps:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
