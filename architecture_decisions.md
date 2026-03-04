# Strategic Radar - Autonomous Strategic Intelligence Snapshot Engine
# Architecture Decisions

This document records the key architectural decisions made during the design and implementation of the Autonomous Strategic Intelligence Snapshot Engine.

The purpose of this log is to:

- Make design reasoning explicit
- Document trade-offs and pivots
- Improve maintainability
- Demonstrate architectural thinking
- Support future evolution of the system

---

# Decision Log

## Decision 1 — Project Re-Scope: From Generic Research Agent to Strategic Signal Engine

**Original Idea:**
Build a generic autonomous company research agent that, given any company name, searches the web, aggregates data from multiple APIs, and generates a comprehensive multi-section competitive intelligence report.

**Why We Changed It:**
Generic company research reports are already available through specialised outlets — Bloomberg, Crunchbase, PitchBook, industry analyst firms. A system that replicates this adds limited business value. The reports it would generate are descriptive, not actionable, and not anchored to any specific strategic context. They answer "what is this company?" rather than "does this matter to us?".

**New Solution:**
A bounded strategic signal evaluation engine. Given a competitor, a time window, and the company's own business identity and strategic objectives, the system finds recent market signals and evaluates each one through the lens of "does this matter to us — and why?". The output is a 1-page executive snapshot ranked by strategic impact, not a long descriptive report.

**Why This Provides More Business Value:**
- Output is immediately actionable — signals are ranked High / Medium / Low impact
- Evaluation is anchored to the company's specific identity and objectives, not generic criteria
- Decision-makers get one page, not ten — faster to read, easier to act on
- The system answers a real business question that no off-the-shelf tool answers well
- Competitive advantage comes from interpretation, not from data aggregation

---

## Decision 2 — Layered Architecture with Clear Separation of Concerns

**Decision:**
Separate the system into distinct layers with explicit responsibilities:

| Layer | Technology | Responsibility |
|---|---|---|
| Orchestration | N8N Cloud | Trigger, delivery, scheduling |
| HTTP Interface | FastAPI + Railway | Entry point, request handling |
| Human Interface | Custom HTML UI | Manual runs, demos |
| Workflow Control | LangGraph | State management, routing |
| Cognition | ReAct Agent | Signal discovery, reasoning |
| Knowledge | Pinecone RAG | Strategic grounding |
| Data | External APIs | Live signal collection |
| Intelligence | LLM | Evaluation, brief generation |
| Delivery | SendGrid | Email delivery |

**Reasoning:**
Monolithic prompt-driven systems mix reasoning, control, and orchestration in ways that are fragile, hard to debug, and impossible to extend. Clear layer boundaries mean each component can be tested, replaced, or extended independently. When something breaks, you know exactly which layer to look at.

---

## Decision 3 — RAG Reframed: From Industry Overview to Strategic Identity Memory

**Original Idea:**
Use Pinecone to store generic industry documents — DOOH market reports, competitor profiles, industry terminology glossaries — as background context for report generation.

**Why We Changed It:**
Generic industry knowledge makes the agent slightly better informed but does not make it strategically useful. An agent that knows "the DOOH market is worth $X billion" is not more valuable than one that knows "this signal directly threatens our airport expansion objective." The difference is anchoring.

**New Solution:**
The RAG knowledge base contains only three types of documents:

1. **Business Profile** — who we are, what we build, where we operate, how we compete
2. **Strategic Direction** — 5-8 active objectives that define where we want to go
3. **Competitor Registry** — controlled list of monitored competitors

In V1.2, a fourth document is added:

4. **Technology Watchlist** — emerging technologies relevant to DOOH and kiosk ecosystem

**Why This Provides More Business Value:**
RAG is no longer general context. It is strategic interpretation memory. Every signal is evaluated against real objectives, not abstract industry knowledge. The system knows not just what happened, but whether it matters to this specific company. That is the difference between information and intelligence.

---

## Decision 4 — Bounded Autonomy: Single ReAct Loop, Max 7 LLM Calls

**Decision:**
Restrict dynamic reasoning to a single ReAct loop in the signal discovery phase only. Cap total LLM calls per run at 7 (1 selection + max 5 evaluation + 1 brief).

**Reasoning:**
Unbounded agentic loops introduce unpredictable costs, infinite loop risk, and opaque failure states. For a system used by executives, predictability and speed matter more than exhaustive research. A well-scoped 7-call run that completes in under 2 minutes is more valuable than an open-ended run that might take 20 minutes and cost 10x more.

**Trade-off:**
Slightly less coverage per run. Mitigated by running the agent regularly (daily or weekly) rather than expecting a single run to be exhaustive.

---

## Decision 5 — Competitor Registry: Controlled Input Over Open-Ended Search

**Original Idea:**
Accept any company name as free text input, allowing the agent to research any competitor on demand.

**Why We Changed It:**
Open-ended input introduces noise, ambiguity, and reliability issues. A query for "JCDecaux" might return results about unrelated companies with similar names. It also removes a useful forcing function — deciding which competitors matter enough to monitor is itself a strategic decision.

**New Solution:**
A predefined competitor registry stored in the knowledge base. The UI presents a dropdown, not a text field. Input validation checks the registry before any API call is made.

**Why This Provides More Business Value:**
- Eliminates noise and ambiguity
- Forces intentional competitor selection
- Makes the system more reliable and predictable
- Registry is easy to extend — adding a new competitor is a one-line change

---

## Decision 6 — Layered MVP Delivery Strategy

**Decision:**
Structure development as three additive layers, each a fully working product:

- **V1.0** — Competitor Intelligence (minimum deliverable, ships no matter what)
- **V1.1** — + Business Opportunities via TED EU tenders API
- **V1.2** — + Technology Developments via technology watchlist

Each version is independently demoable. If time runs out, fall back to the previous version.

**Reasoning:**
A 4-day solo build with an unfamiliar stack (LangGraph, N8N) carries real execution risk. Designing for graceful fallback means there is always something working to show. It also enforces good engineering practice — each layer must be clean and modular before the next one is added.

**Trade-off:**
V1.2 may not ship in the initial build window. This is acceptable. A solid V1.0 that works flawlessly and delivers real value is a better outcome than a fragile V1.2 that breaks during a demo.

---

## Decision 7 — Deployment: FastAPI + Railway + N8N Cloud (Fully Cloud)

**Original Idea:**
Run the agent as a standalone Python script triggered by N8N's Execute Command node running locally.

**Why We Changed It:**
Local execution means the laptop must be on and running for the agent to work. No one can trigger it remotely. The teacher or CEO cannot test it independently. It is not a deployed product — it is a script that works on one machine.

**New Solution:**
FastAPI wraps the LangGraph agent and is deployed to Railway via git push. N8N Cloud sends HTTP requests to the Railway URL. Once deployed, the system runs independently of any local machine.

**Why This Provides More Business Value:**
- Anyone with the URL can trigger a run
- The CEO can receive a live demo without being in the same room
- It demonstrates the full journey from local code to deployed product
- It is how real production systems are built

---

## Decision 8 — Two Entry Points: N8N (Automated) + Custom HTML UI (Human)

**Decision:**
Implement two separate entry points that both call the same FastAPI endpoint:
- N8N Cloud for automated, scheduled, or webhook-triggered runs
- Custom HTML UI for manual runs and live demos

**Reasoning:**
N8N is powerful for automation but requires explaining webhooks and workflow diagrams to a non-technical audience. A custom single-page HTML interface gives anyone a clean browser experience — select a competitor, set a time range, enter an email, click Run, read the snapshot. For a CEO demo, this matters enormously. Both paths go through identical FastAPI → LangGraph → LLM logic, so there is no duplication of intelligence logic.

**Why Custom HTML Over Gradio:**
Gradio was the original plan. It was replaced with a custom HTML/CSS/JS single-page interface served as a static file from FastAPI. Reasons:
- Professional appearance appropriate for executive audience
- Full control over layout, typography, and interaction design
- Live step-by-step progress animation not achievable in Gradio
- Cascading dropdowns for intelligence type → second input not supported in Gradio
- Same deployment complexity — one file, no additional dependencies

---

## Decision 9 — Competitor Registry: JSON for Application Logic, Text for RAG Ingestion

**Decision:**
The competitor registry is stored as JSON (`competitor_registry.json`) rather
than markdown like the other KB documents.

**Reasoning:**
The registry serves two distinct purposes simultaneously:

1. **Application logic** — input validation and UI dropdown population
   require programmatic access to competitor IDs and names. JSON is the
   natural format for this and can be loaded and queried directly in Python
   without any parsing layer.

2. **RAG context** — the `why_we_monitor` field and other descriptive fields
   need to be embedded into Pinecone so the LLM can reason about competitor
   relevance during signal evaluation.

These two purposes require different formats, so the registry is handled
differently in `ingest.py` from the other KB documents.

**Implementation:**
During ingestion, the JSON is parsed and each competitor entry is reconstructed
as a clean text block before chunking and embedding. The JSON structure (keys,
brackets, quotes) is stripped — only the human-readable content is sent to
Pinecone.

**Trade-off:**
This adds a small ETL step in `ingest.py` that the markdown documents do not
require. This is an acceptable cost given the benefit of having a single source
of truth that serves both the application layer and the RAG pipeline.

---

## Decision 10 — Chunking Strategy: Semantic Units Over Token Count

**Decision:**
Chunk all KB documents by semantic unit (## heading level) rather than
by fixed token count.

**Reasoning:**
Token-based chunking is the default in most RAG tutorials but it is wrong
for structured knowledge bases. It splits headings from their content and
breaks logical units arbitrarily — an objective chunk split mid-way through
its Signal Relevance section would return incomplete evaluation criteria
to the LLM.

Chunking by ## heading guarantees that each chunk is a self-contained,
semantically coherent unit. The retriever always returns complete context.

**Chunk map per document:**

business_profile.md — 5 chunks:
- Company Identity and Positioning (~357 tokens)
- Core Hardware Products (~230 tokens)
- Core Software and Services (~200 tokens)
- Target Verticals and Clients (~294 tokens)
- Revenue Model and Sales Motion (~287 tokens)

strategic_direction.md — 6 chunks, one per objective (~193–213 tokens each):
- Objective 1 — International Expansion
- Objective 2 — QSR and Food Service Market Growth
- Objective 3 — Smart Cities and Public Procurement
- Objective 4 — Software and Recurring Revenue Growth
- Objective 5 — Product Innovation and Design Leadership
- Objective 6 — OEM/ODM Partner Network Growth

competitor_registry.json — 6 chunks, one per competitor (~137–153 tokens each):
- Acrelec
- Pyramid Computer
- Wanzl
- Broadsign
- Diebold Nixdorf
- LamasaTech

technology_watchlist.md — 7 chunks, one per technology (~145–173 tokens each):
- Touchless and Gesture-Based Interaction
- AI-Driven Personalisation and Upsell at the Kiosk
- Programmatic DOOH and DSP Integration
- Computer Vision and Audience Measurement
- IoT Connectivity and Predictive Maintenance
- Edge Computing for Kiosks and Digital Signage
- Accessibility and Inclusive Design Standards

**Total chunks in Pinecone: 24**

**Sweet spot target:** 150–300 tokens per chunk.
Chunks outside this range were either fattened with additional relevant
content or merged with semantically related sections.

**Trade-off:**
Semantic chunking requires manual document design decisions upfront.
This is an acceptable cost — the KB is small (4 documents, 24 chunks)
and the quality improvement in retrieval precision justifies the effort.

---

## Decision 11 — Pinecone Metadata Schema

**Decision:**
Each chunk stored in Pinecone carries structured metadata fields that
identify its source, type, and heading.

**Metadata schema:**
```json
{
  "source": "business_profile.md",
  "chunk_type": "business_profile",
  "heading": "Core Hardware Products",
  "document": "business_profile"
}
```

**chunk_type values:**
- "business_profile" — company identity, products, verticals, revenue
- "strategic_objective" — one per objective in strategic_direction.md
- "competitor" — one per competitor in competitor_registry.json
- "technology" — one per technology in technology_watchlist.md

**Reasoning:**
Metadata enables filtered retrieval — during signal evaluation the agent
can instruct Pinecone to retrieve only chunks of a specific type rather
than searching across all 24 chunks indiscriminately. For example:

- Fetch top 2 chunks where chunk_type = "strategic_objective"
- Fetch top 1 chunk where chunk_type = "competitor" and heading = "Acrelec"

This reduces noise, improves retrieval precision, and keeps LLM context
focused on the most relevant KB content for each evaluation step.

**Signal Relevance handling:**
The Signal Relevance section for each strategic objective is kept inside
the same chunk as the objective text — it is not split into a separate
chunk. This ensures the LLM always receives both the strategic intent
and the evaluation criteria in a single retrieval call, without requiring
a second round-trip to Pinecone.

**Trade-off:**
Filtered retrieval requires the ingestion pipeline to attach metadata
correctly at embed time. This adds a small amount of complexity to
ingest.py but is straightforward to implement and significantly improves
retrieval quality in production.

---

## Decision 12 — MCP Integration: In-Process Tool Definitions

**Options Considered:**
1. Use existing remote MCP servers (Tavily has one, NewsAPI has community ones, TED has none)
2. Build and deploy separate MCP server processes
3. Define MCP tools in-process using the `mcp` library alongside the LangGraph agent

**Why We Chose Option 3:**
- TED API has no existing MCP server — building and deploying a separate process adds significant complexity for one tool
- Separate MCP server processes require independent deployment, health monitoring, and inter-process communication — high risk for a 5-day build
- In-process MCP tool definitions using `@mcp.tool()` decorator meet the project requirement, demonstrate understanding of the MCP pattern, and add zero deployment complexity
- All three tools run inside the same Railway process as FastAPI and LangGraph — one deployment, one process

**What This Means in Practice:**
Each tool is a Python function decorated with `@mcp.tool()`. The decorator provides the standardised tool schema (name, description, input types) that LangGraph's ReAct agent uses for tool discovery and invocation. The tools are registered directly with the agent at startup — no network calls, no separate servers.

**Tools implemented:**
- `tavily.py` — web search, primary signal discovery
- `newsapi.py` — news articles, secondary signal discovery
- `hackernews.py` — technology signals via Algolia HN Search API, no API key required

**Trade-off:**
Tools are not exposed as remote MCP endpoints that other agents or clients could call. This is acceptable for MVP — the MCP pattern is correctly implemented and demonstrable. Remote exposure is a post-MVP enhancement.

---

## Decision 13 — Error Handling: Built From the Start, Not Retrofitted

**Decision:**
Implement error handling in every module from the first line of code, not as a cleanup pass at the end.

**Reasoning:**
Retrofitting error handling is expensive and risky — it requires revisiting every function, understanding all failure modes after the fact, and risks introducing new bugs during refactoring. Building it from the start costs 10-15% more time per module but eliminates a full refactoring pass at the end.

**What Can Fail and How We Handle It:**

| Failure | Handler |
|---|---|
| OpenAI API authentication error | Log ERROR, return empty result, do not crash |
| OpenAI rate limit hit | Log WARNING, return empty result, retry logic in agent |
| OpenAI connection error | Log ERROR, return empty result |
| Pinecone connection failure | Log CRITICAL, raise — system cannot function without RAG |
| Pinecone query failure | Log ERROR, return empty result |
| Pinecone returns 0 results | Log WARNING, return empty list |
| Malformed metadata in Pinecone match | Log WARNING, skip that match, continue |
| External API timeout (Tavily, NewsAPI) | Log WARNING, retry up to 3 times, then return empty |
| LLM call failure | Log ERROR, surface uncertainty in output rather than crash |

**Design Principle:**
Retrieval failures return empty results — the agent continues with less context.
Infrastructure failures (Pinecone unavailable) raise — the run cannot proceed meaningfully.
The system always produces output, surfacing uncertainty when data is insufficient.

**Trade-off:**
More verbose code per module. Justified by reduced debugging time, better observability, and a system that degrades gracefully rather than crashing silently.

---

## Decision 14 — Logging: Centralised, Named, Daily Rotating Files

**Decision:**
Implement a single `core/logging_config.py` module imported by every other module. Never configure logging outside this file.

**Implementation:**
- Daily log files: `logs/YYYY-MM-DD.log`
- File handler: DEBUG and above — full detail for debugging
- Console handler: INFO and above — clean output during development
- Named loggers via `get_logger(__name__)` — every entry identifies its source module
- Third party loggers silenced at WARNING — only our code produces DEBUG entries

**Log entry format:**
```
2026-03-03 16:01:51 | INFO     | rag.retriever | Retrieved 3 chunks — top score: 0.5853
2026-03-03 16:01:52 | ERROR    | agent.tools.tavily | Tavily timeout — retrying (1/3)
2026-03-03 16:01:53 | CRITICAL | agent.graph | Run aborted — Pinecone unavailable
```

**Why From the Start:**
Logging added after the fact means the first bugs you encounter during development have no log trail. Every hour spent debugging without logs costs more than the time invested in setting up logging upfront. The log file becomes the primary debugging tool — not print statements, not re-running code.

**Trade-off:**
Small overhead per module (two lines: import + logger instantiation). The payoff is complete observability from the first test run.

---

## Decision 15 — N8N Workflow Design: Two Workflows, One Email Provider

**Decision:**
Implement two separate N8N workflows with distinct triggers and delivery patterns, both using SendGrid as the single email provider.

**Workflow 1 — On-Demand:**
- Triggered by a webhook called by FastAPI `/notify` after every UI run that includes a `notify_email`
- Formats the brief as HTML email and delivers to the user-provided address
- Single recipient, single competitor, triggered in real time

**Workflow 2 — Scheduled Weekly:**
- Triggered by N8N schedule (every Monday 8am)
- Loops through all 6 competitors using SplitInBatches node
- Calls FastAPI `/run` for each competitor sequentially
- Aggregates all 6 briefs into one combined HTML email
- Delivers to fixed recipient defined in N8N

**Why Two Workflows Instead of One:**
- On-demand and scheduled have fundamentally different trigger mechanisms and output shapes
- Combining them would require complex conditional logic that is harder to debug
- Two clean, purpose-built workflows are easier to maintain, test, and explain

**Why SendGrid Over Gmail:**
Gmail blocks N8N Cloud as an unauthorised sender due to DMARC restrictions. SendGrid is purpose-built for transactional email from third-party applications, has no such restrictions, and provides delivery logs for debugging.

**Why Outlook Sender Over Gmail Sender:**
SendGrid requires a verified sender address. Gmail addresses sent via SendGrid trigger Gmail's DMARC alignment check and are deferred or blocked. An Outlook address (`@outlook.com`) does not have this restriction and verifies cleanly in SendGrid.

**Why HTML Email Over PDF:**
- HTML emails are lighter — a weekly brief covering 6 competitors as PDF would exceed 5MB
- Links in HTML emails are clickable — sources open directly
- HTML renders on mobile without requiring an app to open a PDF
- PDF generation adds a dependency (wkhtmltopdf or similar) with no meaningful benefit for this use case

**Trade-off:**
HTML email rendering varies across email clients. Institutional clients (e.g. @ipca.pt) may display raw HTML in some configurations. Acceptable for MVP — the primary delivery target is a modern email client.

---

## Decision 16 — FastAPI /notify Endpoint: Decoupled Email Trigger

**Decision:**
Add a dedicated `/notify` endpoint to FastAPI that is called internally after `/run` completes and forwards the brief payload to the N8N webhook. Email delivery is handled by N8N, not by FastAPI directly.

**Reasoning:**
Two options were considered:

1. FastAPI sends email directly via SendGrid SDK after each run
2. FastAPI calls N8N webhook after each run — N8N handles email

Option 2 was chosen because:
- N8N is already the designated orchestration layer — email delivery belongs there
- Keeping FastAPI free of email logic means one less dependency and one less failure mode
- The N8N workflow is independently testable and replaceable without touching the agent
- It satisfies the project requirement that N8N orchestrates the full workflow

**Implementation:**
The `/notify` call is non-blocking — it runs as a background task after the response is returned to the UI. If N8N is unavailable, the UI response is unaffected. The failure is logged as a warning, not an error.

**Trade-off:**
Adds a network hop between FastAPI and N8N. Acceptable — the UI has already received its response before the notification fires.

---

## Trade-offs Summary

| Trade-off | Decision | Rationale |
|---|---|---|
| Reliability over maximal autonomy | Bounded loops, max 7 LLM calls | Predictable, fast, cost-controlled |
| Depth over breadth | One competitor per run | Better signal quality, less noise |
| Actionability over completeness | 1-page snapshot over full report | Executive time is scarce |
| Controlled input over flexibility | Competitor registry + dropdown | Reliability and intentionality |
| Working MVP over feature density | Layered V1.0 → V1.1 → V1.2 | Always have something to ship |
| Cloud deployment over local script | FastAPI + Railway | Real product, not just a demo |
| Custom HTML over Gradio | Single-page HTML UI | Professional appearance, full control |
| Single source of truth over format purity | Competitor registry as JSON, reconstructed as text for RAG | Application logic and RAG ingestion served from one file |
| Semantic chunking over token-based chunking | Chunk by ## heading, fatten thin chunks | Retrieval precision over implementation simplicity |
| In-process MCP over separate MCP servers | @mcp.tool() decorator, same Railway process | Zero deployment risk over full MCP remote exposure |
| Error handling from the start over retrofitting | Built into every module from line one | 10-15% more time per module, eliminates full refactor pass |
| Centralised logging over per-module configuration | core/logging_config.py, imported everywhere | Two lines per module, complete observability from first run |
| N8N email delivery over FastAPI direct send | /notify endpoint, non-blocking background task | N8N owns orchestration, FastAPI owns intelligence |
| HTML email over PDF | No PDF generation dependency | Lighter, clickable, mobile-friendly |
| Outlook sender over Gmail sender | strategicradar2026@outlook.com verified in SendGrid | No DMARC restrictions, clean delivery |
| Two N8N workflows over one | On-demand + Scheduled are separate concerns | Simpler logic, easier to debug and maintain |

---

# Summary

This architecture prioritises:

- **Bounded autonomy** — the system is autonomous but not unpredictable
- **Strategic anchoring** — every output is grounded in business identity and objectives
- **Actionable output** — signals ranked by impact, not length of report
- **Layered delivery** — working product at every stage of development
- **Observability** — every decision logged, every transition traceable
- **Extensibility** — new intelligence types added as branches, not rewrites

The system is designed not as a demo agent, but as a reference architecture for reliable, strategically-grounded autonomous intelligence workflows.
