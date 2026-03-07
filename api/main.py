# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
"""
api/main.py  —  V1.1 + navigation update xxx

Changes:
  - / now serves index.html (Overview landing page)
  - /tool serves tool.html (the intelligence tool)
  - /slides serves slides.html (the presentation)
  - /ui kept as alias for /tool (backward compatibility)
  - Root JSON endpoint moved to /api/info
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.graph import graph
from agent.state import default_state
from core.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Strategic Radar — Intelligence Snapshot Engine",
    description="Autonomous strategic intelligence agent for PARTTEAM & OEMKIOSKS",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    subject: str = Field(
        ...,
        description=(
            "V1.0 Competitor Moves: competitor name (e.g. 'Acrelec'). "
            "V1.1 Business Opportunities: sector name (e.g. 'Smart Cities')."
        )
    )
    intelligence_type: str = Field(
        default="Competitor Moves",
        description="'Competitor Moves' | 'Business Opportunities'"
    )
    time_range_days: int = Field(
        default=7,
        description="7 | 14 | 30"
    )
    notify_email: Optional[str] = Field(
        default=None,
        description="Optional email for on-demand N8N delivery"
    )
    sector: Optional[str] = Field(
        default=None,
        description="Set automatically for Business Opportunities — mirrors subject"
    )


class NotifyRequest(BaseModel):
    brief_payload: dict


# ---------------------------------------------------------------------------
# Routes — HTML pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_overview():
    """Overview landing page."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Overview page not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/tool", response_class=HTMLResponse)
async def serve_tool():
    """Intelligence tool UI."""
    html_path = Path(__file__).parent / "static" / "tool.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Tool not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    """Alias for /tool — backward compatibility."""
    html_path = Path(__file__).parent / "static" / "tool.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/slides", response_class=HTMLResponse)
async def serve_slides():
    """Presentation slides."""
    html_path = Path(__file__).parent / "static" / "slides.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Slides not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------

@app.get("/api/info")
async def api_info():
    return {
        "service": "Strategic Radar",
        "version": "1.1.0",
        "endpoints": {
            "overview":     "/",
            "tool":         "/tool",
            "slides":       "/slides",
            "run":          "POST /run",
            "health":       "/health",
            "notify":       "POST /notify",
            "docs":         "/docs",
        }
    }


@app.get("/health")
async def health():
    status = {"status": "ok", "checks": {}}

    try:
        from rag.retriever import retrieve
        result = retrieve(query="test health check", top_k=1)
        status["checks"]["pinecone"] = "ok"
    except Exception as e:
        status["checks"]["pinecone"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    try:
        import os
        from dotenv import load_dotenv
        load_dotenv(override=True)
        key = os.getenv("OPENAI_API_KEY", "")
        status["checks"]["openai_key"] = "present" if key and key.startswith("sk-") else "missing"
    except Exception as e:
        status["checks"]["openai_key"] = f"error: {str(e)[:100]}"

    try:
        registry_path = Path(__file__).parent.parent / "rag" / "kb" / "competitor_registry.json"
        with open(registry_path) as f:
            reg = json.load(f)
        entries = reg if isinstance(reg, list) else reg.get("competitors", [])
        status["checks"]["competitor_registry"] = f"ok — {len(entries)} entries"
    except Exception as e:
        status["checks"]["competitor_registry"] = f"error: {str(e)[:100]}"

    return status


@app.post("/run")
async def run_agent(request: RunRequest):
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{request.subject.lower().replace(' ', '_')}"

    logger.info(
        f"[{run_id}] /run — "
        f"subject='{request.subject}' | "
        f"type='{request.intelligence_type}' | "
        f"days={request.time_range_days}"
    )

    try:
        sector = (
            request.subject
            if request.intelligence_type == "Business Opportunities"
            else request.sector
        )
        initial_state = default_state(
            subject=request.subject,
            intelligence_type=request.intelligence_type,
            time_range_days=request.time_range_days,
            run_id=run_id,
            sector=sector,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"[{run_id}] /run — graph execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    if not result.get("validated"):
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Validation failed")
        )

    response_payload = {
        "run_id":                  run_id,
        "subject":                 request.subject,
        "intelligence_type":       request.intelligence_type,
        "time_range_days":         request.time_range_days,
        "signals":                 result.get("evaluated_signals", []),
        "tenders":                 result.get("evaluated_tenders", []),
        "private_opportunities":   result.get("evaluated_private", []),
        "pretender_opportunities": result.get("evaluated_pretender", []),
        "executive_takeaway":      _extract_takeaway(result.get("final_brief", "")),
        "final_brief":             result.get("final_brief", ""),
        "llm_calls_made":          result.get("llm_calls_made", 0),
        "elapsed_seconds":         None,
        "generated_at":            datetime.now(timezone.utc).isoformat(),
        "notify_email":            request.notify_email,
        "error":                   result.get("error"),
    }

    _save_report(run_id, response_payload)

    if request.notify_email:
        asyncio.create_task(_notify_n8n(response_payload))

    return JSONResponse(content=response_payload)


@app.post("/notify")
async def notify(request: NotifyRequest):
    try:
        await _notify_n8n(request.brief_payload)
        return {"status": "ok", "message": "N8N notification triggered"}
    except Exception as e:
        logger.error(f"/notify — error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_takeaway(brief: str) -> str:
    if not brief:
        return ""
    markers = ["── EXECUTIVE TAKEAWAY", "EXECUTIVE TAKEAWAY"]
    for marker in markers:
        if marker in brief:
            section = brief.split(marker, 1)[1]
            section = section.replace("─", "").strip()
            return section
    return brief[-500:] if len(brief) > 500 else brief


def _save_report(run_id: str, payload: dict) -> None:
    try:
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / f"{run_id}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.debug(f"Report saved: {report_path}")
    except Exception as e:
        logger.warning(f"Failed to save report {run_id}: {e}")


async def _notify_n8n(payload: dict) -> None:
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)

    webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("_notify_n8n — N8N_WEBHOOK_URL not set, skipping notification")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info(f"_notify_n8n — notification delivered — status={resp.status_code}")
            else:
                logger.warning(f"_notify_n8n — unexpected status: {resp.status_code}")
    except Exception as e:
        logger.warning(f"_notify_n8n — failed (non-critical): {e}")
