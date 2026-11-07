# ToyOrders: an RL reward for JSON extraction

ToyOrders is a structured-output task used for reinforcement learning: the policy reads a short customer email about
an order and replies with a JSON summary of the order. The reward function compares the summary with a reference and
returns a float in [0, 1], which the trainer uses as the rollout's reward.

## Files

| File | What it is |
|---|---|
| `prompt_template.txt` | the prompt the policy sees, with `{email}` replaced by the email |
| `orders.jsonl` | the 12 training orders: `order_id`, `email`, `reference` (customer, date, items, total) |
| `reward.py` | the reward function under audit, `reward(response, reference)`, with a command line for stored rollouts |
| `responses.jsonl` | 48 stored rollouts: 4 checkpoints of one training run, one rollout per order each |
| `MANIFEST.sha256` | sha256 of every other file in this directory |

There is no reference implementation of the reward.

## What the policy sees

`prompt_template.txt` with `{email}` replaced by the order's `email`, sent as the only user message:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
{email}
```

## Reward specification (from the task's design document)

1. Answer. Whitespace at both ends of the response is removed. If what remains is one fenced block, that is an
   opening line ` ```json ` or ` ``` ` (spaces may follow the tag), then the content, then a closing line ` ``` `,
   the answer is the block's content; otherwise the answer is all of what remains. The answer must be a single JSON
   object with nothing around it but whitespace; otherwise the reward is 0.0. JSON is parsed with Python's `json` module, which keeps the last value of
   a repeated key; numbers are read exactly (decimal fractions as `decimal.Decimal`).
2. Field scores, each from 0 to 1:
   - `customer`: 1 if it is a string equal to the reference name after removing whitespace at both ends and ignoring
     case (`str.casefold`), else 0.
   - `date`: 1 if it is a string exactly equal to the reference date, else 0.
   - `items`: 0 if it is not a list. Otherwise an answer item matches a reference item when it is an object whose
     `sku` is a string equal to the reference sku and whose `qty` is an integer equal to the reference quantity
     (other keys inside an item are ignored); each reference item can be matched by at most one answer item. The
     score is the number of matched reference items divided by the larger of the number of reference items and the
     number of answer items.
   - `total`: 1 if it is a number (not `true` or `false`) within 0.005 of the reference total, else 0.
3. Penalty: 0.1 for each top-level key other than the four above.
4. Reward = (sum of the four field scores) / 4 minus the penalty, clipped to [0, 1].

The reward function must return a float for every response, whatever text the policy produces.

## How the reward is run

The trainer imports `reward.py` and calls `reward(response, reference)` once per rollout, with `reference` loaded
from `orders.jsonl` by `json.loads(line, parse_float=Decimal)`. For stored rollouts, from this directory:

```text
python reward.py                                  # scores responses.jsonl
python reward.py --responses other.jsonl --out rewards.jsonl
```

It prints the mean reward and the number of full rewards (1.0) per checkpoint and, with `--out`, writes one JSON
line per rollout with its reward. A response file is JSON lines with at least `id`, `checkpoint`, `order_id` and
`response`.

## Stored rollouts

`responses.jsonl` holds one rollout per order from each of four checkpoints of one training run, `step-0000` (the
initial policy) to `step-0600`, sampled at temperature 1.0 with `max_tokens` 256. None was truncated. Fields: `id`,
`checkpoint`, `order_id`, `response`, `temperature`, `max_tokens`.

## Pinned inputs

Every file in this directory, by the sha256 in `MANIFEST.sha256`. The reward needs only the Python 3 standard
library.
