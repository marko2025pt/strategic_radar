[//]: # (Version 1.1 — Final demo delivery to Ironhack 2026-03-06)
# Strategic Radar - Autonomous Strategic Intelligence Snapshot Engine
# Project Summary (MVP V1.1)

## Project Identity
- **Name:** Strategic Radar (`strategic_radar`)
- **GitHub:** github.com/marko2025pt/strategic_radar
- **Live System:** https://strategicradar-production.up.railway.app
- **Industry:** DOOH and Self-Service Kiosk ecosystem
- **Company modelled:** PARTTEAM & OEMKIOSKS (Vila Nova de Famalicão, Portugal)
- **Purpose:** Autonomous strategic intelligence agent that monitors competitor moves and business opportunities, evaluates strategic relevance using RAG, and delivers 1-page executive snapshots

---

## MVP V1.1 Status — COMPLETE

All core components built, deployed, tested, and documented.

| Component | Status |
|---|---|
| LangGraph pipeline — V1.0 branch (6 nodes, ReAct loop) | DONE |
| LangGraph pipeline — V1.1 branch (3 nodes, TED + Tavily) | DONE |
| RAG system — 24 chunks in Pinecone | DONE |
| 4 MCP tools — Tavily, NewsAPI, HackerNews, TED EU | DONE |
| FastAPI server v1.1.0 — /, /tool, /slides, /run, /health, /notify | DONE |
| Overview landing page (index.html) | DONE |
| Intelligence tool UI (tool.html) — V1.0 + V1.1 signal cards | DONE |
| Presentation slides (slides.html) | DONE |
| Railway deployment — always-on, auto-deploy | DONE |
| N8N Workflow 1 — on-demand, email delivery | DONE |
| N8N Workflow 2 — scheduled weekly, all competitors | DONE |
| SendGrid email delivery — HTML format | DONE |
| Case study document (casestudy.md) | DONE |
| Architecture documented — 16 decisions | DONE |
| Post-MVP backlog — 22 items | DONE |

---

## Architecture
- MVP layered delivery: V1.0 (Competitor Moves) → V1.1 (Business Opportunities) → V1.2 (Technology Developments)
- V1.0 and V1.1 both COMPLETE and live. V1.2 is the next extension point.
- Full architecture documented in `architecture_decisions.md` (16 decisions logged)
- Post-MVP improvements documented in `product_roadmap.md` (22 items)
- Tech stack: LangGraph + ReAct + Pinecone RAG + FastAPI + Custom HTML UI + N8N Cloud + Railway + SendGrid + OpenAI GPT-4o

---

## Project Structure
```
strategic_radar/
├── core/
│   ├── __init__.py
│   └── logging_config.py             DONE
├── agent/
│   ├── graph.py                      DONE — V1.0 + V1.1 branches live
│   ├── nodes.py                      DONE — 9 nodes (6 V1.0 + 3 V1.1)
│   ├── state.py                      DONE — V1.0 + V1.1 fields
│   └── tools/
│       ├── __init__.py               DONE
│       ├── utils.py                  DONE
│       ├── domain_lists.json         DONE
│       ├── tavily.py                 DONE
│       ├── newsapi.py                DONE
│       ├── hackernews.py             DONE
│       └── ted.py                    DONE — V1.1
├── rag/
│   ├── ingest.py                     DONE — run once, never again
│   ├── retriever.py                  DONE
│   └── kb/
│       ├── business_profile.md       DONE
│       ├── strategic_direction.md    DONE
│       ├── competitor_registry.json  DONE
│       └── technology_watchlist.md   DONE
├── api/
│   ├── main.py                       DONE — v1.1.0
│   └── static/
│       ├── index.html                DONE — Overview landing page
│       ├── tool.html                 DONE — Intelligence tool UI
│       └── slides.html               DONE — Presentation slides
├── n8n/
│   ├── workflow1_ondemand.json       DONE
│   └── workflow2_scheduled.json      DONE
├── logs/
│   └── *.log                         gitignored, one file per day
├── reports/                          generated snapshots saved here
├── Procfile                          DONE
├── railway.json                      DONE
├── .env.example                      DONE
├── requirements.txt                  DONE
├── casestudy.md                      DONE — Ironhack submission
└── README.md                         DONE
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

Pinecone index: `strategic-intelligence-kb` — AWS us-east-1 — verified

---

## Completed Modules

### core/logging_config.py
Centralised logging for all modules. Daily rotating log files.
Named loggers, file handler at DEBUG, console at INFO.

### rag/ingest.py
Run once. Chunks KB documents, embeds with OpenAI, upserts 24
vectors to Pinecone. Do not run again unless KB changes.

### rag/retriever.py
Core retrieval function with chunk_type filtering. Verified
against live Pinecone index. Returns empty list on failure —
never raises.

### agent/state.py
LangGraph TypedDict state schema. V1.0 + V1.1 fields.
Stages: input, validation, query building, V1.0 collection,
V1.1 collection (raw_tenders, raw_private_signals,
raw_pretender_signals), selection, V1.0 evaluation,
V1.1 evaluation (evaluated_tenders, evaluated_private,
evaluated_pretender), output, meta.
`default_state()` factory with input validation guards.

### agent/graph.py
LangGraph workflow definition. Two live branches:
- V1.0: validate → build_queries → collect_signals → select_signals → evaluate_signals → generate_brief
- V1.1: validate → build_queries_opportunities → collect_opportunities → evaluate_opportunities → generate_opportunity_brief
Conditional routing in route_after_validation().
V1.2 extension point stubbed (commented).

### agent/nodes.py
All 9 nodes implemented and tested end to end.

V1.0 nodes (Competitor Moves):
- validate — competitor registry check, deterministic
- build_queries — query construction, deterministic
- collect_signals — ReAct agent loop (Tavily + NewsAPI + HN)
- select_signals — 1 LLM call, top 5 signal selection
- evaluate_signals — up to 5 LLM + RAG calls, confidence scoring
- generate_brief — 1 LLM call, executive snapshot generation

V1.1 nodes (Business Opportunities):
- build_queries_opportunities — sector-specific query construction, deterministic
- collect_opportunities — TED EU tenders (deterministic) + Tavily private/pre-tender signals (ReAct)
- evaluate_opportunities — LLM + RAG calls for tenders, private signals, pre-tender signals
- generate_opportunity_brief — 1 LLM call, opportunity snapshot

Post-V1.1 fixes applied to nodes.py:
- Title translation for non-English TED tenders (inside evaluation prompt)
- Explicit High/Medium/Low impact rubric in all system prompts
- Irrelevant signal filtering — LLM returns "Irrelevant" and item is dropped
- Confidence formula: (llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2)
- Two-layer deduplication: URL exact match + title word-overlap (threshold = 4 meaningful words)

### agent/tools/utils.py
Shared FastMCP instance and _classify_source() utility.
Domain lists loaded from domain_lists.json — editable without
code changes.

### agent/tools/domain_lists.json
Primary and secondary domain lists for source quality
classification. Drives confidence scoring. Editable JSON.

### agent/tools/tavily.py
Web search tool. Primary signal discovery. @mcp.tool() registered.

### agent/tools/newsapi.py
News articles tool. Free tier capped at 28 days. @mcp.tool() registered.

### agent/tools/hackernews.py
Technology signal tool via Algolia HN Search API. No API key
required. @mcp.tool() registered.

### agent/tools/ted.py
EU public tenders tool. TED EU Open Data API. Searches by CPV code,
keyword, country, and publication date. Returns structured tender objects.
No API key required. Called directly in collect_opportunities (deterministic
— no ReAct loop needed). @mcp.tool() registered.

### api/main.py (v1.1.0)
FastAPI server. Endpoints: /, /tool, /slides, /ui (alias), /api/info,
/run, /health, /notify, /docs.
CORS enabled. Report persistence. Non-blocking N8N notification
via asyncio background task.
RunRequest uses `subject` field (competitor name or sector name).
Response includes: signals, tenders, private_opportunities,
pretender_opportunities, executive_takeaway, final_brief, run_id.

### api/static/index.html
Overview landing page. Served at /.

### api/static/tool.html
Intelligence tool UI. Served at /tool (and /ui alias).
Cascading dropdowns (intelligence type → competitor/sector).
Live step-by-step progress animation.
V1.0: signal cards grouped by impact level.
V1.1: tender cards and private opportunity cards with deadline,
value, authority, and recommended action fields.
Stats row adapts per intelligence type.
Executive takeaway panel. Email field for on-demand delivery.
Run history. Export to text.

### api/static/slides.html
Presentation slides. Served at /slides.

### n8n/workflow1_ondemand.json
Webhook-triggered N8N workflow. Receives brief payload from FastAPI
/notify. Formats HTML email. Delivers via SendGrid to user-provided
address. Published and live.

### n8n/workflow2_scheduled.json
Schedule-triggered N8N workflow. Every Monday 8am. Loops through
all 6 competitors via SplitInBatches. Calls FastAPI /run for each.
Aggregates all briefs. Formats combined HTML email. Delivers via
SendGrid to fixed recipient. Published and live.

### casestudy.md
Full case study write-up for the Ironhack AI Consulting submission.
Covers problem framing, solution architecture, design decisions,
output quality, limitations, and roadmap.

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

**Run 4 — QSR and Food Service, Business Opportunities, 30 days:**
- Tenders, private signals, and pre-tender signals evaluated
- Executive takeaway: McDonald's global expansion as kiosk supply opportunity
- Email delivered via N8N on-demand workflow

---

## V1.2 — Technology Developments (Post-MVP)

Similar extension pattern to V1.1. Technology Watchlist already
embedded in Pinecone (7 chunks). Requires:

1. Technology signal collection node — use Tavily + HackerNews
   with technology-specific queries derived from watchlist
2. Technology evaluation node — match signals against watchlist chunks
3. Technology brief node — format technology snapshot
4. UI second input for Technology Developments already implemented

V1.2 extension point is stubbed in route_after_validation() (commented).

---

## Post-MVP Backlog (22 items)
Full list with effort estimates in `product_roadmap.md`.

**Highest priority items:**
- IQ-1 — Tool performance dashboard (M)
- RAG-1 — KB update workflow — edit markdown, one command, Pinecone updated (S)
- ARCH-2 — Cross-signal correlation and deduplication (M)
- OUT-2 — Report persistence and history viewer (S)
- OPS-1 — Scheduling from the UI (Workflow 2 handles scheduled runs via N8N)
- Feedback loop on signal quality (highest strategic value post-MVP)
