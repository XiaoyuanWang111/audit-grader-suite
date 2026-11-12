"""Gate pass rate per run: VG (verifyit) vs the replacement on the same deterministic constraints."""
import collections, json
import numpy as np
rng = np.random.default_rng(20261112)
runs = collections.defaultdict(list)
for p in ("out/panel_A.jsonl", "out/panel_B.jsonl"):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        vg = all(v for v in r["vg"] if v is not None)
        rg = all(rv for rv, gv in zip(r["r"], r["vg"]) if gv is not None)
        nvg = all((bool(n) and not e) for n, e, gv in zip(r["nv"], r["nv_err"], r["vg"]) if gv is not None)
        runs[r["file"]].append((vg, rg, nvg))
for f, xs in sorted(runs.items()):
    a = np.array(xs, float)
    d = a[:, 1] - a[:, 0]
    idx = rng.integers(0, len(d), (2000, len(d)))
    m = d[idx].mean(1)
    print(f"{f:55s} n={len(xs):5d} VG={100*a[:,0].mean():5.1f} R-gate={100*a[:,1].mean():5.1f} NV-on-gate-constraints={100*a[:,2].mean():5.1f} R-VG={100*d.mean():+5.1f} [{100*np.percentile(m,2.5):+5.1f},{100*np.percentile(m,97.5):+5.1f}]")
