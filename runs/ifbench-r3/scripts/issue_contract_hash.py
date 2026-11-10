p = "audit/ISSUE.md"
s = open(p, encoding="utf-8").read()
old = "## Step 2. Contract\n\n(pending)\n"
new = """## Step 2. Contract

- `audit/CONTRACT.md` version 1: sha256 b88caf4afb44ecb4f46c08890ab7006084e7da2af57d624816bb24138cee2f95,
  recorded 2026-11-09 22:16 UTC, before any grader or reference code was opened (only the dataset
  prompts, `case/panel/CONFIGS.md`, the manifest, the lock file and the panel records had been
  read). A byte-identical copy is `audit/frozen/CONTRACT_v1.md`.
- 58 check contracts, shared rules G1 to G6, 46 decision entries (table at the end of the file).
- Later changes to the contract are listed here with their reason.
"""
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("| 2. Contracts | in progress | `audit/CONTRACT.md` |", "| 2. Contracts | done 2026-11-09 22:16 UTC (v1 hash recorded) | `audit/CONTRACT.md` |")
s = s.replace("Next: write `audit/CONTRACT.md` from the prompt texts only, record its sha256 and the time\nbelow, then read the grader code.",
              "Next: read the grader code, record code-level pins, then build fixtures (step 3).")
s = s.replace("- 2026-11-09 22:10 UTC: step 1 record-level pins written; held-out runs chosen.\n",
              "- 2026-11-09 22:10 UTC: step 1 record-level pins written; held-out runs chosen.\n- 2026-11-09 22:16 UTC: contract v1 hashed and recorded; grader code not yet opened.\n")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
