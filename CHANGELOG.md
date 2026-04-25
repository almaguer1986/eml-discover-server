# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
