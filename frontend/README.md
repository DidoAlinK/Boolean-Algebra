# Boolean Lab

A blueprint-themed Boolean function learning frontend for first-year computer science students studying Machine Structure.

## Requirements
- Node.js 20+
- npm
- Running Boolean Lab FastAPI backend

## Install
```bash
npm install
```

Copy `.env.example` to `.env` and configure the backend URL:
```env
VITE_API_URL=http://localhost:8000
```

## Run
```bash
npm run dev
```
Open http://localhost:5173.

## Build
```bash
npm run build
npm run preview
```

## Tests
```bash
npm run test
npm run test:watch
```

## Backend contract
The frontend expects:
- `GET /api/health`
- `GET /api/presets`
- `POST /api/presets/validate`
- `POST /api/analyze`

Swagger: http://localhost:8000/docs  
OpenAPI: http://localhost:8000/openapi.json

The backend remains authoritative for parsing, truth tables, canonical forms, Karnaugh maps and circuit layout. The browser only evaluates the returned circuit for interactive test switches.


## Additional frontend workbench tabs

- **Guide** documents Boolean algebra fundamentals, operator precedence, canonical forms, Karnaugh maps, circuits, and the main lab workflow.
- **Table → Function** is a frontend-only reverse-design prototype. It supports 2–12 variables (up to 4096 rows), virtualizes the visible rows, and previews canonical minterm/maxterm index notation. It does not call a synthesis endpoint. The proposed `POST /api/synthesize` request/response contract and implementation notes are displayed in that tab for backend review.

## UI update notes

The expression field is a single-line input with caret-preserving insertion for examples and operators. Truth-table rows are virtualized. Drafted panels use a shared 2px line utility with 5px corner overshoot; secondary row rules remain 1px. Circuit wires use distinct source-variable colours when low and the yellow signal colour when high. The OR-family gate silhouette has been redrawn.
