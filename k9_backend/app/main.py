from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import APISettings, parse_origins


def _bootstrap_k9_core(settings: APISettings) -> Path:
    """
    Make k9_core importable as `src.*` and ensure relative data paths work.
    """
    here = Path(__file__).resolve()
    configured = Path(settings.k9_core_dir)
    k9_core_dir = (
        configured.resolve()
        if configured.is_absolute()
        else (here.parent / configured).resolve()
    )

    # Add k9_core to sys.path so imports like `from src...` work
    sys.path.insert(0, str(k9_core_dir))

    # Keep process CWD at k9_core so nodes that read `data/...` work.
    os.chdir(str(k9_core_dir))

    return k9_core_dir


settings = APISettings()
_bootstrap_k9_core(settings)

from app.k9_service import K9Service  # noqa: E402  (after sys.path bootstrap)


app = FastAPI(title="K9 API", version="0.1.0")

origins = parse_origins(settings.allowed_origins)
if origins != ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


svc = K9Service()

# Demo scenario state (in-memory). For multi-instance deployments, move to storage.
SCENARIOS: Dict[str, bool] = {"critical_monday": False}


class ChatRequest(BaseModel):
    sessionId: Optional[str] = None
    message: str


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


class ScenarioRequest(BaseModel):
    enabled: bool = True


@app.post("/api/scenario/critical-monday")
def set_critical_monday(req: ScenarioRequest) -> Dict[str, Any]:
    SCENARIOS["critical_monday"] = bool(req.enabled)
    return {"ok": True, "scenario": "critical_monday", "enabled": SCENARIOS["critical_monday"]}


@app.get("/api/summary")
def summary(window: str = "CURRENT_WEEK") -> Dict[str, Any]:
    # Minimal deterministic command (no LLM) to compute metrics + risk_summary.
    command = {
        "type": "K9_COMMAND",
        "intent": "ANALYTICAL_QUERY",
        "entity": "risks",
        "operation": "rank",
        "payload": {"time": {"type": "RELATIVE", "value": window}},
    }
    active_event = {"type": "CRITICAL_MONDAY"} if SCENARIOS.get("critical_monday") else None
    state = svc.run_graph(user_query="summary", k9_command=command, active_event=active_event, demo_mode=True)
    return {
        "ok": True,
        "analysis": state.analysis,
        "trace": svc.build_trace(state=state, k9_command=command),
    }


@app.get("/api/trajectory")
def trajectory(risk: str, window: str = "LAST_MONTH") -> Dict[str, Any]:
    command = {
        "type": "K9_COMMAND",
        "intent": "ANALYTICAL_QUERY",
        "entity": "risks",
        "operation": "evolution",
        "filters": {"risk_id": risk},
        "payload": {"time": {"type": "RELATIVE", "value": window}},
    }
    active_event = {"type": "CRITICAL_MONDAY"} if SCENARIOS.get("critical_monday") else None
    state = svc.run_graph(user_query=f"trajectory {risk}", k9_command=command, active_event=active_event, demo_mode=True)
    analysis = state.analysis if isinstance(state.analysis, dict) else {}
    risk_trajectories = (analysis.get("risk_trajectories") or {}).get(risk) if isinstance(analysis.get("risk_trajectories"), dict) else None
    return {
        "ok": True,
        "risk": risk,
        "trajectory": risk_trajectories,
        "trace": svc.build_trace(state=state, k9_command=command),
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    session_id = req.sessionId or "api"
    user_query = req.message.strip()

    interp = svc.interpret(user_query, session_id=session_id)
    if not interp.ok:
        return {
            "type": "error",
            "message": "Failed to interpret query",
            "details": {"error": interp.error, "parsed": interp.parsed},
        }

    command = interp.parsed or {}

    # Clarification requests are a first-class response
    if command.get("type") == "CLARIFICATION_REQUEST":
        return {
            "type": "clarify",
            "clarification": command,
        }

    # Run deterministic cognition
    active_event = {"type": "CRITICAL_MONDAY"} if SCENARIOS.get("critical_monday") else None
    state = svc.run_graph(user_query=user_query, k9_command=command, active_event=active_event)

    # Synthesize final answer
    answer, synthesis_meta = svc.synthesize(
        user_query=user_query,
        k9_command=command,
        state=state,
        session_id=session_id,
    )

    metrics = (state.analysis or {}).get("metrics") if isinstance(state.analysis, dict) else None
    visual_suggestions = None
    if isinstance(metrics, dict):
        visual_suggestions = metrics.get("visual_suggestions")

    # Recommendations from KG (optional)
    risk_summary = (state.analysis or {}).get("risk_summary") if isinstance(state.analysis, dict) else None
    dominant_risk = risk_summary.get("dominant_risk") if isinstance(risk_summary, dict) else None
    recommendations = svc.get_recommendations(risk_id=dominant_risk) if isinstance(dominant_risk, str) else None

    return {
        "type": "result",
        "answer": answer,
        "k9_command": command,
        "analysis": state.analysis,
        "reasoning": state.reasoning,
        "narrative_context": state.narrative_context,
        "visual_suggestions": visual_suggestions,
        "recommendations": recommendations,
        "trace": svc.build_trace(state=state, k9_command=command),
        "meta": {
            "demo_mode": state.demo_mode,
            "synthesis": synthesis_meta,
        },
    }

