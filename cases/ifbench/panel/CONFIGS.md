# Panel generation settings

Each file `<folder>/<run>.jsonl` holds 300 lines, one per prompt of `data/train-00000-of-00001.parquet`, in the dataset's row order. Each line has the fields `key`, `prompt`, `response`, `raw_response`, `model`, `revision`, `run`, `finish_reason` and `num_tokens`.

- `raw_response` is the full completion. `response` is the text after the last `</think>` in the completion, with leading whitespace removed, or the whole completion when it contains no `</think>`.
- `finish_reason` is vLLM's finish reason; `length` means the completion reached the max new tokens.
- `num_tokens` is the number of generated tokens.

## Generation

- vLLM offline `LLM.chat`, engine seed 10060, context length = max new tokens + 1,024. One vLLM process per configuration ran the ordinary runs; the `bi_` runs came from a second process started with `VLLM_BATCH_INVARIANT=1`.
- Prompt rendering: one user message whose content is the dataset `prompt`, no system message added, rendered by the model's own chat template at the listed revision (vLLM `LLM.chat` defaults). Qwen3 models get the template argument `enable_thinking=False` (thinking off) or `enable_thinking=True` (thinking on); other models get no template arguments.
- Run names:
  - `greedy`: temperature 0, prompts submitted in dataset order.
  - `greedy_shuffled`: temperature 0, prompts submitted in a fixed random order (Python `random.Random(10060).shuffle`); the file is still in dataset order.
  - `greedy_repeat`: a second `greedy` run.
  - `bi_greedy`, `bi_greedy_shuffled`: `greedy` and `greedy_shuffled` in the process started with `VLLM_BATCH_INVARIANT=1`.
  - `sample<i>`: temperature 0.7, per-request seed 10060 + i.
  - No other sampling parameter (top-p, top-k, penalties) was set.
- Revision: the Hugging Face model commit used for generation; it is also in each line's `revision` field.

## Configurations

| Folder | Model id | Revision | Thinking | Max new tokens | vLLM | Prompt rendering | Run files (decoding) | Responses |
|---|---|---|---|---|---|---|---|---|
| `Qwen__Qwen2.5-7B-Instruct` | Qwen/Qwen2.5-7B-Instruct | a09a35458c702b33eeacc393d103063234e8bc28 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `allenai__Llama-3.1-Tulu-3-8B` | allenai/Llama-3.1-Tulu-3-8B | 666943798adbde0b1aff34626007e26986a3c107 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `marin-community__marin-8b-instruct` | marin-community/marin-8b-instruct | 0378f9c932bd64ca189d2f2ca5bd2fb076cba61d | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `allenai__OLMo-2-1124-7B-Instruct` | allenai/OLMo-2-1124-7B-Instruct | 470b1fba1ae01581f270116362ee4aa1b97f4c84 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `mistralai__Mistral-7B-Instruct-v0.3` | mistralai/Mistral-7B-Instruct-v0.3 | c170c708c41dac9275d15a8fff4eca08d52bab71 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `Qwen__Qwen3-8B` | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 | off | 1,024 | 0.30.0 | model chat template, one user turn, `enable_thinking=False` | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `Qwen__Qwen3-8B__thinking` | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 | on | 8,192 | not recorded | model chat template, one user turn, `enable_thinking=True` | greedy, greedy_shuffled, greedy_repeat (temperature 0) | 3 x 300 = 900 |
| `Qwen__Qwen2.5-14B-Instruct` | Qwen/Qwen2.5-14B-Instruct | cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `allenai__OLMo-2-1124-13B-Instruct` | allenai/OLMo-2-1124-13B-Instruct | 3a5c85baefbb1896a54d56fe2e76c0395627ddf4 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `microsoft__phi-4` | microsoft/phi-4 | 2db69c1c3e91a05d2c64a3185acfbaf36f744e25 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `Qwen__Qwen3-14B` | Qwen/Qwen3-14B | 40c069824f4251a91eefaf281ebe4c544efd3e18 | off | 1,024 | 0.30.0 | model chat template, one user turn, `enable_thinking=False` | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample11 (temperature 0.7, seed 10060+i) | 17 x 300 = 5,100 |
| `Qwen__Qwen3-14B__thinking` | Qwen/Qwen3-14B | 40c069824f4251a91eefaf281ebe4c544efd3e18 | on | 8,192 | not recorded | model chat template, one user turn, `enable_thinking=True` | greedy, greedy_shuffled, greedy_repeat (temperature 0) | 3 x 300 = 900 |
| `mistralai__Mistral-Small-24B-Instruct-2501` | mistralai/Mistral-Small-24B-Instruct-2501 | 9527884be6e5616bdd54de542f9ae13384489724 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample7 (temperature 0.7, seed 10060+i) | 13 x 300 = 3,900 |
| `Qwen__Qwen2.5-32B-Instruct` | Qwen/Qwen2.5-32B-Instruct | 5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample7 (temperature 0.7, seed 10060+i) | 13 x 300 = 3,900 |
| `allenai__OLMo-2-0325-32B-Instruct` | allenai/OLMo-2-0325-32B-Instruct | b96024342a77a69aa0dda815c3454a671f477463 | off | 1,024 | 0.30.0 | model chat template, one user turn | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample7 (temperature 0.7, seed 10060+i) | 13 x 300 = 3,900 |
| `Qwen__Qwen3-32B` | Qwen/Qwen3-32B | 9216db5781bf21249d130ec9da846c4624c16137 | off | 1,024 | 0.30.0 | model chat template, one user turn, `enable_thinking=False` | greedy, greedy_shuffled, greedy_repeat, bi_greedy, bi_greedy_shuffled (temperature 0); sample0-sample7 (temperature 0.7, seed 10060+i) | 13 x 300 = 3,900 |

Total: 16 configurations, 228 run files, 68,400 responses.

- `Qwen__Qwen2.5-7B-Instruct`: the ordinary runs came from two processes with the same settings: `greedy`, `greedy_shuffled` and `sample0`-`sample3` from the first, `greedy_repeat` and `sample4`-`sample11` from the second.
- The vLLM version was not recorded for the two thinking configurations.
