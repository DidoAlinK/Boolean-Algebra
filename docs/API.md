# Boolean Lab API

Base URL in development: `http://localhost:8000`
Interactive docs: `/docs` (Swagger) and `/openapi.json` (machine-readable, usable for TypeScript type generation).
All bodies are JSON. The server is stateless: nothing is stored, custom presets are sent with each request.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | `{"status": "ok"}` |
| GET | `/api/presets` | Built-in presets (array of `Preset`), the default (`universal`) first |
| POST | `/api/presets/validate` | Body: a `Preset`. Returns it normalised, or a 422 error explaining the problem |
| POST | `/api/analyze` | The main call, see below |

## POST /api/analyze

Request:

```json
{
  "expression": "x'y + xy'",
  "preset": "universal",
  "custom_preset": null,
  "circuit_mode": "expression"
}
```

| Field | Type | Notes |
|---|---|---|
| `expression` | string, 1 to 300 chars | what the user typed |
| `preset` | string, default `"universal"` | name of a built-in preset |
| `custom_preset` | `Preset` or null | if present it is used INSTEAD of `preset` |
| `circuit_mode` | `"expression"` / `"sop"` / `"pos"`, default `"expression"` | `expression`: circuit exactly as typed. `sop`: two-level AND-OR from the minterms. `pos`: two-level OR-AND from the maxterms |

Response 200, a real example for `x'y + xy'` (nothing removed, key order as returned):

```json
{
  "expression": "x'y + xy'",
  "structure": "OR(AND(NOT(x), y), AND(x, NOT(y)))",
  "preset": "universal",
  "variables": ["x", "y"],
  "function_label": "F(x, y)",
  "tree": {
    "type": "binary",
    "op": "OR",
    "left": {
      "type": "binary",
      "op": "AND",
      "left": {
        "type": "unary",
        "op": "NOT",
        "operand": {"type": "var", "name": "x"}
      },
      "right": {"type": "var", "name": "y"}
    },
    "right": {
      "type": "binary",
      "op": "AND",
      "left": {"type": "var", "name": "x"},
      "right": {
        "type": "unary",
        "op": "NOT",
        "operand": {"type": "var", "name": "y"}
      }
    }
  },
  "truth_table": {
    "variables": ["x", "y"],
    "rows": [
      {"index": 0, "inputs": [0, 0], "output": 0},
      {"index": 1, "inputs": [0, 1], "output": 1},
      {"index": 2, "inputs": [1, 0], "output": 1},
      {"index": 3, "inputs": [1, 1], "output": 0}
    ]
  },
  "minterms": [1, 2],
  "maxterms": [0, 3],
  "forms": {
    "sigma": {"indices": [1, 2], "text": "Σ m(1, 2)"},
    "pi": {"indices": [0, 3], "text": "Π M(0, 3)"},
    "sop": {
      "text": "x'y + xy'",
      "terms": [
        {"index": 1, "bits": "01", "term": "x'y"},
        {"index": 2, "bits": "10", "term": "xy'"}
      ]
    },
    "pos": {
      "text": "(x + y)(x' + y')",
      "terms": [
        {"index": 0, "bits": "00", "term": "(x + y)"},
        {"index": 3, "bits": "11", "term": "(x' + y')"}
      ]
    },
    "shorter": "sop"
  },
  "kmap": {
    "row_vars": ["x"],
    "col_vars": ["y"],
    "row_labels": ["0", "1"],
    "col_labels": ["0", "1"],
    "cells": [
      [{"index": 0, "value": 0}, {"index": 1, "value": 1}],
      [{"index": 2, "value": 1}, {"index": 3, "value": 0}]
    ],
    "corner": "x\\y"
  },
  "circuit": {
    "mode": "expression",
    "nodes": [
      {"id": "n0", "gate": null, "shape": null, "table": null, "nary": false, "inputs": [], "kind": "input", "label": "x", "col": 0, "row": 0.0},
      {"id": "n1", "gate": "NOT", "shape": "not", "table": [1, 0], "nary": false, "inputs": ["n0"], "kind": "gate", "label": "NOT", "col": 1, "row": 0.0},
      {"id": "n2", "gate": null, "shape": null, "table": null, "nary": false, "inputs": [], "kind": "input", "label": "y", "col": 0, "row": 1.0},
      {"id": "n3", "gate": "AND", "shape": "and", "table": [0, 0, 0, 1], "nary": true, "inputs": ["n1", "n2"], "kind": "gate", "label": "AND", "col": 2, "row": 0.0},
      {"id": "n4", "gate": "NOT", "shape": "not", "table": [1, 0], "nary": false, "inputs": ["n2"], "kind": "gate", "label": "NOT", "col": 1, "row": 1.0},
      {"id": "n5", "gate": "AND", "shape": "and", "table": [0, 0, 0, 1], "nary": true, "inputs": ["n0", "n4"], "kind": "gate", "label": "AND", "col": 2, "row": 1.0},
      {"id": "n6", "gate": "OR", "shape": "or", "table": [0, 1, 1, 1], "nary": true, "inputs": ["n3", "n5"], "kind": "gate", "label": "OR", "col": 3, "row": 0.5},
      {"id": "n7", "gate": null, "shape": null, "table": null, "nary": false, "inputs": ["n6"], "kind": "output", "label": "F", "col": 4, "row": 0.5}
    ],
    "edges": [
      {"source": "n0", "target": "n1", "port": 0, "ports": 1},
      {"source": "n1", "target": "n3", "port": 0, "ports": 2},
      {"source": "n2", "target": "n3", "port": 1, "ports": 2},
      {"source": "n2", "target": "n4", "port": 0, "ports": 1},
      {"source": "n0", "target": "n5", "port": 0, "ports": 2},
      {"source": "n4", "target": "n5", "port": 1, "ports": 2},
      {"source": "n3", "target": "n6", "port": 0, "ports": 2},
      {"source": "n5", "target": "n6", "port": 1, "ports": 2},
      {"source": "n6", "target": "n7", "port": 0, "ports": 1}
    ],
    "cols": 5,
    "rows": 2.0,
    "gate_count": 5,
    "output": "n7"
  },
  "warnings": []
}
```

### Field meanings

* `variables`: sorted alphabetically. **The first variable is the most significant bit of the row index.** For `F(x,y,z)`, row 6 is `x=1, y=1, z=0`. Letters are case-insensitive; if every letter typed is uppercase they come back uppercase (A, B), otherwise lowercase.
* `structure`: how the parser grouped the input, shown to teach precedence, e.g. `OR(AND(NOT(x), y), z)`.
* `tree`: the same as nested objects: `{"type":"var","name"}`, `{"type":"const","value"}`, `{"type":"unary","op","operand"}`, `{"type":"binary","op","left","right"}`.
* `truth_table.rows[i]`: `index` is `i`, `inputs` are bits in `variables` order, `output` is F. Up to 1024 rows (10 variables).
* `minterms` / `maxterms`: row indices where F is 1 / 0.
* `forms.sigma` / `forms.pi`: numeric lists with ready-made text, e.g. `Σ m(1, 2)` and `Π M(0, 3)`. An empty list renders as `Σ m()`.
* `forms.sop` / `forms.pos`: canonical (NOT minimised) sum of products and product of sums. `terms[k].index` links a term to its truth-table row and K-map cell, `terms[k].bits` is the row in binary. `text` is `"0"` for an empty SOP and `"1"` for an empty POS.
* `forms.shorter`: `"sop"` or `"pos"`, whichever list is shorter (SOP on a tie). Say "shorter", never "minimal".
* `kmap`: `null` when there are 0 variables or more than 4, and then `warnings` explains why. Otherwise rows and columns use Gray code (`00 01 11 10`) so neighbours differ in one variable. `cells[r][c]` is `{index, value}`, `index` links to the truth-table row. The map wraps around at the edges. `corner` is the label for the top-left cell, e.g. `x\yz`.
* `circuit`: `null` if it would be too large (then `warnings` explains). See the drawing contract below.
* `warnings`: human-readable strings, show them in a note box.

### Circuit drawing contract

* `nodes[]` is in dependency order (every node appears after its inputs). `kind` is `input`, `const`, `gate` or `output`.
* Gates: `gate` is the operator name (`AND`, `NOT`, `NAND`...), `shape` is a drawing hint (`and`, `or`, `not`, `xor`, `nand`, `nor`, `xnor`, or `box` for anything else, drawn as a labelled rectangle), `table` is its truth table, `nary` means it may have more than 2 inputs (AND/OR/XOR chains are merged into one multi-input gate).
* `inputs` lists source node ids in port order, first input = top port.
* `col` is the grid column (0 = inputs, last column = the single `output` node). `row` is the vertical slot in that column, a float already centred (0 to `rows - 1`). No two nodes share a cell. Every edge goes from a smaller `col` to a larger `col`.
* `edges[]`: `{source, target, port, ports}`: wire from the output of `source` to input number `port` (of `ports`) on `target`. One source can feed many targets (fan-out): draw a junction dot.
* Equal sub-expressions are shared (x' used twice is one NOT gate), so the circuit is a DAG, not a tree.
* Evaluating a circuit in the browser (for the interactive switches). Process `nodes` in order:

```ts
// values: Map<string, 0 | 1>
input  -> switch value of the variable named node.label
const  -> Number(node.label)
output -> value of node.inputs[0]
gate   -> const ins = node.inputs.map(id => values.get(id)!);
          if (node.table.length === 2) value = node.table[ins[0]];          // unary
          else { value = ins[0]; for (const x of ins.slice(1)) value = node.table[(value << 1) | x]; }
```

## Errors

Every error uses one envelope:

```json
{"error": {"code": "parse_error", "message": "missing ')'", "position": 5}}
```

| HTTP | `code` | When | Extra |
|---|---|---|---|
| 422 | `parse_error` | the expression is invalid | `position` is the **1-based character index** into the `expression` string that was sent, so a caret can be drawn under it (at the end of the input it equals length + 1) |
| 422 | `invalid_request` | bad body: empty or too long expression, bad `circuit_mode`, invalid preset definition | `message` names the field and the problem |
| 400 | `unknown_preset` | `preset` is not a built-in name | |

## Notation of the built-in `universal` preset

Variables are single letters, so `xy` means `x AND y` (implicit AND). 0 and 1 are constants. Word operators are case-insensitive and need spaces around them (`x nor y`). Symbols are matched longest-first (`~&` is one operator, not `~` then `&`). Higher precedence binds tighter. Truth tables are `[f(0,0), f(0,1), f(1,0), f(1,1)]` for binary operators and `[f(0), f(1)]` for NOT.

| Operator | Fixity | Symbols | Precedence | Assoc | Table |
|---|---|---|---|---|---|
| NOT | prefix | `!`  `~`  `¬`  `not` | 60 | left | `[1, 0]` |
| NOT | postfix | `'`  `’`  `′` | 60 | left | `[1, 0]` |
| AND | infix | `*`  `.`  `·`  `&`  `&&`  `∧`  `and` | 50 | left | `[0, 0, 0, 1]` |
| NAND | infix | `~&`  `↑`  `nand` | 50 | left | `[1, 1, 1, 0]` |
| XOR | infix | `^`  `⊕`  `xor` | 40 | left | `[0, 1, 1, 0]` |
| XNOR | infix | `⊙`  `~^`  `==`  `xnor` | 40 | left | `[1, 0, 0, 1]` |
| OR | infix | `+`  `|`  `||`  `∨`  `or` | 30 | left | `[0, 1, 1, 1]` |
| NOR | infix | `~|`  `↓`  `nor` | 30 | left | `[1, 0, 0, 0]` |
| IMP | infix | `->`  `=>`  `→`  `imp`  `implies` | 20 | right | `[1, 1, 0, 1]` |
| EQV | infix | `<->`  `↔`  `≡`  `eqv`  `iff` | 10 | left | `[1, 0, 0, 1]` |

Other built-in presets: `textbook` (course style, subset of the above, implicit AND on) and `programming` (C/Python style symbols, no implicit AND). Call `GET /api/presets` for exact contents.

## Preset format (built-in and custom)

```json
{
  "name": "my preset",
  "description": "optional",
  "implicit": "AND",
  "operators": [
    {"name": "NOT",  "fixity": "postfix", "symbols": ["'"],  "precedence": 60, "table": [1, 0]},
    {"name": "AND",  "fixity": "infix",   "symbols": ["*"],  "precedence": 50, "table": [0, 0, 0, 1], "nary": true, "shape": "and"},
    {"name": "OR",   "fixity": "infix",   "symbols": ["+"],  "precedence": 30, "table": [0, 1, 1, 1], "nary": true, "shape": "or"},
    {"name": "NIMP", "fixity": "infix",   "symbols": ["-/>", "nimp"], "precedence": 20, "assoc": "left", "table": [0, 0, 1, 0]}
  ]
}
```

| Field | Rules |
|---|---|
| `name` (preset) | 1 to 32 chars |
| `implicit` | optional, name of an infix operator used when two terms touch (`xy`) |
| `operators[].name` | letters, digits, underscore, starts with a letter, up to 16 chars. Two entries may share a name with different fixity (NOT as prefix `!` and postfix `'`) |
| `fixity` | `prefix`, `postfix` or `infix` |
| `symbols` | 1 to 16 entries, each up to 8 chars, unique across the whole preset. Either all ASCII letters, at least 2 (a word like `nimp`, matched case-insensitively), or no ASCII letters at all (`-/>`). No digits, spaces or brackets. A single letter is reserved for variables |
| `precedence` | integer 1 to 99, higher binds tighter. Built-ins: NOT 60, AND 50, XOR 40, OR 30, IMP 20, EQV 10 |
| `assoc` | `left` (default) or `right`, infix only |
| `table` | 2 values for prefix/postfix, 4 for infix, each 0 or 1 |
| `nary` | optional. Only for infix operators that are associative (AND, OR, XOR). Chains become one multi-input gate |
| `shape` | optional drawing hint, one of `and or not xor nand nor xnor box` (default `box`) |

At most 64 operators per preset. The frontend keeps custom presets in the browser (localStorage) and sends the selected one as `custom_preset` with every analyze call.

## Limits

Expression up to 300 characters, up to 10 variables, nesting up to 100 levels, circuits up to 400 nodes (otherwise `circuit` is `null` with a warning).
