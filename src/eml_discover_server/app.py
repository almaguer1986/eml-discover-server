"""FastAPI application factory and the default `app` instance.

The factory pattern (`build_app()`) makes the service easy to
embed in test harnesses or larger ASGI applications. The
module-level `app` is the standard target for `uvicorn
eml_discover_server:app`.
"""
from __future__ import annotations

from typing import Any

import sympy as sp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from eml_discover import FORMULAS, identify
from eml_discover import __version__ as _discover_version

from ._version import __version__ as _self_version


__all__ = ["app", "build_app", "IdentifyRequest", "MatchOut", "IdentifyResponse"]


class IdentifyRequest(BaseModel):
    """Body schema for ``POST /identify``."""

    expr: str = Field(
        ...,
        description="A SymPy expression as a string (sympify-able).",
        examples=["1/(1+exp(-x))", "log(u**2)", "sin(x)**2 + cos(x)**2"],
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of matches to return.",
    )


class MatchOut(BaseModel):
    """One registry match returned by `identify`."""

    name: str
    confidence: str = Field(description='"identical" | "exact" | "axes"')
    domain: str
    citation: str
    description: str = ""
    rename: dict[str, str] = Field(
        default_factory=dict,
        description="Symbol renames used to align the registry template "
                    "with the input expression. Empty for identical / axes "
                    "confidence levels.",
    )


class IdentifyResponse(BaseModel):
    matches: list[MatchOut]
    expr_normalized: str
    server_version: str
    discover_version: str


class FormulaInfo(BaseModel):
    name: str
    domain: str
    citation: str
    description: str = ""


class RegistryResponse(BaseModel):
    formulas: list[FormulaInfo]
    count: int
    discover_version: str


class HealthResponse(BaseModel):
    status: str
    server_version: str
    discover_version: str
    registry_size: int


def _formula_info(formula: Any) -> FormulaInfo:
    return FormulaInfo(
        name=formula.name,
        domain=getattr(formula, "domain", "unknown"),
        citation=getattr(formula, "citation", ""),
        description=getattr(formula, "description", ""),
    )


def build_app(*, title: str = "eml-discover-server") -> FastAPI:
    """Construct a FastAPI application instance.

    Use the factory pattern when you need multiple instances (tests,
    nested mounts) or want to inject configuration. For one-shot
    deployments, the module-level ``app`` is sufficient.
    """
    api = FastAPI(
        title=title,
        version=_self_version,
        description=(
            "REST surface for `eml_discover.identify` — recognize famous "
            "mathematical formulas in arbitrary SymPy expressions."
        ),
    )

    @api.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        """Liveness probe + server / library / registry version snapshot."""
        return HealthResponse(
            status="ok",
            server_version=_self_version,
            discover_version=_discover_version,
            registry_size=len(FORMULAS),
        )

    @api.get("/registry", response_model=RegistryResponse, tags=["catalog"])
    def registry() -> RegistryResponse:
        """List every registered formula name and metadata.

        Useful as a client-side cache: clients can decide locally
        whether ``identify`` is worth calling, or build pickers /
        dropdowns from the registry directly.
        """
        formulas = [_formula_info(f) for f in FORMULAS]
        return RegistryResponse(
            formulas=formulas,
            count=len(formulas),
            discover_version=_discover_version,
        )

    @api.post("/identify", response_model=IdentifyResponse, tags=["identify"])
    def identify_endpoint(payload: IdentifyRequest) -> IdentifyResponse:
        """Identify a SymPy expression against the registry.

        Returns the matches sorted by confidence (``identical`` >
        ``exact`` > ``axes``), plus the parsed expression's string
        form for round-trip verification.
        """
        try:
            expr = sp.sympify(payload.expr)
        except (sp.SympifyError, SyntaxError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not parse expression: {exc}",
            ) from exc

        try:
            raw_matches = identify(expr, max_results=payload.max_results)
        except Exception as exc:   # noqa: BLE001 — surface back to caller
            raise HTTPException(
                status_code=500,
                detail=f"identify() failed: {exc}",
            ) from exc

        matches: list[MatchOut] = []
        for m in raw_matches:
            rename = {
                str(k): str(v) for k, v in (m.rename or {}).items()
            }
            matches.append(MatchOut(
                name=m.formula.name,
                confidence=m.confidence,
                domain=getattr(m.formula, "domain", "unknown"),
                citation=getattr(m.formula, "citation", ""),
                description=getattr(m.formula, "description", ""),
                rename=rename,
            ))

        return IdentifyResponse(
            matches=matches,
            expr_normalized=str(expr),
            server_version=_self_version,
            discover_version=_discover_version,
        )

    return api


# Default ASGI application for uvicorn / production hosts.
app: FastAPI = build_app()
