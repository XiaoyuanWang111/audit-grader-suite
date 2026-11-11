# Sources of this case

Every file of this folder comes from one of the sources below. `TASK.md`, `panel/CONFIGS.md` and this file were written for the case; `deps/requirements.lock.txt` is the output of `uv pip freeze` for the Python environment; `MANIFEST.sha256` lists the sha256 of every other file.

## Grader and reference

Each file is the git blob named in the table, byte for byte (each copy's blob hash was recomputed and matches).

- Marin: github.com/marin-community/marin, commit `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`.
- NVIDIA: github.com/abukharin-nv/verifiable-instructions, commit `f46a5ac87b1400a4f8973039844b6be9b56e3faf`, every tracked file.

| File | Repository | Path in the repository | Git blob | Bytes |
|---|---|---|---|---|
| `grader/experiments/post_training/task_curation/datasets/nemotron_ultra/conversation.py` | Marin | `experiments/post_training/task_curation/datasets/nemotron_ultra/conversation.py` | `91d37ef9325e6f4fa6f8c230270eb2c091d2b84e` | 854 |
| `grader/experiments/post_training/task_curation/datasets/nemotron_ultra/graders.py` | Marin | `experiments/post_training/task_curation/datasets/nemotron_ultra/graders.py` | `b8a1271fcb49cf3aee67805b5d5f475987804bad` | 48,135 |
| `grader/verifyit/__init__.py` | Marin | `lib/verifyit/src/verifyit/__init__.py` | `030cb44b2f96732cf2094f28f7f5e16dea296410` | 147 |
| `grader/verifyit/adapters/__init__.py` | Marin | `lib/verifyit/src/verifyit/adapters/__init__.py` | `250e0450f73abb98a00c221695188860d086626d` | 148 |
| `grader/verifyit/adapters/completion.py` | Marin | `lib/verifyit/src/verifyit/adapters/completion.py` | `6bce38458d6d64fb1c2783b090bc5faa809adaff` | 1,458 |
| `grader/verifyit/adapters/evalchemy_jee.py` | Marin | `lib/verifyit/src/verifyit/adapters/evalchemy_jee.py` | `da1750644f856f094958248846ce827ee471961f` | 4,464 |
| `grader/verifyit/adapters/evalchemy_nupa.py` | Marin | `lib/verifyit/src/verifyit/adapters/evalchemy_nupa.py` | `b1b8805c35ddc944e5f47b3e08583adc6f17bda5` | 3,258 |
| `grader/verifyit/adapters/harbor_answers.py` | Marin | `lib/verifyit/src/verifyit/adapters/harbor_answers.py` | `b513abce5984aa1959715903c60186d9057e4117` | 5,025 |
| `grader/verifyit/adapters/harbor_arc_agi_2.py` | Marin | `lib/verifyit/src/verifyit/adapters/harbor_arc_agi_2.py` | `c64c37b6786fa87ade274225a1ad2a5d55483bdb` | 3,086 |
| `grader/verifyit/adapters/harbor_runtime.py` | Marin | `lib/verifyit/src/verifyit/adapters/harbor_runtime.py` | `95af8bb78f08370481c994e735ae8f785a968a55` | 3,239 |
| `grader/verifyit/adapters/harness_agieval.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_agieval.py` | `61d948e5dca290887d3f342953b0eda92ba8bf12` | 4,640 |
| `grader/verifyit/adapters/harness_babilong.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_babilong.py` | `67e80cce18e4eea55761ab1d2e37440aa131a785` | 4,544 |
| `grader/verifyit/adapters/harness_crows.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_crows.py` | `0c3eb0c8a6cd9efc93f548e993f4e42fd6511452` | 5,702 |
| `grader/verifyit/adapters/harness_drop.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_drop.py` | `e9f707d5e0a33948940077a606799b3ada8d930e` | 6,279 |
| `grader/verifyit/adapters/harness_math_literal.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_math_literal.py` | `6ce1483b3a19eadfeba3454c430af8f281261118` | 7,801 |
| `grader/verifyit/adapters/harness_mmmu.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_mmmu.py` | `e481af8f98e803198f55d8f580130e2487ddb7ee` | 8,991 |
| `grader/verifyit/adapters/harness_native.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_native.py` | `8b1ddf212206777aec53f463bc1058146255099b` | 12,347 |
| `grader/verifyit/adapters/harness_probability.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_probability.py` | `d44fdd8e2712e0d2862f427f2c8e05585c98e7f7` | 5,517 |
| `grader/verifyit/adapters/harness_profiles.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_profiles.py` | `23d964fcce8d74a9745e11c86aba48ab7310e124` | 6,730 |
| `grader/verifyit/adapters/harness_rolling.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_rolling.py` | `859eb0c1e79dd3afb5fef260b3b7fff6686a9156` | 4,245 |
| `grader/verifyit/adapters/harness_runtime.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_runtime.py` | `c7a349e761f3e57dc4209c4da231eb001a76e95c` | 12,433 |
| `grader/verifyit/adapters/harness_validation.py` | Marin | `lib/verifyit/src/verifyit/adapters/harness_validation.py` | `1ea110de4a06250f4720d49c94961fd71957aace` | 4,794 |
| `grader/verifyit/adapters/lm_eval.py` | Marin | `lib/verifyit/src/verifyit/adapters/lm_eval.py` | `2fb1ee4a4fdaaa29635ca2f1754efe4181495c0a` | 3,109 |
| `grader/verifyit/adapters/skyrl.py` | Marin | `lib/verifyit/src/verifyit/adapters/skyrl.py` | `9783b3b957f72553b26d7920810d16f828fc8fb8` | 8,877 |
| `grader/verifyit/adapters/skyrl_qa.py` | Marin | `lib/verifyit/src/verifyit/adapters/skyrl_qa.py` | `b2ef6880a3bb6806f7d2530cb422fd1d7924f51b` | 1,703 |
| `grader/verifyit/candidate.py` | Marin | `lib/verifyit/src/verifyit/candidate.py` | `8962914124c5a3545499e745d83417cbee07e710` | 4,181 |
| `grader/verifyit/candidate_file.py` | Marin | `lib/verifyit/src/verifyit/candidate_file.py` | `3b0a9a9b2a9db45f6ef2f556700ab77c9c6eb8dd` | 1,386 |
| `grader/verifyit/closure_scoring.py` | Marin | `lib/verifyit/src/verifyit/closure_scoring.py` | `01b7556cc23a66db10b70079fd3ab7d055b847a3` | 6,589 |
| `grader/verifyit/execution/README.md` | Marin | `lib/verifyit/src/verifyit/execution/README.md` | `1a4132ff3b822ffa2af6355222e2fa3220ccb491` | 430 |
| `grader/verifyit/execution/__init__.py` | Marin | `lib/verifyit/src/verifyit/execution/__init__.py` | `93ac23bc855342c53167ee6bc496b36265291098` | 129 |
| `grader/verifyit/execution/command.py` | Marin | `lib/verifyit/src/verifyit/execution/command.py` | `ff6555cb677359dec4d9427cdcff8fa8b711905d` | 1,941 |
| `grader/verifyit/execution/worker.py` | Marin | `lib/verifyit/src/verifyit/execution/worker.py` | `274de977d3f4057232f3b9b81ea722cdba0d8e9f` | 2,698 |
| `grader/verifyit/file_ops/__init__.py` | Marin | `lib/verifyit/src/verifyit/file_ops/__init__.py` | `767af26669d54cb23f4f56e28cbe8da6c232c848` | 129 |
| `grader/verifyit/file_ops/read.py` | Marin | `lib/verifyit/src/verifyit/file_ops/read.py` | `422d567866956ffd6523c15d30f9b193c83afaec` | 1,702 |
| `grader/verifyit/file_ops/restore.py` | Marin | `lib/verifyit/src/verifyit/file_ops/restore.py` | `9577b2d5168f74c7c26d3de7dda2d2d29da54da8` | 861 |
| `grader/verifyit/grade.py` | Marin | `lib/verifyit/src/verifyit/grade.py` | `0cd03539b3d43049655e6f3e7b59da5bca0df270` | 15,728 |
| `grader/verifyit/instruction_observations.py` | Marin | `lib/verifyit/src/verifyit/instruction_observations.py` | `71990351be3c13cde98dc0c20f6c3580b156b660` | 18,743 |
| `grader/verifyit/json_comparison.py` | Marin | `lib/verifyit/src/verifyit/json_comparison.py` | `b6afe38c3a2f3a99b0fec9b46913d652d9f3b38b` | 1,734 |
| `grader/verifyit/json_objects.py` | Marin | `lib/verifyit/src/verifyit/json_objects.py` | `9b92546fc494835023f32bb750d5f12b5bc8e933` | 396 |
| `grader/verifyit/modes/README.md` | Marin | `lib/verifyit/src/verifyit/modes/README.md` | `fee9f01d3aed451029db9d0a84f06c66266749c4` | 1,044 |
| `grader/verifyit/modes/__init__.py` | Marin | `lib/verifyit/src/verifyit/modes/__init__.py` | `5185414ea13f1e4ea6ef4de04805c0615d461cbb` | 167 |
| `grader/verifyit/modes/extract.py` | Marin | `lib/verifyit/src/verifyit/modes/extract.py` | `57e9707f1eb0f34a864ef2dac032e05d1e5b3a7b` | 3,650 |
| `grader/verifyit/modes/grade_csv.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_csv.py` | `ee8679fb765255f6b130fcce2f6d14685614f8a3` | 2,474 |
| `grader/verifyit/modes/grade_exact.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_exact.py` | `e801b88742425623575784f855872dba15dd75d8` | 10,523 |
| `grader/verifyit/modes/grade_gotest.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_gotest.py` | `eaa63de7831ac0eed1627c7d8b89b30879052580` | 3,672 |
| `grader/verifyit/modes/grade_ifeval.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_ifeval.py` | `a2481c0b9f4c168158215f711e12d05c219eb48a` | 3,936 |
| `grader/verifyit/modes/grade_json_schema.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_json_schema.py` | `fa5b70155f2a671002cf5870a0902dd6693304d1` | 6,488 |
| `grader/verifyit/modes/grade_judge.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_judge.py` | `3cb9b3104c8b5955870ea65d4c653f845e328f12` | 31,898 |
| `grader/verifyit/modes/grade_junit.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_junit.py` | `a64214b7df7ec2737c39fb9f71a773f5e53c0789` | 4,453 |
| `grader/verifyit/modes/grade_math.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_math.py` | `af6e7e3ca0428a74329df5bda512cb6eecd5a430` | 20,641 |
| `grader/verifyit/modes/grade_mcq.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_mcq.py` | `c00ba7d6541ef60f2dfdf34fa7781b7e73210275` | 7,434 |
| `grader/verifyit/modes/grade_nl2bash.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_nl2bash.py` | `6a322cf9952986f2a78a4520a15333d8db1b2178` | 1,477 |
| `grader/verifyit/modes/grade_predicted_action.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_predicted_action.py` | `53079180c9613cbc4527153a320c9dddfd4d38d9` | 3,720 |
| `grader/verifyit/modes/grade_pytest.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_pytest.py` | `1e25b731bbd48ec08b57ce51dcc3f6f23e233d46` | 20,693 |
| `grader/verifyit/modes/grade_reasoning_gym.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_reasoning_gym.py` | `bb49fd898330a357c2b1f7b1cbc28b6c015a3240` | 6,043 |
| `grader/verifyit/modes/grade_script.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_script.py` | `b80badb8cc905557d8e3fdc1e572c5202a1a1cca` | 10,495 |
| `grader/verifyit/modes/grade_stdio.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_stdio.py` | `323b404a39fea64d4fa46e99dbe71ef2f2221d0c` | 8,946 |
| `grader/verifyit/modes/grade_structure_closure.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_structure_closure.py` | `2965162a271b1475cc4738085313586dce8e76a8` | 2,265 |
| `grader/verifyit/modes/grade_structured_exact.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_structured_exact.py` | `7cb01cad6df03a9f5ed5db5d1c526d9564cc4a6e` | 1,425 |
| `grader/verifyit/modes/grade_xml.py` | Marin | `lib/verifyit/src/verifyit/modes/grade_xml.py` | `02961068b877ca9f2b349fafdee1f04e5ec6fdda` | 2,672 |
| `grader/verifyit/modes/ifeval.py` | Marin | `lib/verifyit/src/verifyit/modes/ifeval.py` | `575f2a453f75531db3486c0e9b83345dc69ae16e` | 25,642 |
| `grader/verifyit/modes/run.py` | Marin | `lib/verifyit/src/verifyit/modes/run.py` | `cb00703e070533dcb6b7b4e0976e4a671f08d054` | 2,887 |
| `grader/verifyit/numeric.py` | Marin | `lib/verifyit/src/verifyit/numeric.py` | `aed3729f0252b1edf6b1dd3dd3ab1648aaa09dba` | 3,585 |
| `grader/verifyit/preparation/__init__.py` | Marin | `lib/verifyit/src/verifyit/preparation/__init__.py` | `1123a6a7f9063ed1950e5d3b0142e9110587d3f7` | 151 |
| `grader/verifyit/preparation/errors.py` | Marin | `lib/verifyit/src/verifyit/preparation/errors.py` | `43fd0e017c9d2aac9beb2282b8f4cb1ee245c6cb` | 863 |
| `grader/verifyit/preparation/sqlite.py` | Marin | `lib/verifyit/src/verifyit/preparation/sqlite.py` | `8484c48e8e3f921de28e5ab7046e215194eb4b24` | 2,148 |
| `grader/verifyit/preparation/text.py` | Marin | `lib/verifyit/src/verifyit/preparation/text.py` | `35d0bedb49d01c05794473d70f751122fcfcf5c9` | 4,675 |
| `grader/verifyit/spec.py` | Marin | `lib/verifyit/src/verifyit/spec.py` | `d7863d447c8b4fd9fb40f57d8d127e93a8eaf2fa` | 18,149 |
| `grader/verifyit/structure_closure.py` | Marin | `lib/verifyit/src/verifyit/structure_closure.py` | `3c776f4fbee43d0eeb20220d95632e9d0372a3e6` | 14,136 |
| `grader/verifyit/test_support.py` | Marin | `lib/verifyit/src/verifyit/test_support.py` | `ed1feb80d0458dad5c05e02b313d61b4b5f3e3ad` | 1,760 |
| `grader/verifyit/tool_call_markup.py` | Marin | `lib/verifyit/src/verifyit/tool_call_markup.py` | `2295ac4b1904cd4fbe702b60534c679d61de35c6` | 4,139 |
| `reference/skyrl_gym/__init__.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/__init__.py` | `5abc8e53e9ba82cf772263864b27a128711e06c7` | 67 |
| `reference/skyrl_gym/envs/__init__.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/__init__.py` | `2fc6e449f9a63dcef2a1fea25b2c7157125f630f` | 55 |
| `reference/skyrl_gym/envs/aime/utils.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/aime/utils.py` | `6848937295f251e2d7e1888a8680e825d920f575` | 17,258 |
| `reference/skyrl_gym/envs/instruction_verifyit.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/instruction_verifyit.py` | `6c441f63851ad7d257054e1e9dc1f778314033a6` | 19,942 |
| `reference/skyrl_gym/envs/nemotron_ultra/__init__.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/nemotron_ultra/__init__.py` | `b3745cff6cd5dd5b5244a19698cfa50d5210a9e3` | 1,649 |
| `reference/skyrl_gym/envs/nemotron_ultra/answer_extraction.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/nemotron_ultra/answer_extraction.py` | `7e88cf74d5013dd85eab460a6bf92f133ad74f43` | 1,587 |
| `reference/skyrl_gym/envs/nemotron_ultra/instruction_following.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/nemotron_ultra/instruction_following.py` | `969e81185985215d885661b58a4c75455e445301` | 4,029 |
| `reference/skyrl_gym/envs/nemotron_ultra/instruction_references.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/envs/nemotron_ultra/instruction_references.py` | `775b04ba34e3cd52047a33776be3b65f49d74e67` | 2,510 |
| `reference/skyrl_gym/nemotron_tasks.py` | Marin | `vendor/skyrl/skyrl-gym/skyrl_gym/nemotron_tasks.py` | `98a958eb41cb6dde9b2892d6e30a9283397f4511` | 23,332 |
| `reference/verifiable-instructions/.gitignore` | NVIDIA | `.gitignore` | `4e442df3e75227b2ad9ff7b9966a8cefe13d46ad` | 1,841 |
| `reference/verifiable-instructions/README.md` | NVIDIA | `README.md` | `3e6d60b0f50029d908642a0167f2e2d957aaa0d9` | 2,560 |
| `reference/verifiable-instructions/requirements.txt` | NVIDIA | `requirements.txt` | `0f388187ce81ed55e52068b3471718afe78eceb0` | 64 |
| `reference/verifiable-instructions/setup.py` | NVIDIA | `setup.py` | `a99abc3fd985907f6c3f35a06737502ab20b45ef` | 1,159 |
| `reference/verifiable-instructions/verifiable_instructions/__init__.py` | NVIDIA | `verifiable_instructions/__init__.py` | `1297f5a2fd0607e11506c2ab1423ebd40f8f94a4` | 475 |
| `reference/verifiable-instructions/verifiable_instructions/instructions.py` | NVIDIA | `verifiable_instructions/instructions.py` | `253ec6af3496ffc22ad1a30403566b312033638a` | 98,442 |
| `reference/verifiable-instructions/verifiable_instructions/instructions_registry.py` | NVIDIA | `verifiable_instructions/instructions_registry.py` | `bdfe9c097606f4a7ef7649b4c7a09e4d31bf71c5` | 16,126 |
| `reference/verifiable-instructions/verifiable_instructions/instructions_util.py` | NVIDIA | `verifiable_instructions/instructions_util.py` | `60cdc6b1fe6d149825f95ac8b6e9da8a8e7c9cb9` | 25,807 |
| `reference/verifiable-instructions/verifiable_instructions/synthesis.py` | NVIDIA | `verifiable_instructions/synthesis.py` | `396bebba8937b392fdcaa3a66a5ce63ec5d8e328` | 6,397 |

## Data

`data/rlvr1_instruction_following.jsonl` (28,965,128 bytes, sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159`) holds the rows of huggingface.co/datasets/open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 at revision `600262dd37891b86075a80517e61dbfb105d7cbe`, file `data/train.parquet` (84,403 rows, sha256 `fde7259ad17170b6a57292ea85fdd20d9a2428b078cc3aa67cdeab8155fc0b1b`), whose `extra_info.nemotron_ultra.agent` is `instruction_following_simple_agent`: 11,817 rows, in file order. Each line is one row with all five columns, read with pyarrow and written with `json.dumps(row, ensure_ascii=False)`; no field is added, removed or changed.

## Panel

The run files of the panel's generation run (`gen/<folder>/<run>.jsonl`), one case file per run file under the same folder and file name. Each line is the source line's JSON object without the fields `response` and `reasoning_closed`, which the generation script derived from `raw_response`, written again with `json.dumps(record, ensure_ascii=False)`; with no field removed, that call reproduces every source line byte for byte. The generation manifests are not included; `panel/CONFIGS.md` gives their settings.

| File | Responses | sha256 | sha256 of the source file |
|---|---|---|---|
| `panel/Qwen__Qwen2.5-7B-Instruct/sample0.jsonl` | 4,000 | `0dd1b738749f2a69ecb320629b7becdb048c1ae9a846d21b452a02b8531a1dcc` | `29b6d727231a58887bdc52f239fa4a1fe9c9312376a6bb55004f26c7fba0fff7` |
| `panel/Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl` | 1,000 | `558f73839c5786146aacf7c0d623178e4b639e82e25a8b675d7d38ce0229bf97` | `8a683ee8dc639e27df89e64f2c45eacdee2ad5424cacab30af68f9111d005f02` |
| `panel/Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl` | 1,000 | `ad0910da8398f7e5c44a32b4ee870db644a136b3130d9854ae24b4d9d91f1a05` | `913c8e2230bb198009815ba3bc342e5bd9c1d434527efa7cde8292ed360c1e7e` |
| `panel/Qwen__Qwen3-4B-Instruct-2507/sample0.jsonl` | 11,817 | `b343de37464790d0cd7be7e6441aecf2b645235c54df2f031a9aaa7c4596ef78` | `e0eabdf43db157bf4cab4b1ca0c75f44c6f06d770b353f41f98d0bab368e0c44` |
| `panel/Qwen__Qwen3-4B-Thinking-2507__thinking/sample0.jsonl` | 1,500 | `c619fa0bbc2b01c814825976a7d7c3813e80c5dc34852331cc37b555c5eccd7d` | `31a62cc1131ba6e5fc3785601ee8e53c413f7d0149fa5b4365b6b0c1e5d2c16b` |
| `panel/allenai__OLMo-2-1124-7B-Instruct/sample0.jsonl` | 3,998 | `bd39b38334cceecb9e0cc274dba6e4c7f40de4c6ee0784bb7ddd6b77c74274f0` | `08375c9578f28a396f602017983ffc754a65f1a54911287d08c8bbcee4159292` |

## NLTK data

The 77 files under `deps/nltk_data/tokenizers/punkt_tab/` are the contents of the zip file of NLTK's `punkt_tab` package, sha256 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`, unzipped unchanged (the zip's CRC of each file was checked on extraction). NLTK data has no version number; the hash identifies the file.

## Python environment

The environment is the folder `.venv` next to this folder; the manifest does not cover it. It is a CPython 3.12.10 virtual environment made with uv 0.11.24, with the 27 packages of `deps/requirements.lock.txt` at those versions. `marin-verifyit` and `verifiable-instructions` are installed from git at the two commits above, non-editable. Its base interpreter in `.venv/base/` is a copy of a CPython 3.12.10 installation for Windows: the interpreter and its DLLs, and the standard library without `Lib/test` and `Lib/site-packages`.
