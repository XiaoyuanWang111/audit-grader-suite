"""Choose the held-out run of each configuration (step 5), before the panel is used to change the replacement grader."""
import glob, os, random
SEED = 20261109
rng = random.Random(SEED)
for cfg in sorted(os.listdir("case/panel")):
    d = os.path.join("case/panel", cfg)
    if not os.path.isdir(d):
        continue
    runs = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(d, "*.jsonl")))
    samples = sorted((r for r in runs if r.startswith("sample")), key=lambda r: int(r[6:]))
    pool = samples if samples else sorted(runs)
    print(f"{cfg}\t{rng.choice(pool)}")
