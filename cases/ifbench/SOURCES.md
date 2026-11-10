# Sources of the IFBench case

The run's case folder held 425 files, 341 MB in all: stored model responses (281 MB), NLTK data (54 MB), third-party
code and the dataset. This folder keeps the four files that identify the case:

- `TASK.md`: the run's `TASK.md`, with the workspace's absolute path written as `<W>` (five times with forward
  slashes, once with backslashes in the PowerShell line). Nothing else is changed.
- `MANIFEST.sha256`: the sha256 of every other file of the case, byte-identical to the run's copy.
- `panel/CONFIGS.md`: the generation settings of the stored responses, byte-identical.
- `deps/requirements.lock.txt`: the Python packages of the run's environment, byte-identical.

The other 421 files come from the public sources below. The paths in the first column are relative to the case folder.

| Part | Files | Bytes | Source | Revision | Path in the source |
|---|---|---|---|---|---|
| `grader/IFBench/` | 6 | 115,984 | github.com/marin-community/marin | commit `2d9bb829d879230390ef06a4b9786c7afa060a85` | `vendor/evalchemy/eval/chat_benchmarks/IFBench/`, every file |
| `reference/IFBench/` | 31 | 6,451,943 | github.com/allenai/IFBench | commit `1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d` | the whole tree |
| `data/train-00000-of-00001.parquet` | 1 | 94,446 | huggingface.co/datasets/allenai/IFBench_test | revision `2e8a48de45ff3bf41242f927254ca81b59ca3ae2` | `data/train-00000-of-00001.parquet` |
| `panel/<folder>/<run>.jsonl` | 228 | 280,691,620 | release v0.1 of github.com/XiaoyuanWang111/ifbench-audit | asset `gen_final.tgz` | `gen/<folder>/<run>.jsonl` |
| `deps/nltk_data/` | 155 | 53,924,312 | github.com/nltk/nltk_data, branch `gh-pages` | the commit was not recorded; the four zip files are pinned by the sha256 values below | `packages/<category>/<package>.zip`, unzipped |
| Python environment | none in the case | | PyPI | the versions in `deps/requirements.lock.txt` | |

## Grader

The six files of Marin's vendored copy of Evalchemy's IFBench benchmark: `__init__.py`, `eval_instruct.py`,
`grader.py`, `instructions.py`, `instructions_registry.py` and `instructions_util.py`. In a clone of
marin-community/marin, `git archive 2d9bb829d879230390ef06a4b9786c7afa060a85 vendor/evalchemy/eval/chat_benchmarks/IFBench`
gives them; copy them to `grader/IFBench/`.

## Reference

All 31 files of allenai/IFBench at that commit, as `git archive 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d` gives them,
in `reference/IFBench/`. They include the `.coverage` file and the five `__pycache__/*.pyc` files that the repository
tracks; the manifest lists them.

## Dataset

The IFBench_test parquet file, 300 prompts, 94,446 bytes. Its sha256,
`80037e4d99c39a55c1e2e7d5a863d8d9edeb5ebe136ba8c1e849f8c015027c6a`, is also its Git LFS object id on the Hub.

## Panel

Release v0.1 of the earlier IFBench audit's repository has `gen_final.tgz` in six parts, `gen_final.tgz.part00` to
`gen_final.tgz.part05`, with `SHA256SUMS.txt`. The joined archive has sha256
`5c5486b95565a76a341b18b8ad353d76ca166a04453114c410abe03f0723c2c8`. It holds 230 run files (69,000 lines) as
`gen/<folder>/<run>.jsonl`, and 31 generation manifests (`gen/<folder>/manifest*.json`).

The case has 228 of the run files, each unchanged under the same folder and file name: `gen/<folder>/<run>.jsonl`
became `panel/<folder>/<run>.jsonl`. It leaves out `gen/Qwen__Qwen3-8B__thinking/sample0.jsonl` and
`gen/Qwen__Qwen3-14B__thinking/sample0.jsonl`, two aborted partial runs that the earlier audit also left out, and
the manifests. That gives 16 folders and 68,400 responses; `panel/CONFIGS.md` lists each folder's model, revision and
runs. With the six parts and `SHA256SUMS.txt` in one folder:

```text
cat gen_final.tgz.part0* > gen_final.tgz && sha256sum -c SHA256SUMS.txt
tar -xzf gen_final.tgz
mkdir -p case/panel && cp -r gen/* case/panel/
rm case/panel/*/manifest*.json case/panel/Qwen__Qwen3-8B__thinking/sample0.jsonl case/panel/Qwen__Qwen3-14B__thinking/sample0.jsonl
```

The Hugging Face dataset `xiaoyuanwang/ifbench-audit` (configuration `panel_verdicts`) lists the same 68,400
responses by `config`, `run` and `prompt_key`, with `response_sha256`, the sha256 of each line's `response` field.

## NLTK data

The unzipped contents of four packages of NLTK's data repository, without the zip files:

| Package | Files | sha256 of the zip file |
|---|---|---|
| `packages/tokenizers/punkt_tab.zip` | 77 | `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106` |
| `packages/tokenizers/punkt.zip` | 41 | `51c3078994aeaf650bfc8e028be4fb42b4a0d177d41c012b6a983979653660ec` |
| `packages/corpora/stopwords.zip` | 34 | `48c0e52d8b52546e827f53761fb30300c0ab94f70660d28bd65ba0a86270946b` |
| `packages/taggers/averaged_perceptron_tagger_eng.zip` | 3 | `6025f530624335c67d6547d44757b357b4e79bae030a0383e9887a92c1718f0b` |

NLTK data has no version number. These are the hashes that the earlier audit pinned in its
`scripts/fetch_nltk_data.py`, which downloads the files from
`https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/`. Each zip file unpacks into a folder named
after the package; unzip it into the category folder, for example `python -m zipfile -e punkt_tab.zip
case/deps/nltk_data/tokenizers/`.

## Python environment

The environment is not part of the case and the manifest does not cover it. It was a CPython 3.12.10 virtual
environment made with uv 0.11.24. It held the 60 packages of `deps/requirements.lock.txt`, at those versions, and
pip. The grader's checkers import nltk 3.10.0, emoji 2.15.0 and syllapy 0.8.0; the reference and its tests import
some of the others. To rebuild it, install exactly these versions into a Python 3.12 environment, for example with
`uv pip install -r deps/requirements.lock.txt`, and compare the installed names and versions with the file.

## Checking a rebuilt case

Copy `panel/CONFIGS.md` and `deps/requirements.lock.txt` from this folder into the rebuilt case and write its
`TASK.md` with the new workspace path. The manifest's line for `TASK.md` hashes the run's original text, which named
the run's own workspace path, so leave that line out of the check. Inside the rebuilt case folder:

```text
grep -v '  TASK.md$' MANIFEST.sha256 | sha256sum -c --quiet
```

It prints nothing when the other 423 files match. The manifest does not show extra files; the case has 425 files,
`MANIFEST.sha256` included.
