# Task

Audit the two graders that score the 11,817 instruction-following rows of Marin's Nemotron RLVR1 data: the SkyRL environment's reward, which runs NVIDIA's verifiable-instructions checkers, and the deterministic checks of Marin's task-curation grader, which run verifyit's `ifeval` checks. NVIDIA's checkers are the data's own grader, so they are also the reference implementation for verifyit's checks.

## What is where

Paths are relative to this folder, `<W>/case`. Marin files come from github.com/marin-community/marin at commit af9c6789e878bed1a6fc9513232bcfc54ac73b3a and keep their package-relative paths; `SOURCES.md` gives each file's path in its repository and its git blob.

- `reference/`: the first grader under audit, with the checkers it runs.
  - `verifiable-instructions/`: NVIDIA's checkers, the whole repository github.com/abukharin-nv/verifiable-instructions at commit f46a5ac87b1400a4f8973039844b6be9b56e3faf (it has no tests). The checker classes are in `verifiable_instructions/instructions.py`, the map from instruction id to class in `instructions_registry.py`, and helpers in `instructions_util.py`.
  - `skyrl_gym/`: Marin's SkyRL environment files that run them (Marin path `vendor/skyrl/skyrl-gym/skyrl_gym/`). `nemotron_tasks.py`: the task session, which grades a row by its agent. `envs/nemotron_ultra/instruction_following.py`: the reward, `grade_instruction_following`. `envs/nemotron_ultra/answer_extraction.py`: `final_answer_text`, which the session applies to the model's text before grading; it imports `envs/aime/utils.py`. `envs/instruction_verifyit.py`: `grade_nemotron_instructions`, the session's other reward for these rows. `envs/nemotron_ultra/instruction_references.py`: resolves source-generated instruction parameters before candidate generation.
- `grader/`: the second grader under audit.
  - `verifyit/`: Marin's verifyit package (Marin path `lib/verifyit/src/verifyit/`), every file. `modes/ifeval.py`: the checks, keyed by instruction id in `CONSTRAINTS`. `modes/grade_ifeval.py`: `resolve_checks`, which maps constraints to checks. `modes/grade_judge.py`: the judge mode, whose deterministic gate runs the checks.
  - `experiments/post_training/task_curation/datasets/nemotron_ultra/`: `graders.py`, the task-curation grader, whose `convert_instruction_following` builds the task for these rows; `conversation.py`, from the same folder.
- `data/rlvr1_instruction_following.jsonl`: the 11,817 rows, one JSON object per line with the five columns of the source file (`data_source`, `prompt`, `env_class`, `reward_model`, `extra_info`), in file order. Source: huggingface.co/datasets/open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 at revision 600262dd37891b86075a80517e61dbfb105d7cbe, file `data/train.parquet` (sha256 fde7259ad17170b6a57292ea85fdd20d9a2428b078cc3aa67cdeab8155fc0b1b), the rows whose `extra_info.nemotron_ultra.agent` is `instruction_following_simple_agent`. A row's constraints are `instruction_id_list` and `kwargs` in `extra_info.nemotron_ultra.record_json`, a JSON string: 28,219 constraints of 47 instruction ids in all. Each row has one user message and no system message; its stored request settings (`request_json`) are temperature 1.0 and top-p 1.0 with no tools. No row sets `grading_mode`.
- `panel/<folder>/<run>.jsonl`: stored model responses to those rows, keyed by the row's `uuid`; models and generation settings in `panel/CONFIGS.md`.
- `deps/nltk_data/`: NLTK's `punkt_tab`, unzipped from `punkt_tab.zip` (sha256 e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106). `deps/requirements.lock.txt`: the packages installed in the Python environment.
- `SOURCES.md`: the source of every file. `MANIFEST.sha256`: SHA-256 of every other file in this folder.

The rest of Marin is not included. `nemotron_tasks.py`, `answer_extraction.py` (through `envs/aime/utils.py`), `graders.py` and verifyit's `modes/grade_judge.py` import packages that are not installed here, so they cannot be imported. The LLM judge is not part of this case. There is no network access.

## How each pipeline forms a row's reward

SkyRL (`nemotron_tasks.py`, `NemotronTaskSession`): the record is `record_json` parsed. `advance` passes the model's text through `final_answer_text`; for the agent `instruction_following_simple_agent`, `_answer_grade` then calls `grade_instruction_following(action, record)`, or `grade_nemotron_instructions` when the session config sets `verifyit_enabled` (default false). `grade_instruction_following` builds each constraint with `build_instruction` from NVIDIA's registry and the constraint's kwargs without `None` values, and calls its `check_following`; with `grading_mode` `binary`, the default, the reward is 1.0 when every constraint passes and 0.0 otherwise.

Task curation (`graders.py`, `convert_instruction_following`): one verifyit `Constraint` per constraint of the row, with its kwargs without `None` values; a row whose `grading_mode` is not `binary` is not converted. The constraints whose id is in `SEMANTIC_INSTRUCTION_CONSTRAINTS` (`count:count_unique`, `detectable_format:bigram_wrapping`, `language:response_language`, `letters:letter_counting`) go to the LLM judge as criteria and get no deterministic check; the others are the `constraints` of the task's `JudgeSpec`. `grade_judge_candidate` (`modes/grade_judge.py`) strips reasoning blocks from the candidate (`strip_candidate_reasoning_blocks=True`) and runs the check of every deterministic constraint: if one fails, the reward is 0.0 and the judge is not called. Otherwise the reward is the fraction of the judge's criteria, one general criterion plus one per judged constraint, that the judge scores 1.

## Running Python

Use the interpreter `<W>/.venv/Scripts/python.exe` (Python 3.12.10, packages as in `deps/requirements.lock.txt`) with `NLTK_DATA` set to `<W>/case/deps/nltk_data`. verifyit and verifiable-instructions are installed from git at the commits above, byte-identical to `grader/verifyit/` and `reference/verifiable-instructions/verifiable_instructions/`. The SkyRL files are not installed: import them as the package `skyrl_gym` with `reference/` on `sys.path`. Set `PYTHONDONTWRITEBYTECODE=1`; without it, importing them writes `__pycache__` folders into `reference/skyrl_gym/`.

Git Bash:

```bash
cd <W>/case
export NLTK_DATA=<W>/case/deps/nltk_data
export PYTHONDONTWRITEBYTECODE=1
```

The SkyRL reward on the first row and one response (the session first passes the text through `final_answer_text`; the example's response has no reasoning block):

```bash
../.venv/Scripts/python.exe - <<'EOF'
import json, sys
sys.path.insert(0, "reference")
from skyrl_gym.envs.nemotron_ultra.instruction_following import grade_instruction_following
with open("data/rlvr1_instruction_following.jsonl", encoding="utf-8") as f:
    row = json.loads(f.readline())
record = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
print(grade_instruction_following("Here is my answer.", record))
EOF
```

The task-curation gate's deterministic checks on the same row and response, as `convert_instruction_following` and `grade_judge_candidate` apply them (`grade_judge_candidate` first strips reasoning blocks; the example's response has none):

```bash
../.venv/Scripts/python.exe - <<'EOF'
import json
from verifyit.modes.grade_ifeval import resolve_checks
from verifyit.spec import Constraint
SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping",
            "language:response_language", "letters:letter_counting"}  # graders.py
with open("data/rlvr1_instruction_following.jsonl", encoding="utf-8") as f:
    row = json.loads(f.readline())
record = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
constraints = tuple(Constraint(name, {k: v for k, v in (args or {}).items() if v is not None})
                    for name, args in zip(record["instruction_id_list"], record["kwargs"]))
resolve_checks(constraints)
gate = tuple(c for c in constraints if c.name not in SEMANTIC)
response = "Here is my answer."
failed = []
for constraint, check in resolve_checks(gate) if gate else []:
    try:
        passed, detail = check(response, constraint.params)
    except Exception as error:
        passed, detail = False, repr(error)
    print(constraint.name, passed, detail)
    if not passed:
        failed.append(constraint.name)
print("gate failed: reward 0.0" if failed else "gate passed: the judge decides the reward")
EOF
```

One NVIDIA checker on its own:

```bash
../.venv/Scripts/python.exe -c "from verifiable_instructions import instructions_registry as r; c = r.INSTRUCTION_DICT['punctuation:no_comma']('punctuation:no_comma'); c.build_description(); print(c.check_following('No commas here.'))"
```

PowerShell:

```powershell
$env:NLTK_DATA = "<W>\case\deps\nltk_data"
$env:PYTHONDONTWRITEBYTECODE = "1"
```
