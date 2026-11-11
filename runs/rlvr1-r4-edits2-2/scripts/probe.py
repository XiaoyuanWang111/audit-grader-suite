"""Ad-hoc probes: python probe.py '<iid>' '<kwargs json>' '<text as JSON string>' ..."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness  # noqa: E402

harness.setup()
args = sys.argv[1:]
for i in range(0, len(args), 3):
    iid, kw, text = args[i], json.loads(args[i + 1]), json.loads(args[i + 2])
    n = harness.skyrl_constraint(iid, kw, text)
    v = harness.verifyit_constraint(iid, kw, text)
    print(f"{iid} {kw} {text[:60]!r}: nvidia={n} verifyit={v}")
