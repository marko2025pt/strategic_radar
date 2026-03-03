# Product Backlog (post MVP) — Strategic Radar

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
Gradio UI          →  Human-facing interface
LangGraph          →  Cognitive workflow controller
ReAct Agent        →  Signal discovery & research loop
Pinecone RAG       →  Strategic identity & objectives grounding
External APIs      →  Live signal data (tools)
LLM                →  Strategic evaluation & brief generation
Logs               →  Observability and run history
```

---

## IQ - Intelligence Quality

### IQ-1 — Tool Performance Evaluation Dashboard
Track which tools contribute signals that survive selection and reach
the final brief. Surface per-tool hit rates, selection rates, and
impact level distributions over time.
- Layers: logs, new reporting module, optional Gradio UI tab
- Effort: M
- Data is already in log files — needs a parsing and display layer

### IQ-2 — Domain List Expansion and Curation
Expand domain_lists.json with industry-specific domains discovered
through real runs. Primary/secondary classification directly affects
confidence scores.
- Layers: agent/tools/domain_lists.json only
- Effort: S (ongoing, not a one-time task)
- No code changes required — edit JSON, redeploy

### IQ-3 — Domain List Editor in Gradio UI
Allow non-technical users to add/remove domains from domain_lists.json
directly in the browser without touching files or redeploying.
- Layers: api/main.py (Gradio UI), agent/tools/utils.py
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
- Layers: rag/ingest.py, optional Gradio UI tab
- Effort: S

### RAG-2 — Strategy Editor in Gradio UI
Allow leadership to update strategic objectives directly in the browser.
Changes persist to strategic_direction.md and re-embed automatically.
- Layers: api/main.py (Gradio UI), rag/ingest.py, rag/kb/
- Effort: L

### RAG-3 — Competitor Registry Editor in Gradio UI
Add/remove competitors from the registry via browser UI.
Automatically updates dropdown and re-embeds registry chunks.
- Layers: api/main.py (Gradio UI), rag/ingest.py,
          rag/kb/competitor_registry.json, agent/nodes.py (validate)
- Effort: L

### RAG-4 — Retrieval Quality Monitoring
Log which RAG chunks are retrieved per signal and their scores.
After many runs, identify which chunks are never retrieved —
they may need rewriting or splitting.
- Layers: agent/nodes.py (evaluate_signals), logs, reporting
- Effort: S
- Data partially already in logs at DEBUG level

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

### ARCH-3 — Multi-Competitor Runs
Accept a list of competitors and run the pipeline for each,
producing a comparative brief.
- Layers: agent/state.py, agent/graph.py, agent/nodes.py,
          api/main.py
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
Convert final_brief string to a formatted PDF for email delivery.
Currently N8N handles this — moving it into the FastAPI layer gives
more control over formatting.
- Layers: api/main.py, new output/pdf.py module
- Effort: M

### OUT-2 — Report Persistence
Save every generated brief to the reports/ directory with run_id,
competitor, timestamp. Build a simple report history viewer in Gradio.
- Layers: agent/nodes.py (generate_brief), api/main.py
- Effort: S

### OUT-3 — Brief Quality Feedback Loop
Allow the user to rate each brief (1-5) and flag signals as
irrelevant. Feed this back into tool evaluation (IQ-1) and
confidence score calibration (IQ-6).
- Layers: api/main.py (Gradio UI), new feedback module
- Effort: L

---

## OPS - Deployment and Operations

### OPS-1 — Scheduled Runs via N8N
Configure N8N to run the pipeline automatically on a schedule
(daily or weekly per competitor) without manual triggering.
- Layers: n8n/workflow.json only
- Effort: S

### OPS-2 — Run History and Observability Dashboard
Parse log files and display run history, tool performance, LLM
call counts, and error rates in a simple dashboard.
- Layers: logs, new reporting module, optional Gradio UI tab
- Effort: L

### OPS-3 — Environment-Based Configuration
Move all hardcoded values (model name, max signals, LLM call budget,
time range options) to environment variables or a config file.
Allows tuning without code changes.
- Layers: agent/nodes.py, agent/state.py, .env / config.py
- Effort: S

### OPS-4 — Health Check Endpoint
Add a /health FastAPI endpoint that verifies Pinecone connectivity,
OpenAI API key validity, and tool availability. Used by Railway
and N8N to confirm the service is live before triggering runs.
- Layers: api/main.py
- Effort: S