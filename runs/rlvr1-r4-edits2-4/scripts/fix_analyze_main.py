"""One-off: move analyze_panel.py's top-level work into main() under a __main__ guard (Windows spawn)."""
from pathlib import Path

p = Path("<W>/audit/scripts/analyze_panel.py")
s = p.read_text(encoding="utf-8")
head, body = s.split("\nsummary = {}\n", 1)
head = head.replace(
    '''def boot_ci(diffs, n_boot=2000, seed=0):
    rng = random.Random(seed)
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0)
    means = []
    for _ in range(n_boot):
        s = sum(diffs[rng.randrange(n)] for _ in range(n))
        means.append(s / n)
    means.sort()
    return (means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1])''',
    '''def boot_ci(diffs, n_boot=2000, seed=0):
    """95% percentile bootstrap interval of the mean of paired row differences."""
    import numpy as np

    if not diffs:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    x = np.asarray(diffs, dtype=float)
    means = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(axis=1)
    return (float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975)))''')
load = '''def main():
    rows = h.load_rows()
    recs = [json.loads(line) for line in open(A / "work" / "panel_verdicts.jsonl", encoding="utf-8")]
    raw = {}
    for path in sorted((CASE / "panel").glob("*/*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                raw[(path.parent.name, path.stem, i)] = json.loads(line)["raw_response"]
    summary = {}
'''
body_indented = "\n".join(("    " + line) if line.strip() else line for line in body.split("\n"))
p.write_text(head + "\n\n" + load + body_indented + '\n\nif __name__ == "__main__":\n    main()\n', encoding="utf-8", newline="\n")
print("ok")
