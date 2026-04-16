"""Tests for main_v2.py (v2 API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main_v2 import app

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
        assert body["version"] == "0.2.0"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_returns_expected_keys(self) -> None:
        r = client.get("/dashboard")
        assert r.status_code == 200
        body = r.json()
        for key in ("activePolicies", "decisions24h", "boundaryAlerts", "systemStatus"):
            assert key in body

    def test_dashboard_v1_alias(self) -> None:
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 200
        assert r.json() == client.get("/dashboard").json()

    def test_dashboard_with_request_id_header(self) -> None:
        r = client.get("/dashboard", headers={"X-Request-ID": "req-abc"})
        assert r.status_code == 200

    def test_system_status_healthy(self) -> None:
        r = client.get("/dashboard")
        assert r.json()["systemStatus"] == "healthy"


# ---------------------------------------------------------------------------
# Boundary Stress
# ---------------------------------------------------------------------------


class TestBoundaryStress:
    def test_stress_endpoint(self) -> None:
        r = client.get("/stress")
        assert r.status_code == 200
        body = r.json()
        assert "stressLevel" in body
        assert "criticalBoundaries" in body
        assert "recommendations" in body

    def test_boundary_stress_alias(self) -> None:
        r = client.get("/boundary-stress")
        assert r.status_code == 200
        assert r.json() == client.get("/stress").json()

    def test_api_v1_boundary_stress_alias(self) -> None:
        r = client.get("/api/v1/boundary-stress")
        assert r.status_code == 200
        assert r.json() == client.get("/stress").json()

    def test_stress_level_is_int(self) -> None:
        body = client.get("/stress").json()
        assert isinstance(body["stressLevel"], int)

    def test_recommendations_are_strings(self) -> None:
        recs = client.get("/stress").json()["recommendations"]
        assert isinstance(recs, list)
        for rec in recs:
            assert isinstance(rec, str)


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
        assert body["status"] == "simulated"
        assert body["simulatedOutcome"] == "SAFE_TO_ADOPT"
        assert body["impactScore"] == 4
        assert isinstance(body["logs"], list)

    def test_production_returns_review(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-102", "environment": "production"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["simulatedOutcome"] == "REVIEW_BEFORE_ADOPT"
        assert body["impactScore"] == 17

    def test_api_v1_dryrun_alias(self) -> None:
        payload = {"policyId": "POL-102", "environment": "staging"}
        r1 = client.post("/policy/dryrun", json=payload)
        r2 = client.post("/api/v1/policy/dryrun", json=payload)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()

    def test_default_environment_is_staging(self) -> None:
        r = client.post("/policy/dryrun", json={"policyId": "POL-100"})
        assert r.status_code == 200
        assert r.json()["simulatedOutcome"] == "SAFE_TO_ADOPT"

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

    def test_logs_contain_policy_id(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-999", "environment": "staging"},
        )
        logs = r.json()["logs"]
        assert any("POL-999" in log for log in logs)

    def test_dryrun_with_request_id(self) -> None:
        r = client.post(
            "/policy/dryrun",
            json={"policyId": "POL-102"},
            headers={"X-Request-ID": "req-xyz"},
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
        assert "context" in body
        assert body["context"]["currentOutcome"] == "REVIEW"

    def test_decision_replay_alias(self) -> None:
        r = client.get("/decision-replay/DEC-001")
        assert r.status_code == 200
        assert r.json()["decisionId"] == "DEC-001"

    def test_api_v1_decision_replay_alias(self) -> None:
        r = client.get("/api/v1/decision-replay/DEC-001")
        assert r.status_code == 200
        assert r.json()["decisionId"] == "DEC-001"

    def test_whitespace_only_decision_id_rejected(self) -> None:
        r = client.get("/replay/%20")
        assert r.status_code == 400

    def test_replay_includes_timestamp(self) -> None:
        body = client.get("/replay/DEC-001").json()
        assert "timestamp" in body

    def test_replay_includes_policy_applied(self) -> None:
        body = client.get("/replay/DEC-001").json()
        assert "policyApplied" in body

    def test_various_decision_ids_accepted(self) -> None:
        for did in ("DEC-001", "abc-123", "1"):
            r = client.get(f"/replay/{did}")
            assert r.status_code == 200
            assert r.json()["decisionId"] == did

    def test_replay_with_request_id(self) -> None:
        r = client.get("/replay/DEC-001", headers={"X-Request-ID": "req-1"})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Apply Policy (admin)
# ---------------------------------------------------------------------------


class TestApplyPolicy:
    def test_apply_policy_success(self) -> None:
        r = client.post(
            "/api/v1/admin/policy/apply",
            json={"policyId": "POL-102", "reason": "Approved after review"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "auditId" in body

    def test_apply_policy_audit_id_contains_policy(self) -> None:
        r = client.post(
            "/api/v1/admin/policy/apply",
            json={"policyId": "POL-200", "reason": "test"},
        )
        assert "pol-200" in r.json()["auditId"]

    def test_apply_policy_audit_id_contains_request_id(self) -> None:
        r = client.post(
            "/api/v1/admin/policy/apply",
            json={"policyId": "POL-1", "reason": "test"},
            headers={"X-Request-ID": "req-42"},
        )
        assert "req-42" in r.json()["auditId"]

    def test_apply_policy_no_request_id_fallback(self) -> None:
        r = client.post(
            "/api/v1/admin/policy/apply",
            json={"policyId": "POL-1", "reason": "test"},
        )
        assert "no-request-id" in r.json()["auditId"]

    def test_apply_policy_empty_policy_id_rejected(self) -> None:
        r = client.post(
            "/api/v1/admin/policy/apply",
            json={"policyId": "", "reason": "test"},
        )
        assert r.status_code == 422

    def test_apply_policy_empty_reason_rejected(self) -> None:
        r = client.post(
            "/api/v1/admin/policy/apply",
            json={"policyId": "POL-1", "reason": ""},
        )
        assert r.status_code == 422

    def test_apply_policy_missing_fields_rejected(self) -> None:
        r = client.post("/api/v1/admin/policy/apply", json={})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# CORS / Origins helper
# ---------------------------------------------------------------------------


class TestOrigins:
    def test_default_wildcard(self, monkeypatch) -> None:
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        from main_v2 import _origins
        assert _origins() == ["*"]

    def test_single_origin(self, monkeypatch) -> None:
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com")
        from main_v2 import _origins
        assert _origins() == ["https://example.com"]

    def test_multiple_origins(self, monkeypatch) -> None:
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com, https://b.com")
        from main_v2 import _origins
        result = _origins()
        assert result == ["https://a.com", "https://b.com"]


# ---------------------------------------------------------------------------
# Request-ID helper
# ---------------------------------------------------------------------------


class TestRequestIdHelper:
    def test_with_id(self) -> None:
        from main_v2 import _request_id
        assert _request_id("req-1") == "req-1"

    def test_without_id(self) -> None:
        from main_v2 import _request_id
        assert _request_id(None) == "no-request-id"


# ---------------------------------------------------------------------------
# 404 on unknown routes
# ---------------------------------------------------------------------------


class TestNotFound:
    def test_unknown_route_returns_404(self) -> None:
        r = client.get("/nonexistent")
        assert r.status_code == 404
