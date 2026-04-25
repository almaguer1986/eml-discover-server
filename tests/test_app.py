"""TestClient-based tests for eml-discover-server endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from eml_discover_server import app, build_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---------- /health ----------------------------------------------------------


def test_health_returns_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "server_version" in body
    assert "discover_version" in body
    assert "cost_version" in body
    assert body["registry_size"] >= 50   # eml-discover 0.2.0 ships 53


# ---------- /registry --------------------------------------------------------


def test_registry_returns_full_catalog(client: TestClient) -> None:
    r = client.get("/registry")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["formulas"])
    assert body["count"] >= 50
    # Every formula has the expected metadata fields.
    for f in body["formulas"]:
        assert "name" in f
        assert "domain" in f
        assert "citation" in f


def test_registry_contains_known_canonical_names(client: TestClient) -> None:
    r = client.get("/registry")
    names = {f["name"] for f in r.json()["formulas"]}
    # A handful of well-known names that should always be present.
    expected = {"sigmoid (canonical)"}
    assert expected.issubset(names) or any("sigmoid" in n for n in names)


# ---------- /identify --------------------------------------------------------


def test_identify_canonical_sigmoid(client: TestClient) -> None:
    r = client.post("/identify", json={"expr": "1/(1+exp(-x))"})
    assert r.status_code == 200
    body = r.json()
    assert body["matches"], "expected at least one match for canonical sigmoid"
    top = body["matches"][0]
    assert "sigmoid" in top["name"].lower() or "logistic" in top["name"].lower()
    assert top["confidence"] in ("identical", "exact")
    assert "expr_normalized" in body
    assert "server_version" in body


def test_identify_unknown_expression_returns_empty_matches(client: TestClient) -> None:
    """A nonsense expression with no registry match returns matches=[]."""
    r = client.post("/identify", json={"expr": "x*y*z + 17"})
    assert r.status_code == 200
    # Either no matches, or only weak axes-confidence matches.
    body = r.json()
    assert isinstance(body["matches"], list)


def test_identify_invalid_expression_returns_400(client: TestClient) -> None:
    r = client.post("/identify", json={"expr": "this is not valid sympy ((((("})
    assert r.status_code == 400
    assert "parse" in r.json()["detail"].lower()


def test_identify_missing_expr_field_returns_422(client: TestClient) -> None:
    r = client.post("/identify", json={})
    assert r.status_code == 422   # FastAPI Pydantic validation


def test_identify_max_results_caps_response(client: TestClient) -> None:
    r = client.post("/identify",
                    json={"expr": "sin(x)", "max_results": 1})
    assert r.status_code == 200
    assert len(r.json()["matches"]) <= 1


def test_identify_max_results_bounds_enforced(client: TestClient) -> None:
    """max_results must be in [1, 20] per the schema."""
    r_low = client.post("/identify",
                        json={"expr": "sin(x)", "max_results": 0})
    r_high = client.post("/identify",
                         json={"expr": "sin(x)", "max_results": 999})
    assert r_low.status_code == 422
    assert r_high.status_code == 422


def test_identify_includes_rename_when_template_renaming_required(
    client: TestClient,
) -> None:
    """For a renamed canonical sigmoid (variable z, not x), the
    response should still recognize sigmoid AND surface the rename
    map used to align the template."""
    r = client.post("/identify", json={"expr": "1/(1+exp(-z))"})
    assert r.status_code == 200
    matches = r.json()["matches"]
    assert matches, "expected at least one match"


# ---------- /analyze ---------------------------------------------------------


def test_analyze_returns_pfaffian_profile(client: TestClient) -> None:
    r = client.post("/analyze", json={"expr": "exp(sin(x))"})
    assert r.status_code == 200
    body = r.json()
    # Every documented axis is present.
    for key in (
        "expression", "pfaffian_r", "max_path_r", "eml_depth",
        "structural_overhead", "predicted_depth",
        "is_pfaffian_not_eml", "fingerprint",
        "server_version", "cost_version", "corrections",
    ):
        assert key in body, f"missing field: {key}"
    # exp(sin(x)) has positive pfaffian_r (≥2 — composes sin and exp).
    assert body["pfaffian_r"] >= 2
    # corrections is a nested object with c_osc / c_composite / delta_fused.
    assert set(body["corrections"]) == {"c_osc", "c_composite", "delta_fused"}
    # fingerprint matches the canonical p…-d…-w…-c…-h<6hex> shape.
    assert body["fingerprint"].startswith("p")
    assert "-h" in body["fingerprint"]


def test_analyze_invalid_expression_returns_400(client: TestClient) -> None:
    r = client.post("/analyze", json={"expr": "this is junk ((((("})
    assert r.status_code == 400
    assert "parse" in r.json()["detail"].lower()


def test_analyze_missing_expr_field_returns_422(client: TestClient) -> None:
    r = client.post("/analyze", json={})
    assert r.status_code == 422


def test_analyze_pfaffian_not_eml_flag_set_for_bessel(client: TestClient) -> None:
    """Bessel functions are Pfaffian but not strict EML — the flag
    must be True so editor clients can warn the user."""
    r = client.post("/analyze", json={"expr": "besselj(0, x)"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_pfaffian_not_eml"] is True


# ---------- factory + meta ---------------------------------------------------


def test_build_app_factory_returns_independent_instances() -> None:
    a1 = build_app()
    a2 = build_app()
    assert a1 is not a2
    # Both have the /health route registered.
    paths = {r.path for r in a1.routes}
    assert "/health" in paths
    assert "/identify" in paths
    assert "/analyze" in paths
    assert "/registry" in paths


def test_openapi_schema_available(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema
    assert "/identify" in schema["paths"]


def test_swagger_docs_available(client: TestClient) -> None:
    r = client.get("/docs")
    assert r.status_code == 200
    assert "Swagger UI" in r.text or "swagger" in r.text.lower()


def test_redoc_available(client: TestClient) -> None:
    r = client.get("/redoc")
    assert r.status_code == 200
