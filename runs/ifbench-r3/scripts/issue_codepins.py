p = "audit/ISSUE.md"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
rep("one hash per row in `audit/frozen/dataset_row_hashes.tsv` (sha256 b7e4d7df493b9ba25ff3737c91629a54ceb4d23ce95eede6a335b1f8319d8b56; row hash = sha256 of the sorted-key compact JSON of key, prompt, instruction_id_list, non-null kwargs)",
    "one hash per row in `audit/frozen/dataset_row_hashes.tsv` (sha256 dead3343c495ada3bba42201f71851f9ec69d5c8ffbd5233e29b323460fe7ad7; row hash = sha256 of the sorted-key compact JSON of key, prompt, instruction_id_list, non-null kwargs, read with pyarrow `to_pylist()` so int64 kwargs stay integers as `datasets.load_dataset` returns them; the first version of this file, b7e4d7df…8b56, was computed from the pandas view in which those kwargs are floats and is superseded)")
rep("Which of these the grader actually loads (and any extraction rule it applies itself) is read from\nthe code only after the contract hash is recorded; see \"Step 1, code-level pins\" below.\n",
"""Which of these the grader actually loads (and any extraction rule it applies itself) is read from
the code only after the contract hash is recorded; see "Step 1, code-level pins" below.

### Step 1, code-level pins (recorded 2026-11-09 22:30 UTC, after the contract hash)

- What the grader loads: `instructions.py` imports nltk 3.10.0 (`sent_tokenize` and
  `word_tokenize` use `tokenizers/punkt_tab/english`; `pos_tag` uses
  `taggers/averaged_perceptron_tagger_eng`; `count_stopwords` uses `corpora/stopwords/english`;
  `RegexpTokenizer(r"\w+")` counts words), emoji 2.15.0 (`emoji.is_emoji`), syllapy 0.8.0
  (`syllapy.count`), and the standard library `csv`, `unicodedata` (Python 3.12.10, Unicode
  15.0), `re`, `string`. The pickled `tokenizers/punkt/english.pickle` is referenced only by an
  unused helper.
- Import-time side effects: `instructions.py` creates a `.nltk_data` folder next to itself, puts
  it first on `nltk.data.path`, and sets `NLTK_DATA` to it when the variable is unset;
  `instructions_util.download_nltk_resources()` then downloads `punkt`, `punkt_tab`, `stopwords`
  and `averaged_perceptron_tagger_eng` from the network when they are missing (F-pin-3).
- Dataset loading: `eval_instruct.py` calls `load_dataset("allenai/IFBench_test", split="train")`
  with no revision (F-pin-4).
- Extraction: neither `eval_instruct.py` nor `grader.py` removes reasoning or `</think>`; the
  graded text is whatever Evalchemy's generation step stores, which is not in the case.
  Unverified; location: Evalchemy `eval/sources/common.py` (`text_specs`) and the `instructions`
  grader it dispatches to. Verify by reading those files at the commit Marin pins.
- Generation settings in code: `generation_kwargs={"do_sample": False, "temperature": 0,
  "max_gen_toks": max_tokens}` with `max_tokens=1024` by default (matches the panel's thinking-off
  configurations; the thinking configurations used 8,192).
- Strict grading (`grader.py`): an empty or whitespace-only response fails every instruction;
  otherwise `check_following(response)` on the unstripped response. Loose grading tries eight
  variants (the response, without its first line, without its last line, without both, and
  each of these with every `*` removed) and passes if any passes. The reference
  (`evaluation_lib.py`) applies the same two transforms.
- Responses are looked up by prompt text; the 300 prompts are distinct, so no collisions.
- How the audit runs the code: byte-identical copies in `audit/work/pkgs/grader/IFBench` and
  `audit/work/pkgs/reference/ifbench` (+ `evaluation_lib.py`, `instructions_test.py`), imported
  with bytecode writing off, so that importing does not create folders under `case/`.
  `audit/lib/ifb.py` (`verify_pins`) checks every copy, the parquet and the lock file against the
  manifest before each run. Its per-instruction wrapper reproduces `grader.py`'s strict and loose
  functions exactly (344 of 344 verdicts on one stored run, `audit/scripts/smoke_grader.py`).
""")
rep("| F-pin-2 | generation settings | Stop sequences are not recorded for any configuration, and the vLLM version is not recorded for the two thinking configurations. | `case/panel/CONFIGS.md` |\n",
    "| F-pin-2 | generation settings | Stop sequences are not recorded for any configuration, and the vLLM version is not recorded for the two thinking configurations. | `case/panel/CONFIGS.md` |\n"
    "| F-pin-3 | grader dependencies | At import the grader downloads any missing NLTK package (latest version, from the network) into a folder it creates next to its own code; the NLTK data it grades with is therefore pinned only when the caller provides it. | `instructions.py` lines 25-32, `instructions_util.py` lines 1551-1571 |\n"
    "| F-pin-4 | dataset | `eval_instruct.py` loads `allenai/IFBench_test` without a revision, so a dataset update changes prompts and kwargs silently. | `eval_instruct.py` `load_questions` |\n")
rep("| `audit/frozen/dataset_row_hashes.tsv` | b7e4d7df493b9ba25ff3737c91629a54ceb4d23ce95eede6a335b1f8319d8b56 | 2026-11-09 22:05 UTC |",
    "| `audit/frozen/dataset_row_hashes.tsv` | dead3343c495ada3bba42201f71851f9ec69d5c8ffbd5233e29b323460fe7ad7 | 2026-11-09 22:29 UTC (supersedes b7e4d7df…8b56 of 22:05, see Step 1) |\n| `audit/frozen/CONTRACT_v1.md` | b88caf4afb44ecb4f46c08890ab7006084e7da2af57d624816bb24138cee2f95 | 2026-11-09 22:16 UTC |")
rep("| 1. Pin the inputs | done 2026-11-09 22:10 UTC (record-level pins); code-level pins added after step 2 | this file, \"Step 1\" |",
    "| 1. Pin the inputs | done (record-level 22:10 UTC, code-level 22:30 UTC) | this file, \"Step 1\" |")
rep("Next: read the grader code, record code-level pins, then build fixtures (step 3).",
    "Next: build fixtures (step 3) in `audit/tests/`, labeled from `audit/CONTRACT.md` alone.")
rep("- 2026-11-09 22:16 UTC: contract v1 hashed and recorded; grader code not yet opened.\n",
    "- 2026-11-09 22:16 UTC: contract v1 hashed and recorded; grader code not yet opened.\n- 2026-11-09 22:30 UTC: read the grader and the reference code (diff: the reference commit fixes 7 checkers); code-level pins recorded.\n")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
