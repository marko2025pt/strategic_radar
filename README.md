# Autonomous Competitive Intelligence Agent  
### Evidence-Driven Agent Architecture for Reliable Market Research

---

## Executive Overview

Organizations increasingly rely on AI agents for research and competitive intelligence. However, most implementations lack structural validation, bounded autonomy, and observability — leading to hallucinations, unreliable outputs, and opaque decision-making.

This project implements a modular, evidence-driven autonomous research agent designed to generate structured competitive intelligence reports.  

The MVP is instantiated in the **Digital Out-of-Home (DOOH)** ecosystem (MUPIS, Digital Signage, Self-Service Kiosks), while the architecture remains industry-agnostic and reusable.

The objective is not merely automation — but **reliable autonomy**.

The system integrates:

- ReAct reasoning for intelligent tool selection  
- LangGraph for stateful workflow orchestration  
- Pinecone RAG for contextual industry grounding  
- MCP-based API integration (Search, News, Financial data)  
- N8N for operational deployment and automated delivery  

The result is an end-to-end autonomous workflow capable of producing structured business intelligence reports with transparent confidence indicators and bounded retry logic.

---

## Why This Architecture Matters

Most AI agents fail in production due to:

- Lack of validation before synthesis  
- Over-reliance on LLM judgment  
- Hidden reasoning steps  
- Unbounded loops  
- Poor observability  

This system addresses those issues through:

- Structural evidence coverage rules before analysis  
- Deterministic workflow routing  
- Bounded retry mechanisms (max 1 improvement pass per section)  
- Explicit state schema  
- Execution logging for traceability  
- Confidence scoring and data gap reporting  

The architecture separates cognition, control, and orchestration to ensure clarity and extensibility.

---

## System Architecture

### Layered Design

**Cognition Layer**  
ReAct Research Agent — performs reasoning and tool selection.

**Control Layer**  
LangGraph workflow — manages state, routing, retries, and transitions.

**Knowledge Layer**  
Pinecone RAG — stores structured industry archetypes.

**Data Layer**  
External APIs (Search, News, Financial data).

**Orchestration Layer**  
N8N workflow — triggers execution and delivers final report via email.

Only the research phase uses dynamic reasoning.  
All subsequent phases (analysis, reporting, delivery) are deterministic and structured.

---

## Workflow Overview

1. Input received (company + research objective)
2. Research plan generated (visible planning step)
3. ReAct loop performs multi-source research
4. Structural coverage validation applied
5. Single-pass quality evaluation
6. Optional bounded retry (max 1 per section)
7. Structured report generation
8. Email delivery via N8N

The system always produces output while surfacing uncertainty when data quality is insufficient.

---

## Input Schema

```json
{
  "company": "string",
  "research_objective": "string",
  "include_opportunities": true
}
```

## State & Observability

The system uses an explicit shared state model to ensure transparency and maintainability.

### Core State Elements

- `research_plan`
- `evidence` (categorized by section)
- `coverage_validation_flags`
- `quality_scores`
- `analysis`
- `report_text`
- `execution_log`
- `retry_counter`
- `needs_human_review`
- `errors`

Each workflow node owns a specific portion of the state to prevent side effects and debugging ambiguity.

---

### Execution Log

The `execution_log` acts as a trace layer, recording:

- Major decisions
- Tool executions
- Phase transitions
- Errors

This improves debugging, transparency, and demo clarity.

---

## Knowledge Base Design (Reusable Schema)

The RAG system is structured around reusable industry archetypes:

- Industry Context
- Business Models
- Financial Patterns
- Risk Patterns
- Competitive Dynamics

This allows the agent architecture to be reused across industries by replacing domain documents without modifying workflow logic.

For the MVP, the knowledge base is instantiated with DOOH / MUPIS industry materials.

---

## Tools & APIs

- DuckDuckGo Search API → Company discovery & web intelligence
- NewsAPI → Industry trends & updates
- Yahoo Finance (`yfinance`) → Financial metrics
- Pinecone → Vector database for contextual retrieval
- LangChain + LangGraph → Agentic workflow framework
- N8N → Production-style orchestration & delivery

Minimum three real-world APIs integrated as required by project constraints.

---

## Report Structure

Each generated report includes:

- Executive Summary
- Company Overview
- Industry Context
- Competitive Landscape
- Financial Highlights
- Risks & Opportunities
- Confidence & Data Gaps
- How This Report Was Created

The final section enhances transparency and demonstrates autonomous planning.

---

## Strategic Design Decisions

- Structural validation precedes interpretation
- Autonomy is bounded, not open-ended
- Human-in-the-loop escalation path designed (future phase)
- Architecture prioritizes extensibility over short-term complexity
- Observability embedded from the start

---

## Future Extensions

- Industry-adaptive report templates
- Reliability weighting per data source
- Human review escalation workflow
- Multi-company comparative analysis
- Dashboard interface

---

## Setup & Execution

1. Create virtual environment
2. Install dependencies
3. Configure `.env` with API keys
4. Initialize Pinecone index
5. Run standalone Python agent
6. Trigger workflow via N8N

Detailed setup instructions available in `/docs`.

---

## Positioning

This project demonstrates:

- Agentic architecture design
- Failure-mode awareness
- Governance-aware AI implementation
- Modular extensibility
- Practical integration of RAG, ReAct, LangGraph, MCP, and N8N

The focus is not on maximizing autonomy, but on designing reliable autonomous systems suitable for real-world deployment.