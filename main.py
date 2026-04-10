from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def _origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI(
    title="CASA Python FastAPI Backend",
    version="0.1.0",
    description="Minimal CASA governance backend for dashboard, stress, dry-run, and replay flows.",
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
    policyId: str
    environment: str
    result: Literal["simulated"] = "simulated"
    decisionsAnalyzed: int
    decisionsThatChange: int
    recommendation: Literal["REVIEW_BEFORE_ADOPT", "SAFE_TO_ADOPT"]


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "casa-python-backend",
        "version": "0.1.0",
    }


@app.get("/dashboard")
def dashboard() -> dict[str, Any]:
    return {
        "status": "ok",
        "activePolicies": 3,
        "activeAlerts": 1,
        "reviewQueue": 4,
        "recentDecisions": 27,
    }


@app.get("/stress")
@app.get("/boundary-stress")
def boundary_stress() -> dict[str, Any]:
    return {
        "overallStress": "normal",
        "criticalBoundaries": [
            {
                "id": "support_agent.write_database",
                "level": "warning",
                "score": 0.62,
            }
        ],
    }


@app.post("/policy/dryrun", response_model=DryRunResponse)
def policy_dry_run(payload: DryRunRequest) -> DryRunResponse:
    recommendation = (
        "REVIEW_BEFORE_ADOPT"
        if payload.environment == "production"
        else "SAFE_TO_ADOPT"
    )
    return DryRunResponse(
        policyId=payload.policyId,
        environment=payload.environment,
        decisionsAnalyzed=124,
        decisionsThatChange=17 if payload.environment == "production" else 4,
        recommendation=recommendation,
    )


@app.get("/replay/{decision_id}")
@app.get("/decision-replay/{decision_id}")
def decision_replay(decision_id: str) -> dict[str, Any]:
    if not decision_id.strip():
        raise HTTPException(status_code=400, detail="decision_id is required")

    return {
        "decisionId": decision_id,
        "originalOutcome": "ALLOW",
        "currentOutcome": "REVIEW",
        "reason": "Policy threshold changed after boundary stress increase.",
        "evidence": {
            "policyVersion": "2026.04.09",
            "boundary": "support_agent.write_database",
        },
    }
