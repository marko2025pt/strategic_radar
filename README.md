# Autonomous Strategic Intelligence Snapshot Engine
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


## What This System Does

Most competitive intelligence tools generate generic company profiles.
This system does something different.

Given a competitor name and a time window, it autonomously finds recent market signals, evaluates each one against your company's specific business identity and strategic objectives, and produces a 1-page executive snapshot answering one question:

**"Does this signal matter to us — and why?"**

The output is not a report. It is a bounded, actionable intelligence brief.

---

## MVP Roadmap — Layered Delivery Strategy

Each version is a fully working, demoable product.
Development is additive — each layer builds on the previous one.
If time runs out, fall back to the previous version. It still works.

**MVP V1.0 — Competitor Intelligence** ← Build first
Monitor competitor moves. Evaluate strategic relevance. Deliver executive snapshot.
- Tools: Tavily + NewsAPI
- Input: competitor name + time window
- Output: 1-page ranked signal brief

**MVP V1.1 — + Business Opportunities** ← Add second
Monitor EU public tenders aligned with strategic objectives.
- Adds: TED API (EU public procurement)
- Adds: Business Opportunities branch in LangGraph
- Everything from V1.0 remains unchanged

**MVP V1.2 — + Technology Developments** ← Add third
Monitor emerging technologies relevant to DOOH and kiosk ecosystem.
- Adds: Technology Developments branch in LangGraph
- Adds: Technology Watchlist to Knowledge Base
- Everything from V1.1 remains unchanged

**Fallback rule:**
V1.2 not finished → demo V1.1
V1.1 not finished → demo V1.0
V1.0 is the minimum deliverable. It ships no matter what.

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
Gradio UI          →  Human-facing interface for manual runs & demos
LangGraph          →  Cognitive workflow controller
ReAct Agent        →  Signal discovery & research loop
Pinecone RAG       →  Strategic identity & objectives grounding
External APIs      →  Live signal data
LLM                →  Strategic evaluation & brief generation
```

### Design Principles

- Cognition, control, and orchestration are strictly separated
- Only the research phase uses dynamic reasoning (ReAct)
- All subsequent phases are deterministic and structured
- Autonomy is bounded — max 7 LLM calls per run (V1.0)
- The system always produces output, surfacing uncertainty when data is insufficient
- Every decision is logged for observability and debugging

---

## Workflow — MVP V1.0 (Competitor Moves)
```
START
  → Input Validation        (deterministic — competitor registry check)
  → Query Builder           (deterministic — no LLM)
  → API Signal Collection   (Tavily + NewsAPI, filtered by time window)
  → Strategic Selection     (LLM — selects top 5 signals from raw results)
  → Per-Signal Evaluation   (LLM + RAG — max 5 calls, one per signal)
  → Executive Brief         (LLM — single call, ranked by impact)
  → Return to N8N
END
```

## Workflow — MVP V1.1 (+ Business Opportunities)
```
START
  → Input Validation
  → Route by intelligence_type
      → Competitor Moves    (V1.0 workflow)
      → Business Opps       (TED API → tender matching → opportunity brief)
  → Return to N8N
END
```

## Workflow — MVP V1.2 (+ Technology Developments)
```
START
  → Input Validation
  → Route by intelligence_type
      → Competitor Moves       (V1.0 workflow)
      → Business Opps          (V1.1 workflow)
      → Technology Developments (signal collection → tech watchlist matching → tech brief)
  → Return to N8N
END
```

### LLM Call Budget (Per Run — V1.0)

| Step | Calls |
|---|---|
| Strategic selection | 1 |
| Per-signal evaluation | max 5 |
| Executive brief generation | 1 |
| **Total** | **max 7** |

---

## User Input
```json
{
  "company": "JCDecaux",
  "intelligence_type": "Competitor Moves",
  "time_range_days": 7
}
```

**Constraints:**
- Company must exist in the competitor registry
- One intelligence type per run
- One competitor per run
- Max 5 signals evaluated per run

---

## Output

A 1-page executive strategic snapshot:
```
Strategic Snapshot — JCDecaux (Last 7 Days)

High Impact
...

Medium Impact
...

Low Impact
...

Executive Takeaway
3–4 concise sentences.
```

Delivered via email as PDF (automated) or displayed in Gradio UI (manual/demo).

---

## Knowledge Base (RAG) — Strategic Grounding Memory

The RAG system is not a generic industry overview.
It is the company's strategic identity — used to evaluate whether a signal matters.

### Documents

**1. Business Profile**
- Core products and services
- Target verticals
- Revenue model
- Geographic focus
- Competitive positioning

**2. Strategic Direction**
- 5–8 active strategic objectives
- Used to assess signal relevance and impact

**3. Competitor Registry**
- Controlled list of monitored competitors
- Prevents noise and scope creep

**4. Technology Watchlist** ← Added in V1.2
- Emerging technologies relevant to DOOH and kiosk ecosystem
- e.g. programmatic DOOH platforms, AI-driven audience measurement,
  touchless kiosk interfaces, computer vision for OOH analytics,
  5G-connected signage, edge computing for kiosks
- Used during Technology Developments evaluation

### RAG is used only during signal evaluation.
It answers: *"Given who we are and where we want to go, does this signal matter?"*

---

## Tools & APIs

| Tool | Purpose | Version |
|---|---|---|
| Tavily API | Web search — competitor signal discovery | V1.0 |
| NewsAPI | News articles — competitor signal discovery | V1.0 |
| TED API | EU public tenders — business opportunities | V1.1 |
| Pinecone | Vector database — strategic grounding | All |

---

## Entry Points

**Gradio UI** (`/ui`)
Human-facing interface. Competitor selected from dropdown (registry-controlled).
Intelligence type selector. Time range selector (7 / 14 / 30 days).
Displays snapshot in browser. Used for manual runs and demos.

**N8N Cloud**
Automated orchestration. Webhook or scheduled trigger.
Sends input to FastAPI, receives output, converts to PDF, delivers via email.

Both entry points call the same FastAPI endpoint.

---

## Deployment
```
Your PC       →  VS Code + Git only
GitHub        →  Code repository (auto-deploy trigger)
Railway       →  FastAPI + LangGraph server (always-on)
N8N Cloud     →  Workflow orchestration & email delivery
Pinecone      →  Vector database (free tier)
LLM           →  Anthropic Claude / OpenAI
```

`git push` → Railway auto-deploys. Laptop can be closed.

---

## What Is NOT in MVP

- Multi-competitor runs
- Scheduling and monitoring
- Cross-signal correlation
- Trend synthesis
- Editable strategy via UI
- Long analytical reports
- Open-ended company input

All moved to post-MVP backlog.

---

## Project Structure
```
autonomous-strategic-intelligence/
├── agent/
│   ├── agent.py              ← Main entrypoint
│   ├── graph.py              ← LangGraph workflow definition
│   ├── nodes.py              ← Node implementations
│   ├── state.py              ← TypedDict state schema
│   └── tools/
│       ├── tavily.py         ← Web search tool (V1.0)
│       ├── newsapi.py        ← News search tool (V1.0)
│       └── ted.py            ← EU tenders tool (V1.1)
├── rag/
│   ├── ingest.py             ← Document chunking & embedding
│   ├── retriever.py          ← Pinecone vector search
│   └── kb/
│       ├── business_profile.md
│       ├── strategic_direction.md
│       ├── competitor_registry.json
│       └── technology_watchlist.md  ← V1.2
├── api/
│   └── main.py               ← FastAPI server + Gradio mount
├── n8n/
│   └── workflow.json         ← Exported N8N workflow
├── reports/                  ← Generated sample snapshots
├── tests/                    ← API test scripts
├── .env.example
├── architecture_decisions.md ← Architecture decision log
├── requirements.txt
└── README.md
```

---

## Setup

1. Clone the repository
2. Create virtual environment and install dependencies
3. Configure `.env` with API keys (see `.env.example`)
4. Initialize Pinecone index and ingest KB documents
5. Run FastAPI server locally to test
6. Push to GitHub — Railway auto-deploys
7. Configure N8N Cloud workflow with Railway URL
8. Open Gradio UI at `/ui` to run first snapshot

---

## Environment Variables
```
ANTHROPIC_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX=
TAVILY_API_KEY=
NEWS_API_KEY=
```

---

## Learning Goals

- Build a working MVP and validate with real industry feedback
- Learn to scope and not overengineer — ship something that works over something that is perfect
- Get hands-on exposure to LangGraph and N8N beyond the labs
- Learn the full journey: from code running on a laptop to a live deployed product that others can actually use