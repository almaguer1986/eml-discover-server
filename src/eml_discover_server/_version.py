"""Single source of truth for the package version.

Kept in a leaf module so any other module can import it without
triggering the package's full ``__init__.py`` (which would cycle
back through ``app.py`` and the FastAPI route definitions).
"""
__version__ = "0.3.1"
