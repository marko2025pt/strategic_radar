# Project Summary — Strategic Radar

## Project Identity
- **Name:** Strategic Radar (`strategic_radar`)
- **GitHub:** github.com/marko2025pt/strategic_radar
- **Industry:** DOOH and Self-Service Kiosk ecosystem
- **Company modelled:** PARTTEAM & OEMKIOSKS (Vila Nova de Famalicão, Portugal)
- **Purpose:** Autonomous competitive intelligence agent that monitors market signals, evaluates strategic relevance using RAG, and delivers 1-page executive snapshots

---

## Architecture
- MVP layered delivery: V1.0 (Competitor Moves) → V1.1 (Business Opportunities) → V1.2 (Technology Developments)
- Fallback rule: if V1.2 not done demo V1.1, if V1.1 not done demo V1.0
- Full architecture documented in `architecture_decisions.md` (15 decisions logged)
- Post-MVP improvements documented in `product_backlog.md` (22 items)
- Tech stack: LangGraph + ReAct + Pinecone RAG + FastAPI + Gradio + N8N Cloud + Railway

---

## Project Structure
```
strategic_radar/
├── core/
│   ├── __init__.py
│   └── logging_config.py         ✅ DONE
├── agent/
│   ├── graph.py                  ✅ DONE
│   ├── nodes.py                  ✅ DONE
│   ├── state.py                  ✅ DONE
│   └── tools/
│       ├── __init__.py           ✅ DONE
│       ├── utils.py              ✅ DONE
│       ├── domain_lists.json     ✅ DONE
│       ├── tavily.py             ✅ DONE
│       ├── newsapi.py            ✅ DONE
│       ├── hackernews.py         ✅ DONE
│       └── ted.py                ← V1.1
├── rag/
│   ├── ingest.py                 ✅ DONE — run once, never again
│   ├── retriever.py              ✅ DONE
│   └── kb/
│       ├── business_profile.md       ✅ DONE
│       ├── strategic_direction.md    ✅ DONE
│       ├── competitor_registry.json  ✅ DONE
│       └── technology_watchlist.md   ✅ DONE
├── api/
│   └── main.py                   ← next
├── n8n/
│   └── workflow.json             ← after api
├── logs/
│   └── *.log                     ← gitignored, one file per day
├── reports/                      ← generated snapshots saved here
├── .env
├── .env.example
├── requirements.txt
└── README.md
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

---

## Pipeline Status

End-to-end pipeline verified ✅

First real run — Acrelec, Competitor Moves, 7 days:
- 5 raw signals collected (all from Tavily)
- 3 signals selected by LLM
- 3 signals evaluated with RAG grounding
- Executive brief generated
- 5/7 LLM calls used
- Key finding: Glory fully acquired Acrelec + leadership reset
  → High impact on PARTTEAM's QSR and international expansion objectives

---

## Immediate Next Step
Build `api/main.py` — FastAPI server with Gradio UI mounted at /ui.