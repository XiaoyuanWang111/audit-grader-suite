"""Fill skill/references/reviewer-prompt.md for reviewers A and B (step 6.4 hand-off).

Writes audit/frozen/review_round1/prompt_reviewer_A.md and prompt_reviewer_B.md. The prompt text is
the reference's text block with its placeholders filled; the only wording change is that a
reviewer gets an ordered list of batch files instead of one file.
"""
import glob
import os
import re

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WS = W.replace(os.sep, "/")
src = open(os.path.join(W, "skill", "references", "reviewer-prompt.md"), encoding="utf-8").read()
block = re.search(r"```text\n(.*?)\n```", src, flags=re.S).group(1)
R1 = os.path.join(W, "audit", "frozen", "review_round1")
helper = f"{WS}/.venv/Scripts/python.exe {WS}/audit/frozen/review_round1/show_case.py <case id>   (add --repr to see whitespace, --json for the full case)"
for who in ("A", "B"):
    batches = sorted(glob.glob(os.path.join(R1, f"batches_{who}", "*.md")))
    blist = "\n".join("  " + b.replace(os.sep, "/") for b in batches)
    out_path = f"{WS}/audit/frozen/reviews/review_{who}.jsonl"
    text = block
    text = text.replace("<benchmark>", "IFBench")
    text = text.replace("Your batch file: <batch path>", "Your batch files, to be judged in this order:\n" + blist)
    text = text.replace("<output path>", out_path)
    text = text.replace("<helper command>", helper)
    text = text.replace("read only your batch file, the helper above", "read only your batch files, the helper above")
    text = text.replace("in the batch's case order", "in the batches' case order")
    assert "<" not in text.replace("<case id>", ""), text
    with open(os.path.join(R1, f"prompt_reviewer_{who}.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    print(who, len(batches), "batches ->", out_path)
