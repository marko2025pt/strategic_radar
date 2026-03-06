# Strategic Radar - Autonomous Strategic Intelligence Snapshot Engine
# Product Backlog

## Document Purpose

This document captures identified post-MVP improvements to the
Strategic Radar system. It is a living document — items are added
as they are identified, prioritised as the product evolves, and
moved to architecture_decisions.md when a decision to implement
is made.

This is not a task list. It is a structured record of known
improvement opportunities, the layers they touch, and the effort
required to implement them.

---

## How to Use This Document

**Adding items:**
Any team member can add items. Follow the format below.
Group under the correct category. Assign a unique ID.

**Prioritising items:**
Prioritisation happens separately — in sprint planning or
strategic reviews. This document does not track priority.

**Implementing items:**
When an item is approved for implementation, move the key
decision to architecture_decisions.md. Reference the backlog
ID in the decision log entry.

---

## Effort Scale

| Label | Estimate |
|---|---|
| S | Half day or less |
| M | 1 day |
| L | 2–3 days |
| XL | 4+ days |

---

## Layers Reference
```
N8N Cloud          →  Operational orchestration & delivery
FastAPI + Railway  →  HTTP interface & entry point
Custom HTML UI     →  Human-facing interface
LangGraph          →  Cognitive workflow controller
ReAct Agent        →  Signal discovery & research loop
Pinecone RAG       →  Strategic identity & objectives grounding
External APIs      →  Live signal data (tools)
LLM                →  Strategic evaluation & brief generation
Logs               →  Observability and run history
```

---

## MVP Status

### ✅ MVP V1.0 — Competitor Intelligence — COMPLETE
Monitor competitor moves. Evaluate strategic relevance. Deliver executive snapshot.
- LangGraph pipeline — 6 nodes, ReAct loop ✅
- RAG system — 24 chunks in Pinecone ✅
- 3 MCP tools — Tavily, NewsAPI, HackerNews ✅
- FastAPI — /run, /health, /notify ✅
- Custom HTML UI — cascading dropdowns, live progress, signal cards ✅
- Railway deployment — always-on, auto-deploy on git push ✅
- N8N Workflow 1 — on-demand email delivery ✅
- N8N Workflow 2 — scheduled weekly, all competitors ✅
- SendGrid email delivery — HTML format ✅
- 16 architecture decisions documented ✅
- Sample reports in reports/ directory ✅

✅ MVP V1.1 — Business Opportunities (TED EU Tenders) — COMPLETE
Monitor live EU public procurement tenders and private sector expansion
signals relevant to PARTTEAM's target sectors. Surface opportunities
before competitors, with strategic fit scores and recommended actions.
What was built:

agent/tools/ted.py ✅

TED EU Open Data API integration
Search by CPV code, keyword, country, publication date
@mcp.tool() registered (in-process MCP pattern)
No API key required (open data)
Called directly in collect_opportunities (deterministic, no ReAct needed)


New nodes in agent/nodes.py ✅

collect_opportunities — calls TED directly + runs ReAct agent
(Tavily + NewsAPI + HackerNews) for private/pre-tender signals
evaluate_opportunities — LLM + RAG, match against strategic
objectives, classify as Live Tender or Private Opportunity,
assign impact_level, bid_fit_summary, deadline_urgency,
recommended_action, confidence score
generate_opportunity_brief — formats three-section output:
LIVE TENDERS / PRIVATE OPPORTUNITIES / EXECUTIVE TAKEAWAY


New branch in agent/graph.py ✅

route_after_validation() extension point activated
"Business Opportunities" routes to collect_opportunities


agent/state.py ✅

Field renamed: competitor → subject (generic across all types)
New field: sector (Optional[str]) for Business Opportunities runs
New fields: raw_tenders, raw_private_signals,
evaluated_tenders, evaluated_private


api/main.py ✅

RunRequest.company renamed to RunRequest.subject
Response payload returns tenders + private_opportunities
alongside existing signals (V1.0 backward compatible)


api/static/index.html ✅

Payload field updated: company → subject
renderBrief updated: reads data.subject (was data.competitor)
renderBrief updated: renders tenders + private_opportunities
with tender-specific fields (authority, country, deadline, value,
deadline_urgency, recommended_action)
Stats row shows Tenders + Private counts for Business Opportunities
exportBrief updated: uses data.subject throughout
demoRun updated: uses subject key



Output shape:
Business Opportunities — Smart Cities (Last 30 days)

── LIVE TENDERS ─────────────────────────────────
- Lisbon Metro Digital Signage — Deadline: 21 March 2026
  Value: €450,000 · CPV: 32321200
  Strategic Link: Smart Cities objective

── PRIVATE OPPORTUNITIES ────────────────────────
- Porto Smart Mobility Budget Approved — Feb 2026
  Signal: City council approved €2.1M smart mobility budget
  Tender expected: Q3 2026
  Strategic Link: Smart Cities + International Expansion

── EXECUTIVE TAKEAWAY ───────────────────────────
Position for Porto now. Submit for Lisbon by March 21.
LLM call budget: Max 7 calls per run. Opportunity evaluation
replaces signal evaluation. Budget allocation unchanged.

Effort: L
Risk: Medium — known pattern, new API, new prompt design
Status: ✅ COMPLETE

### 🔲 MVP V1.2 — Technology Developments — PLANNED
Monitor emerging technologies relevant to DOOH and kiosk ecosystem.
Evaluate against existing products for obsolescence risk, upgrade
opportunities, and new product gaps.

**What makes this strategically valuable:**
Not just "what technology is emerging" but "what does it mean for
our specific products." Three outputs per signal:
- Obsolescence warning — existing product at risk
- Upgrade opportunity — next hardware revision direction
- New product idea — gap in the market

**Prerequisite:** V1.1 complete. Technology Watchlist already embedded
in Pinecone (7 chunks, V1.2 ready).

- Effort: L
- Risk: Low — identical pattern to V1.1, KB already done

---

## IQ - Intelligence Quality

### IQ-1 — Tool Performance Evaluation Dashboard
Track which tools contribute signals that survive selection and reach
the final brief. Surface per-tool hit rates, selection rates, and
impact level distributions over time.
- Layers: logs, new reporting module, optional UI tab
- Effort: M
- Data is already in log files — needs a parsing and display layer

### IQ-2 — Domain List Expansion and Curation
Expand domain_lists.json with industry-specific domains discovered
through real runs. Primary/secondary classification directly affects
confidence scores.
- Layers: agent/tools/domain_lists.json only
- Effort: S (ongoing, not a one-time task)
- No code changes required — edit JSON, redeploy

### IQ-3 — Domain List Editor in UI
Allow non-technical users to add/remove domains from domain_lists.json
directly in the browser without touching files or redeploying.
- Layers: api/main.py (Custom HTML UI), agent/tools/utils.py
- Effort: M

### IQ-4 — Tool Replacement or Augmentation
Replace or supplement underperforming tools based on IQ-1 data.
NewsAPI consistently returns 0 for niche B2B queries — candidates
include Perigon, NewscatcherAPI, or a specialised DOOH RSS feed.
- Layers: agent/tools/ (new tool file), agent/tools/utils.py
- Effort: M per tool
- Prerequisite: IQ-1 data to justify the switch

### IQ-5 — Multi-Query ReAct Strategy
Currently the ReAct agent runs suggested queries as-is. Allow the
agent to generate its own follow-up queries based on what it finds —
e.g. if it finds an acquisition, search for the acquirer too.
- Layers: agent/nodes.py (collect_signals), agent/tools/
- Effort: M
- Risk: increases LLM call count — needs budget management

### IQ-6 — Confidence Score Calibration
Current formula: (rag_score * 0.6) + (source_quality * 0.4) * 10.
Weights are assumptions. After 20-30 real runs, validate whether
high-confidence signals actually prove more strategically significant.
Adjust weights based on evidence.
- Layers: agent/nodes.py (evaluate_signals)
- Effort: S (code change is one line — analysis takes longer)

---

## RAG - RAG and Knowledge Base

### RAG-1 — Strategic Knowledge Base Update Workflow
Currently KB documents require manual editing and re-running ingest.py.
Build a lightweight update workflow — edit a markdown file, run one
command, Pinecone is updated.
- Layers: rag/ingest.py, optional UI tab
- Effort: S

### RAG-2 — Strategy Editor in UI
Allow leadership to update strategic objectives directly in the browser.
Changes persist to strategic_direction.md and re-embed automatically.
- Layers: api/main.py (Custom HTML UI), rag/ingest.py, rag/kb/
- Effort: L

### RAG-3 — Competitor Registry Editor in UI
Add/remove competitors from the registry via browser UI.
Automatically updates dropdown and re-embeds registry chunks.
- Layers: api/main.py (Custom HTML UI), rag/ingest.py,
          rag/kb/competitor_registry.json, agent/nodes.py (validate)
- Effort: L

### RAG-4 — Retrieval Quality Monitoring
Log which RAG chunks are retrieved per signal and their scores.
After many runs, identify which chunks are never retrieved —
they may need rewriting or splitting.
- Layers: agent/nodes.py (evaluate_signals), logs, reporting
- Effort: S
- Data partially already in logs at DEBUG level

### RAG-5 — Product-Opportunity Matching (V1.1 enhancement)
Enrich KB with product catalogue, certifications, partner
capabilities, and past contract wins. During Business Opportunities
evaluation, retrieve product chunks alongside strategic objective
chunks to generate bid fit assessment.

Example output:
"Strong match. NOMYU Digital Signage fits spec.
Consider partnering with Broadsign for content platform.
Similar to Porto Metro win 2023. Submit."

- Layers: rag/kb/ (new product catalogue doc), rag/ingest.py,
          agent/nodes.py (evaluate_opportunities)
- Effort: L (KB enrichment is the main work)
- Prerequisite: V1.1 Business Opportunities branch

### RAG-6 — Product Lifecycle Intelligence (V1.2 enhancement)
Enrich KB with product architecture details, technology dependencies,
and hardware revision roadmap. During Technology Developments
evaluation, assess each signal against existing products for:
- Obsolescence risk — existing product at risk
- Upgrade opportunity — next hardware revision direction
- New product gap — market opportunity

- Layers: rag/kb/ (new product architecture doc), rag/ingest.py,
          agent/nodes.py (evaluate_technologies)
- Effort: L (KB enrichment is the main work)
- Prerequisite: V1.2 Technology Developments branch

---

## ARCH - Agent Architecture

### ARCH-1 — Retry Logic for Tool Failures
Currently tools return empty on failure with no retry. Add exponential
backoff retry (max 3 attempts) for transient API failures.
- Layers: agent/tools/ (all tool files)
- Effort: S per tool

### ARCH-2 — Cross-Signal Correlation
Detect when multiple signals tell the same story (e.g. all three
Acrelec signals are about the same Glory acquisition event).
Group them in the brief rather than listing separately.
- Layers: agent/nodes.py (new deduplication step between
          evaluate_signals and generate_brief)
- Effort: M

### ARCH-3 — Multi-Competitor Runs from UI
Select any combination of competitors (up to 6) via checkboxes in
the UI. Run all selected sequentially. Receive combined brief.
Currently requires running one competitor at a time.
- Layers: agent/state.py, agent/graph.py, agent/nodes.py,
          api/main.py, api/static/index.html
- Effort: L
- Risk: multiplies LLM call count — needs budget management

### ARCH-4 — Agentically Driven Signal Evaluation (Node 5)
Currently Node 5 uses fixed retrieval per signal. Allow the LLM
to decide which RAG chunks to retrieve based on signal content —
e.g. pull competitor chunk + relevant objective in sequence.
- Layers: agent/nodes.py (evaluate_signals)
- Effort: M
- Discussed and deferred during initial design

### ARCH-5 — LLM Call Budget Enforcement
Currently llm_calls_made is tracked but not hard-enforced at graph
level. Add a graph-level budget check that routes to generate_brief
early if budget is nearly exhausted.
- Layers: agent/graph.py, agent/nodes.py, agent/state.py
- Effort: S

---

## OUT - Output and Delivery

### OUT-1 — PDF Generation
~~Convert final_brief to formatted PDF for email delivery.~~
**Won't do** — decided against PDF in favour of HTML email.
HTML is lighter, links are clickable, renders on mobile, no
generation dependency required. See architecture_decisions.md
Decision 15 for full rationale.

### OUT-2 — Report Persistence and History Viewer
Reports are saved to `reports/` directory on each run but Railway's
ephemeral filesystem means they are lost on redeploy. Build
persistent storage (S3 or Railway volume) and a simple history
viewer in the UI.
- Layers: agent/nodes.py (generate_brief), api/main.py,
          api/static/index.html
- Effort: M

### OUT-3 — Brief Quality Feedback Loop
Allow the user to rate each brief (1-5) and flag signals as
irrelevant. Feed this back into tool evaluation (IQ-1) and
confidence score calibration (IQ-6).
This is the feedback loop that makes the system smarter over time —
CEO corrections improve KB accuracy and prompt tuning.
- Layers: api/main.py (Custom HTML UI), new feedback module
- Effort: L

---

## OPS - Deployment and Operations

### OPS-1 — Scheduled Runs Configuration from UI ✅ PARTIAL
N8N Workflow 2 runs every Monday 8am for all 6 competitors.
Schedule is configured directly in N8N — not editable from the UI.
Post-MVP: allow users to set frequency (weekly/bi-weekly) and
select which competitors to include via the UI. Requires FastAPI
to N8N API integration for programmatic workflow updates.
- Layers: api/main.py, api/static/index.html, n8n/workflow2
- Effort: L
- Note: N8N API for programmatic workflow updates is complex —
  requires persistent state storage for schedule configuration

### OPS-2 — Run History and Observability Dashboard
Parse log files and display run history, tool performance, LLM
call counts, and error rates in a simple dashboard.
- Layers: logs, new reporting module, optional UI tab
- Effort: L

### OPS-3 — Environment-Based Configuration
Move all hardcoded values (model name, max signals, LLM call budget,
time range options) to environment variables or a config file.
Allows tuning without code changes.
- Layers: agent/nodes.py, agent/state.py, .env / config.py
- Effort: S

### OPS-4 — Health Check Endpoint ✅ DONE
/health endpoint verifies Pinecone connectivity, LLM API key
validity, and competitor registry status. Live at:
https://strategicradar-production.up.railway.app/health

---

## PRODUCT - Productisation and Business Model

### PROD-1 — Multi-Client Architecture
Currently the system is hardcoded for PARTTEAM & OEMKIOSKS.
Refactor to support multiple clients from the same infrastructure:
- Client-specific KB namespaces in Pinecone
- Client-specific competitor registries
- Client-specific N8N workflows
- Onboarding workflow: 4 questions → KB generated → deployed in 1 day

### PROD-2 — Onboarding Wizard
Guide a new client through KB setup via a structured interview:
1. "What keeps you awake at night?" → defines intelligence types
2. "Who are you?" → generates business_profile.md
3. "Where do you want to go?" → generates strategic_direction.md
4. "Who threatens you?" → populates competitor_registry.json
LLM generates draft KB documents from answers. Human reviews and approves.
- Effort: XL

### PROD-3 — Intelligence Type Library
Reusable intelligence type templates that can be activated per client:
- Competitor Moves (V1.0)
- Business Opportunities (V1.1)
- Technology Developments (V1.2)
- Regulatory Intelligence (new — legislation and compliance monitoring)
- Market Trends (new — industry shift and demand signal monitoring)
- Patent Intelligence (new — competitor R&D and IP monitoring)
Each type is a self-contained LangGraph branch with its own tools,
prompts, and output shape.
