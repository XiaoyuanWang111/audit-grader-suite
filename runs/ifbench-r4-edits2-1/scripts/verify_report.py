"""Rerun the fixture tests and every command that audit/AUDIT.md gives, check the printed verdicts,
hash the frozen files, and rewrite section 9 of AUDIT.md with the results.

Run from W:  NLTK_DATA=W/case/deps/nltk_data .venv/Scripts/python.exe audit/scripts/verify_report.py
"""
import datetime
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
PY = str(W / ".venv/Scripts/python.exe")
ENV = dict(os.environ, NLTK_DATA=str(W / "case/deps/nltk_data"), PYTHONIOENCODING="utf-8")
REPORT = W / "audit/AUDIT.md"

# (arguments to repro.py, substring the output must contain)
CHECKS = [
    ("count:conjunctions:ed138c62", "grader: pass"),
    ("count:keywords_multiple:ef66cefd", "grader: fail"),
    ("count:numbers:0151d9ec", "grader: fail"),
    ("count:numbers:8b94ccdd", "grader: fail"),
    ("count:pronouns:7c383df6", "grader: pass"),
    ("count:unique_word_count:8d1f1bd4", "grader: pass"),
    ("count:words_japanese:4e2f74db", "grader: pass"),
    ("custom:character_reverse:3414f40a", "grader: pass"),
    ("custom:word_reverse:1647f6d9", "grader: pass"),
    ("custom:csv_quotes:04299ef9", "grader: exception IndexError"),
    ("custom:csv_city:50634567", "grader: exception Error"),
    ("custom:csv_special_character:37c3ede3", "grader: pass"),
    ("custom:date_format_list:4044c581", "grader: pass"),
    ("custom:european_capitals_sort:7c1bd6bc", "grader: fail"),
    ("custom:mcq_count_length:9b728045", "grader: fail"),
    ("custom:mcq_count_length:b0ad9938", "grader: pass"),
    ("custom:sentence_alphabet:df10cf8d", "grader: fail"),
    ("format:emoji:576623f0", "grader: fail"),
    ("format:emoji:b02e212f", "grader: fail"),
    ("format:line_indent:6a29162b", "grader: fail"),
    ("format:line_indent:f198466c", "grader: fail"),
    ("format:list:310a74c6", "grader: pass"),
    ("format:list:bf1e2523", "grader: pass"),
    ("format:newline:fc6a9098", "grader: pass"),
    ("format:newline:f6c7651b", "grader: fail"),
    ("format:no_bullets_bullets:89b3ea33", "grader: fail"),
    ("format:no_bullets_bullets:d43bb2cf", "grader: pass"),
    ("format:options:e4dbcaf3", "grader: fail"),
    ("format:output_template:38bbf473", "grader: pass"),
    ("format:output_template:fe5a21db", "grader: pass"),
    ("format:parentheses:36e53364", "grader: pass"),
    ("format:quote_unquote:e6392a99", "grader: pass"),
    ("format:quote_unquote:9d94d30f", "grader: pass"),
    ("format:quotes:333cde68", "grader: pass"),
    ("format:quotes:c98bf891", "grader: fail"),
    ("format:sub-bullets:1f02301c", "grader: pass"),
    ("format:sub-bullets:db5643b9", "grader: fail"),
    ("format:sub-bullets:d473f339", "grader: pass"),
    ("format:thesis:676eb9b3", "grader: pass"),
    ("format:thesis:c4a67127", "grader: pass"),
    ("format:title_case:56cb87df", "grader: fail"),
    ("format:title_case:c5900440", "grader: fail"),
    ("ratio:sentence_balance:d6d61bf5", "grader: pass"),
    ("ratio:sentence_type:18b41e80", "grader: pass"),
    ("ratio:sentence_words:852f3edd", "grader: pass"),
    ("repeat:repeat_change:fad2c014", "grader: pass"),
    ("repeat:repeat_span:58490b7b", "grader: pass"),
    ("repeat:repeat_span:535a1668", "grader: fail"),
    ("repeat:repeat_span:cdf30836", "grader: fail"),
    ("sentence:alliteration_increment:09b864b9", "grader: pass"),
    ("words:alphabet:ad8812f7", "grader: fail"),
    ("words:alphabet:5e40f5d7", "grader: fail"),
    ("words:prime_lengths:e73b1050", "grader: fail"),
    ("words:repeats:f57b8624", "grader: pass"),
    ("words:no_consecutive:7c092686", "grader: fail"),
    ("words:last_first:4d7c3c92", "grader: fail"),
    ("words:consonants:e554994a", "grader: fail"),
    ("words:paragraph_last_first:1c5d48de", "grader: fail"),
    ("words:paragraph_last_first:7ab69715", "grader: fail"),
    ("words:last_first:d0c757b7", "grader: fail"),
    ("words:start_verb:eecfbb69", "grader: fail"),
    ("words:start_verb:d60aabf0", "grader: fail"),
    ("words:words_position:aaf6291a", "grader: fail"),
    ("words:words_position:f5c66cf4", "grader: fail"),
    ("sentence:keyword:61e6b0e1", "grader: fail"),
    ("words:last_first:f594e8a3", "grader: pass"),
    ("custom:reverse_newline:16842d1e", "grader: pass"),
    ("--panel Qwen__Qwen3-14B__thinking/greedy/52", "count:unique_word_count: grader strict: pass"),
    ("--panel Qwen__Qwen3-14B__thinking/greedy/52", "reasoning_never_closed=True"),
    ("--loose 0", "grader strict: fail; grader loose: pass"),
    ("--lstrip mistralai__Mistral-7B-Instruct-v0.3/bi_greedy/298",
     "grader on stored response: fail; grader without leading whitespace: pass"),
]
GREPS = [
    (["grep", "-n", r"mkdir\|setdefault\|nltk.download", "case/grader/IFBench/instructions.py",
      "case/grader/IFBench/instructions_util.py"], ["mkdir(exist_ok=True)", 'nltk.download("punkt", quiet=True)',
                                                    'nltk.download("punkt_tab", quiet=True)', 'nltk.download("stopwords", quiet=True)',
                                                    'nltk.download("averaged_perceptron_tagger_eng", quiet=True)']),
    (["grep", "-n", "load_dataset", "case/grader/IFBench/eval_instruct.py"],
     ['dataset: Dataset = load_dataset("allenai/IFBench_test", split="train")']),
]
FROZEN = ["audit/CONTRACTS.md", "audit/frozen/CONTRACTS_v1.md", "audit/frozen/dataset_rows.jsonl",
          "audit/frozen/dataset_row_sha256.tsv", "audit/frozen/instruction_templates.json", "audit/frozen/pip_freeze.txt",
          "audit/frozen/panel_stats.json", "audit/frozen/panel_verdicts.tsv.gz", "audit/frozen/panel_rep_graderreadings.tsv.gz",
          "audit/frozen/panel_tables.md", "audit/frozen/panel_tables_heldout.md", "audit/frozen/panel_numbers.json",
          "audit/frozen/panel_numbers_heldout.json", "audit/frozen/finding_shares.json", "audit/frozen/leading_ws_effect.json",
          "audit/frozen/disagreement_decomposition.json", "audit/frozen/stress_results.json",
          "audit/frozen/reftests_replacement_v4.json", "audit/frozen/reftests_grader.json", "audit/frozen/fixture_table.tsv",
          "audit/replacement/contract_grader.py", "audit/tests/fixtures_data.py"]


def sha(p):
    return hashlib.sha256((W / p).read_bytes()).hexdigest()


def main():
    lines = []
    ok_all = True
    t = subprocess.run([PY, "-m", "pytest", "audit/tests", "-q", "-p", "no:cacheprovider"], cwd=W, env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    summary = [l for l in t.stdout.splitlines() if "passed" in l or "failed" in l][-1:]
    pytest_ok = t.returncode == 0
    ok_all &= pytest_ok
    lines.append(f"- Fixture tests (`python -m pytest audit/tests -q`): {summary[0] if summary else t.stdout[-200:]} "
                 f"({'OK' if pytest_ok else 'FAILED'}).")
    # coverage: every repro.py argument in the report is checked
    text = REPORT.read_text(encoding="utf-8")
    body = text.split("## 9.")[0]
    mentioned = set(re.findall(r"repro\.py (--(?:panel|lstrip|loose) [^`\s<]+|[a-z_]+:[a-z_\-]+:[0-9a-f]{8})", body))
    mentioned |= set(re.findall(r"`([a-z_]+:[a-z_\-]+:[0-9a-f]{8})`", body))
    checked = {a for a, _ in CHECKS}
    missing = sorted(m for m in mentioned if m not in checked)
    if missing:
        ok_all = False
    lines.append(f"- Commands in this report: {len(mentioned)} distinct `repro.py` targets, all covered by the check list"
                 if not missing else f"- NOT COVERED: {missing}")
    fails = []
    for args, want in CHECKS:
        r = subprocess.run([PY, "audit/scripts/repro.py"] + args.split(), cwd=W, env=ENV, capture_output=True, text=True,
                           encoding="utf-8")
        if want not in r.stdout:
            fails.append((args, want, r.stdout[-300:] + r.stderr[-300:]))
    ok_all &= not fails
    lines.append(f"- `repro.py` checks: {len(CHECKS) - len(fails)} of {len(CHECKS)} print the verdict the report states.")
    for a, w_, out in fails:
        lines.append(f"  - MISMATCH `{a}` expected `{w_}`; got: {out!r}")
    for cmd, wants in GREPS:
        r = subprocess.run(cmd, cwd=W, capture_output=True, text=True, encoding="utf-8")
        miss = [x for x in wants if x not in r.stdout]
        ok_all &= not miss
        lines.append(f"- `{' '.join(cmd[:2])} ... {cmd[-1]}`: " + ("prints the lines the report cites." if not miss else f"MISSING {miss}"))
    lines.append("")
    lines.append("sha256 of frozen and versioned files:")
    lines.append("")
    for p in FROZEN:
        lines.append(f"- `{p}` `{sha(p)}`")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = text.split("## 9.")[0]
    new9 = (f"## 9. Verification and frozen-file hashes\n\nRun {stamp} by `audit/scripts/verify_report.py` "
            f"(result: {'all checks pass' if ok_all else 'SEE MISMATCHES'}).\n\n" + "\n".join(lines) + "\n")
    REPORT.write_text(head + new9, encoding="utf-8", newline="\n")
    print(new9)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
