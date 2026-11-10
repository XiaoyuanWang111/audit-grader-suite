# Task

Audit the IFBench grader that Marin's evaluation policy runs through Evalchemy.

## What is where

Paths are relative to this folder, `<W>/case`.

- `grader/IFBench/`: the grader under audit, Marin's vendored copy of Evalchemy's IFBench benchmark.
  - `instructions.py`: the instruction checkers.
  - `instructions_registry.py`: the map from instruction id to checker class.
  - `instructions_util.py`: helpers the checkers use.
  - `eval_instruct.py` and `grader.py`: the harness that applies strict and loose grading.
- `reference/IFBench/`: the benchmark authors' implementation and its unit tests (`instructions_test.py`), from github.com/allenai/IFBench at commit 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d. The checker code is in `reference/IFBench/ifbench/`.
- `data/train-00000-of-00001.parquet`: the IFBench_test set, 300 prompts (huggingface.co/datasets/allenai/IFBench_test at revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2).
- `panel/<folder>/<run>.jsonl`: stored model responses to those prompts; generation settings in `panel/CONFIGS.md`.
- `deps/nltk_data/`: the NLTK data the checkers load. `deps/requirements.lock.txt`: the packages installed in the Python environment.
- `MANIFEST.sha256`: SHA-256 of every other file in this folder.

The rest of Evalchemy and of Marin is not included; `eval_instruct.py` imports Evalchemy modules that are not here. There is no network access.

## Running Python

Use the interpreter `<W>/.venv/Scripts/python.exe` (Python 3.12, packages as in `deps/requirements.lock.txt`) with `NLTK_DATA` set to `<W>/case/deps/nltk_data`.

Git Bash:

    cd <W>/case
    export NLTK_DATA=<W>/case/deps/nltk_data
    ../.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'grader'); from IFBench import instructions_registry"

PowerShell:

    $env:NLTK_DATA = "<W>\case\deps\nltk_data"

The checker modules use relative imports: import the grader as the package `IFBench` with `grader/` on `sys.path`, and the reference as the package `ifbench` with `reference/IFBench/` on `sys.path`.
