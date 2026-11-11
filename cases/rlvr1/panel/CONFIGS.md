# Panel configurations

Responses to the prompts of `data/rlvr1_instruction_following.jsonl`, generated with vLLM 0.11.0, torch 2.8.0 (+cu128) and transformers 4.57.1 under Python 3.12.3. Each model ran at its Hugging Face revision below. Row samples were drawn with a fixed seed; Qwen2.5-7B-Instruct and OLMo-2-1124-7B-Instruct answered the same 4,000 rows.

| Folder | Model | Revision | Run | Rows | Decoding | Token limit | vLLM `max_model_len` |
|---|---|---|---|---|---|---|---|
| `Qwen__Qwen3-4B-Instruct-2507` | Qwen/Qwen3-4B-Instruct-2507 | `cdbee75f17c01a7cc42f958dc650907174af0554` | `sample0` | all 11,817 | sampled, temperature 1.0, top-p 1.0 | 2,048 | 8,192 |
| `Qwen__Qwen3-4B-Instruct-2507` | Qwen/Qwen3-4B-Instruct-2507 | `cdbee75f17c01a7cc42f958dc650907174af0554` | `greedy` | 1,000 sampled rows | greedy | 2,048 | 8,192 |
| `Qwen__Qwen3-4B-Instruct-2507` | Qwen/Qwen3-4B-Instruct-2507 | `cdbee75f17c01a7cc42f958dc650907174af0554` | `greedy_repeat` | the same 1,000 rows | greedy; a rerun of `greedy` with the same settings | 2,048 | 8,192 |
| `Qwen__Qwen2.5-7B-Instruct` | Qwen/Qwen2.5-7B-Instruct | `a09a35458c702b33eeacc393d103063234e8bc28` | `sample0` | 4,000 sampled rows | sampled, temperature 1.0, top-p 1.0 | 2,048 | 8,192 |
| `allenai__OLMo-2-1124-7B-Instruct` | allenai/OLMo-2-1124-7B-Instruct | `470b1fba1ae01581f270116362ee4aa1b97f4c84` | `sample0` | the same 4,000 rows, 3,998 answered | sampled, temperature 1.0, top-p 1.0 | 2,048 (1,903 for one row) | 4,096 |
| `Qwen__Qwen3-4B-Thinking-2507__thinking` | Qwen/Qwen3-4B-Thinking-2507 | `768f209d9ea81521153ed38c47d515654e938aea` | `sample0` | 1,500 sampled rows | sampled, temperature 1.0, top-p 1.0, thinking | 8,192 | 14,336 |

The token limit is lowered for a row whose prompt leaves less room in the model's context. OLMo-2-1124-7B-Instruct's 4,096-token context left fewer than 512 tokens to answer 2 of its 4,000 rows, which were skipped: `6e2b59b7-2819-4687-9159-317bc8ba4aa7` and `86d409c7-4edf-44fd-8d37-f0cc97c01020`.

Each line of a run file is one response: `uuid` (the row's `extra_info.nemotron_ultra.uuid`), `raw_response` (the generated text), `model`, `revision`, `run`, `finish_reason` (`stop` or `length`), `num_tokens` (generated tokens) and `max_tokens` (the row's token limit).
