# eml-discover-server

REST surface for [`eml-discover`](https://github.com/almaguer1986/eml-discover):
recognize famous mathematical formulas in arbitrary SymPy expressions
over HTTP. Build it into a web app, an IDE extension, a Slack bot,
or any other client without installing the Python stack.

## Quick start

```bash
pip install 'eml-discover-server[serve]'
eml-discover-server                # bind 0.0.0.0:8000
# or
uvicorn eml_discover_server:app    # explicit ASGI host
```

```bash
# Probe the registry
curl http://localhost:8000/health
curl http://localhost:8000/registry

# Identify a sigmoid
curl -X POST http://localhost:8000/identify \
  -H "Content-Type: application/json" \
  -d '{"expr": "1/(1+exp(-x))"}'
```

```json
{
  "matches": [
    {
      "name": "sigmoid (canonical)",
      "confidence": "identical",
      "domain": "ml",
      "citation": "https://en.wikipedia.org/wiki/Sigmoid_function",
      "description": "...",
      "rename": {}
    }
  ],
  "expr_normalized": "1/(1 + exp(-x))",
  "server_version": "0.1.0",
  "discover_version": "0.2.0"
}
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/health`   | Liveness + version snapshot |
| `GET`  | `/registry` | List all 53 formulas + domains + citations |
| `POST` | `/identify` | Identify a SymPy expression against the registry |

OpenAPI / Swagger UI are served automatically at `/docs`; ReDoc at
`/redoc`. Both come from FastAPI for free.

## Embedding

Use the `build_app()` factory if you need to mount under a path
prefix, inject middleware, or run multiple instances:

```python
from fastapi import FastAPI
from eml_discover_server import build_app

root = FastAPI()
root.mount("/discover", build_app(title="My discover"))
```

## Hosting

The server is stateless and CPU-light. Free-tier deployment options
proven elsewhere:

- **Cloud Run** — `gcloud run deploy --source . --port 8000`
- **Fly.io** — `fly launch` (Python detector picks up `pyproject.toml`)
- **Render** — `eml-discover-server` as the start command
- **Vercel** — via the FastAPI Python runtime

A `Dockerfile` is intentionally NOT shipped in v0.1 so deployments
can pick their preferred base image. v0.2 will include one once a
canonical hosting target is chosen.

## Status

Beta. v0.1.0 wraps `eml-discover 0.2.0` (53 formulas). Patent
pending. Public release follows post-prosecution licensing.
