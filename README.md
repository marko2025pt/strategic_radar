# Strategic Radar - Autonomous Strategic Intelligence Snapshot Engine
### Bounded Signal Evaluation for Competitive Decision-Making
### Built for the DOOH & Self-Service Kiosk Industry

## Important Note

PARTTEAM & OEMKIOSKS is used as a case study for demonstration purposes only.
All information was sourced from publicly available sources. This project has
no affiliation with or endorsement from PARTTEAM & OEMKIOSKS.

The strategic objectives defined in `rag/kb/strategic_direction.md` are
invented but plausible — they are informed by publicly available information
about the company but do not represent the actual strategic priorities of
PARTTEAM & OEMKIOSKS.

---

## Project Documents

| Document | Purpose |
|---|---|
| **README.md** | Project overview, architecture, setup and deployment guide |
| **architecture_decisions.md** | Every architectural decision, the reasoning behind it, and trade-offs made |
| **project_summary.md** | Current build status, completed modules, and immediate next step |
| **product_backlog.md** | Post-MVP improvements — categorised, layered, and effort-estimated |

> Start with this file for project context and setup instructions.
> To understand why the system was designed the way it was, read `architecture_decisions.md`.
> To see what has been built and what is currently in progress, read `project_summary.md`.
> To explore planned improvements and future capabilities, read `product_backlog.md`.

---

## Live System

| Service | URL |
|---|---|
| **UI** | https://strategicradar-production.up.railway.app/ui |
| **API** | https://strategicradar-production.up.railway.app/run |
| **Health** | https://strategicradar-production.up.railway.app/health |
| **API Docs** | https://strategicradar-production.up.railway.app/docs |

The system is always-on. No local machine required.

---

## What This System Does

Most competitive intelligence tools generate generic company profiles.
This system does something different.

Given a competitor name and a time window, it autonomously finds recent market
signals, evaluates each one against your company's specific business identity
and strategic objectives, and produces a 1-page executive snapshot answering
one question:

**"Does this signal matter to us — and why?"**

The output is not a report. It is a bounded, actionable intelligence brief.

---

## MVP Status — v1.0 Complete ✅

**MVP V1.0 — Competitor Intelligence** ✅ COMPLETE
Monitor competitor moves. Evaluate strategic relevance. Deliver executive snapshot.
- Tools: Tavily + NewsAPI + HackerNews
- Input: competitor name + time window + optional email
- Output: ranked signal brief in UI + HTML email delivery

**MVP V1.1 — + Business Opportunities** ← Post-MVP
Monitor EU public tenders aligned with strategic objectives.
- Adds: TED API (EU public procurement)
- Adds: Business Opportunities branch in LangGraph

**MVP V1.2 — + Technology Developments** ← Post-MVP
Monitor emerging technologies relevant to DOOH and kiosk ecosystem.
- Adds: Technology Developments branch in LangGraph
- Adds: Technology Watchlist to Knowledge Base

---

## Industry Focus

The MVP is instantiated for the **DOOH and Self-Service Kiosk ecosystem**:
- MUPIS (Municipal Urban Passenger Information Systems)
- Digital Signage
- Self-Service Kiosks (airports, QSR, retail, smart cities)

The architecture is industry-agnostic and reusable across verticals.

---

## System Architecture

### Layer Model
```
N8N Cloud          →  Operational orchestration & delivery
FastAPI + Railway  →  HTTP interface & entry point
Custom HTML UI     →  Human-facing interface for manual runs & demos
LangGraph          →  Cognitive workflow controller
ReAct Agent        →  Signal discovery & research loop
Pinecone RAG       →  Strategic identity & objectives grounding
External APIs      →  Live signal data (Tavily, NewsAPI, HackerNews)
LLM                →  Strategic evaluation & brief generation (OpenAI)
SendGrid           →  Email delivery
```

### Design Principles

- Cognition, control, and orchestration are strictly separated
- Only the research phase uses dynamic reasoning (ReAct)
- All subsequent phases are deterministic and structured
- Autonomy is bounded — max 7 LLM calls per run
- The system always produces output, surfacing uncertainty when data is insufficient
- Every decision is logged for observability and debugging

---

## Workflow — MVP V1.0 (Competitor Moves)
```
START
  → Input Validation        (deterministic — competitor registry check)
  → Query Builder           (deterministic — no LLM)
  → API Signal Collection   (Tavily + NewsAPI + HackerNews, filtered by time window)
  → Strategic Selection     (LLM — selects top 5 signals from raw results)
  → Per-Signal Evaluation   (LLM + RAG — max 5 calls, one per signal)
  → Executive Brief         (LLM — single call, ranked by impact)
  → Notify N8N              (non-blocking — triggers email delivery)
  → Return brief to UI
END
```

### LLM Call Budget (Per Run)

| Step | Calls |
|---|---|
| Strategic selection | 1 |
| Per-signal evaluation | max 5 |
| Executive brief generation | 1 |
| **Total** | **max 7** |

---

## N8N Workflows

Two workflows handle automated orchestration and email delivery.

**Workflow 1 — On-Demand**
```
Webhook (called by FastAPI /notify after a UI run)
  → Check brief exists
  → Format HTML email
  → Send via SendGrid to user-provided address
```

**Workflow 2 — Scheduled Weekly**
```
Schedule trigger (every Monday 8am)
  → Loop through all 6 competitors
  → Call FastAPI /run for each
  → Collect all 6 briefs
  → Format combined HTML email
  → Send via SendGrid to fixed recipient
```

Both workflows are exported as JSON in the `n8n/` directory.

---

## Knowledge Base (RAG) — Strategic Grounding Memory

The RAG system is not a generic industry overview.
It is the company's strategic identity — used to evaluate whether a signal matters.

| Document | Chunks | Purpose |
|---|---|---|
| `business_profile.md` | 5 | Company identity, products, verticals, revenue model |
| `strategic_direction.md` | 6 | 6 active strategic objectives with signal relevance criteria |
| `competitor_registry.json` | 6 | Controlled list of monitored competitors |
| `technology_watchlist.md` | 7 | Emerging technologies relevant to DOOH and kiosk ecosystem |
| **Total** | **24** | Pinecone index: `strategic-intelligence-kb` |

RAG is used only during signal evaluation.
It answers: *"Given who we are and where we want to go, does this signal matter?"*

---

## MCP Tools

| Tool | API | Purpose | Version |
|---|---|---|---|
| `tavily.py` | Tavily API | Web search — primary signal discovery | V1.0 |
| `newsapi.py` | NewsAPI | News articles — signal discovery | V1.0 |
| `hackernews.py` | HN Algolia API | Technology signals — no API key required | V1.0 |
| `ted.py` | TED EU API | EU public tenders — business opportunities | V1.1 |

All tools are defined using `@mcp.tool()` decorator — in-process MCP implementation.
See `architecture_decisions.md` Decision 12 for rationale.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Service info and available endpoints |
| `GET` | `/health` | Verify Pinecone, LLM, and registry status |
| `POST` | `/run` | Trigger the LangGraph agent — returns intelligence brief |
| `POST` | `/notify` | Trigger N8N webhook for email delivery |
| `GET` | `/ui` | Serve the HTML interface |
| `GET` | `/docs` | Swagger UI — interactive API documentation |

### POST /run — Request
```json
{
  "company": "Acrelec",
  "intelligence_type": "Competitor Moves",
  "time_range_days": 7,
  "notify_email": "user@example.com"
}
```

### POST /run — Response
```json
{
  "competitor": "Acrelec",
  "intelligence_type": "Competitor Moves",
  "time_range_days": 7,
  "signals": [...],
  "executive_takeaway": "...",
  "llm_calls_made": 5,
  "elapsed_seconds": 34.2,
  "generated_at": "2026-03-04T10:00:00Z",
  "notify_email": "user@example.com"
}
```

---

## Deployment Architecture

```
Developer PC  →  VS Code + Git only
GitHub        →  Code repository (auto-deploy trigger)
Railway       →  FastAPI + LangGraph server (always-on, auto-deploys on git push)
N8N Cloud     →  Workflow orchestration & email delivery
Pinecone      →  Vector database (free tier, AWS us-east-1)
OpenAI        →  LLM (GPT-4o)
SendGrid      →  Email delivery (free tier)
```

`git push` → Railway auto-deploys in ~60 seconds. Laptop can be closed.

---

## Project Structure
```
strategic_radar/
├── agent/
│   ├── graph.py                  ← LangGraph workflow definition
│   ├── nodes.py                  ← 6 node implementations
│   ├── state.py                  ← TypedDict state schema
│   └── tools/
│       ├── __init__.py
│       ├── utils.py              ← Shared FastMCP instance + source classifier
│       ├── domain_lists.json     ← Primary/secondary domain lists
│       ├── tavily.py             ← Web search tool
│       ├── newsapi.py            ← News search tool
│       ├── hackernews.py         ← HackerNews technology signals
│       └── ted.py                ← EU tenders tool (V1.1)
├── rag/
│   ├── ingest.py                 ← Run once — chunks, embeds, upserts to Pinecone
│   ├── retriever.py              ← Pinecone vector search with metadata filtering
│   └── kb/
│       ├── business_profile.md
│       ├── strategic_direction.md
│       ├── competitor_registry.json
│       └── technology_watchlist.md
├── api/
│   ├── main.py                   ← FastAPI server + /run + /health + /notify
│   └── static/
│       └── index.html            ← Single-page HTML UI
├── core/
│   ├── __init__.py
│   └── logging_config.py         ← Centralised logging, daily rotating files
├── n8n/
│   ├── workflow1_ondemand.json   ← On-demand webhook workflow
│   └── workflow2_scheduled.json  ← Scheduled weekly workflow
├── reports/                      ← Generated intelligence briefs (JSON)
├── logs/                         ← Daily rotating log files (gitignored)
├── .env.example
├── .gitignore
├── Procfile                      ← Railway start command
├── railway.json                  ← Railway deployment config
├── requirements.txt
├── architecture_decisions.md
├── product_backlog.md
├── project_summary.md
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- Git
- API keys (see Environment Variables below)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/marko2025pt/strategic_radar.git
cd strategic_radar

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# 5. Ingest knowledge base into Pinecone (run once)
python rag/ingest.py

# 6. Start the FastAPI server
uvicorn api.main:app --reload --port 8000

# 7. Open the UI
# http://localhost:8000/ui
```

---

## Railway Deployment

```bash
# 1. Push to GitHub
git push origin main

# 2. Railway auto-deploys from GitHub
# Monitor at: https://railway.app

# 3. Add environment variables in Railway dashboard
# Settings → Variables → add all keys below

# 4. Health check
# https://your-railway-url.up.railway.app/health
```

---

## N8N Setup

1. Create N8N Cloud account at https://app.n8n.cloud
2. Import `n8n/workflow1_ondemand.json` — On-Demand workflow
3. Import `n8n/workflow2_scheduled.json` — Scheduled Weekly workflow
4. In each workflow, update the **Send Email** node with your verified SendGrid sender
5. Add `RAILWAY_URL` environment variable in N8N settings
6. Publish both workflows
7. Copy the Workflow 1 webhook URL → add as `N8N_WEBHOOK_URL` in Railway variables

---

## Environment Variables

```bash
# LLM
OPENAI_API_KEY=

# Vector Database
PINECONE_API_KEY=
PINECONE_INDEX=strategic-intelligence-kb

# Search Tools
TAVILY_API_KEY=
NEWS_API_KEY=

# Email Delivery
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=

# N8N Integration
N8N_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook/strategic-radar-ondemand
```

Copy `.env.example` to `.env` and fill in your keys. Never commit `.env`.

---

## What Is NOT in MVP v1.0

All of the following are documented in `product_backlog.md` with effort estimates:

- Business Opportunities branch (TED EU tenders) — V1.1
- Technology Developments branch — V1.2
- Multi-competitor runs
- Scheduling via UI
- Cross-signal correlation and deduplication
- Trend synthesis across time windows
- Editable strategy and competitor registry via UI
- Report history viewer
- Tool performance dashboard

---

## Learning Goals

- Build a working MVP and validate with real industry use case
- Learn to scope deliberately — ship something that works over something perfect
- Hands-on exposure to LangGraph and N8N beyond labs
- Learn the full journey: from local code to live deployed product
- Understand the difference between information and intelligence
