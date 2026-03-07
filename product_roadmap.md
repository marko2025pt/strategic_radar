[//]: # (Version 1.1 — Final demo delivery to Ironhack 2026-03-06)
# Strategic Radar — Product Roadmap
### From Demo to Deployed: V1.2 to V3.0

---

## Document Purpose

This document is the single source of truth for product direction.
It replaces `product_backlog.md` — all backlog items have been absorbed
into the version where they will be built.

Each version is a shippable increment. No version starts until the
previous one is complete and stable. The sequence is deliberate:
reliability and security before features, onboarding before scale,
intelligence depth before intelligence breadth.

**Business model — unchanged from V2.0 to V3.0:**
The consultant manages setup, KB quality, and intelligence scope for every client.
Clients configure delivery preferences and rate their briefs. That is the full client
surface area. The consultant is the product. The tool is what makes the consultant's
service remarkable.

---

## Effort Scale

| Label | Estimate |
|---|---|
| S | Half day or less |
| M | 1 day |
| L | 2–3 days |
| XL | 4+ days |

---

## Version Overview

| Version | Tagline | Theme | Gate |
|---|---|---|---|
| V1.0 | Competitor Intelligence | Core product | DONE |
| V1.1 | + Business Opportunities | Intelligence breadth | DONE |
| V1.2 | + Technology Developments | Complete triple | Demo-ready |
| V1.3 | Security + Prompt Foundation | Client-safe | Before any external user |
| V1.4 | Persistent Memory | Client continuity | Before first client |
| V1.5 | Operational Hardening | Production safety | Before first paid client |
| V1.6 | Client Onboarding Engine | Onboarding speed | Gate to beta |
| V1.7 | Consultant KB Tools | Consultant efficiency | Beta sustainability |
| V1.8 | Smarter Delivery | Engagement | Beta value |
| V1.9 | White-Label + Configurability | Product feel | V2.0 readiness |
| V2.0 | Beta Launch | First paying clients — consultant-managed | Multi-client isolation |
| V2.1 | Intelligence Quality | Learn what works | Post-beta data |
| V2.2 | Feedback Loop | Learn from clients | Brief rating data |
| V2.3 | Cross-Signal Intelligence | Brief quality | Run history data |
| V2.4 | Intelligence Expansion | Regulatory + product matching | Stable client base |
| V2.5 | Power Features | Scale | Mature client relationships |
| V3.0 | Strategic Intelligence Suite | Products, markets, sales + consultant licensing | Deep client relationships |

---

## Completed

### V1.0 — Competitor Intelligence
Monitor competitor moves. Evaluate strategic relevance. Deliver executive snapshot.

- LangGraph pipeline — 6 nodes, ReAct loop
- RAG system — 24 chunks in Pinecone (4 KB documents)
- 3 MCP tools — Tavily, NewsAPI, HackerNews
- FastAPI server — /run, /health, /notify
- Custom HTML tool UI — cascading dropdowns, live progress, signal cards
- Railway deployment — always-on, auto-deploy on git push
- N8N Workflow 1 — on-demand email delivery
- N8N Workflow 2 — scheduled weekly, all competitors
- SendGrid email delivery — HTML format

---

### V1.1 — Business Opportunities
Monitor EU public tenders and private sector expansion signals.

- ted.py — TED EU Open Data API, no API key required
- 3 new LangGraph nodes: collect_opportunities, evaluate_opportunities, generate_opportunity_brief
- Three signal types: live tenders, private expansion, pre-tender signals
- LLM signal classification (private vs pre-tender)
- Hybrid collection: deterministic TED + ReAct for web signals
- State schema extended: raw_tenders, raw_private_signals, raw_pretender_signals
- API updated: subject replaces company, response includes tenders + opportunities
- UI updated: tender cards, private opportunity cards, pre-tender cards

---

## In Development

---

### V1.2 — Technology Developments
**"Complete the three intelligence types"**

The third intelligence type closes the core product loop. Technology
Watchlist is already ingested (7 chunks in Pinecone). Pattern is
identical to V1.1 — low risk, well-understood.

| Feature | Ref | Effort |
|---|---|---|
| Technology signal collection node — Tavily + HackerNews with watchlist-derived queries | RAG-6 prereq | M |
| Technology evaluation node — match signals against watchlist chunks | — | M |
| Three evaluation outputs per signal: obsolescence risk / upgrade opportunity / new product gap | — | S |
| Technology brief node — formatted technology snapshot | — | S |
| UI: technology signal cards with product impact fields | — | S |
| Graph branch activated — V1.2 route in route_after_validation() | — | S |

**Total effort:** L
**Unlocks:** a complete three-mode demo; stronger pitch to any prospect

---

## Road to Beta

---

### V1.3 — Security + Prompt Foundation
**"Close the door and remove the client name from the code"**

Two things must happen before any external person touches this system:
it must be secure, and the prompts must be client-generic. Both are
prerequisites for every version that follows.

**Immediate prerequisite — do before anything else in V1.3:**
Remove all hardcoded PARTTEAM & OEMKIOSKS references from `nodes.py`.
Replace with generic templates: `{CLIENT_NAME}` and `{CLIENT_INDUSTRY}`
injected from env vars. RAG context provides the strategic identity at
evaluation time. This should have been done from the start — fix it
before any client-facing work begins. Every prompt becomes a reusable
template; the KB makes it client-specific.

| Feature | Ref | Effort |
|---|---|---|
| Prompt template refactoring — remove all hardcoded client references from nodes.py | — | M |
| Generic prompt templates with {CLIENT_NAME}, {CLIENT_INDUSTRY} placeholders from env vars | — | S |
| API key validation on /run and /notify — reject unauthenticated requests with 401 | A | S |
| Login screen on /tool — username + password from env vars, session cookie | A | S |
| CLIENT_USERNAME, CLIENT_PASSWORD added to env vars and .env.example | A | S |

**Total effort:** M
**Unlocks:** the URL can safely be shared with anyone

---

### V1.4 — Persistent Memory
**"Reports that survive a redeploy"**

Railway's filesystem is ephemeral. Reports written to `reports/` are
wiped on every push. An SMB client who wants to compare briefs across
weeks gets nothing. Persistent storage is required before any real
client relationship begins.

| Feature | Ref | Effort |
|---|---|---|
| Supabase integration — Postgres, free tier | OUT-2, B | S |
| FastAPI writes each run result to Supabase (replaces local reports/ write) | OUT-2 | S |
| FastAPI reads run history from Supabase | OUT-2 | S |
| Run history tab in tool UI — list of past runs, click to reload any brief | OUT-2 | M |
| Railway deployment becomes fully stateless — no local filesystem dependency | B | S |

**Total effort:** M
**Unlocks:** brief comparison (V1.8), per-client analytics (V2.1), client continuity

---

### V1.5 — Operational Hardening
**"Production safety before the first paying client"**

Before anyone pays for this system, three questions must have answers:
Does it alert when it breaks? Can you tell clients what it costs? Are
all tunable values configurable without touching code?

| Feature | Ref | Effort |
|---|---|---|
| Run failure alerting — N8N Workflow 2 error handler node sends alert email to operator on any failure | C | S |
| Cost tracking — estimated_cost_usd field in run response (llm_calls_made × configurable rate) | E | S |
| Cost display in UI — estimated cost shown per run in the tool | E | S |
| Monthly budget cap — MONTHLY_BUDGET_CAP_USD env var blocks runs when exceeded, notifies operator | E | S |
| Retry logic — exponential backoff (max 3 attempts) for transient API failures in all tool files | ARCH-1 | S |
| Hard LLM budget enforcement — graph-level check routes to brief generation early if budget nearly exhausted | ARCH-5 | S |
| Environment-based configuration — all hardcoded values (model name, max signals, call budget, time ranges) moved to env vars | OPS-3 | S |

**Total effort:** M
**Unlocks:** you can answer the CFO question; you know immediately when Monday's brief fails

---

### V1.6 — Client Onboarding Engine
**"From first meeting to first brief in one day"**

The biggest bottleneck to offering beta slots is the time it takes to
build a new client's knowledge base. An LLM can draft all four KB
documents from a 15-minute structured conversation. The consultant
reviews, approves, and ingests — first brief runs immediately after.
This version is the gate to beta.

| Feature | Ref | Effort |
|---|---|---|
| Onboarding page (/onboard) — structured intake form with 6 questions covering company identity, strategy, competitors, sectors, and technology | D, PROD-2 | M |
| LLM-assisted KB draft — single call generates business_profile.md, strategic_direction.md, competitor_registry.json, technology_watchlist.md from intake answers | D | M |
| In-browser draft review — consultant edits the four generated documents before approval | D | M |
| Approve + ingest — FastAPI triggers rag/ingest.py on approval, KB live in Pinecone in seconds | D | S |
| Onboarding page is auth-protected (consultant-only) | D | S |

**Total effort:** L
**Risk:** Medium — LLM draft quality depends on prompt design; human review step is the safety net
**Unlocks:** onboarding a new client takes one meeting, not one week; beta becomes feasible

---

### V1.7 — Consultant KB Tools
**"Update any client's knowledge base without touching the server"**

When a beta client's strategy shifts, the consultant should be able to
update their KB from a browser — without SSH, without redeployment,
without touching the Pinecone dashboard. These tools live in the
consultant admin view, not the client UI. The consultant stays in full
control of what goes into each client's knowledge base.

| Feature | Ref | Effort |
|---|---|---|
| KB editor in consultant admin view — single interface per client: business profile, strategic direction, competitors, sectors, technology watchlist | RAG-1, F | S |
| Strategic objectives editor — edit strategic_direction.md in the browser (markdown editor) | RAG-2 | M |
| Competitor registry editor — add, edit, remove competitors; updates client dropdown immediately | RAG-3 | M |
| Sector list editor — add, remove monitored sectors | RAG-3 | S |
| Technology watchlist editor — update watched technologies | RAG-1 | S |
| Save → re-embed — FastAPI re-embeds only changed chunks; Pinecone namespace updated without full re-ingest | RAG-1 | M |
| KB change log — what was changed and when, stored in Supabase (consultant audit trail) | — | S |

**Total effort:** L
**Unlocks:** a client's context can be improved in minutes after any strategic conversation; no redeploy needed

---

### V1.8 — Smarter Delivery
**"Meet clients where they already are"**

Two features that significantly increase the perceived value of the
weekly brief: Slack delivery for clients who live in Slack, and a
comparison view for clients asking "what changed this week?"

| Feature | Ref | Effort |
|---|---|---|
| Slack delivery — N8N Workflow 2 gets a Slack webhook node; SLACK_WEBHOOK_URL env var; brief formatted as Slack Block Kit message with executive takeaway first | H | S |
| Brief comparison view — select competitor + two dates from run history; side-by-side highlights new signals, impact level changes, disappeared signals | G | M |

**Total effort:** M
**Prerequisite:** V1.4 (persistent storage required for comparison view)
**Unlocks:** higher brief engagement; richer beta feedback

---

### V1.9 — White-Label + Full Configurability
**"Each deployment feels like a product, not a script"**

Before beta launch, each client deployment should feel like their own
intelligence system. This version makes the system fully configurable
from env vars — no code changes, no redeployment for tuning.

| Feature | Ref | Effort |
|---|---|---|
| White-label branding — SYSTEM_NAME, CLIENT_LOGO_URL, PRIMARY_COLOR env vars; UI reads at render time | I | S |
| Client name in all outputs — brief headers, email subjects, Slack messages use CLIENT_NAME | I | S |
| Per-client .env file documented as the complete configuration surface for each deployment | OPS-3 | S |
| Domain list editor — add/remove domains in domain_lists.json from browser UI without redeploy | IQ-3 | M |

**Total effort:** S–M
**Unlocks:** V2.0 beta launch — each client has a named, branded, independently configured deployment

---

## Beta Phase

---

### V2.0 — Beta Launch
**"First paying clients — consultant-managed end to end"**

V2.0 is not primarily a feature release. It is the operational moment
where the system moves from demo to paid product. The consultant manages
setup, KB quality, and intelligence scope for every client. Clients
configure delivery preferences and rate their briefs. That is the full
client surface area. The increment is multi-client isolation: multiple
live deployments from one codebase, each with their own KB, branding,
configuration, and brief history.

| Feature | Ref | Effort |
|---|---|---|
| Pinecone namespace isolation — each client has their own namespace; PINECONE_NAMESPACE env var routes all queries to the correct KB | PROD-1 | M |
| Per-client Railway deployment — separate Railway project per client, all pointing to main branch, differentiated by env vars | PROD-1 | S |
| Per-client N8N workflows — copy + configure workflows per client; independent webhook URLs, email addresses, schedules | PROD-1 | S |
| Client delivery preferences — frequency (weekly/bi-weekly/monthly) and delivery channel (email/Slack) configurable from client UI without consultant involvement | — | S |
| Consultant admin view — internal page listing all active clients, last run date, KB status, monthly cost per client | PROD-1 | M |
| Beta client onboarding runbook — internal document: step-by-step guide for the consultant to set up a new client end to end | — | S |

**Total effort:** M
**Unlocks:** recurring revenue; 10 clients × €500–1000/month; real prompt engineering learning from real strategic conversations

---

### V2.1 — Intelligence Quality Dashboard
**"Learn which sources, prompts, and KB chunks are actually working"**

After several weeks of real client runs, enough data exists to answer:
which tools produce signals that survive selection? Which RAG chunks
are never retrieved? Which intelligence types generate the most value?
This version makes that data visible and actionable.

| Feature | Ref | Effort |
|---|---|---|
| Tool performance metrics — signals collected vs selected vs in final brief, by tool source, per run | IQ-1 | M |
| RAG chunk retrieval frequency — identify chunks never retrieved across all runs (may need rewriting) | RAG-4 | S |
| Per-client run analytics — average impact level, confidence scores, LLM calls, cost per run over time | OPS-2 | M |
| Analytics tab in tool UI (or consultant admin view) | IQ-1, OPS-2 | M |
| Tool replacement guidance — based on IQ-1 data, identify underperforming tools (e.g. NewsAPI on niche B2B queries) and evaluate replacements (Perigon, NewscatcherAPI) | IQ-4 | S |

**Total effort:** M
**Unlocks:** evidence-based prompt engineering; data to justify tool changes

---

### V2.2 — Feedback Loop
**"The system learns from every correction"**

The most important mechanism for improving prompt quality and KB
precision over time. Every signal a client rates as irrelevant is a
data point. Every brief they find useful is a calibration signal.
This version closes the loop between output quality and system design.

| Feature | Ref | Effort |
|---|---|---|
| Signal rating in UI — thumbs up / thumbs down per signal in the brief (one click, no friction) | OUT-3 | M |
| Brief quality classification — client marks each brief: Relevant / Partially relevant / Off target | OUT-3 | S |
| Mark as irrelevant — removes signal category from future runs via exclusion list stored in Supabase | OUT-3 | M |
| Brief ingestion — highly-rated briefs can be ingested back into the client's KB as strategic memory; consultant approves before ingestion | OUT-3 | M |
| Feedback stored in Supabase alongside the run | OUT-3 | S |
| Monthly feedback summary emailed to consultant — top-rated signals, most-rejected types, confidence accuracy, KB ingestion candidates | OUT-3 | M |
| Confidence score calibration — adjust (llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2) weights based on feedback evidence | IQ-6 | S |

**Total effort:** L
**Unlocks:** the system improves with every brief; clients see their feedback shaping the next run; KB grows richer over time

---

### V2.3 — Cross-Signal Intelligence
**"Briefs that tell stories, not lists"**

The most common beta feedback will be: "three of these signals are
all about the same event." This version makes the brief smarter by
grouping related signals and detecting when the ReAct agent found
multiple angles on the same story.

| Feature | Ref | Effort |
|---|---|---|
| Cross-signal correlation — LLM call between evaluate_signals and generate_brief groups signals sharing the same underlying event | ARCH-2 | M |
| Grouped brief format — "3 stories, 7 signals" rather than "7 independent items" | ARCH-2 | M |
| Trend detection across runs — flag when the same competitor appears in High impact for 3+ consecutive weeks | — | M |
| Multi-query ReAct strategy — agent generates follow-up queries based on what it finds (e.g. if it finds an acquisition, search the acquirer) | IQ-5 | M |

**Total effort:** M
**Prerequisite:** V1.4 (persistent storage for trend detection across runs)
**Unlocks:** higher brief quality without changing data collection; clients stop seeing repetition

---

### V2.4 — Intelligence Expansion
**"New markets, deeper analysis"**

Two expansions that increase the system's strategic value and open
new client segments. Regulatory intelligence targets SMBs in regulated
industries. Product-opportunity matching makes Business Opportunities
briefs significantly more specific and actionable.

| Feature | Ref | Effort |
|---|---|---|
Each intelligence type below is a self-contained LangGraph branch with its own tools, prompts, and output shape. They can be activated per client depending on their industry and needs.

| Intelligence Type | Feature | Ref | Effort |
|---|---|---|---|
| **Regulatory** | New LangGraph branch monitoring legislation, compliance changes, and regulatory announcements via EUR-Lex API and government gazette feeds | PROD-3 | L |
| **Regulatory** | Regulatory watchlist KB document — client-specific regulations and compliance areas per industry | PROD-3 | M |
| **Regulatory** | Regulatory evaluation prompt — how does this regulation affect our products, markets, certifications? | PROD-3 | S |
| **Market Trends** | New LangGraph branch monitoring industry shifts, demand signals, sector-level movements — feeds from industry publications, analyst reports, Google Trends signals | — | L |
| **Market Trends** | Market trends KB document — client-defined sectors, demand signals, and trend triggers to monitor | — | S |
| **Market Trends** | Market trends evaluation prompt — is this a trend that opens or closes demand for our products? | — | S |
| **Patent Intelligence** | New LangGraph branch monitoring competitor R&D activity, IP filings, and patent grants via public patent APIs (EPO, USPTO, Google Patents) | — | L |
| **Patent Intelligence** | Patent watchlist KB document — competitor names, technology areas, and product domains to track | — | S |
| **Patent Intelligence** | Patent evaluation prompt — what does this IP activity signal about competitor direction and product roadmap? | — | S |
| **Product Matching** | Enrich KB with product catalogue and past contract wins; bid fit assessment references specific products | RAG-5 | L |
| **Product Matching** | Product lifecycle intelligence — KB with product details; Technology Developments evaluation assesses obsolescence risk, upgrade opportunity, new product gap per product | RAG-6 | M |

**Total effort:** XL (activate per client per need — Regulatory first as most common, then Market Trends, then Patent)
**Unlocks:** healthcare, finance, public sector, and R&D-intensive SMBs all become addressable; each intelligence type adds a distinct service line the consultant can offer

---

### V2.5 — Power Features
**"More capability for clients with larger intelligence needs"**

Clients who have been using the system for months will want more:
more competitors in one run, more control over their schedule, and
more adaptive research. This version serves clients who have grown
into the product.

| Feature | Ref | Effort |
|---|---|---|
| Multi-competitor / multi-sector batch runs — select 2–6 targets from UI; receive one combined brief | ARCH-3 | L |
| Scheduling from UI — set frequency (weekly/bi-weekly), select targets, set delivery channel; FastAPI updates N8N via API | OPS-1 | L |
| Agentically driven RAG retrieval — LLM decides which KB chunks to retrieve per signal rather than fixed retrieval | ARCH-4 | M |
| Combined brief format — one executive takeaway across all targets in a batch run | ARCH-3 | S |

**Total effort:** XL (can be split — Multi-competitor first, then scheduling)
**Unlocks:** clients with broader competitive landscapes; reduced consultant involvement in scheduling

---

## V3.0 — Strategic Intelligence Suite
**"More of the business — same model"**

At V3.0, the consultant expands what the tool monitors. The existing
three intelligence types (Competitor Moves, Business Opportunities,
Technology Developments) cover one dimension of a client's strategic
environment. V3.0 adds the commercial and market dimensions: products,
markets, sales. The consultant's role grows — not the client's.

By V3.0, the consultant has 12–18 months of real client data, refined
prompts, and validated KB structure. The tool gets significantly more
valuable. The relationship gets significantly deeper. The business model
stays the same.

**Product Intelligence**

Match every signal against the client's product catalogue. Which products
fit an incoming tender? Which products are being displaced by a competitor
move? Which technology shift threatens a specific product line?

| Feature | Ref | Effort |
|---|---|---|
| Product catalogue KB document — client-specific product/service list with descriptions, target sectors, differentiators; ingested at onboarding | — | M |
| Product-signal matching — every brief enriched with product fit assessment: which products are relevant to this signal and why | RAG-5 | L |
| Product lifecycle signals — Technology Developments evaluation explicitly assesses obsolescence risk and upgrade opportunity per product line | RAG-6 | M |
| Competitor product tracking — monitor competitor product launches, discontinuations, and repositioning as a dedicated signal type | — | M |

**Market Intelligence**

Monitor geographic expansion, new market entrants, sector consolidation,
and funding events that signal where an industry is moving.

| Feature | Ref | Effort |
|---|---|---|
| Market signals LangGraph branch — new intelligence type monitoring market-level events (funding rounds, M&A, market entry, sector consolidation) | — | L |
| Market watchlist KB document — client-defined target geographies, adjacent sectors, market triggers to monitor | — | S |
| Market brief node — formatted market intelligence snapshot | — | S |

**Sales Intelligence**

Track prospect company signals that create conversation opportunities:
a target company wins a tender (they have budget), a key contact moves
to a new company, a prospect expands into a new market.

| Feature | Ref | Effort |
|---|---|---|
| Prospect registry KB document — named target companies with context; consultant-managed | — | S |
| Prospect signal monitoring — track named companies across all intelligence sources for trigger events | — | L |
| Sales trigger brief — when a prospect trigger fires, notify consultant immediately (not on schedule) | — | M |

**Quarterly Strategic Synthesis**

Four times a year the consultant authors a synthesis brief — drawing on
3 months of signal history across all intelligence types. Not automated.
Consultant-written, tool-assisted. This is the highest-value deliverable.

| Feature | Ref | Effort |
|---|---|---|
| Synthesis mode — consultant triggers a synthesis run covering a date range across all intelligence types | — | M |
| Synthesis prompt — LLM produces a structured synthesis draft: key themes, competitive shifts, emerging risks, strategic implications | — | M |
| Consultant edits and delivers — synthesis arrives as a document the consultant reviews, refines, and sends | — | S |

**Total effort:** XL (delivered across multiple sprints; Product Intelligence first, then Market, then Sales)
**Unlocks:** the consultant covers more of a client's strategic surface area; higher value per engagement; deeper relationship; referrals

---

**Consultant License Program**

By V3.0, the methodology is proven: the strategic clarity session, the KB
structure, the prompt patterns, the signal evaluation rubric, the client
relationship model. Other consultants can license the tool and the method.

This is not a SaaS play. It is a franchise model for boutique consultants
who want to offer intelligence services to their own SMB clients. Marco
trains them on the methodology; they do the setup and maintain the
relationship with their clients. The tool is white-labelled to their brand.

| Feature | Ref | Effort |
|---|---|---|
| Consultant onboarding package — methodology guide, KB setup playbook, prompt engineering notes, client intake template | — | M |
| White-label configuration — CONSULTANT_NAME, CONSULTANT_LOGO, BRAND_COLOR; all UI and email output reflects the licensed consultant's brand | I | S |
| Consultant admin panel — licensed consultants manage their own client list, KBs, and deployments independently | — | L |
| License management — each licensed consultant gets their own Railway + Pinecone setup; Marco's codebase; their brand; their client relationships | — | S |

**Business model:** license fee + optional ongoing support retainer from the
licensed consultant. Marco stays one level up: training, methodology updates,
prompt engineering improvements that all licensees benefit from.

**Unlocks:** revenue that does not require Marco's direct time per client;
a network of consultants improving the methodology; referrals across industries

---

## The Arc

```
V1.2  Complete the product      (three intelligence types)
V1.3  Secure it                 (auth + prompt templates)
V1.4  Give it memory            (persistent storage)
V1.5  Make it reliable          (alerting + cost control + retry)
V1.6  Make it onboardable       (LLM-assisted KB setup)
V1.7  Make it maintainable      (consultant KB tools)
V1.8  Make it engaging          (Slack + comparison view)
V1.9  Make it feel like a product (white-label + configurability)
──────────────────────────────────────────────────────────────────
V2.0  BETA LAUNCH               (first paying clients — consultant-managed)
──────────────────────────────────────────────────────────────────
V2.1  Learn what works          (intelligence quality dashboard)
V2.2  Learn from clients        (feedback + brief ingestion loop)
V2.3  Better briefs             (cross-signal correlation + trends)
V2.4  Expand depth              (regulatory + product matching)
V2.5  More power                (batch runs + scheduling from UI)
──────────────────────────────────────────────────────────────────
V3.0  STRATEGIC INTELLIGENCE SUITE  (products + markets + sales)
──────────────────────────────────────────────────────────────────
      The consultant is the product.
      The tool is what makes the service remarkable.
```

---

## Won't Build

| Item | Reason |
|---|---|
| PDF export | HTML email is lighter, links are clickable, renders on mobile, no generation dependency. See architecture_decisions.md Decision 15. |
| Multi-tenant SaaS architecture | Out of scope for the consulting model — per-client Railway projects is the right pattern throughout |
| Client self-service KB management | The consultant manages the KB. Quality of intelligence depends on quality of input. This is not delegated to clients. |
| Mobile app | Not relevant for this audience or use case |
| Fully automated onboarding without consultant involvement | The strategic clarity session before KB creation is a feature, not a bug. It is where the consultant's value starts. |

---

## Continuous Improvements (No Version Gate)

These are not features — they are ongoing practices that run in
parallel with all versions.

- **Domain list expansion (IQ-2)** — add industry-specific domains discovered through real client runs to `domain_lists.json`. No code changes required. Edit JSON, redeploy.
- **KB document quality** — rewrite chunks that are never retrieved (identified in V2.1). Better chunking = better retrieval = better evaluation.
- **Prompt engineering** — refine system prompts based on feedback data (V2.2) and real run output. The prompts are the product's competitive moat.
- **Competitor and sector registry** — expand the default lists as new industries are served.
- **API tool evaluation and selection** — the current toolset (Tavily, NewsAPI, HackerNews, TED) covers general and EU public sector signals well, but more specialised tools exist for niche industries and signal types. From V2.1 onwards, the performance dashboard gives data on which tools actually produce signals that survive into the final brief. Use this data to evaluate and replace underperformers. Candidates: Perigon, NewscatcherAPI, sector-specific RSS feeds, LinkedIn company signals, Crunchbase funding data. Track experiments in a dedicated log. This is not a one-time task — every new client industry is an opportunity to find a better tool for that vertical.
- **LLM provider and model evaluation** — the system currently runs on OpenAI GPT-4o exclusively. This creates a single point of dependency on pricing, rate limits, and model changes. As the model landscape evolves, evaluate alternatives on three axes: output quality (brief coherence, signal evaluation accuracy), cost per run, and reliability. Candidates: Anthropic Claude, Google Gemini, Mistral (for cost-sensitive runs), open-source models via Ollama (for on-premise clients). Run parallel evaluations on the same signal sets with different models and compare results. The goal is not to switch wholesale, but to maintain the ability to route by cost tier or client requirement. Document every evaluation with prompt version, model, sample output, and cost — the record becomes institutional knowledge.
