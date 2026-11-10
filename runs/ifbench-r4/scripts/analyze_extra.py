"""Extra panel numbers for the report.

1. G vs X disagreements per check, split into extraction failures (G1) and checker fixes.
2. X - G on the held-out files against the other files (prompt level, pooled).
3. A lower bound for F-startverb-tagger: G fails although the first word is a verb from a
   fixed list of imperatives that are not nouns, and the next word is not a verb.
4. Truncation: G prompt-level pass rate on truncated vs complete responses.
Writes audit/frozen/panel_extra.json and prints it.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VD = os.path.join(W, "audit", "frozen", "panel_verdicts")
PANEL = os.path.join(W, "case", "panel")
IMPERATIVES = {"imagine", "explore", "create", "describe", "explain", "discuss", "consider", "analyze", "analyse",
               "delve", "envision", "embrace", "discover", "unveil", "ensure", "examine", "write", "compose",
               "generate", "provide", "develop", "identify", "summarize", "visualize", "behold", "let",
               "begin", "craft", "reflect", "observe", "enter", "join", "prepare", "follow",
               "investigate", "evaluate", "assess", "define", "think", "remember", "meet",
               "uncover", "unlock", "construct", "implement"}


def held(cfg, run):
    return run == "sample7" or ("thinking" in cfg and run == "greedy_repeat")


def ok(v):
    return v is True


def main():
    split = defaultdict(Counter)
    hp = {True: Counter(), False: Counter()}
    sv = Counter()
    trunc = Counter()
    for cfg in sorted(os.listdir(VD)):
        for fn in sorted(os.listdir(os.path.join(VD, cfg))):
            run = fn[:-6]
            recs = [json.loads(l) for l in open(os.path.join(VD, cfg, fn), encoding="utf-8")]
            panel = None
            h = held(cfg, run)
            for i, rec in enumerate(recs):
                g_all = all(ok(x["G"]) for x in rec["inst"])
                x_all = all(ok(x["X"]) for x in rec["inst"])
                hp[h]["n"] += 1
                hp[h]["G"] += g_all
                hp[h]["X"] += x_all
                t = "length" if rec["fin"] == "length" else "stop"
                trunc[(t, "n")] += 1
                trunc[(t, "G")] += g_all
                for ins in rec["inst"]:
                    if ok(ins["G"]) != ok(ins["X"]):
                        kind = "extraction_failure" if rec["xf"] else "checker_fix"
                        split[ins["id"]][kind + (":G>X" if ok(ins["G"]) else ":G<X")] += 1
                    if ins["id"] == "words:start_verb" and not rec["xf"]:
                        if panel is None:
                            panel = open(os.path.join(PANEL, cfg, fn), encoding="utf-8").read().splitlines()
                        resp = json.loads(panel[i])["response"]
                        head = re.sub(r"[*_`#>\"']+", "", resp).lstrip()
                        ws = re.findall(r"[A-Za-z]+", head[:80])
                        sv["n"] += 1
                        if not ok(ins["G"]):
                            sv["G_fail"] += 1
                            if ws and ws[0].lower() in IMPERATIVES and ws[0][0].isupper():
                                sv["G_fail_first_word_listed_imperative"] += 1
    out = {
        "G_vs_X_split": {k: dict(v) for k, v in sorted(split.items())},
        "heldout": {("heldout" if k else "other"): {"n": v["n"], "G_prompt": 100 * v["G"] / v["n"],
                                                  "X_prompt": 100 * v["X"] / v["n"],
                                                  "X_minus_G": 100 * (v["X"] - v["G"]) / v["n"]} for k, v in hp.items()},
        "start_verb": dict(sv),
        "truncation": {t: {"n": trunc[(t, "n")], "G_prompt_pass": 100 * trunc[(t, "G")] / trunc[(t, "n")]} for t in ("stop", "length")},
    }
    with open(os.path.join(W, "audit", "frozen", "panel_extra.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
