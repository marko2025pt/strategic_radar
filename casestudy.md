[//]: # (Version 1.1 — Final demo delivery to Ironhack 2026-03-06)
# Strategic Radar — Case Study
### An Autonomous Strategic Intelligence Engine
**By Marco Martins · Ironhack AI Consulting · 2026**

---

## Disclaimer

Strategic Radar uses PARTTEAM & OEMKIOSKS as a case study for demonstration purposes only. All information about the company was sourced from publicly available sources. This project has no affiliation with or endorsement from PARTTEAM & OEMKIOSKS. Strategic objectives referenced in this system are illustrative — informed by public information but not representative of the company's actual strategy.

This was an unsolicited case study, selected independently to ground the tool in a real company operating in a real, competitive market.

---

## 1. Executive Summary

Strategic Radar is an autonomous strategic intelligence engine built to solve a problem that most mid-to-large companies face but rarely address systematically: the gap between market signals and strategic action.

Built as a final project for the Ironhack AI Consulting programme, Strategic Radar monitors competitor moves and business opportunities in real time, evaluates every signal against a company's strategic objectives, and delivers a ranked, actionable intelligence brief — automatically, every Monday morning, before the week begins.

The system was built using PARTTEAM & OEMKIOSKS — a Portuguese leader in digital kiosks and DOOH solutions — as the case study subject. The choice was deliberate: PARTTEAM operates in a fast-moving, competitive market where tender windows are short, competitor moves are frequent, and the cost of missing a signal is a lost deal.

The result is a fully functional, deployed system — not a prototype. It runs on a live API, connects to real data sources, grounds its analysis in a structured knowledge base, and delivers formatted intelligence briefs via email.

---

## 2. The Company & Context

**PARTTEAM & OEMKIOSKS** is a Portuguese technology company specialising in the design and manufacturing of digital kiosks, interactive displays, and digital out-of-home (DOOH) solutions. Founded in Vila Nova de Famalicão, the company serves clients across multiple verticals — including retail, quick service restaurants (QSR), airports, smart cities, and public services — with a growing international footprint.

Their market is characterised by:

- **Fast-moving tender cycles** — public procurement opportunities open and close within weeks, often with pre-positioning windows that are even shorter
- **Active competitor landscape** — global players like Acrelec, Pyramid Computer, Broadsign, Wanzl, Diebold Nixdorf, and LamasaTech are constantly repositioning, acquiring, and expanding
- **Technology disruption** — AI integrations, new display standards, and evolving DOOH ecosystems are reshaping the competitive dynamics faster than traditional intelligence cycles can track

In this environment, the cost of missing a signal is not theoretical. A competitor acquisition changes the market. A tender published on a Monday can expire before anyone on the team has read the briefing notes.

PARTTEAM was selected as the case study subject precisely because of this tension — a strong, growth-oriented company operating in exactly the kind of market where autonomous strategic intelligence creates real competitive advantage.

---

## 3. The Problem

Most companies rely on a combination of Google Alerts, manual news scanning, LinkedIn monitoring, and the occasional consultant report to stay informed about their competitive environment. For a company operating at PARTTEAM's scale and ambition, this is not enough.

The core problem is not a lack of information. It is a lack of capacity to process it.

**Three specific failure modes emerge:**

**Generic intelligence with no strategic context.** Standard market monitoring tools return articles, news, and company updates — but leave the interpretation entirely to the reader. You still have to figure out if it matters, why it matters, and what to do about it. By the time someone has done that analysis, the window may already be closed.

**Manual scanning is slow and inconsistent.** The people best positioned to interpret market signals — senior leadership and strategy teams — are also the least likely to have time to find them. Scanning gets delegated, deprioritised, or simply abandoned during busy periods. The result is reactive decision-making based on incomplete information.

**No connection to strategic objectives.** Even when signals are captured, they rarely get connected back to what the company is actually trying to achieve. A competitor's new product launch is noted, discussed briefly in a meeting, and forgotten — because nobody has a system that says "this matters to objective 3, and here is why."

The cumulative effect is a slow erosion of competitive positioning. Not dramatic. Not visible until a deal is lost or a tender deadline is missed.

---

## 4. The Solution

Strategic Radar addresses all three failure modes with a single, autonomous system.

**Every signal is evaluated against strategy, not just collected.** Before any signal reaches the intelligence brief, it is measured against the company's active strategic objectives using a vector search over the company's knowledge base. The system does not just ask "what happened?" — it asks "does this matter to us, and why?"

**The system runs itself.** Strategic Radar is triggered automatically every Monday morning at 8am via a scheduled workflow. It researches, evaluates, and delivers the brief without any human intervention. Leadership opens their inbox on Monday morning and the analysis is already there.

**Output is designed for decisions, not reading.** The intelligence brief is a single page. Signals are ranked by strategic impact. Each signal comes with a rationale — why it matters — and a recommended action. There are no walls of text. No noise. Just what matters and what to do next.

The system operates in two intelligence modes:

- **Competitor Moves** — monitors a controlled list of competitors across live sources (Tavily, NewsAPI, HackerNews), selects the top signals, evaluates their strategic impact, and generates a competitor snapshot
- **Business Opportunities** — searches the TED EU public procurement database for active tenders, pre-tender signals, and private opportunities relevant to the company's target sectors, evaluated for fit and urgency

Both modes can also be triggered manually on demand via the web interface, with results delivered in under 60 seconds.

---

## 5. Architecture & Design Decisions

Strategic Radar is built on an eight-layer stack, designed to be modular, extensible, and deployable.

### The Stack

| Layer | Technology | Role |
|---|---|---|
| Orchestration | N8N Cloud | Scheduled workflows, loops, email assembly |
| API & Deployment | FastAPI + Railway | HTTP interface, cloud hosting |
| User Interface | Custom HTML/CSS/JS | Manual runs, live demos, result display |
| Cognitive Workflow | LangGraph | Stateful graph with conditional routing |
| Research Agent | ReAct Agent | Signal discovery loop across live sources |
| Strategy Grounding | Pinecone RAG | Vector search over the knowledge base |
| Live Data | Tavily, NewsAPI, HackerNews, TED EU | Real-time signal sources |
| Intelligence & Delivery | OpenAI GPT-4o + SendGrid | Evaluation, brief generation, email |

### Key Design Decisions

**LangGraph for workflow control.** A simple chain would not support the conditional routing needed to branch between competitor and opportunity modes, or handle the iterative research loop of the ReAct agent. LangGraph provides a stateful graph with explicit node transitions and conditional edges — giving precise control over the intelligence pipeline.

**RAG for strategy grounding.** The most important design decision in the system is the use of retrieval-augmented generation against a structured knowledge base. Without this, the system produces generic intelligence — the same analysis anyone with a ChatGPT subscription could generate. With it, every signal is interpreted through the company's specific identity, objectives, and competitive context.

**N8N for orchestration.** Rather than building scheduling and looping logic into the FastAPI application, N8N handles the operational layer — running competitor loops, sector loops, combining briefs, and triggering email delivery. This keeps the core intelligence logic clean and separates operational concerns.

**ReAct Agent for research.** The research loop uses a ReAct (Reasoning + Acting) agent pattern — the model reasons about what to search for, acts by calling the search tools, observes the results, and iterates until it has sufficient signal coverage. This produces more targeted and thorough research than a single-pass query.

### Portability & Deployment Flexibility

One of the core architectural principles behind Strategic Radar is that the intelligence logic is completely decoupled from the infrastructure it runs on. This was a deliberate design decision — not an afterthought.

The current deployment runs as a cloud-native stack: Railway for hosting, Pinecone for vector storage, N8N Cloud for orchestration, SendGrid for email delivery, and OpenAI for language model inference. This makes it fast to deploy, easy to demo, and accessible from anywhere.

But every layer is independently replaceable:

| Current (Cloud) | Alternative (On-Premise / Enterprise) |
|---|---|
| Pinecone | Chroma, Weaviate, pgvector, Qdrant |
| SendGrid | Company SMTP, Microsoft Exchange, internal mail relay |
| N8N Cloud | On-premise N8N, Apache Airflow, internal scheduler |
| Railway | Company server, private cloud, on-premise VM |
| OpenAI API | Azure OpenAI (data residency), Ollama + local models |

This means the same system that runs as a cloud-native demo today can be deployed fully inside a corporate network tomorrow — with no changes to the core intelligence logic. The LangGraph pipeline, the RAG evaluation, the ReAct research agent — all of it runs identically regardless of the infrastructure layer beneath it.

This matters for enterprise deployment in two specific ways.

**Data sovereignty.** Strategic intelligence is sensitive by definition. Competitor analysis, tender strategy, and market positioning are not data that most companies want transiting external APIs or stored in third-party vector databases. A fully on-premise deployment keeps everything behind the firewall — the knowledge base, the search queries, the generated briefs, and the email delivery.

**Vendor independence.** The layered architecture avoids lock-in to any single provider. If OpenAI pricing changes, swap the model layer. If the company already runs an internal orchestration platform, replace N8N. If there is an existing email infrastructure, point the delivery layer at it. The system adapts to the company's existing technology landscape rather than requiring the company to adapt to it.

For an organisation like PARTTEAM — or any mid-to-large enterprise evaluating this as a production tool — the path from demo to internal deployment is a configuration change, not a rebuild.

---

## 6. The Knowledge Base

The knowledge base is the strategic identity of the company, encoded and queryable. It is what transforms Strategic Radar from a news aggregator into a strategic intelligence system.

Four documents form the knowledge base, stored as vector embeddings in Pinecone:

**`business_profile.md`** — Company identity, products, verticals, and revenue model. Gives the system a grounded understanding of who the client is, what they sell, and which markets they serve. Without this, signals cannot be evaluated for relevance.

**`strategic_direction.md`** — Active strategic objectives with explicit signal relevance criteria. This is the core filter. Every incoming signal is measured against these objectives. A signal that is globally significant but irrelevant to the company's current priorities scores low. A signal that directly threatens or enables a specific objective scores high.

**`competitor_registry.json`** — A controlled list of monitored competitors with structured metadata. Keeps research focused on the right players and prevents the system from drifting toward irrelevant market actors. The registry is the boundary of the competitive intelligence scope.

**`technology_watchlist.md`** — Emerging technologies relevant to the client's ecosystem. Keeps the system aware of disruptive trends — AI integrations, new display standards, evolving DOOH infrastructure — before they reach mainstream adoption. This is the early warning layer.

Together, these four documents answer the system's core question before any signal is evaluated: *"Does this matter to us — and why?"*

For PARTTEAM, the knowledge base was constructed from publicly available information — company website, press releases, LinkedIn, industry publications, and tender history. In a production deployment, this would be replaced with proprietary internal documents, making the intelligence significantly sharper.

---

## 7. Results & Output Quality

Strategic Radar produces two types of output: **competitor snapshots** and **opportunity briefs**.

### Sample Output — Business Opportunities

**QSR and Food Service · 06 Mar 2026**

> **Executive Takeaway**
>
> The biggest opportunity this week lies in McDonald's aggressive global expansion plans, which present a significant chance to supply self-ordering kiosks and digital signage solutions. Leadership should prioritise establishing connections with McDonald's regional procurement and technology teams to position the company as a key supplier in their expansion strategy. This proactive engagement could secure a substantial market share in the QSR and Food Service sector, aligning with strategic growth objectives.

Each brief includes:

- **Signal title** with source link
- **Impact summary** — why this signal matters strategically
- **Strategic link** — which objective it connects to
- **Impact level** — High / Medium / Low
- **Confidence score** — 0–10
- **Recommended action** — what to do next
- **Deadline urgency** (for tenders)

### What the Output Demonstrates

The system consistently produces signals that are specific, contextualised, and actionable — not generic summaries that could apply to any company. The strategic link to a specific objective, combined with a concrete recommended action, means the brief is ready to be acted on, not just read.

In testing across multiple competitors and sectors, the system produced relevant, non-obvious signals in the majority of runs — including pre-tender signals months before formal publication, competitor leadership changes with market positioning implications, and technology partnerships that indicated strategic pivots.

---

## 8. Limitations & Honest Reflection

A case study without honest limitations is marketing, not analysis.

**The knowledge base is illustrative, not real.** PARTTEAM's strategic objectives were inferred from public information — website, press releases, LinkedIn, and industry context. The real strategic priorities of the company are internal. This means the relevance scoring, while coherent and well-reasoned, is not calibrated against the company's actual decision-making framework.

**Signal quality depends on source coverage.** The system is limited to its configured data sources — Tavily, NewsAPI, HackerNews, and TED EU. Signals that appear only in paywalled publications, private databases, or non-English sources may be missed. Production deployment would require broader source coverage.

**No feedback loop.** The current system has no mechanism for the user to rate signal quality or mark briefs as useful or irrelevant. Without this, the system cannot learn and improve over time. A feedback loop is the highest-priority item in the product backlog.

**N8N scheduling is not fault-tolerant.** If the Monday morning run fails silently, there is no alerting or retry mechanism beyond N8N's basic error handling. A production system would need monitoring and alerting on the orchestration layer.

**LLM costs are not negligible at scale.** Each full run — competitor loop plus sector loop — makes multiple GPT-4o calls. At scale, across many companies and geographies, this needs cost optimisation through caching, model selection, and smart routing.

These limitations are not reasons the system doesn't work — it does, and the output quality demonstrates it. They are the honest map of the distance between a well-built MVP and a production-grade product.

---

## 9. What's Next — Product Backlog

Strategic Radar was built in one week as a final project. The roadmap extends well beyond that.

### From Demo to Real Value for Businesses

Strategic Radar is a working demonstration of a thinking system — not just a technical tool. The code can be replicated. What is harder to replicate is the design logic behind it: how to structure a company's strategic identity into a queryable knowledge base, how to define signal relevance criteria that are specific enough to be useful, how to connect raw market data to the questions that actually matter to leadership.

That thinking is the real asset. And it points to two paths forward.

**Path 1 — Partner with a company that wants to take this further**
A company that sees the potential of autonomous strategic intelligence — and wants a version deeply customised to their context, their data, their infrastructure, and their competitive landscape — could partner to develop this into a proprietary internal system. The starting point is not a blank page. The architecture is proven, the pipeline is running, and the knowledge base framework is already designed. What a partner brings is the internal context, the strategic priorities, and the ambition to make it a core part of how they compete. What I bring is the system, the thinking, and the ability to build what comes next.

**Path 2 — Strategic intelligence consulting, powered by the system**
The tool itself could become the engine behind a strategic intelligence consulting practice. Not a software product sold by the seat — but a service where the value is the quality of the intelligence delivered, and the system is what makes that delivery consistent, fast, and scalable. The knowledge base design, the signal evaluation framework, and the brief format are all transferable across industries and company types. The consultant's role is to ask the right questions, build the right knowledge base, and interpret what the system surfaces into decisions that matter.

In both cases, the tool is not the point. The point is what it makes possible: a company that always knows what the market is doing, why it matters, and what to do about it — before the week begins.

---

**Short term — hardening the MVP**
- User feedback loop on signal quality
- Monitoring and alerting on the orchestration layer
- Expanded source coverage (paywalled publications, non-English sources)
- Cost optimisation on LLM usage

**Medium term — expanding the product**
- Multi-company support — run the same system for multiple clients with isolated knowledge bases
- Slack and Teams delivery in addition to email
- Dashboard for signal history and trend tracking
- Configurable alert thresholds — only notify when a High impact signal is detected

**Long term — the platform vision**
- Self-serve knowledge base builder — clients configure their own strategic identity
- Industry-specific signal packages — retail, smart cities, transport, healthcare
- API for integration into existing BI and strategy tools
- White-label deployment for consulting firms

The full product backlog is available on GitHub.

---

## 10. About the Author

**Marco Martins** is a professional with 10+ years of experience, currently completing the AI Consulting programme at Ironhack. Strategic Radar was built as a final project to demonstrate the practical application of AI agents, RAG systems, and autonomous workflows to real business problems.

The project was conceived, designed, and built independently — from problem framing to architecture to deployment — in one week.

Marco is interested in roles and collaborations at the intersection of AI, strategy, and product — where the goal is not to build AI for its own sake, but to build systems that create real competitive advantage for real organisations.

**Connect:** [linkedin.com/in/marcojoelmartins](https://www.linkedin.com/in/marcojoelmartins/)

---

*Strategic Radar · Built with LangGraph, FastAPI, Pinecone, OpenAI, N8N, and SendGrid · Deployed on Railway · 2026*
