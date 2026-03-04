"""
api/main.py — Strategic Radar FastAPI Server

Entry points:
  POST /run      — trigger the LangGraph agent, return intelligence brief
  POST /notify   — called internally after /run to trigger N8N email delivery
  GET  /health   — verify all services are reachable (used by Railway + N8N)
  GET  /ui       — static HTML interface (served from api/static/index.html)

Both N8N Cloud and the HTML UI call POST /run.
Response shape is identical regardless of caller.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator

from core.logging_config import get_logger
from agent.graph import graph as agent_graph
from agent.state import default_state

logger = get_logger(__name__)

# ── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Strategic Radar — Intelligence Snapshot Engine",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── STATIC UI ─────────────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")
    logger.info("Static UI mounted at /ui")
else:
    logger.warning("api/static/ not found — create it and add index.html")

# ── COMPETITOR REGISTRY ───────────────────────────────────────────────────────

_registry_path = Path(__file__).parent.parent / "rag" / "kb" / "competitor_registry.json"

def _load_registry() -> dict:
    try:
        with open(_registry_path) as f:
            data = json.load(f)
        registry = {c["name"].lower(): c for c in data["competitors"]}
        logger.info(f"Registry loaded — {len(registry)} competitors")
        return registry
    except FileNotFoundError:
        logger.warning(f"Registry not found at {_registry_path}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load registry: {e}")
        return {}

COMPETITOR_REGISTRY = _load_registry()

# ── MODELS ────────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    company: str = Field(..., example="Acrelec")
    intelligence_type: Literal[
        "Competitor Moves",
        "Business Opportunities",
        "Technology Developments"
    ] = Field(default="Competitor Moves")
    time_range_days: int = Field(default=7, ge=1, le=30)
    notify_email: Optional[str] = Field(
        default="",
        description="Optional email address to send the brief to via N8N"
    )

    @validator("company")
    def company_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("company must not be empty")
        return v.strip()

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: dict

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Strategic Radar",
        "ui":      "/ui",
        "docs":    "/docs",
        "health":  "/health",
        "run":     "POST /run"
    }


@app.get("/health", response_model=HealthResponse)
def health():
    """
    Verify all services are reachable.
    Called by Railway health checks and N8N before triggering a run.
    Returns 200 if everything is up, 503 if a critical service is down.
    """
    services = {}
    overall  = "ok"

    # Pinecone
    try:
        from rag.retriever import retrieve
        retrieve("health check", top_k=1)
        services["pinecone"] = "ok"
    except Exception as e:
        logger.error(f"Health check — Pinecone failed: {e}")
        services["pinecone"] = "error"
        overall = "degraded"

    # LLM — check the key exists
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        services["llm"] = "ok"
    else:
        services["llm"] = "no api key"
        overall = "degraded"

    # Competitor registry
    services["registry"] = (
        f"{len(COMPETITOR_REGISTRY)} competitors loaded"
        if COMPETITOR_REGISTRY else "empty"
    )

    response = HealthResponse(
        status=overall,
        timestamp=datetime.utcnow().isoformat() + "Z",
        services=services,
    )

    if overall != "ok":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=response.dict())

    return response


@app.post("/run")
async def run(request: RunRequest):
    """
    Trigger the LangGraph agent.

    Validates the competitor against the registry, builds the initial
    state, runs the full graph, and returns the intelligence brief.

    Called by:
      - The HTML UI (api/static/index.html)
      - N8N Cloud scheduled workflow
    """
    start = time.time()
    logger.info(
        f"Run requested — company={request.company!r} "
        f"type={request.intelligence_type!r} "
        f"days={request.time_range_days} "
        f"notify={request.notify_email!r}"
    )

    # Validate competitor against registry
    if COMPETITOR_REGISTRY:
        if request.company.lower() not in COMPETITOR_REGISTRY:
            known = [c["name"] for c in COMPETITOR_REGISTRY.values()]
            raise HTTPException(
                status_code=422,
                detail=(
                    f"'{request.company}' not in competitor registry. "
                    f"Known competitors: {known}"
                )
            )

    # Snap time_range_days to nearest valid value (7, 14, or 30)
    days = request.time_range_days
    snapped_days = min([7, 14, 30], key=lambda x: abs(x - days))

    # Build run_id for log correlation
    run_id = (
        f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_"
        f"{request.company.lower().replace(' ', '-')}"
    )

    # Build fully initialised agent state
    initial_state = default_state(
        competitor=request.company,
        intelligence_type=request.intelligence_type,
        time_range_days=snapped_days,
        run_id=run_id,
    )

    # Run the LangGraph graph in a thread pool
    # (graph.invoke is synchronous — run_in_executor keeps FastAPI responsive)
    try:
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, agent_graph.invoke, initial_state
        )
    except Exception as e:
        logger.error(f"Agent run failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent run failed: {str(e)}"
        )

    elapsed = round(time.time() - start, 1)
    logger.info(f"Run complete — {elapsed}s — company={request.company!r}")

    # Save report to reports/ directory
    _save_report(request, result, elapsed)

    # Build response payload
    response_payload = {
        "competitor":         request.company,
        "intelligence_type":  request.intelligence_type,
        "time_range_days":    snapped_days,
        "signals":            result.get("evaluated_signals", []),
        "executive_takeaway": result.get("final_brief", ""),
        "llm_calls_made":     result.get("llm_calls_made", 0),
        "elapsed_seconds":    elapsed,
        "generated_at":       datetime.utcnow().isoformat() + "Z",
        "notify_email":       request.notify_email or "",
    }

    # Notify N8N for email delivery if email provided (non-blocking)
    if request.notify_email and result.get("final_brief"):
        asyncio.create_task(_notify_n8n(response_payload))

    return response_payload


@app.post("/notify")
async def notify(payload: dict):
    """
    Can be called directly to trigger N8N email delivery.
    Useful for testing the N8N workflow independently.
    """
    result = await _notify_n8n(payload)
    return result


# ── N8N NOTIFICATION ──────────────────────────────────────────────────────────

async def _notify_n8n(payload: dict) -> dict:
    """
    POST the brief payload to the N8N webhook URL.
    N8N Workflow 1 listens on this webhook and handles
    PDF formatting and email delivery.
    Silent on failure — never crashes the response.
    """
    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "")

    if not n8n_webhook_url:
        logger.warning("N8N_WEBHOOK_URL not set — skipping N8N notification")
        return {"status": "skipped", "reason": "N8N_WEBHOOK_URL not configured"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(n8n_webhook_url, json=payload)
            response.raise_for_status()
        logger.info(f"N8N notified — status={response.status_code}")
        return {"status": "notified"}
    except httpx.TimeoutException:
        logger.warning("N8N notification timed out (non-critical)")
        return {"status": "timeout"}
    except Exception as e:
        logger.warning(f"N8N notification failed (non-critical): {e}")
        return {"status": "failed", "error": str(e)}


# ── REPORT PERSISTENCE ────────────────────────────────────────────────────────

def _save_report(request: RunRequest, result: dict, elapsed: float):
    """
    Save every generated brief to reports/ as a JSON file.
    Filename: reports/YYYY-MM-DD_competitor_type.json
    Silent on failure — never crashes the response.
    """
    try:
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        date_str    = datetime.utcnow().strftime("%Y-%m-%d")
        company_str = request.company.lower().replace(" ", "-")
        type_str    = request.intelligence_type.lower().replace(" ", "-")
        filename    = reports_dir / f"{date_str}_{company_str}_{type_str}.json"

        payload = {
            "competitor":         request.company,
            "intelligence_type":  request.intelligence_type,
            "time_range_days":    request.time_range_days,
            "generated_at":       datetime.utcnow().isoformat() + "Z",
            "elapsed_seconds":    elapsed,
            "signals":            result.get("evaluated_signals", []),
            "executive_takeaway": result.get("final_brief", ""),
            "llm_calls_made":     result.get("llm_calls_made", 0),
        }

        with open(filename, "w") as f:
            json.dump(payload, f, indent=2)

        logger.info(f"Report saved — {filename.name}")

    except Exception as e:
        logger.warning(f"Report save failed (non-critical): {e}")