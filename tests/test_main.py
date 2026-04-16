"""Tests for main.py (v1 API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_ok(self) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["service"] == "casa-python-backend"
        assert body["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_returns_expected_keys(self) -> None:
        r = client.get("/dashboard")
        assert r.status_code == 200
        body = r.json()
        for key in ("status", "activePolicies", "activeAlerts", "reviewQueue", "recentDecisions"):
            assert key in body

    def test_dashboard_status_ok(self) -> None:
        r = client.get("/dashboard")
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Boundary Stress
# ---------------------------------------------------------------------------


class TestBoundaryStress:
    def test_stress_endpoint(self) -> None:
        r = client.get("/stress")
        assert r.status_code == 200
        body = r.json()
        assert "overallStress" in body
        assert "criticalBoundaries" in body

    def test_boundary_stress_alias(self) -> None:
        r = client.get("/boundary-stress")
        assert r.status_code == 200
        assert r.json() == client.get("/stress").json()

    def test_critical_boundaries_structure(self) -> None:
        boundaries = client.get("/stress").json()["criticalBoundaries"]
        assert isinstance(boundaries, list)
        for b in boundaries:
            assert "id" in b
            assert "level" in b
            assert "score" in b


# ---------------------------------------------------------------------------
# Policy Dry-Run
# ---------------------------------------------------------------------------


class TestPolicyDryRun:
    def test_staging_returns_safe(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-102", "environment": "staging"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["result"] == "simulated"
        assert body["recommendation"] == "SAFE_TO_ADOPT"
        assert body["decisionsThatChange"] == 4

    def test_production_returns_review(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-102", "environment": "production"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["recommendation"] == "REVIEW_BEFORE_ADOPT"
        assert body["decisionsThatChange"] == 17

    def test_default_environment_is_staging(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-100"},
        )
        assert r.status_code == 200
        assert r.json()["environment"] == "staging"

    def test_empty_policy_id_rejected(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "", "environment": "staging"},
        )
        assert r.status_code == 422

    def test_missing_policy_id_rejected(self) -> None:
        r = client.post("/policy/dryrun", json={"environment": "staging"})
        assert r.status_code == 422

    def test_invalid_environment_rejected(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-1", "environment": "invalid"},
        )
        assert r.status_code == 422

    def test_empty_body_rejected(self) -> None:
        r = client.post("/policy/dryrun", json={})
        assert r.status_code == 422

    def test_extra_parameters_accepted(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={
                "policyId": "POL-102",
                "environment": "staging",
                "parameters": {"threshold": 0.75},
            },
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Decision Replay
# ---------------------------------------------------------------------------


class TestDecisionReplay:
    def test_replay_returns_expected_fields(self) -> None:
        r = client.get("/replay/DEC-001")
        assert r.status_code == 200
        body = r.json()
        assert body["decisionId"] == "DEC-001"
        assert body["originalOutcome"] == "ALLOW"
        assert body["currentOutcome"] == "REVIEW"
        assert "evidence" in body

    def test_decision_replay_alias(self) -> None:
        r = client.get("/decision-replay/DEC-001")
        assert r.status_code == 200
        assert r.json()["decisionId"] == "DEC-001"

    def test_whitespace_only_decision_id_rejected(self) -> None:
        r = client.get("/replay/%20")
        assert r.status_code == 400

    def test_various_decision_ids_accepted(self) -> None:
        for did in ("DEC-001", "abc-123", "1"):
            r = client.get(f"/replay/{did}")
            assert r.status_code == 200
            assert r.json()["decisionId"] == did


# ---------------------------------------------------------------------------
# CORS / Origins helper
# ---------------------------------------------------------------------------


class TestOrigins:
    def test_default_wildcard(self, monkeypatch) -> None:
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        from main import _origins
        assert _origins() == ["*"]

    def test_single_origin(self, monkeypatch) -> None:
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com")
        from main import _origins
        assert _origins() == ["https://example.com"]

    def test_multiple_origins(self, monkeypatch) -> None:
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com, https://b.com")
        from main import _origins
        result = _origins()
        assert result == ["https://a.com", "https://b.com"]

    def test_empty_entries_filtered(self, monkeypatch) -> None:
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com,,, https://b.com,")
        from main import _origins
        result = _origins()
        assert result == ["https://a.com", "https://b.com"]


# ---------------------------------------------------------------------------
# 404 on unknown routes
# ---------------------------------------------------------------------------


class TestNotFound:
    def test_unknown_route_returns_404(self) -> None:
        r = client.get("/nonexistent")
        assert r.status_code == 404
