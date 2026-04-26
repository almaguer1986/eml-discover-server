# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.2] — 2026-04-25 — `verified_in_lean=True` propagated via eml-witness 0.2.0

### Changed
- Bump `eml-witness` floor from `>=0.1.0` to `>=0.2.0` to pin the
  `verified_in_lean=True` default that flipped in eml-witness
  0.2.0. `POST /witness` responses now carry `verified_in_lean=True`
  and a populated `lean_url` field for any expression in the EML
  class. Bessel / Airy / Lambert W still return
  `verified_in_lean=False` and `lean_url=null` because they're
  outside the Lean theorem's scope.
- `/health` `witness_version` now reports `0.2.0`, making the
  flag flip visible at the health-probe level.

### Tests
- 24 cases — `test_witness_for_canonical_sigmoid` and
  `test_witness_pfaffian_not_eml_for_bessel` updated to assert
  the new flag values + lean_url presence. mypy strict clean.

## [0.3.1] — 2026-04-25 — Security hardening (sympify, length cap, error masking)

### Security
- **CRITICAL fix: replaced `sp.sympify()` with hardened
  `parse_expr()`** for every endpoint that accepts user-supplied
  expression strings (`/identify`, `/analyze`, `/witness`).
  `sympify` is documented as `eval`-equivalent — under the
  default parser it falls back to Python's `eval()` on
  non-trivial input, allowing constructs like
  `__import__('os').system(...)` to execute remote code on the
  server. `parse_expr` uses a dedicated tokeniser + transformations
  pipeline with no `eval` path while still accepting the standard
  mathematical syntax (`sin`, `exp`, `log`, etc.) SymPy users
  expect.
- **Added `max_length=2000` to every `expr` Pydantic field**.
  Caps DoS via huge expression strings forced through the SymPy
  parser.
- **Stripped exception detail from 400 responses**. The handler
  was echoing `str(exc)` which can leak SymPy traceback fragments
  + internal module paths. Now returns a generic
  "Expression could not be parsed." with the full exception
  logged at DEBUG level server-side.

### Note
Rate limiting (e.g. `slowapi`) and auth are NOT included in this
hotfix; both remain prerequisites for deploying the server to a
public network. Deferred to v0.4.0 alongside the hosting
decision.

## [0.3.0] — 2026-04-25 — `/witness` endpoint (universality witnesses over HTTP)

### Added
- **`POST /witness`** — wraps `eml_witness.universality_witness`.
  Returns the JSON-serialised `UniversalityWitness`: Pfaffian
  profile + registry identification + canonical-equivalent path
  (when `walk_canonical=True`, default) + savings + Lean status
  flag (`verified_in_lean`, defaults to `False` until
  `EML_Universality.lean` is user-verified per the project's Lean
  writing protocol).
- `WitnessRequest`, `WitnessResponse` schemas exported.
- `/health` now reports `witness_version` alongside the existing
  `cost_version`, `discover_version`, `server_version`.
- New hard dependency: `eml-witness>=0.1.0`.

### Tests
- 6 new cases in `tests/test_app.py` (witness happy path with
  identification, walk_canonical=True path emission,
  walk_canonical=False skip, parse failure, missing field,
  Pfaffian-not-EML for `besselj(0, x)`). Full suite: 24 passing.

## [0.2.0] — 2026-04-25 — `/analyze` endpoint

### Added
- **`POST /analyze`** — wraps `eml_cost.analyze` + `eml_cost.fingerprint`.
  Returns the Pfaffian profile (`pfaffian_r`, `max_path_r`,
  `eml_depth`, `structural_overhead`, `predicted_depth`,
  `is_pfaffian_not_eml`, full `corrections` breakdown) plus the
  axes-and-tail fingerprint string. Lets editor and dashboard
  clients show cost insight without installing the Python stack
  locally.
- `AnalyzeRequest`, `AnalyzeResponse`, `CorrectionsOut` schemas
  exported from `eml_discover_server`.

### Changed
- `/health` now reports `cost_version` alongside the existing
  `server_version`, `discover_version`, `registry_size`. Useful
  for diagnosing version skew between the rest of the stack.
- New hard dependency: `eml-cost>=0.2.0`.

### Tests
- 4 new cases in `tests/test_app.py` covering `/analyze` happy path,
  parse failure (400), missing field (422), and Pfaffian-not-EML
  flag for `besselj(0, x)`. Full suite: 18 passing.

## [0.1.0] — 2026-04-25 — Initial release

FastAPI surface wrapping `eml_discover.identify`.

### Endpoints

- **`GET /health`** — liveness probe + server / discover / registry
  version snapshot.
- **`GET /registry`** — list every registered formula (name,
  domain, citation, description). Useful as a client-side cache.
- **`POST /identify`** — recognize a SymPy expression against the
  registry. Body: `{"expr": "...", "max_results": N}`. Returns
  ordered matches with confidence (`identical` > `exact` > `axes`),
  rename map (when applicable), and the parsed expression's
  string form for round-trip verification.

### Architecture

- **App factory pattern.** `build_app()` constructs a fresh FastAPI
  instance for embedding / multi-mount / testing. Module-level
  `app` is the canonical ASGI target for production hosts.
- **CLI entry point.** `eml-discover-server` (and `python -m
  eml_discover_server`) starts a uvicorn server. Reads `$PORT`
  from env to fit free-tier host conventions (Cloud Run, Render,
  Fly).
- **Pydantic v2 schemas.** `IdentifyRequest`, `IdentifyResponse`,
  `MatchOut`, `RegistryResponse`, `HealthResponse`, `FormulaInfo`
  — all generated as OpenAPI schemas at `/docs` automatically.
- **Errors:** sympify failures → 400 with parser message;
  identify() failures → 500 with traceback message. No
  silent fallbacks.

### Tests

- 14 cases in `tests/test_app.py` — TestClient based, covers
  every endpoint + happy paths + edge cases (bad expression,
  empty body, missing field, max_results bounds, factory
  isolation, OpenAPI doc availability).

### Status

Beta. Patent pending. Hosting decisions deferred (no Dockerfile
in v0.1; v0.2 will pin a canonical target).
