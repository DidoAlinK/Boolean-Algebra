# Boolean Lab

Type a boolean function, get its truth table, canonical forms (Σm, ΠM, SOP, POS), Karnaugh map and logic circuit.

```
boolean-lab/
  backend/    FastAPI + pure Python logic (parser, truth table, forms, K-map, circuit layout), 150 tests
  frontend/   React app (to be generated from docs/FRONTEND_PROMPT.md)
  docs/       API.md (the contract), FRONTEND_PROMPT.md, PROJECT_BRIEF.md
```

## Run the backend (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest                                  # should end with: 150 passed
uvicorn app.main:app --reload           # http://localhost:8000/docs
```

macOS / Linux / MSYS: `python3 -m venv .venv && source .venv/bin/activate` (MSYS: `source .venv/bin/activate` after creating it with MSYS python), then the same `pip`, `pytest`, `uvicorn` lines.

If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

Try it without any frontend: open `http://localhost:8000/docs`, click `POST /api/analyze`, "Try it out", and send `{"expression": "x'y + xy'"}`.

## Run backend and frontend together

1. Generate the frontend: paste `docs/FRONTEND_PROMPT.md` into ChatGPT, save its files in `frontend/`.
2. Terminal 1: backend as above (port 8000).
3. Terminal 2: `cd frontend && npm install && npm run dev` (port 5173; the backend already allows this origin).

To serve everything from one process after `npm run build`:
`set BOOLEAN_LAB_STATIC=..\frontend\dist` (PowerShell: `$env:BOOLEAN_LAB_STATIC="..\frontend\dist"`) and start `uvicorn` again. For other origins set `BOOLEAN_LAB_CORS="https://example.com,https://other.com"`.

## How the backend is organised (read in this order)

| File | What it does |
|---|---|
| `app/presets.py` | Operators defined by truth tables; built-in presets; validation of custom presets |
| `app/tokenizer.py` | Text to tokens (letters are variables, word operators, longest-symbol-first) |
| `app/parser.py` | Pratt parser: precedence comes from numbers on the operators, not from code |
| `app/ast_nodes.py`, `app/evaluator.py` | The expression tree and its evaluation |
| `app/forms.py`, `app/kmap.py` | Minterms/maxterms, SOP/POS text, Gray-code K-map |
| `app/circuit.py` | Gates, wires and grid layout; also builds two-level SOP/POS circuits |
| `app/service.py` | Runs the whole pipeline for one expression |
| `app/main.py`, `app/schemas.py` | HTTP routes, error envelope, request/response models |

## Adding things

* **A new built-in operator**: add one row to `_MASTER` in `app/presets.py` (name, fixity, precedence, truth table, symbols per style). Tests: add a case to `test_operator_spellings`.
* **A user-defined operator**: no code, send it in `custom_preset` (see `docs/API.md`).

## Not included (on purpose)

Minimisation (Quine-McCluskey / K-map grouping) and step-by-step simplification with named rules. The structure leaves room: add `app/minimize.py` and a new field on the response.
