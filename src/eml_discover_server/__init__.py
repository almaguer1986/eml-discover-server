"""eml-discover-server — FastAPI service wrapping eml_discover.identify.

Serves the formula-identification capability over HTTP so any
client (web app, IDE extension, CLI, Slack bot, homework checker)
can POST a SymPy expression string and get back named registry
matches without installing the Python stack.

    >>> from eml_discover_server import app
    >>> # ...mount in your ASGI host, or run via the bundled CLI:
    >>> # $ uvicorn eml_discover_server:app

Endpoints:

  - ``GET  /health``   liveness probe
  - ``GET  /registry`` list registered formula names + domains
  - ``POST /identify`` recognize a SymPy expression against the registry
"""
from __future__ import annotations

from ._version import __version__
from .app import app, build_app

__all__ = ["__version__", "app", "build_app"]
