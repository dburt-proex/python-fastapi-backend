from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def _origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI(
    title="CASA Python FastAPI Backend",
    version="0.2.0",
    description="CASA governance backend compatible with CASA-Flagship contracts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DryRunRequest(BaseModel):
    policyId: str = Field(..., min_length=1, examples=["POL-102"])
    environment: Literal["staging", "production"] = "staging"
    parameters: dict[str, Any] = Field(default_factory=dict)


class DryRunResponse(BaseModel):
    status: Literal["simulated"] = "simulated"
    simulatedOutcome: str
    impactScore: int
    logs: list[str]



class ApplyPolicyRequest(BaseModel):
    policyId: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


def _request_id(x_request_id: str | None) -> str:
    return x_request_id or "no-request-id"


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "casa-python-backend",
        "version": "0.2.0",
    }


@app.get("/dashboard")
@app.get("/api/v1/dashboard")
def dashboard(x_request_id: str | None = Header(default=None)) -> dict[str, Any]:
    _ = _request_id(x_request_id)
    return {
        "activePolicies": 3,
        "decisions24h": 27,
        "boundaryAlerts": 1,
        "systemStatus": "healthy",
    }


@app.get("/stress")
@app.get("/boundary-stress")
@app.get("/api/v1/boundary-stress")
def boundary_stress(x_request_id: str | None = Header(default=None)) -> dict[str, Any]:
    _ = _request_id(x_request_id)
    return {
        "stressLevel": 62,
        "criticalBoundaries": ["support_agent.write_database"],
        "recommendations": [
            "Increase review threshold for write_database operations.",
            "Re-run replay checks for recent support agent decisions.",
        ],
    }


@app.post("/policy/dryrun", response_model=DryRunResponse)
@app.post("/api/v1/policy/dryrun", response_model=DryRunResponse)
def policy_dry_run(
    payload: DryRunRequest,
    x_request_id: str | None = Header(default=None),
) -> DryRunResponse:
    _ = _request_id(x_request_id)
    production = payload.environment == "production"
    return DryRunResponse(
        simulatedOutcome="REVIEW_BEFORE_ADOPT" if production else "SAFE_TO_ADOPT",
        impactScore=17 if production else 4,
        logs=[
            f"Policy {payload.policyId} evaluated in {payload.environment}.",
            "Boundary stress incorporated into dry-run scoring.",
        ],
    )


@app.get("/replay/{decision_id}")
@app.get("/decision-replay/{decision_id}")
@app.get("/api/v1/decision-replay/{decision_id}")
def decision_replay(
    decision_id: str,
    x_request_id: str | None = Header(default=None),
) -> dict[str, Any]:
    _ = _request_id(x_request_id)
    if not decision_id.strip():
        raise HTTPException(status_code=400, detail="decision_id is required")

    return {
        "decisionId": decision_id,
        "timestamp": "2026-04-10T14:30:00Z",
        "originalOutcome": "ALLOW",
        "policyApplied": "POL-102",
        "context": {
            "currentOutcome": "REVIEW",
            "reason": "Policy threshold changed after boundary stress increase.",
            "boundary": "support_agent.write_database",
        },
    }


@app.post("/api/v1/admin/policy/apply")
def apply_policy(
    payload: ApplyPolicyRequest,
    x_request_id: str | None = Header(default=None),
) -> dict[str, Any]:
    request_id = _request_id(x_request_id)
    return {
        "success": True,
        "auditId": f"audit-{payload.policyId.lower()}-{request_id}",
    }
