# Boolean Lab: project brief (for humans and coding agents)

## Goal
A web tool for first-year CS students (Machine Structure). The user types a boolean function and gets: truth table, Σm / ΠM, canonical SOP / POS, Karnaugh map, logic circuit. Real users are classmates, feedback goes on the owner's GitHub/CV.

## Architecture
* `backend/`: FastAPI, pure-Python logic. Stateless. All logic lives here.
* `frontend/`: React + TypeScript + Tailwind, blueprint-paper look. Only calls the API and draws; it never re-implements parsing or layout (it only evaluates an already built circuit for the interactive switches).
* The contract is `docs/API.md`. Change code and contract together, with a test.

## Conventions (do not change without asking)
* Variables are single letters, sorted alphabetically, **the first variable is the most significant bit** of the row index.
* Minterm m_i: rows where F = 1. Maxterm M_i: rows where F = 0.
* Precedence (universal preset): NOT 60 > AND 50 > XOR 40 > OR 30 > IMP 20 > EQV 10. Implicit AND (`xy`).
* Operators are data: a truth table plus symbols plus a precedence number. No operator is hard-coded in the parser.
* One error envelope: `{"error": {"code", "message", "position"?}}`.
* "Shorter" means fewer terms to write, never "minimal".

## Rules for any coding agent working here
* The owner is still learning Python and FastAPI. Keep code plain and readable, explain a new concept in two or three lines the first time it appears, no clever one-liners.
* Run `pytest` in `backend/` after every change. Everything must pass before you report done.
* Every new behaviour gets a test with a hand-checked expectation. If a hand-computed expectation and the code disagree, work out who is wrong and say so.
* Do not add features outside the request. Ask first.
* Be direct: if something proposed is wrong or risky, say so and say why.

## Roadmap
1. Backend (done): parse, forms, K-map, circuit, presets, API, tests.
2. Frontend from `docs/FRONTEND_PROMPT.md`.
3. Show the teacher, give classmates a link (single-process deploy: see README), collect feedback.
4. Later: minimisation with steps and rule names (Quine-McCluskey for the answer, a rewrite engine for the explanation), circuit to expression.
