# API addendum: simplify, body limit, rate limits (append to docs/API.md)

## POST /api/simplify
Request: `{"expression": "...", "preset": "universal", "custom_preset": null}` (same preset rules as /api/analyze).
Expression: 1 to 2000 characters (`BOOLEAN_LAB_MAX_SIMPLIFY_LENGTH`), up to 12 variables. The result is always written in textbook notation (`x'`, `+`, `xy`), whatever preset the input used.

Response 200 (abridged, for `a + a'b`):
```json
{
  "expression": "a + a'b", "parsed": "a + a'b", "result": "a + b", "variables": ["a", "b"],
  "start_literals": 3, "result_literals": 2, "step_count": 1,
  "steps": [{
    "number": 1, "rule": "T4a", "rule_name": "Half-absorption", "equation": "x + x'·y = x + y",
    "on_sheet": true, "dual": "T4b", "phase": "reduce", "direction": "forward",
    "also": [], "explain": "...", "focus_before": "a + a'b", "focus_after": "a + b",
    "before_span": [0, 7], "after": "a + b", "after_span": [0, 5], "literals": 2
  }],
  "routes": [{"name": "as is, then factor", "status": "ok", "reason": null, "literals": 2, "steps": 1, "chosen": true}],
  "verified": true, "stopped": null, "warnings": []
}
```
* `rule`: `P1a`..`P5b`, `T1a`..`T6b` from the course sheet (a = the "+" version, b = its dual). Extra ids not on the sheet: `INV` (double complement), `NOT01` (complement of 0/1), `DEF` (XOR/NAND/... written with AND/OR/NOT; custom operators are defined from their truth table). `on_sheet` is false for these.
* `also`: supporting P2/P3 used to bring terms together before the rule applies.
* `direction: "backward"`: a distributive law read right to left (factoring).
* `phase`: `definitions`, `negations`, `reduce`, `expand` (multiplying out), `factor`.
* `before_span` indexes the text BEFORE the step (previous step's `after`, or `parsed` for step 1); `after_span` indexes `after`. Offsets are in characters.
* `routes`: the strategies tried (as is / multiply out to SOP / multiply out to POS); the one with fewest written variables is shown. `status: "gave_up"` means that route hit a limit.
* `verified`: the result was compared with the original on every truth-table row. If this ever fails the server answers 500 `check_failed`.
* `stopped`: `time`, `steps` (300) or `size` (3000 nodes) when work was cut short. The result is still correct, only possibly not fully simplified.
* The result is simplified, NOT proven minimal.

## GET /api/simplify/rules
The rule sheet: array of `{id, name, equation, dual, on_sheet, note}`.

## Limits
| What | Default | Answer | Env override |
|---|---|---|---|
| Request body | 32 KB | 413 `payload_too_large` | `BOOLEAN_LAB_MAX_BODY_BYTES` |
| /api/simplify | 15 per 60 s per address | 429 `rate_limited` + `retry_after` + `Retry-After` header | `BOOLEAN_LAB_RATE_SIMPLIFY` |
| /api/analyze | 120 per 60 s | 429 | `BOOLEAN_LAB_RATE_ANALYZE` |
| /api/synthesize | 60 per 60 s | 429 | `BOOLEAN_LAB_RATE_SYNTHESIZE` |
| other /api/ | 240 per 60 s | 429 | `BOOLEAN_LAB_RATE_OTHER` |
| Simplifications at once | 2 | 503 `busy` | `BOOLEAN_LAB_SIMPLIFY_PARALLEL` |
| Time per simplification | 3 s | partial result, `stopped: "time"` | `BOOLEAN_LAB_SIMPLIFY_SECONDS` |

Counters are per process, in memory (see `app/limits.py`). Set `BOOLEAN_LAB_TRUST_PROXY=1` only behind exactly one reverse proxy that appends `X-Forwarded-For`.

New error codes: `rate_limited`, `payload_too_large`, `busy`, `too_complex` (422), `check_failed` (500).
