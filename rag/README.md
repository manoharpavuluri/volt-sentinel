# VoltSentinel Cognitive RAG Pipeline — Full Package

This is the complete RAG package for the VoltSentinel project, not only the fixes. It contains a full contract-grounded workflow for using PPA documents to explain and support revenue-leakage dispute recommendations.

## What this pipeline does

The RAG pipeline connects a **Gold fact-table breach event** to the relevant **PPA contract evidence**.

It does not calculate the final dollar amount. The Gold table is the source of truth for dollars. RAG explains whether the contract supports dispute review.

## End-to-end flow

1. **Document Inputs**: PPA PDFs, amendments, rate schedules, legal clauses.
2. **Layout Parsing**: Azure Document Intelligence extracts text, tables, headings, and page structure.
3. **Chunking & Metadata**: chunks retain clause/page/section/version metadata.
4. **Embeddings & Index**: OpenAI embeddings stored in Supabase/Postgres pgvector with HNSW index.
5. **Retrieval**: breach event drives contract-scoped semantic search.
6. **Deterministic Guardrails**: validates contract ID, chunk IDs, similarity threshold, Gold variance, and evidence presence.
7. **LLM Synthesis**: produces structured JSON dispute recommendation and explanation.
8. **Human & CRM Action**: human approval required before Salesforce case creation.

See `diagrams/voltsentinel_rag_pipeline_workflow_diagram.png` for the infographic.

## Folder structure

```text
volt_sentinel_rag_full/
├── README.md
├── RAG_TRD_FULL.md
├── .env.rag.example
├── requirements-rag.txt
├── diagrams/
├── source_originals/
├── stateful_ai_framework/
│   ├── ddl_pgvector.sql
│   ├── parse_and_vectorize.py
│   ├── semantic_retriever.py
│   ├── langgraph_orchestrator.py
│   ├── outbound_crm_connector.py
│   └── legal_assets/
├── sample_payloads/
└── tests/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-rag.txt
cp .env.rag.example .env
```

Fill in `.env` values for:

- OpenAI
- Azure Document Intelligence
- Supabase/Postgres
- Upstash Redis REST
- Salesforce sandbox

## Database setup

Run this in Supabase SQL editor:

```bash
stateful_ai_framework/ddl_pgvector.sql
```

This creates:

- `ppa_parent_documents`
- `ppa_child_chunks`
- `rag_dispute_audit_log`
- pgvector indexes

## Ingest a contract

```bash
python stateful_ai_framework/parse_and_vectorize.py \
  --document-path stateful_ai_framework/legal_assets/sample_wildorado_google_ppa.txt \
  --contract-id PPA_GOOG_WILDORADO_WIND \
  --asset-id CW_WIND_WILDORADO \
  --offtaker-name "Google Cloud Operations LLC"
```

## Test retrieval

```bash
python stateful_ai_framework/semantic_retriever.py \
  --contract-id PPA_GOOG_WILDORADO_WIND \
  --query "curtailment compensation and settlement adjustment rules"
```

## Run the graph

Use `sample_payloads/breach_event_sample.json` as the breach event input.

The graph flow is:

```text
retrieve_context → deterministic_pre_guard → synthesize_discrepancy → deterministic_post_guard → human_approval → crm_dispatch
```

## Key design principle

```text
Gold fact table computes dollars.
RAG explains contractual support.
Human approves external action.
```

## Added in v2: Headroom + RAG observability + evolution diagram

This package now includes optional Headroom context optimization, RAG runtime observability, dashboard KPI specs, and a before/after architecture evolution diagram.

New additions:

```text
stateful_ai_framework/context_optimizer.py
architecture/headroom_context_optimization.md
observability/README.md
observability/rag_event_logger.py
observability/dashboard_schema.sql
dashboards/control_tower_kpis.md
diagrams/ai_architecture_evolution_infographic.png
```

### Headroom role

Headroom is optional. It compresses only non-authoritative LLM prompt context after retrieval. Raw evidence, Gold breach event values, guardrail inputs, approval payloads, and Salesforce audit records remain unchanged.

### RAG observability role

RAG observability captures:

- retrieval quality
- citation quality
- similarity scores
- guardrail outcomes
- LLM tokens and cost
- Headroom savings
- Redis cache hit/miss rate
- LangGraph node latency
- human approval status
- Salesforce dispatch status

### Architecture evolution view

The new evolution diagram shows:

```text
Original CCR design → What changed → Current contract-grounded, auditable RAG
```
