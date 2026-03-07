[//]: # (Version 1.1 — Final demo delivery to Ironhack 2026-03-06)
# CHANGELOG

Track every change to every file, by version and date.

Format:
```
## [Version] — YYYY-MM-DD — Description
### file/path.ext
- What changed
```

---

## V1.1 — 2026-03-06 — Final demo delivery to Ironhack

### agent/graph.py
- V1.1 branch added: Business Opportunities (collect_opportunities, evaluate_opportunities, generate_opportunity_brief)
- route_after_validation() extended with V1.1 conditional edge
- V1.2 Technology Developments extension point stubbed and commented

### agent/nodes.py
- 3 new nodes: collect_opportunities, evaluate_opportunities, generate_opportunity_brief
- Three signal types: live_tenders, private_expansion, pre_tender
- LLM classification call to separate private vs pre-tender signals
- Hybrid collection: deterministic TED API + ReAct for web signals
- Confidence formula updated: (llm_score * 0.5) + (rag_score * 0.3) + (source_quality * 0.2)
- FIX: translated_title used to overwrite raw TED title in evaluated output
- FIX: Explicit High/Medium/Low rubric added to all 4 evaluation prompts
- FIX: Irrelevant signal filtering — _evaluate_item returns None for off-target signals
- FIX: Two-layer deduplication (URL exact match + title word-overlap threshold = 4 words)
- VALID_SECTORS: QSR and Food Service, Smart Cities, Airport and Transport, Retail, Public Services

### agent/state.py
- V1.1 fields added: raw_tenders, raw_private_signals, raw_pretender_signals
- V1.1 evaluation fields added: evaluated_tenders, evaluated_private, evaluated_pretender
- run_id and llm_calls_made added to meta section

### agent/tools/ted.py
- New MCP tool: TED EU Open Data API, no API key required
- CPV code mapping per sector (5 sectors, 3-4 CPV codes each)
- Keyword search per sector as secondary pass
- Multilingual text extractor for TED title fields (ENG / EN / eng fallback)
- Deduplication by notice_id across CPV and keyword passes

### agent/tools/tavily.py
- No functional changes in V1.1

### agent/tools/hackernews.py
- No functional changes in V1.1

### agent/tools/newsapi.py
- No functional changes in V1.1

### agent/tools/utils.py
- No functional changes in V1.1

### rag/retriever.py
- No functional changes in V1.1

### rag/ingest.py
- No functional changes in V1.1

### core/logging_config.py
- No functional changes in V1.1

### api/main.py
- Version bumped to 1.1.0
- New routes: / (index.html), /tool (tool.html), /slides (slides.html), /ui (alias for /tool)
- /api/info endpoint added (version, intelligence types, valid sectors, time ranges)
- POST /run: subject field replaces company; response schema extended with tenders, private_opportunities, pretender_opportunities fields
- Navigation updated across all three pages

### api/static/index.html
- New page: project overview (Overview tab)
- Disclaimer updated: Ironhack bootcamp context added, Case Study link added

### api/static/tool.html
- subject field replaces company input
- Tender cards, private opportunity cards, pre-tender cards added to output
- Sector dropdown added for Business Opportunities runs
- Disclaimer updated: Ironhack bootcamp context added, Case Study link added

### api/static/slides.html
- New page: 9-slide presentation deck
- Slide 09 (Next Steps): product roadmap link and case study link added
- Slide 04 (Architecture): Pinecone RAG description shortened
- Slide 05 (Graph): "Route by Intelligence Type" label shortened
- Disclaimer updated: Ironhack bootcamp context added, Case Study link added

### README.md
- Full rewrite to align with V1.1
- casestudy.md added to Project Documents table
- Live System URLs updated: /tool and /slides added
- MVP V1.1 section added (was listed as Post-MVP — now COMPLETE)
- POST /run request field: company → subject
- POST /run response schema: tenders, private_opportunities, pretender_opportunities, final_brief
- Project Structure updated: tool.html, slides.html, casestudy.md added
- What Is NOT in MVP section updated to reference product_roadmap.md

### architecture_decisions.md
- Decision 3 corrected: technology_watchlist.md is already ingested from V1.0 (was incorrectly listed as V1.2 addition)
- Decision 16 (duplicate): multilingual TED translation renumbered to Decision 17
- Decision 5 updated: VALID_SECTORS controlled input principle extended to V1.1
- Decision 8 updated: three-page UI structure documented
- Decision 12 updated: ted.py added to implemented MCP tools
- Decision 18 added: V1.1 three-type signal taxonomy
- Decision 19 added: Hybrid collection — deterministic TED + ReAct
- Decision 20 added: Confidence formula evolution and weight rationale
- Trade-offs Summary: 4 new rows added
- Final Summary updated: V1.1 complete, V1.2 arc described

### project_summary.md
- Full rewrite to reflect V1.1 completion
- Status table updated: 4 MCP tools, 3 HTML pages, V1.1 branch DONE
- 9 nodes documented (6 V1.0 + 3 V1.1)
- 5 post-V1.1 fixes documented
- Sample run 4 added (Business Opportunities)
- All product_backlog.md references replaced with product_roadmap.md

### product_roadmap.md
- Created: replaces product_backlog.md (deleted)
- V1.2 → V3.0 versioned roadmap with effort estimates
- Business model statement: consultant-managed end to end, unchanged V2.0 → V3.0
- V1.7 reframed: Consultant KB Tools (consultant admin view, not client self-service)
- V2.0 description updated: client surface area is delivery preferences + brief feedback only
- V2.2 Feedback Loop: brief classification + brief ingestion into KB added
- V2.4 Intelligence Expansion: Market Trends and Patent Intelligence added as self-contained branches
- V3.0 complete rewrite: Strategic Intelligence Suite (Product, Market, Sales, Quarterly Synthesis)
- Consultant License Program added within V3.0
- Continuous Improvements: API tool evaluation and LLM model evaluation added
- Won't Build: client self-service KB management and fully automated onboarding added

### casestudy.md
- Created: full case study write-up for Ironhack AI Consulting submission

### Deleted
- product_backlog.md — superseded by product_roadmap.md

---

## How to use this file

Every time you change a file — even a single line — add an entry here.

```
## V1.2 — YYYY-MM-DD — Short description of the release or change
### path/to/file.ext
- What changed and why (one line per logical change)
```

Keep entries specific. "Updated nodes.py" is not useful. "Added collect_technology node — V1.2 branch" is.
