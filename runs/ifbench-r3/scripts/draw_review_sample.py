"""Step 6.1-6.3: draw, freeze and render the blinded review sample (round 1).

Population: the held-out runs (audit/frozen/heldout_runs.tsv), every instruction instance except
extraction failures (contract G1 fails them; counted separately). Strata:
  S1a grader pass, replacement fail      S1b grader fail, replacement pass
  S2  grader = replacement, reference differs
  S3  grader = replacement = reference
Writes under audit/frozen/review_round1/:
  cases.jsonl          frozen case list (case id, stratum, check, prompt key, instruction index, response sha256)
  key.jsonl            source configuration and run, every grader verdict (never shown to reviewers)
  review_cases.jsonl   what the helper prints from: case id, check, requirement, prompt, response
  responses/<id>.txt   exact response of every case
  batches_A/, batches_B/  batch files, cases in a different order for each reviewer
  show_case.py         helper that prints a case's exact response
  strata.json          population and sample size of each stratum, seed
Run from W:  .venv/Scripts/python.exe -B audit/scripts/draw_review_sample.py
"""
import hashlib
import json
import os
import random
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
import ifb  # noqa: E402

SEED = 61109
SIZES = {"S1a": 170, "S1b": 125, "S2": 3, "S3": 160}
BATCH = 25
TRUNC = 6000
OUT = os.path.join(W, "audit", "frozen", "review_round1")

REQ = {
    "count:conjunctions": r"Use at least [\d.]+ different coordinating conjunctions in the response\.",
    "count:keywords_multiple": r"Include keyword .+? seven times in your response\.",
    "count:numbers": r"Include exactly [\d.]+ numbers in the response\.",
    "count:person_names": r"Mention at least [\d.]+ different person names in the response, from this list of person names: .*?Jonathan \.",
    "count:pronouns": r"The response should include at least [\d.]+ pronouns\.",
    "count:punctuation": r"Use every standard punctuation mark at least once, including semicolons, colons, and the interrobang \(\?!\)\.",
    "count:unique_word_count": r"Use at least [\d.]+ unique words in the response\.",
    "count:word_count_range": r"The response must contain between [\d.]+ and [\d.]+ words\.",
    "count:words_japanese": r"Every [\d.]+\w* word of your response must be in Japanese\.",
    "format:emoji": r"Please use an emoji at the end of every sentence\.",
    "format:line_indent": r"Create stairs by incrementally indenting each new line\.",
    "format:list": r"Answer with a list of items, instead of bullet points use \S+?\.(?=\s|$)",
    "format:newline": r"Write each word on a new line\.",
    "format:no_bullets_bullets": r"Your answer must contain at least two sentences ending in a period followed by at least two bullet points denoted by \*\.",
    "format:no_whitespace": r"The output should not contain any whitespace\.",
    "format:options": r"Answer with one of the following options: .+?\.(?=\s|$)(?: Do not give any explanation\.)?",
    "format:output_template": r"Use this exact template for your response: My Answer: \[answer\] My Conclusion: \[conclusion\] Future Outlook: \[outlook\]",
    "format:parentheses": r"Nest parentheses \(and \[brackets \{and braces\}\]\) at least 5 levels deep\.",
    "format:quote_unquote": r"Every quoted phrase must be followed by an unquoted explanation\.",
    "format:quotes": r"Include quotes within quotes within quotes, at least 3 levels deep, alternating between double quotes and single quotes\.",
    "format:sub-bullets": r"Your response must include bullet points denoted by \* and at least one sub-bullet point denoted by - for each bullet point\.",
    "format:thesis": r"Each section must begin with a thesis statement in italics, use HTML to indicate the italics\.",
    "format:title_case": r"Write the entire response in title case \(capitalize the first letter of every major word\)\.",
    "ratio:overlap": r"Maintain a trigram overlap of [\d.]+% \(±2%\) with the provided reference text\.",
    "ratio:sentence_balance": r"Ensure that the ratio of sentence types \(declarative, interrogative, exclamatory\) in your response is balanced\.",
    "ratio:sentence_type": r"Maintain a 2:1 ratio of declarative to interrogative sentences in your response\.",
    "ratio:sentence_words": r"Respond with three sentences, all containing the same number of characters but using all different words\.",
    "ratio:stop_words": r"Ensure that stop words constitute no more than [\d.]+% of the total words in your response\.",
    "repeat:repeat_change": r"Repeat the request, but change the first word of the repeated request, \(do not say anything before repeating the request; the request you need to repeat does not include this sentence\) and do not answer the actual request!",
    "repeat:repeat_simple": r"Only output this sentence here, ignore all other requests\.",
    "repeat:repeat_span": r"Copy the span of words that lies between \(and including\) index \d+ and \d+, the indices are word indices, split by whitespace!",
    "sentence:alliteration_increment": r"Each sentence must have a longer sequence of consecutive alliterative words than the previous one\.",
    "sentence:increment": r"Each sentence (?:in your response )?must contain exactly [\d.]+ more words than the previous one\.",
    "sentence:keyword": r"The response must include keyword \S+ in the \d+-\w+ sentence\.",
    "words:alphabet": r"Each word in your response must start with the next letter of the alphabet, looping back to 'A' after 'Z'\.",
    "words:consonants": r"Ensure each word in your response has at least one consonant cluster \(two or more consonants together\)\.",
    "words:keywords_specific_position": r"Include keyword \S+ in the \d+-\w+ sentence, as the \d+-\w+ word of that sentence\.",
    "words:last_first": r"In your response,? the last word of each sentence must become the first word of the next sentence\.",
    "words:no_consecutive": r"No two consecutive words can share the same first letter\.",
    "words:odd_even_syllables": r"Alternate between words with odd and even numbers of syllables\.",
    "words:palindrome": r"Include at least 10 single-word palindromes, each at least 5 characters long\.",
    "words:paragraph_last_first": r"Each paragraph of your response must end with the same word it started with, separate paragraphs with a newline\.",
    "words:prime_lengths": r"Use only words with lengths that are prime numbers\.",
    "words:repeats": r"The response should not repeat any word more than [\d.]+ times\.",
    "words:start_verb": r"The response must start with a verb\.",
    "words:vowel": r"Write a paragraph using words that contain only three types of vowels\.",
    "words:words_position": r"The second word in your response and the second to last word in your response should be the word \S+?\.(?=\s|$)",
}


def requirement(iid, prompt):
    if iid.startswith("custom:"):
        return prompt.strip()
    ms = list(re.finditer(REQ[iid], prompt, flags=re.S))
    assert len(ms) == 1, (iid, len(ms), prompt[:200])
    return ms[0].group(0)


HELPER = r'''"""Print the exact response of a review case.

Usage (from any folder):
  python show_case.py CASE_ID          the response exactly as graded, nothing added
  python show_case.py CASE_ID --repr   the response as a Python string literal (shows spaces, tabs, newlines)
  python show_case.py CASE_ID --json   one JSON object with case_id, check, requirement, prompt, response
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cid = sys.argv[1]
    with open(os.path.join(HERE, "review_cases.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            c = json.loads(line)
            if c["case_id"] == cid:
                break
        else:
            sys.exit(f"unknown case id {cid}")
    out = sys.stdout
    if hasattr(out, "reconfigure"):
        out.reconfigure(encoding="utf-8", newline="")
    if "--json" in sys.argv:
        out.write(json.dumps(c, ensure_ascii=False))
    elif "--repr" in sys.argv:
        out.write(repr(c["response"]) + "\n")
    else:
        out.write(c["response"])


if __name__ == "__main__":
    main()
'''

INTRO = """# IFBench blinded review, round 1, reviewer {who}, batch {b} of {nb}

Each case below starts with a line `## Case <id>` and gives the case id, the CHECK name, the
REQUIREMENT TO JUDGE, the PROMPT the model received and the RESPONSE to judge. The prompt sits
between the lines `=====BEGIN PROMPT <id>=====` and `=====END PROMPT <id>=====`, the response
between `=====BEGIN RESPONSE <id>=====` and `=====END RESPONSE <id>=====`. The text starts right
after the newline that ends the BEGIN line and stops right before the newline that comes before
the END line, so a response that ends with a newline shows a blank line before its END line,
and leading or trailing spaces are part of the response. A response longer than {trunc}
characters is cut in this file and marked TRUNCATED with the name of the file that holds it in
full. The helper `show_case.py` prints any case's exact response (`--repr` shows whitespace).
"""


def main():
    ifb.verify_pins()
    held = ifb.heldout()
    pv = [json.loads(l) for l in open(os.path.join(W, "audit", "work", "panel_verdicts.jsonl"), encoding="utf-8")]
    pop = [r for r in pv if r["heldout"] and not r["extraction_failure"]]
    assert all(held[r["cfg"]] == r["run"] for r in pop)
    for r in pop:
        assert r["g"] is not None and r["p"] is not None and r["r"] is not None, r
        if bool(r["g"]) != bool(r["p"]):
            r["stratum"] = "S1a" if r["g"] else "S1b"
        elif bool(r["g"]) != bool(r["r"]):
            r["stratum"] = "S2"
        else:
            r["stratum"] = "S3"
    strata = {}
    rng = random.Random(SEED)
    sample = []
    for s in ("S1a", "S1b", "S2", "S3"):
        members = sorted((r for r in pop if r["stratum"] == s), key=lambda r: (r["cfg"], r["run"], int(r["key"]), r["j"]))
        k = min(SIZES[s], len(members))
        chosen = rng.sample(members, k)
        strata[s] = {"population": len(members), "sample": k}
        sample.extend(chosen)
    responses = {}
    for cfg, run, i, rec in ifb.iter_panel():
        if held.get(cfg) == run:
            responses[(cfg, run, rec["key"])] = rec
    rows = {r["key"]: r for r in ifb.load_rows()}
    ids = set()
    cases, keys, rcases = [], [], []
    for r in sample:
        while True:
            cid = "R1-%05x" % rng.getrandbits(20)
            if cid not in ids:
                ids.add(cid)
                break
        rec = responses[(r["cfg"], r["run"], r["key"])]
        row = rows[r["key"]]
        resp = rec["response"]
        req = requirement(r["iid"], row["prompt"])
        sha = hashlib.sha256(resp.encode("utf-8")).hexdigest()
        cases.append({"case_id": cid, "stratum": r["stratum"], "check": r["iid"], "key": r["key"], "j": r["j"],
                      "response_sha256": sha})
        keys.append({"case_id": cid, "cfg": r["cfg"], "run": r["run"], "key": r["key"], "j": r["j"], "check": r["iid"],
                     "stratum": r["stratum"], "grader": r["g"], "grader_loose": r["gl"], "reference": r["r"],
                     "reference_loose": r["rl"], "replacement": r["p"], "replacement_alt": r["alt"],
                     "finish_reason": r["finish"]})
        rcases.append({"case_id": cid, "check": r["iid"], "requirement": req, "prompt": row["prompt"], "response": resp})
    cases.sort(key=lambda c: c["case_id"])
    keys.sort(key=lambda c: c["case_id"])
    rcases.sort(key=lambda c: c["case_id"])
    os.makedirs(os.path.join(OUT, "responses"), exist_ok=True)

    def dump(name, items):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            for it in items:
                fh.write(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n")

    dump("cases.jsonl", cases)
    dump("key.jsonl", keys)
    dump("review_cases.jsonl", rcases)
    for c in rcases:
        with open(os.path.join(OUT, "responses", c["case_id"] + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(c["response"])
    with open(os.path.join(OUT, "show_case.py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(HELPER)
    by_id = {c["case_id"]: c for c in rcases}
    orders = {}
    for who, seed in (("A", SEED + 1), ("B", SEED + 2)):
        order = sorted(by_id)
        random.Random(seed).shuffle(order)
        orders[who] = order
        d = os.path.join(OUT, f"batches_{who}")
        os.makedirs(d, exist_ok=True)
        chunks = [order[i:i + BATCH] for i in range(0, len(order), BATCH)]
        for b, chunk in enumerate(chunks, 1):
            parts = [INTRO.format(who=who, b=b, nb=len(chunks), trunc=TRUNC)]
            for cid in chunk:
                c = by_id[cid]
                resp = c["response"]
                shown = resp if len(resp) <= TRUNC else resp[:TRUNC]
                note = "" if len(resp) <= TRUNC else (
                    f"TRUNCATED: only the first {TRUNC} of {len(resp)} characters are shown below; the full response is in "
                    f"audit/frozen/review_round1/responses/{cid}.txt (or print it with the helper).\n\n")
                parts.append(
                    f"## Case {cid}\n\nCASE ID: {cid}\nCHECK: {c['check']}\nREQUIREMENT TO JUDGE: {c['requirement']}\n\n"
                    f"PROMPT:\n=====BEGIN PROMPT {cid}=====\n{c['prompt']}\n=====END PROMPT {cid}=====\n\n"
                    f"{note}RESPONSE:\n=====BEGIN RESPONSE {cid}=====\n{shown}\n=====END RESPONSE {cid}=====\n")
            with open(os.path.join(d, f"batch_{who}{b:02d}.md"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(parts))
    with open(os.path.join(OUT, "strata.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"seed": SEED, "sizes_requested": SIZES, "strata": strata, "batch_size": BATCH,
                   "population_definition": "held-out runs, all instruction instances, extraction failures excluded",
                   "order_seeds": {"A": SEED + 1, "B": SEED + 2}, "n_cases": len(cases)}, fh, indent=1)
    print("strata", strata, "cases", len(cases))


if __name__ == "__main__":
    main()
