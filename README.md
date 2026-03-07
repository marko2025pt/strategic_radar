[//]: # (Version 1.1 — Final demo delivery to Ironhack 2026-03-06)
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
| **casestudy.md** | Full case study write-up — the Ironhack AI Consulting submission |
| **architecture_decisions.md** | Every architectural decision, the reasoning behind it, and trade-offs made |
| **project_summary.md** | Current build status, completed modules, and immediate next step |
| **product_roadmap.md** | Full product roadmap V1.2 → V3.0 — versioned features, effort estimates, and strategic rationale |

> Start with this file for project context and setup instructions.
> Read `casestudy.md` for the full problem framing, solution narrative, and design thinking.
> To understand why the system was designed the way it was, read `architecture_decisions.md`.
> To see what has been built and what is currently in progress, read `project_summary.md`.
> To explore the product roadmap from V1.2 to V3.0, read `product_roadmap.md`.

---

## Live System

| Service | URL |
|---|---|
| **Overview** | https://strategicradar-production.up.railway.app/ |
| **Tool UI** | https://strategicradar-production.up.railway.app/tool |
| **Slides** | https://strategicradar-production.up.railway.app/slides |
| **API** | https://strategicradar-production.up.railway.app/run |
| **Health** | https://strategicradar-production.up.railway.app/health |
| **API Docs** | https://strategicradar-production.up.railway.app/docs |

The system is always-on. No local machine required.

---

## What This System Does

Most competitive intelligence tools generate generic company profiles.
This system does something different.

Given a competitor name (or a target sector) and a time window, it autonomously
finds recent market signals, evaluates each one against your company's specific
business identity and strategic objectives, and produces a 1-page executive
snapshot answering one question:

**"Does this signal matter to us — and why?"**

The output is not a report. It is a bounded, actionable intelligence brief.

---

## MVP Status — V1.1 Complete

**MVP V1.0 — Competitor Intelligence** COMPLETE
Monitor competitor moves. Evaluate strategic relevance. Deliver executive snapshot.
- Tools: Tavily + NewsAPI + HackerNews
- Input: competitor name + time window + optional email
- Output: ranked signal brief in UI + HTML email delivery

**MVP V1.1 — + Business Opportunities** COMPLETE
Monitor EU public tenders and private sector opportunities aligned with strategic objectives.
- Adds: TED EU Open Data API (public tenders)
- Adds: Private opportunity and pre-tender signal collection via Tavily
- Adds: Business Opportunities branch in LangGraph
- Input: sector name + time window + optional email
- Output: ranked tender/opportunity brief in UI + HTML email delivery

**MVP V1.2 — + Technology Developments** Post-MVP
Monitor emerging technologies relevant to DOOH and kiosk ecosystem.
- Adds: Technology Developments branch in LangGraph
- Adds: Technology Watchlist queries (KB already ingested)

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
External APIs      →  Live signal data (Tavily, NewsAPI, HackerNews, TED EU)
LLM                →  Strategic evaluation & brief generation (OpenAI GPT-4o)
SendGrid           →  Email delivery
```

### Design Principles

- Cognition, control, and orchestration are strictly separated
- Only the research phase uses dynamic reasoning (ReAct)
- All subsequent phases are deterministic and structured
- Autonomy is bounded — max 7 LLM calls per run (Competitor Moves)
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

### LLM Call Budget — Competitor Moves (Per Run)

| Step | Calls |
|---|---|
| Strategic selection | 1 |
| Per-signal evaluation | max 5 |
| Executive brief generation | 1 |
| **Total** | **max 7** |

---

## Workflow — MVP V1.1 (Business Opportunities)
```
START
  → Input Validation         (deterministic — sector name check)
  → Query Builder            (deterministic — no LLM)
  → Opportunity Collection   (TED EU tenders + Tavily private/pre-tender signals)
  → Opportunity Evaluation   (LLM + RAG — tenders, private signals, pre-tender signals)
  → Opportunity Brief        (LLM — single call, ranked by urgency and fit)
  → Notify N8N               (non-blocking — triggers email delivery)
  → Return brief to UI
END
```

Signal types collected in V1.1:
- **Tenders** — live EU public procurement notices via TED Open Data API
- **Private opportunities** — commercial expansion signals via Tavily (press, trade press)
- **Pre-tender signals** — budget approvals, city council decisions, EU fund allocations (3–12 month positioning window)

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

| Tool | API | Purpose | Status |
|---|---|---|---|
| `tavily.py` | Tavily API | Web search — primary signal discovery | V1.0 |
| `newsapi.py` | NewsAPI | News articles — signal discovery | V1.0 |
| `hackernews.py` | HN Algolia API | Technology signals — no API key required | V1.0 |
| `ted.py` | TED EU Open Data API | EU public tenders — business opportunities | V1.1 |

All tools are defined using `@mcp.tool()` decorator — in-process MCP implementation.
See `architecture_decisions.md` Decision 12 for rationale.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Overview landing page |
| `GET` | `/tool` | Intelligence tool UI |
| `GET` | `/slides` | Presentation slides |
| `GET` | `/ui` | Alias for `/tool` — backward compatibility |
| `GET` | `/api/info` | Service info and available endpoints (JSON) |
| `GET` | `/health` | Verify Pinecone, LLM, and registry status |
| `POST` | `/run` | Trigger the LangGraph agent — returns intelligence brief |
| `POST` | `/notify` | Trigger N8N webhook for email delivery |
| `GET` | `/docs` | Swagger UI — interactive API documentation |

### POST /run — Request

For **Competitor Moves**, `subject` is the competitor name.
For **Business Opportunities**, `subject` is the sector name.

```json
{
  "subject": "Acrelec",
  "intelligence_type": "Competitor Moves",
  "time_range_days": 7,
  "notify_email": "user@example.com"
}
```

```json
{
  "subject": "Smart Cities",
  "intelligence_type": "Business Opportunities",
  "time_range_days": 30,
  "notify_email": "user@example.com"
}
```

### POST /run — Response
```json
{
  "run_id": "run_20260306_100000_acrelec",
  "subject": "Acrelec",
  "intelligence_type": "Competitor Moves",
  "time_range_days": 7,
  "signals": [...],
  "tenders": [...],
  "private_opportunities": [...],
  "pretender_opportunities": [...],
  "executive_takeaway": "...",
  "final_brief": "...",
  "llm_calls_made": 5,
  "generated_at": "2026-03-06T10:00:00Z",
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
│   ├── graph.py                  ← LangGraph workflow definition (V1.0 + V1.1 branches)
│   ├── nodes.py                  ← Node implementations (6 V1.0 nodes + 3 V1.1 nodes)
│   ├── state.py                  ← TypedDict state schema (V1.0 + V1.1 fields)
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
│   ├── main.py                   ← FastAPI server v1.1.0
│   └── static/
│       ├── index.html            ← Overview landing page
│       ├── tool.html             ← Intelligence tool UI (V1.0 + V1.1)
│       └── slides.html           ← Presentation slides
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
├── casestudy.md                  ← Ironhack submission case study
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
# http://localhost:8000/tool
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

## What Is NOT in MVP v1.1

All of the following are documented in `product_roadmap.md` with version targets and effort estimates:

- Technology Developments branch — V1.2
- Multi-competitor / multi-sector runs in a single request
- Scheduling via UI
- Cross-signal correlation and deduplication
- Trend synthesis across time windows
- Editable strategy and competitor registry via UI
- Report history viewer
- Tool performance dashboard
- User feedback loop on signal quality

---

## Learning Goals

- Build a working MVP and validate with real industry use case
- Learn to scope deliberately — ship something that works over something perfect
- Hands-on exposure to LangGraph and N8N beyond labs
- Learn the full journey: from local code to live deployed product
- Understand the difference between information and intelligence
