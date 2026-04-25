"""Entry point for ``python -m eml_discover_server`` and the
``eml-discover-server`` console script.

Starts a uvicorn server on the chosen host/port. Defaults match
typical free-tier hosts (Cloud Run, Render, Fly): bind 0.0.0.0,
read PORT from env if present.
"""
from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eml-discover-server",
        description="Run the eml-discover-server FastAPI app via uvicorn.",
    )
    parser.add_argument("--host", default="0.0.0.0",
                        help="Bind address (default: 0.0.0.0).")
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("PORT", "8000")),
                        help="Bind port (default: $PORT or 8000).")
    parser.add_argument("--reload", action="store_true",
                        help="Auto-reload on code changes (development only).")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "uvicorn is not installed. Reinstall with the 'serve' extra:\n"
            "  pip install 'eml-discover-server[serve]'"
        ) from exc

    uvicorn.run(
        "eml_discover_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
