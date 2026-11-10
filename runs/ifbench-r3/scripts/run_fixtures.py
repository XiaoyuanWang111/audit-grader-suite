"""Print every fixture's label and the grader, reference verdicts (strict); flag mismatches with their recorded status."""
import sys
sys.path.insert(0, "audit/tests"); sys.path.insert(0, "audit/lib")
import ifb
ifb.verify_pins()
from fixtures_data import FIXTURES
bad = 0
for f in FIXTURES:
    g, ge = ifb.verdict("grader", f.check, f.kwargs, f.prompt, f.response)
    r, re_ = ifb.verdict("reference", f.check, f.kwargs, f.prompt, f.response)
    lab = f.label == "pass"
    gs = "ok" if g == lab else ("EXC " + ge if g is None else "WRONG")
    rs = "ok" if r == lab else ("EXC " + re_ if r is None else "WRONG")
    gflag = (gs != "ok") != bool(f.grader)
    rflag = (rs != "ok") != bool(f.reference)
    if gflag or rflag or "-v" in sys.argv:
        bad += gflag or rflag
        print(f"{'!!' if (gflag or rflag) else '  '} {f.id:48s} label={f.label:4s} kind={f.kind:9s} grader={gs:5s} [{f.grader}] ref={rs:5s} [{f.reference}] {f.note[:50]}")
print("fixtures", len(FIXTURES), "status mismatches", bad)
print("grader wrong", sum(1 for f in FIXTURES if f.grader), "reference wrong", sum(1 for f in FIXTURES if f.reference))
