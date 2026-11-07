# Boolean Lab: handoff

Date: 2026-11-07. Owner: Ali. Read `PROJECT_BRIEF.md` for working rules and `API.md` for the exact API contract. This file is the current state, what is left, and the technical facts someone needs to continue.

## How this was verified

| Label | Meaning |
|---|---|
| **Verified** | checked today by running code or reading the source |
| **Reported** | the owner said so, not independently checked |
| **Unverified** | assumed, needs a check |

* Backend: **verified**. `pytest` gives 212 passed. The server was also run over real HTTP (CORS preflight, success, errors, a 12-variable table).
* Frontend: only `frontend_1.zip` (Nov 6) was inspected. In that version the Table → Function tab was still UI-only (`api.synthesize` did not exist yet). The wiring of that tab to `/api/synthesize` is **reported** built, **unverified**.

## Status in one paragraph

The backend does everything in the restart scope: parsing with built-in and custom operator presets, truth table, Σm / ΠM, canonical SOP / POS, K-map, three circuit modes, and table to function. The frontend (blueprint style) covers the lab, a guide tab, and the Table → Function tab. What remains is mostly **getting it in front of users**: deployment, a feedback loop, and the GitHub/CV packaging. Minimisation and step-by-step explanations were cut on purpose and are not built.

## Scope compared with what is built

| # | Requirement (from the restart message and later decisions) | Status | Notes |
|---|---|---|---|
| 1 | Take user input | Done, verified in frontend_1 | Single-line input, 500 ms debounce, example chips, operator palette, Enter plots |
| 2 | Know how many variables and which | Done | Letters a to z, sorted alphabetically, **always lowercase**, at most 12 per function |
| 3 | All operators (NOT to NAND, XNOR...) as presets, plus user presets | Done | 9 operators (NOT, AND, NAND, XOR, XNOR, OR, NOR, IMP, EQV; NOT has a prefix and a postfix form), 3 built-in presets, custom presets sent per request, editor with live server validation |
| 4 | Truth table and forms (POS, SOP, Π, Σ) | Done, canonical only | Not minimised. "shorter" badge means fewer terms, not minimal |
| 5 | Draw the circuit | Done | 3 modes, shared gates, multi-input gates, routed layout, interactive input switches, SVG/PNG export |
| 6 | Prompt for ChatGPT to build the React frontend, FastAPI backend by me | Done | `FRONTEND_PROMPT.md` and `FRONTEND_PROMPT_TABLE_TO_FUNCTION.md` |
| 7 | Blueprint look (blue paper, yellow accent, white lines and copy) | Done in frontend_1 | Drafted boxes, title block, drafting copywriting |
| 8 | Prebuilt libraries allowed | Used | react-query, lucide-react, react-zoom-pan-pinch, Tailwind, vitest. Backend: FastAPI, pydantic |
| + | K-map (1 to 4 variables) | Done | Gray code, wraps at the edges, no grouping drawn |
| + | Manual / guide tab | Done in frontend_1 (GUIDE tab) | |
| + | Shareable links | Done in frontend_1 | `?f=...&preset=...&mode=...` plus localStorage |
| + | Table → Function | Backend done and tested. Frontend **reported** built | `POST /api/synthesize` |
| from the first idea | Optimisation and step-by-step with rule names (x AND 1 = x) | **Not built** | Cut on purpose |
| from the first idea | "SOP optimised or POS optimised" | Partly | Only the shorter canonical list is chosen |
| from the first idea | Circuit to expression | **Not built** | |

## What is left, in the order that matters for the goal (real users, feedback, GitHub/CV)

**A. Check the full stack (an hour)**
Run backend and the current frontend together and go through this list: `x'y + xy'` (all sections fill in); `(x+y` (caret under position 5); `a nand b`; a custom preset with `NIMP` (`-/>`, table `[0,0,1,0]`); Table → Function with 3 variables, then OPEN IN LAB; Table → Function with 12 variables (should not freeze, K-map and circuit show warnings); copy a share link in a private window; export SVG and PNG; a 360 px wide phone viewport; refresh with the backend stopped (offline message, retry works).

**B. Deploy so classmates can open a link**
* Same-origin deploy is the least work: `npm run build`, then run uvicorn with `BOOLEAN_LAB_STATIC` pointing at `frontend/dist`.
* **Trap:** `src/api/client.ts` uses `VITE_API_URL || 'http://localhost:8000'`, so an empty value falls back to localhost. For a deployed build either set `VITE_API_URL` to the public URL before `npm run build`, or change the default to a relative URL.
* Split hosting also works (static frontend host plus a backend host). Then set `BOOLEAN_LAB_CORS` to the frontend's origin.
* Hardening before a public link: no auth and no rate limit exist. Put a reverse proxy in front with a body size limit (a legitimate request is under about 15 KB) and a rate limit. The server is stateless, so any host that runs Python works.

**C. Feedback loop and packaging**
A visible feedback link (form or issue tracker), a GitHub repository with README, screenshots or a short GIF, and a licence. Show the teacher first, as planned.

**D. Deferred features (each is its own piece of work)**
1. Minimisation with steps and rule names: Quine-McCluskey for the answer, a rewrite engine for the explanation (add `app/minimize.py` and new response fields; do not change the canonical forms).
2. K-map grouping overlay (needs minimisation first) and a 5-variable K-map (two 4x4 maps).
3. "Expand to basic gates" circuit mode (NAND drawn as NOT(AND)). Offered earlier, held.
4. Circuit to expression.

**E. Technical debt**
* `frontend/src/App.tsx` was a single 788-line file with a 408-line stylesheet. The Table → Function prompt asks for a shared `ResultSheet`, which is a good first split.
* Frontend tests are thin (circuit evaluator and error caret only). The backend is well covered.
* No CI. A GitHub Action that runs `pytest` and `npm test` is a small, high-value addition.
* The `tree` field in responses is large (most of a 12-variable payload) and the frontend does not use it. Keep it for now, it is part of the contract.
* `FRONTEND_PROMPT.md` is now historical; `API.md` is the authority.

## Architecture

```
boolean-lab/
  backend/            FastAPI, pure Python logic, 212 tests, about 1,300 lines in app/
  frontend/           React 18 + TypeScript + Tailwind (built from the prompts)
  docs/               API.md (authority), PROJECT_BRIEF.md, HANDOFF.md, prompts
```

Backend files, in reading order:

| File | Job |
|---|---|
| `app/config.py` | Limits: 300 chars, 12 variables (env override, cap 16), nesting 100, circuit 400 nodes, K-map up to 4 variables |
| `app/presets.py` | `OperatorDef` / `PresetDef` models with validation, `CompiledPreset` lookups, the `_MASTER` operator table, built-in presets |
| `app/tokenizer.py` | Text to tokens. Letters are single variables. A whole letter run that is a word operator (`and`, `nor`, `implies`) becomes an operator. Symbols match longest first |
| `app/parser.py` | Pratt parser. Precedence is data (a number on each operator). Implicit AND when two terms touch |
| `app/ast_nodes.py`, `app/evaluator.py` | Tree types, iterative `flatten`, evaluation through each operator's truth table |
| `app/forms.py`, `app/kmap.py` | Minterms/maxterms, SOP/POS text, Gray-code K-map |
| `app/circuit.py` | Gate dedupe, multi-input gates, layered layout with waypoints, SOP/POS tree builders (balanced), `simulate()` used by tests |
| `app/service.py` | `analyze()` (text to everything), `synthesize()` (table to function), shared `_assemble()` response builder |
| `app/schemas.py`, `app/main.py` | Request/response models, routes, one error envelope, optional static file serving |

Frontend facts (verified in frontend_1): `src/api/client.ts` and `types.ts` follow the contract, `src/utils/circuit-evaluator.ts` evaluates a returned circuit for the input switches, `storage.ts` handles localStorage and share links, `react-zoom-pan-pinch` provides circuit pan and zoom, tables are virtualised, tabs are LAB / GUIDE / TABLE → FUNCTION.

## Conventions that must not change without a decision

* **The first variable is the most significant bit** of the row index. For `F(a,b,c)`, row 6 is `a=1, b=1, c=0`. This holds in the truth table, K-map indices, minterm numbers, and in `/api/synthesize` (`outputs[i]` is row i).
* Variables are single letters, sorted alphabetically, always lowercase. `A` and `a` are the same variable.
* Minterm m_i = rows where F is 1. Maxterm M_i = rows where F is 0. SOP minterm term: variable if its bit is 1, complemented if 0. POS maxterm: variable if its bit is 0, complemented if 1.
* Operators are data: a truth table (`[f(0), f(1)]` or `[f(0,0), f(0,1), f(1,0), f(1,1)]`), symbols, precedence, associativity. Nothing is hard-coded in the parser.
* Precedence (universal preset): NOT 60 > AND/NAND 50 > XOR/XNOR 40 > OR/NOR 30 > IMP 20 (right-assoc) > EQV 10.
* One error envelope everywhere: `{"error": {"code", "message", "position?"}}`. `parse_error` position is 1-based into the sent text.
* The wording is "shorter", never "minimal".
* Circuits are DAGs: equal sub-expressions share a gate. AND, OR and XOR chains merge into one multi-input gate. NAND, NOR, XNOR, IMP and EQV never merge.
* Advanced gates are evaluated from their own table and drawn as their own symbol, never split into basic gates.

## API summary (full detail in API.md)

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | liveness |
| `GET /api/presets` | built-in presets, `universal` first |
| `POST /api/presets/validate` | validate and normalise a custom preset |
| `POST /api/analyze` | text to truth table, forms, K-map, circuit |
| `POST /api/synthesize` | table to function, **same response shape as analyze** |

Environment variables: `BOOLEAN_LAB_CORS` (comma-separated origins, default Vite on 5173 and 3000), `BOOLEAN_LAB_MAX_VARIABLES` (default 12, hard cap 16), `BOOLEAN_LAB_STATIC` (folder of the built frontend to serve at `/`).

Performance (measured): 12-variable analyze about 0.05 s and 0.95 MB; 12-variable random synthesize about 0.1 to 0.2 s and 3 to 3.5 MB. Circuits are skipped above 400 nodes (about 10 variables with many ones) with a warning. The K-map is skipped above 4 variables with a warning.

## Why things are the way they are

| Decision | Reason |
|---|---|
| Dropped the C version, FastAPI + React | C needed a compiler setup and a web bridge; classmates need a link, and the owner wants to learn FastAPI |
| Truth-table limit 12, not 26 | The table has 2^n rows; 26 variables is 67 million rows. 12 is 4096 rows |
| Operators defined by truth tables | Custom operators need no code, and every operator is tested the same way |
| Pratt parser with numeric precedence | Presets can add or reorder operators without touching the parser |
| Canonical forms only | Minimisation was explicitly postponed to keep the first version shippable |
| Server draws nothing, only lays out | The backend gives gates, wires, grid slots and waypoints; the frontend draws. Keeps drawing style a frontend concern |
| Custom presets kept in the browser | No accounts and no database to run or secure |
| Balanced trees for generated SOP/POS | See the recursion bug below |

## Gotchas that already cost time

* **Recursion bug at 12 variables.** SOP/POS circuit mode folded 2048 terms into a left-leaning chain 2048 levels deep, and Python raised `RecursionError` (an HTTP 500). Fixed by building balanced trees (`_fold` in `circuit.py`) and an iterative `flatten`. A test covers the maximum size. Any new code that walks trees must not assume shallow depth.
* Python 3.10 or newer is required (the models use `X | None`).
* Pydantic prefixes validation text with "Value error, "; the error handler in `main.py` strips it so users see clean messages.
* Word operators need spaces (`x nor y`). A letter run that equals an operator word is always the operator, so `nor` can never mean the variables n, o, r.
* NAND, NOR and IMP are not associative; chains group left to right (IMP right to left).
* `pytest.ini` sets `pythonpath = .` so plain `pytest` finds `app`.
* The first frontend zip included `node_modules` (160 MB). It is in `.gitignore`; leave it out of zips.
* The very first frontend showed the offline message twice (heading and body). Cosmetic, unverified whether fixed.
* `route` waypoints: each circuit edge carries `route` (one point per skipped column) so wires can avoid gates. frontend_1 ignores it (its types do not include it). If wires visibly run through gates, have the frontend draw through `route`.

## Run and test (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest                                  # 212 passed
uvicorn app.main:app --reload           # http://localhost:8000/docs

cd ..\frontend
npm install
npm run dev                             # http://localhost:5173
npm test                                # vitest
```

Single-process serving after `npm run build`: set `BOOLEAN_LAB_STATIC` to the `dist` folder and start uvicorn (see the build-time `VITE_API_URL` trap above).

## How to add things

* **A built-in operator:** add one row to `_MASTER` in `app/presets.py` (name, fixity, precedence, associativity, truth table, `nary`, shape, symbols per style), then add a case to `test_operator_spellings` in `tests/test_parser.py`. Use a new `shape` only if the frontend can draw it, otherwise `box`.
* **A user operator:** no code, send `custom_preset` (format in API.md).
* **A response field:** add it in `service._assemble`, the model in `schemas.py`, the TypeScript type in the frontend, and a line in API.md, in the same change.
* **Minimisation:** new module, new optional response fields, never overwrite the canonical `forms`.

## Suggested next three steps

1. Run the checklist in section A against the current frontend and fix anything it turns up.
2. Deploy (section B), then send the link to the teacher and a few classmates with one question: "which screen confused you?"
3. Put the repository on GitHub with screenshots, then decide from the feedback whether minimisation with steps is the next feature.
