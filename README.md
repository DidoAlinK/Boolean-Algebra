# Boolean Lab

A web tool for first-year CS students (Machine Structure course). Type a boolean function and get, instantly:

* the **truth table**
* the **canonical forms**: Σm, ΠM, SOP, POS
* the **Karnaugh map** (1 to 4 variables)
* the **logic circuit**, drawn, zoomable, with clickable input switches
* the reverse direction: draw a **truth table and get the function** (Table → Function)

Built by Ali (CS student, ENSIA) as a learning project and as a real tool for classmates. Feedback from real users is part of the goal.

```
x'y + xy'   →   Σ m(1, 2)   |   Π M(0, 3)   |   x'y + xy'   |   (x + y)(x' + y')   |   K-map   |   circuit
```

---

## Table of contents

1. [Project scope](#1-project-scope)
2. [Decisions and why](#2-decisions-and-why)
3. [How AI was used](#3-how-ai-was-used)
4. [Requirements and dependencies](#4-requirements-and-dependencies)
5. [Install and run](#5-install-and-run)
6. [How to use the app](#6-how-to-use-the-app)
7. [Project structure, file by file](#7-project-structure-file-by-file)
8. [Key functions and why they exist](#8-key-functions-and-why-they-exist)
9. [API reference](#9-api-reference)
10. [Conventions that must not change](#10-conventions-that-must-not-change)
11. [Known gotchas](#11-known-gotchas)
12. [Testing](#12-testing)
13. [Deployment](#13-deployment)
14. [Extending the project](#14-extending-the-project)
15. [Roadmap and what is not built](#15-roadmap-and-what-is-not-built)

---

## 1. Project scope

### In scope (built)

| Feature | Details |
|---|---|
| Expression input | Single-line input, example chips, an operator palette, debounced live analysis |
| Variables | Single letters `a` to `z`, case-insensitive, sorted alphabetically, always shown lowercase, up to **12 per function** |
| Operators | NOT, AND, NAND, XOR, XNOR, OR, NOR, IMP, EQV (NOT has a prefix and a postfix form) |
| Presets | 3 built-in notation presets (`universal`, `textbook`, `programming`) plus **user-defined presets** with no code, validated live by the server |
| Truth table | Up to 4096 rows (12 variables), virtualised in the browser |
| Forms | Σm, ΠM, canonical SOP, canonical POS, and a "shorter" badge (fewer terms, not "minimal") |
| K-map | 1 to 4 variables, Gray code, wraps at the edges |
| Circuit | 3 modes (as typed, two-level SOP, two-level POS), shared gates, multi-input gates, routed wires, interactive switches, SVG and PNG export |
| Table → Function | Fill in a truth table, get the function back through the same pipeline |
| Guide tab | In-app manual |
| Share links | `?f=...&preset=...&mode=...`, plus localStorage for custom presets |
| Look | Blueprint style: blue paper, yellow accent, white lines and copy |

### Out of scope (on purpose)

* **Minimisation** (Quine-McCluskey, K-map grouping) and **step-by-step simplification with named rules** (`x AND 1 = x`). Cut to keep the first version shippable. The structure leaves room for it (see [Extending](#14-extending-the-project)).
* **Circuit to expression.**
* A 5-variable K-map.
* "Expand to basic gates" circuit mode (drawing NAND as NOT(AND)).
* Accounts, databases, or any stored user data. The server is stateless.

### Audience

First-year CS students. The tool teaches: it shows how the parser grouped the input (`structure` field), explains precedence, and uses the textbook vocabulary (minterm, maxterm, SOP, POS).

---

## 2. Decisions and why

| Decision | Reason |
|---|---|
| **FastAPI + React instead of a C program** | The first attempt was in C. It needed a compiler setup and a bridge to the web, and classmates need a link, not a build step. FastAPI was also something I wanted to learn. |
| **All logic in the backend, frontend only draws** | One source of truth. The frontend never re-implements parsing or layout (the only exception is evaluating an already-built circuit for the input switches). |
| **Operators are data, not code** | Each operator is a truth table plus symbols plus a precedence number. Custom operators need no code, and every operator is tested the same way. |
| **Pratt parser with numeric precedence** | Presets can add or reorder operators without touching the parser. |
| **Truth-table limit of 12 variables, not 26** | A table has 2^n rows. 26 variables is 67 million rows; 12 is 4096. |
| **Canonical forms only** | Minimisation was explicitly postponed. The word is "shorter", never "minimal", so the app never claims something it does not guarantee. |
| **Server lays out, frontend draws** | The backend returns gates, wires, grid slots and waypoints. Drawing style stays a frontend concern. |
| **Custom presets stored in the browser** | No accounts and no database to run or secure. They are sent with each request. |
| **Balanced trees for generated SOP/POS circuits** | A left-leaning chain of 2048 terms caused a `RecursionError` (see [Gotchas](#11-known-gotchas)). |
| **Circuits are DAGs** | Equal sub-expressions share one gate (x' used twice is one NOT gate), as in a real schematic. |
| **Advanced gates keep their own symbol** | NAND, NOR, XNOR, IMP and EQV are evaluated from their own truth table and drawn as their own shape, never split into basic gates. |
| **Prebuilt libraries allowed** | Backend: FastAPI and pydantic. Frontend: react-query, lucide-react, react-zoom-pan-pinch, Tailwind, vitest. Time goes into the domain logic, not into reinventing zoom and pan. |

---

## 3. How AI was used

This project was built with AI assistance, and this section says how, so the line between my decisions and the tools is clear.

**What I decided and owned**

* The idea, the audience, and the scope, including what to cut (minimisation, circuit to expression).
* The architecture: backend does the logic, frontend only draws, operators are data.
* The conventions in [section 10](#10-conventions-that-must-not-change), especially the bit-order rule and the "shorter, never minimal" wording.
* The visual identity (blueprint style) and the decision to move from C to FastAPI + React.
* Reviewing results, running the tests, and deciding what is done.

**What AI did**

* **Frontend:** generated by an AI chat model from prompts I wrote and kept in `docs/` (`FRONTEND_PROMPT.md`, `FRONTEND_PROMPT_TABLE_TO_FUNCTION.md`). The prompts describe the API contract and the look; the model produced the React code.
* **Backend:** written with an AI coding agent working under rules recorded in `docs/PROJECT_BRIEF.md`.
* **Documentation:** handoff notes and this README were drafted with AI from the project files.

**Rules the AI had to follow** (from `PROJECT_BRIEF.md`)

1. Keep code plain and readable, no clever one-liners, because I am still learning Python and FastAPI.
2. Explain a new concept in two or three lines the first time it appears.
3. Run `pytest` after every change; everything must pass before "done".
4. Every new behaviour gets a test with a **hand-checked** expectation. If a hand-computed expectation and the code disagree, work out which one is wrong.
5. Do not add features outside the request. Ask first.
6. Be direct: if something is wrong or risky, say so and say why.

**Where manual verification mattered**

AI-written code is only trusted here when it is checked. The handoff notes label every claim as *verified* (run or read today), *reported* (someone said so), or *unverified* (assumed). The backend has 212 automated tests, and the server was also exercised over real HTTP (CORS preflight, success, errors, a 12-variable table). A concrete example of why this matters: the recursion bug at 12 variables was found by testing the maximum size, not by reading the code.

**What I learned from working this way**

* A precise contract (`API.md`) is what makes AI-generated frontend and handwritten-style backend fit together.
* Prompts are specifications. The better the spec, the less rework.
* Tests with hand-computed answers catch the cases where the AI and the author agree on the wrong thing.

---

## 4. Requirements and dependencies

### System

| Tool | Version | Why |
|---|---|---|
| Python | **3.10 or newer** | The models use the `X | None` type syntax |
| Node.js + npm | a current LTS release | Builds and runs the React frontend |
| Git | any | Cloning |

### Backend (Python)

Installed from `backend/requirements-dev.txt`.

| Package | Role |
|---|---|
| `fastapi` | Web framework: routes, request validation, automatic `/docs` page |
| `pydantic` | Request/response models and the validation of operators and presets |
| `uvicorn` | The server that runs the FastAPI app |
| `pytest` | Test runner (212 tests) |

> The exact pinned versions are in `backend/requirements.txt` and `backend/requirements-dev.txt`. Those files are the source of truth.

### Frontend (JavaScript / TypeScript)

Installed with `npm install` from `frontend/package.json`.

| Package | Role |
|---|---|
| `react` 18 + `typescript` | UI and type safety against the API contract |
| `vite` | Dev server and build tool |
| `tailwindcss` | Styling |
| `@tanstack/react-query` | Server calls, caching, loading and error states |
| `lucide-react` | Icons |
| `react-zoom-pan-pinch` | Pan and zoom on the circuit drawing |
| `vitest` | Frontend tests |

> Exact versions are in `frontend/package.json`.

---

## 5. Install and run

### Backend (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest                                  # should end with: 212 passed
uvicorn app.main:app --reload           # http://localhost:8000/docs
```

macOS / Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
uvicorn app.main:app --reload
```

If PowerShell refuses to run `Activate.ps1`, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Try the backend with no frontend:** open `http://localhost:8000/docs`, click `POST /api/analyze`, then "Try it out", and send:

```json
{"expression": "x'y + xy'"}
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm test           # vitest
```

### Both together

1. Terminal 1: start the backend (port 8000).
2. Terminal 2: start the frontend (port 5173). The backend already allows this origin through CORS.

### Single process (backend serves the built frontend)

```powershell
cd frontend
npm run build
cd ..\backend
$env:BOOLEAN_LAB_STATIC="..\frontend\dist"
uvicorn app.main:app
```

See the [deployment trap](#13-deployment) about `VITE_API_URL` before building for a public site.

### Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `BOOLEAN_LAB_CORS` | Vite on 5173 and 3000 | Comma-separated list of allowed origins |
| `BOOLEAN_LAB_MAX_VARIABLES` | 12 | Variable limit (hard cap 16) |
| `BOOLEAN_LAB_STATIC` | unset | Folder of the built frontend to serve at `/` |
| `BOOLEAN_LAB_MAX_BODY_BYTES` | 32 KB | Request body limit (simplify addendum) |
| `BOOLEAN_LAB_RATE_ANALYZE` / `_SYNTHESIZE` / `_SIMPLIFY` / `_OTHER` | 120 / 60 / 15 / 240 per 60 s | Rate limits per address |
| `BOOLEAN_LAB_SIMPLIFY_PARALLEL` | 2 | Simplifications running at once |
| `BOOLEAN_LAB_SIMPLIFY_SECONDS` | 3 | Time budget per simplification |
| `BOOLEAN_LAB_MAX_SIMPLIFY_LENGTH` | 2000 | Max characters for simplify |
| `BOOLEAN_LAB_TRUST_PROXY` | unset | Set to `1` only behind exactly one reverse proxy that appends `X-Forwarded-For` |

---

## 6. How to use the app

The app has three tabs: **LAB**, **GUIDE**, and **TABLE → FUNCTION**.

### LAB: from expression to everything

1. Type a function in the input, for example `x'y + xy'`. The result updates after a short pause (500 ms), or press Enter to plot immediately.
2. Use the example chips or the operator palette if you do not remember the symbols.
3. Read the sections that fill in below the input:
   * **Structure:** how the parser grouped your input, e.g. `OR(AND(NOT(x), y), AND(x, NOT(y)))`. This teaches precedence.
   * **Truth table:** one row per input combination.
   * **Forms:** `Σ m(1, 2)`, `Π M(0, 3)`, canonical SOP, canonical POS, and a badge saying which list is shorter.
   * **K-map:** for 1 to 4 variables. Neighbouring cells differ in exactly one variable and the map wraps around the edges.
   * **Circuit:** pan and zoom it, flip the input switches to watch the signals change, and export it as SVG or PNG.
4. Choose a **circuit mode**:
   * `expression`: the circuit exactly as you typed it
   * `sop`: two-level AND-OR built from the minterms
   * `pos`: two-level OR-AND built from the maxterms
5. Choose a **preset** to change the notation you type in.
6. Copy the **share link** to send the exact same state to someone else.

### Notation (`universal` preset)

Variables are single letters, so `xy` means `x AND y` (implicit AND). `0` and `1` are constants. Word operators are case-insensitive and need spaces around them (`x nor y`).

| Operator | Symbols | Precedence |
|---|---|---|
| NOT (prefix) | `!` `~` `¬` `not` | 60 |
| NOT (postfix) | `'` `’` `′` | 60 |
| AND | `*` `.` `·` `&` `&&` `∧` `and` (or just write letters together) | 50 |
| NAND | `~&` `↑` `nand` | 50 |
| XOR | `^` `⊕` `xor` | 40 |
| XNOR | `⊙` `~^` `==` `xnor` | 40 |
| OR | `+` `\|` `\|\|` `∨` `or` | 30 |
| NOR | `~\|` `↓` `nor` | 30 |
| IMP (right-assoc) | `->` `=>` `→` `imp` `implies` | 20 |
| EQV | `<->` `↔` `≡` `eqv` `iff` | 10 |

Higher precedence binds tighter. The other built-in presets are `textbook` (course style, implicit AND on) and `programming` (C/Python-style symbols, no implicit AND).

### Errors

If the expression is invalid, a caret is drawn under the exact character where the parser failed, e.g. `(x+y` points at position 5 with the message `missing ')'`.

### Custom presets

Open the preset editor, define an operator by its name, fixity, symbols, precedence and **truth table** (for example `NIMP`, infix, symbol `-/>`, table `[0,0,1,0]`). The server validates it live. Custom presets are stored in your browser (localStorage) and sent with each request.

### TABLE → FUNCTION

1. Choose the number of variables.
2. Set the output column of the truth table (row 0 first; the first variable is the most significant bit).
3. The app returns the function, with the same sections as the LAB tab (forms, K-map, circuit).
4. **OPEN IN LAB** moves the result into the LAB tab.

Above 4 variables the K-map is skipped, and above about 10 variables with many ones the circuit is skipped. In both cases a warning explains why.

---

## 7. Project structure, file by file

```
boolean-lab/
  backend/
    app/                 pure-Python logic and the HTTP layer
    tests/               212 tests
    pytest.ini
    requirements.txt
    requirements-dev.txt
  frontend/
    src/
      App.tsx
      api/
      utils/
    package.json
  docs/
    API.md               the contract (authority)
    PROJECT_BRIEF.md     working rules for humans and coding agents
    HANDOFF.md           current state and what is left
    FRONTEND_PROMPT.md   historical: prompt used to generate the frontend
    FRONTEND_PROMPT_TABLE_TO_FUNCTION.md
  README.md
```

### Backend: `backend/app/` (read in this order)

| File | What it does | Why it exists |
|---|---|---|
| `config.py` | All limits: 300 chars of expression, 12 variables (env override, cap 16), nesting 100, circuit 400 nodes, K-map up to 4 variables | One place to change a limit instead of magic numbers scattered around |
| `presets.py` | `OperatorDef` and `PresetDef` models with validation, `CompiledPreset` lookups, the `_MASTER` operator table, the built-in presets | Makes operators **data**. Adding or validating an operator never touches the parser |
| `tokenizer.py` | Turns text into tokens. Letters are single variables; a whole letter run that is a word operator (`and`, `nor`, `implies`) becomes an operator; symbols match longest first (`~&` is one operator, not `~` then `&`) | Keeps the parser free of text handling |
| `parser.py` | Pratt parser. Precedence is a number on each operator. Inserts implicit AND when two terms touch (`xy`) | A Pratt parser lets presets reorder operators with no code change |
| `ast_nodes.py` | The expression tree types (variable, constant, unary, binary) and an iterative `flatten` | A simple tree that the evaluator, forms and circuit all share |
| `evaluator.py` | Evaluates a tree for a given input through each operator's truth table | One evaluation rule for every operator, built-in or custom |
| `forms.py` | Minterms, maxterms, Σ/Π text, canonical SOP and POS text, the "shorter" decision | Produces the course's standard representations |
| `kmap.py` | Gray-code Karnaugh map for 1 to 4 variables | Neighbouring cells differ in one variable, as the course teaches |
| `circuit.py` | Gate deduplication, multi-input gates, layered grid layout with wire waypoints, balanced SOP/POS builders, `simulate()` used by tests | Turns a tree into something the frontend can draw without doing any layout |
| `service.py` | `analyze()` (text to everything), `synthesize()` (table to function), shared `_assemble()` response builder | Runs the whole pipeline. The routes stay thin |
| `schemas.py` | Request and response models | The API contract in code, and the source of `/openapi.json` |
| `main.py` | HTTP routes, the single error envelope, CORS, optional static file serving | The only file that knows about HTTP |
| `limits.py` | Per-process rate limiting and body-size limits (see the API addendum) | Hardening before a public link |

### Frontend: `frontend/src/`

| File | What it does | Why it exists |
|---|---|---|
| `App.tsx` | The app shell: tabs (LAB / GUIDE / TABLE → FUNCTION), input, result sections | Main UI. Currently one large file (see [technical debt](#15-roadmap-and-what-is-not-built)) |
| `api/client.ts` | Calls to the backend. Base URL is `VITE_API_URL`, falling back to `http://localhost:8000` | The only place that talks to the network |
| `api/types.ts` | TypeScript types that mirror `docs/API.md` | Catches contract drift at compile time |
| `utils/circuit-evaluator.ts` | Evaluates an already-built circuit for the interactive input switches | The one piece of logic allowed in the frontend, because it needs to react instantly |
| `utils/storage.ts` | localStorage for custom presets, and share-link encoding/decoding (`?f=...&preset=...&mode=...`) | State without accounts |

### Docs: `docs/`

| File | Purpose |
|---|---|
| `API.md` | The contract. Code and contract change together, with a test |
| `PROJECT_BRIEF.md` | Goal, architecture, conventions and rules for any coding agent |
| `HANDOFF.md` | Current state, verified/reported/unverified claims, what is left |
| `FRONTEND_PROMPT*.md` | The prompts used to generate the frontend. Historical; `API.md` wins in any conflict |

---

## 8. Key functions and why they exist

| Function / object | File | What it does | Why |
|---|---|---|---|
| `analyze()` | `service.py` | Takes an expression, preset and circuit mode. Runs tokenizer, parser, evaluator, forms, K-map and circuit, and returns one response | One entry point for the main feature |
| `synthesize()` | `service.py` | Takes a truth table (`outputs[i]` is row i) and builds the same response as `analyze()` | Table → Function reuses the entire pipeline, so there is no second code path to keep correct |
| `_assemble()` | `service.py` | Builds the response (variables, table, forms, K-map, circuit, warnings) from a function | Shared by `analyze()` and `synthesize()` so both return the identical shape |
| `_MASTER` | `presets.py` | The master table of operators: name, fixity, precedence, associativity, truth table, symbols per style | Adding a built-in operator is one row |
| `OperatorDef` / `PresetDef` | `presets.py` | Pydantic models that validate a whole preset (symbol rules, table sizes, unique symbols, limits) | Safe custom presets with clear error messages |
| `CompiledPreset` | `presets.py` | Fast lookups (symbol to operator) built from a validated preset | The tokenizer and parser need quick lookups |
| `flatten` | `ast_nodes.py` | Iteratively merges associative chains (AND, OR, XOR) into multi-input nodes | **Iterative on purpose**: deep trees must not hit Python's recursion limit |
| `_fold` | `circuit.py` | Builds balanced trees for generated SOP/POS circuits | Fixes the 12-variable `RecursionError` (2048 terms in a chain) |
| `simulate()` | `circuit.py` | Runs a generated circuit on every input | Used by tests to prove the circuit computes the same function as the expression |
| `evaluate circuit` | `utils/circuit-evaluator.ts` | Walks `nodes` in order and computes each value from the input switches (rules in `API.md`) | Live feedback when you flip a switch |

> This table lists the functions named in the project's design documents. A line-by-line reference of every helper lives in the source: read the files in the order given in [section 7](#7-project-structure-file-by-file), and each module's docstrings and tests show the intended behaviour.

---

## 9. API reference

Base URL in development: `http://localhost:8000`. Interactive docs at `/docs` (Swagger) and `/openapi.json` (machine-readable, usable for TypeScript type generation). The server is stateless: nothing is stored.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | `{"status": "ok"}` |
| GET | `/api/presets` | Built-in presets, `universal` first |
| POST | `/api/presets/validate` | Validate and normalise a custom preset |
| POST | `/api/analyze` | Text to truth table, forms, K-map, circuit |
| POST | `/api/synthesize` | Table to function, same response shape as analyze |
| POST | `/api/simplify` | Simplification with named rules (see the addendum in `docs/`) |
| GET | `/api/simplify/rules` | The rule sheet |

### `POST /api/analyze`

```json
{
  "expression": "x'y + xy'",
  "preset": "universal",
  "custom_preset": null,
  "circuit_mode": "expression"
}
```

| Field | Notes |
|---|---|
| `expression` | 1 to 300 characters |
| `preset` | Name of a built-in preset (default `universal`) |
| `custom_preset` | If present, used **instead of** `preset` |
| `circuit_mode` | `expression`, `sop` or `pos` |

The response contains: `expression`, `structure`, `preset`, `variables`, `function_label`, `tree`, `truth_table`, `minterms`, `maxterms`, `forms` (`sigma`, `pi`, `sop`, `pos`, `shorter`), `kmap` (or `null`), `circuit` (or `null`), and `warnings`. Full field meanings and a complete example are in `docs/API.md`.

### Errors

One envelope everywhere:

```json
{"error": {"code": "parse_error", "message": "missing ')'", "position": 5}}
```

| HTTP | Code | When |
|---|---|---|
| 422 | `parse_error` | Invalid expression. `position` is the 1-based character index |
| 422 | `invalid_request` | Bad body, empty/too long expression, bad `circuit_mode`, invalid preset |
| 400 | `unknown_preset` | `preset` is not a built-in name |
| 413 | `payload_too_large` | Body over the limit |
| 429 | `rate_limited` | Too many requests (`Retry-After` header) |
| 503 | `busy` | Too many simplifications at once |

### Limits

Expression up to 300 characters, up to 12 variables, nesting up to 100 levels, circuits up to 400 nodes (otherwise `circuit` is `null` with a warning), K-map up to 4 variables.

**Performance (measured):** 12-variable analyze about 0.05 s and 0.95 MB; 12-variable random synthesize about 0.1 to 0.2 s and 3 to 3.5 MB.

---

## 10. Conventions that must not change

These are decisions, not accidents. Change them only deliberately, in code, contract and tests together.

* **The first variable is the most significant bit** of the row index. For `F(a, b, c)`, row 6 is `a=1, b=1, c=0`. This holds in the truth table, K-map indices, minterm numbers, and in `/api/synthesize`.
* Variables are single letters, sorted alphabetically, always lowercase. `A` and `a` are the same variable.
* **Minterm** m_i: rows where F is 1. **Maxterm** M_i: rows where F is 0.
* SOP minterm term: the variable if its bit is 1, complemented if 0. POS maxterm: the variable if its bit is 0, complemented if 1.
* Operators are data (truth table, symbols, precedence, associativity). Nothing is hard-coded in the parser.
* Precedence (universal preset): NOT 60 > AND/NAND 50 > XOR/XNOR 40 > OR/NOR 30 > IMP 20 (right-assoc) > EQV 10.
* One error envelope. `parse_error` position is 1-based into the text that was sent.
* The wording is **"shorter"**, never "minimal".
* Circuits are DAGs: equal sub-expressions share a gate. AND, OR and XOR chains merge into one multi-input gate. NAND, NOR, XNOR, IMP and EQV never merge.

---

## 11. Known gotchas

* **Recursion bug at 12 variables.** SOP/POS circuit mode folded 2048 terms into a chain 2048 levels deep and Python raised `RecursionError` (HTTP 500). Fixed with balanced trees (`_fold`) and an iterative `flatten`. A test covers the maximum size. Any new code that walks trees must not assume shallow depth.
* Python 3.10 or newer is required.
* Pydantic prefixes validation text with "Value error, ". The error handler in `main.py` strips it so users see clean messages.
* Word operators need spaces (`x nor y`). A letter run that equals an operator word is always the operator, so `nor` can never mean the variables n, o, r.
* NAND, NOR and IMP are not associative. Chains group left to right (IMP right to left).
* `pytest.ini` sets `pythonpath = .` so a plain `pytest` finds `app`.
* Never commit or zip `node_modules` (it was 160 MB once). It is in `.gitignore`.
* Each circuit edge carries a `route` (one waypoint per skipped column) so wires can avoid gates. If wires visibly run through gates, the frontend must draw through `route`.

---

## 12. Testing

```powershell
cd backend
pytest                # 212 tests
cd ..\frontend
npm test              # vitest
```

Backend testing rules:

* Every new behaviour gets a test with a **hand-checked** expectation.
* If a hand-computed expectation and the code disagree, work out which one is wrong and say so.
* Operators are all tested the same way, through their truth tables (`test_operator_spellings` in `tests/test_parser.py`).
* A test covers the maximum-size circuit (the recursion bug).

Frontend coverage is thin (circuit evaluator and error caret only). The backend is well covered.

---

## 13. Deployment

**Same-origin (least work):** `npm run build`, then run uvicorn with `BOOLEAN_LAB_STATIC` pointing at `frontend/dist`.

> **Trap:** `src/api/client.ts` uses `VITE_API_URL || 'http://localhost:8000'`, so an **empty value falls back to localhost**. For a deployed build either set `VITE_API_URL` to the public URL before `npm run build`, or change the default to a relative URL.

**Split hosting:** static frontend host plus a backend host. Then set `BOOLEAN_LAB_CORS` to the frontend's origin.

**Before a public link:** put a reverse proxy in front with a request-size limit (a legitimate request is under about 15 KB) and a rate limit. The server also has built-in per-process limits (see the environment variables above). The server is stateless, so any host that runs Python works.

---

## 14. Extending the project

* **A built-in operator:** add one row to `_MASTER` in `app/presets.py` (name, fixity, precedence, associativity, truth table, `nary`, shape, symbols per style), then add a case to `test_operator_spellings`. Use a new `shape` only if the frontend can draw it, otherwise `box`.
* **A user operator:** no code. Send `custom_preset` (format in `docs/API.md`).
* **A response field:** add it in `service._assemble`, the model in `schemas.py`, the TypeScript type in the frontend, and a line in `API.md`, all in the same change.
* **Minimisation:** a new module (`app/minimize.py`) with new optional response fields. Never overwrite the canonical `forms`.

---

## 15. Roadmap and what is not built

**Next**

1. Run the full-stack checklist: `x'y + xy'`; `(x+y` (caret at position 5); `a nand b`; a custom `NIMP` preset; Table → Function with 3 and 12 variables; a share link in a private window; SVG and PNG export; a 360 px phone viewport; refresh with the backend stopped.
2. Deploy and send the link to classmates and the teacher with one question: "which screen confused you?"
3. Collect feedback, add screenshots and a licence, then decide whether minimisation is the next feature.

**Deferred (each is its own piece of work)**

* Minimisation with steps and rule names (Quine-McCluskey for the answer, a rewrite engine for the explanation)
* K-map grouping overlay and a 5-variable K-map
* "Expand to basic gates" circuit mode
* Circuit to expression

**Technical debt**

* `App.tsx` is one very large file with a large stylesheet. Splitting out a shared result component is the first step.
* Frontend tests are thin.
* No CI yet. A GitHub Action that runs `pytest` and `npm test` is a small, high-value addition.
* The `tree` field is large (most of a 12-variable payload) and unused by the frontend. It is kept because it is part of the contract.

---

## License

Not chosen yet. Add a `LICENSE` file before sharing widely (MIT is a common choice for a learning project).

## Author

**Ali**, CS student at ENSIA.
