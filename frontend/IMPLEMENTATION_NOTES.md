# Implementation notes

- API response types follow the supplied `FRONTEND_PROMPT.md` contract.
- The browser does not parse Boolean expressions or generate truth tables/forms/K-maps/circuit layouts.
- Circuit evaluation follows the backend's node-order algorithm.
- Custom presets are stored in localStorage and sent as `custom_preset` on analyze requests.
- Built-in preset definitions are fetched from `GET /api/presets`.
- Preset validation requires a live backend connection.
- Circuit export uses the generated SVG; PNG export rasterizes it at 2x resolution.
- The circuit canvas supports wheel zoom, drag pan and pinch through `react-zoom-pan-pinch`.


## November 2026 frontend revision

- Kept the API client and circuit evaluator unchanged.
- Replaced the formula textarea with a spellcheck-disabled single-line text input; Enter submits.
- Example chips and operator symbols insert at the current selection and restore the caret.
- Virtualized truth-table rendering for up to 4096 rows and reverse-workbench rendering.
- Added a shared drafted-box border utility, 2px control/frame strokes, 1px secondary rules, and scroll-frame styling. `--draft-filter` can be switched from `none` to a static SVG filter if rough line treatment is later desired.
- Reworked OR-family SVG geometry and applied source-variable wire colours; output-high wires remain yellow.
- Added Guide and Table → Function tabs. The reverse tab is intentionally UI-only; the proposed `/api/synthesize` contract is documentation, not an implemented endpoint.
