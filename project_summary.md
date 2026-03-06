# Strategic Radar - Autonomous Strategic Intelligence Snapshot Engine
# Project Summary (MVP V1.0)

## Project Identity
- **Name:** Strategic Radar (`strategic_radar`)
- **GitHub:** github.com/marko2025pt/strategic_radar
- **Live System:** https://strategicradar-production.up.railway.app
- **Industry:** DOOH and Self-Service Kiosk ecosystem
- **Company modelled:** PARTTEAM & OEMKIOSKS (Vila Nova de Famalicão, Portugal)
- **Purpose:** Autonomous competitive intelligence agent that monitors market signals, evaluates strategic relevance using RAG, and delivers 1-page executive snapshots

---

## MVP V1.0 Status — COMPLETE ✅

All core components built, deployed, tested, and documented.

| Component | Status |
|---|---|
| LangGraph pipeline — 6 nodes, ReAct loop | ✅ DONE |
| RAG system — 24 chunks in Pinecone | ✅ DONE |
| 3 MCP tools — Tavily, NewsAPI, HackerNews | ✅ DONE |
| FastAPI server — /run, /health, /notify | ✅ DONE |
| Custom HTML UI — cascading dropdowns, live progress | ✅ DONE |
| Railway deployment — always-on, auto-deploy | ✅ DONE |
| N8N Workflow 1 — on-demand, email delivery | ✅ DONE |
| N8N Workflow 2 — scheduled weekly, all competitors | ✅ DONE |
| SendGrid email delivery — HTML format | ✅ DONE |
| Architecture documented — 16 decisions | ✅ DONE |
| Post-MVP backlog — 22 items | ✅ DONE |

---

## Architecture
- MVP layered delivery: V1.0 (Competitor Moves) → V1.1 (Business Opportunities) → V1.2 (Technology Developments)
- Fallback rule: if V1.2 not done demo V1.1, if V1.1 not done demo V1.0
- Full architecture documented in `architecture_decisions.md` (16 decisions logged)
- Post-MVP improvements documented in `product_backlog.md` (22 items)
- Tech stack: LangGraph + ReAct + Pinecone RAG + FastAPI + Custom HTML UI + N8N Cloud + Railway + SendGrid

---

## Project Structure
```
strategic_radar/
├── core/
│   ├── __init__.py
│   └── logging_config.py             ✅ DONE
├── agent/
│   ├── graph.py                      ✅ DONE
│   ├── nodes.py                      ✅ DONE
│   ├── state.py                      ✅ DONE
│   └── tools/
│       ├── __init__.py               ✅ DONE
│       ├── utils.py                  ✅ DONE
│       ├── domain_lists.json         ✅ DONE
│       ├── tavily.py                 ✅ DONE
│       ├── newsapi.py                ✅ DONE
│       ├── hackernews.py             ✅ DONE
│       └── ted.py                    ← V1.1
├── rag/
│   ├── ingest.py                     ✅ DONE — run once, never again
│   ├── retriever.py                  ✅ DONE
│   └── kb/
│       ├── business_profile.md       ✅ DONE
│       ├── strategic_direction.md    ✅ DONE
│       ├── competitor_registry.json  ✅ DONE
│       └── technology_watchlist.md   ✅ DONE
├── api/
│   ├── main.py                       ✅ DONE
│   └── static/
│       └── index.html                ✅ DONE
├── n8n/
│   ├── workflow1_ondemand.json       ✅ DONE
│   └── workflow2_scheduled.json      ✅ DONE
├── logs/
│   └── *.log                         ← gitignored, one file per day
├── reports/                          ← generated snapshots saved here
├── Procfile                          ✅ DONE
├── railway.json                      ✅ DONE
├── .env.example                      ✅ DONE
├── requirements.txt                  ✅ DONE
└── README.md                         ✅ DONE
```

---

## Knowledge Base — 4 Documents, 24 Chunks in Pinecone

| Document | Chunks |
|---|---|
| business_profile.md | 5 |
| strategic_direction.md | 6 |
| competitor_registry.json | 6 |
| technology_watchlist.md | 7 |
| **Total** | **24** |

Pinecone index: `strategic-intelligence-kb` — AWS us-east-1 — verified ✅

---

## Completed Modules

### core/logging_config.py ✅
Centralised logging for all modules. Daily rotating log files.
Named loggers, file handler at DEBUG, console at INFO.

### rag/ingest.py ✅
Run once. Chunks KB documents, embeds with OpenAI, upserts 24
vectors to Pinecone. Do not run again unless KB changes.

### rag/retriever.py ✅
Core retrieval function with chunk_type filtering. Verified
against live Pinecone index. Returns empty list on failure —
never raises.

### agent/state.py ✅
LangGraph TypedDict state schema. 8 pipeline stages, 13 fields.
`default_state()` factory with input validation guards.

### agent/graph.py ✅
LangGraph workflow definition. 6 nodes, 1 conditional edge
after validate, linear from there. V1.1 and V1.2 extension
points commented in route_after_validation().

### agent/nodes.py ✅
All 6 nodes implemented and tested end to end:
- validate — competitor registry check, deterministic
- build_queries — query construction, deterministic
- collect_signals — ReAct agent loop (Tavily + NewsAPI + HN)
- select_signals — 1 LLM call, top 5 signal selection
- evaluate_signals — up to 5 LLM + RAG calls, confidence scoring
- generate_brief — 1 LLM call, executive snapshot generation

### agent/tools/utils.py ✅
Shared FastMCP instance and _classify_source() utility.
Domain lists loaded from domain_lists.json — editable without
code changes.

### agent/tools/domain_lists.json ✅
Primary and secondary domain lists for source quality
classification. Drives confidence scoring. Editable JSON.

### agent/tools/tavily.py ✅
Web search tool. Primary signal discovery. @mcp.tool() registered.

### agent/tools/newsapi.py ✅
News articles tool. Free tier capped at 28 days. @mcp.tool() registered.

### agent/tools/hackernews.py ✅
Technology signal tool via Algolia HN Search API. No API key
required. @mcp.tool() registered.

### agent/tools/ted.py ✅
EU public tenders tool. TED EU Open Data API. Searches by CPV code,
keyword, country, and publication date. Returns structured tender objects.
No API key required. Called directly in collect_opportunities (deterministic
— no ReAct loop needed). @mcp.tool() registered.

### api/main.py ✅
FastAPI server. Endpoints: /run, /health, /notify, /ui.
CORS enabled. Competitor registry validation. Report persistence.
Non-blocking N8N notification via asyncio background task.

### api/static/index.html ✅
Single-page HTML UI. Cascading dropdowns (intelligence type →
competitor/sector/technology). Live step-by-step progress animation.
V1.0: signal cards grouped by impact level. V1.1: tender cards and
private opportunity cards with deadline, value, authority, and
recommended action fields. Stats row adapts per intelligence type.
Executive takeaway panel. Email field for on-demand delivery.
Run history. Export to text.

### n8n/workflow1_ondemand.json ✅
Webhook-triggered N8N workflow. Receives brief payload from FastAPI
/notify. Formats HTML email. Delivers via SendGrid to user-provided
address. Published and live.

### n8n/workflow2_scheduled.json ✅
Schedule-triggered N8N workflow. Every Monday 8am. Loops through
all 6 competitors via SplitInBatches. Calls FastAPI /run for each.
Aggregates all briefs. Formats combined HTML email. Delivers via
SendGrid to fixed recipient. Published and live.

---

## Pipeline Verified — Sample Runs

**Run 1 — Acrelec, Competitor Moves, 7 days:**
- 3 signals selected and evaluated
- All High impact
- Key finding: Glory acquisition + CEO appointment + facial auth tech
- 5/7 LLM calls, 27.5s

**Run 2 — Wanzl, Competitor Moves, 7 days:**
- 3 Medium impact signals
- North America expansion activity
- 5/7 LLM calls, 34.4s

**Run 3 — Weekly Scheduled Run, All 6 Competitors:**
- 6 competitors processed sequentially
- Combined HTML email delivered
- Total: ~28 LLM calls, ~3.5 minutes end to end

---

## V1.1

### V1.1 — Business Opportunities (TED EU Tenders)
The LangGraph graph already has the extension point stubbed in
`route_after_validation()`. Adding V1.1 requires:

V1.1 — Business Opportunities (TED EU Tenders) ✅ COMPLETE
ted.py built and integrated. New nodes collect_opportunities,
evaluate_opportunities, generate_opportunity_brief added to
nodes.py. Graph branch activated in graph.py. State fields updated
(subject, sector, raw_tenders, raw_private_signals,
evaluated_tenders, evaluated_private). API updated (subject
replaces company in request/response). UI updated to render tender
and private opportunity cards with V1.1-specific fields.

### V1.2 — Technology Developments
Similar extension pattern to V1.1. Technology Watchlist already
embedded in Pinecone (7 chunks). Requires:

1. Technology signal collection node — use Tavily + HackerNews
   with technology-specific queries derived from watchlist
2. Technology evaluation node — match signals against watchlist chunks
3. Technology brief node — format technology snapshot
4. UI second input for Technology Developments already implemented

### Post-MVP Backlog (22 items)
Full list with effort estimates in `product_backlog.md`.

**Highest priority items:**
- IQ-1 — Tool performance dashboard (M)
- RAG-1 — KB update workflow — edit markdown, one command, Pinecone updated (S)
- ARCH-2 — Cross-signal correlation and deduplication (M)
- OUT-2 — Report persistence and history viewer (S)
- OPS-1 — Scheduled runs via N8N UI (S — already done in Workflow 2)
- OPS-4 — /health endpoint already done ✅

### Scheduling from the UI (Post-MVP)
Currently schedules are configured directly in N8N. Post-MVP, the UI
could offer a "Schedule" tab where users set frequency, competitors,
and recipient. FastAPI would register the schedule via N8N API.
Documented in product_backlog.md as OPS-1 variant.
