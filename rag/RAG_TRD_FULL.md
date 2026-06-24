# VoltSentinel Cognitive RAG Pipeline — Full Technical Reference Design

## 1. Objective

The VoltSentinel Cognitive RAG Pipeline connects structured financial breach events from the lakehouse Gold layer with unstructured PPA contract evidence.

The goal is to support dispute decisions with contract-grounded explanations, not to let the LLM become the system of record for revenue calculations.

## 2. Core design rule

```text
Gold computes dollars. RAG explains contract support. Human approves CRM action.
```

## 3. Inputs

### 3.1 Contract inputs

- PPA PDFs or text extracts
- amendments
- rate schedules
- settlement exhibits
- curtailment compensation clauses
- force majeure / limitation clauses

### 3.2 Breach event input

A breach event comes from the Gold fact table and includes:

- `fact_record_hash`
- `reconciliation_hour`
- `asset_id`
- `associated_ppa_id`
- `actual_generation_mwh`
- `expected_available_mwh`
- `eligible_compensable_mwh`
- `actual_settlement_usd`
- `expected_settlement_usd`
- `estimated_leakage_revenue_usd`

## 4. Topology

```text
[PPA documents]
    │
    ▼
[Azure Document Intelligence]
    │
    ▼
[Clause-aware chunker]
    │
    ▼
[OpenAI embeddings]
    │
    ▼
[Supabase/Postgres pgvector]
    ▲
    │
[Gold breach event] ──► [contract-scoped retriever]
    │                         │
    │                         ▼
    │                  [evidence pack]
    │                         │
    ▼                         ▼
[deterministic guardrails] → [LLM synthesis] → [post-guardrails] → [human approval] → [Salesforce case]
```

## 5. Storage schema

The database schema uses pgvector and parent-child document storage.

### 5.1 Parent document

Stores one record per contract version.

Important columns:

- `contract_id`
- `contract_name`
- `offtaker_name`
- `asset_id`
- `document_version_hash`
- `raw_text_content`
- `source_file_name`

### 5.2 Child chunks

Stores clause-aware chunks and metadata.

Important columns:

- `chunk_id`
- `contract_id`
- `document_version_hash`
- `chunk_index`
- `page_number`
- `section_heading`
- `clause_type`
- `text_snippet`
- `source_locator`
- `embedding_model`
- `embedding_vector`

## 6. Ingestion process

`parse_and_vectorize.py` performs:

1. read contract file
2. attempt Azure Document Intelligence layout extraction
3. preserve pages, tables, headings, and paragraph context where possible
4. create clause-aware chunks
5. generate document version hash
6. embed chunks using `text-embedding-3-small`
7. write parent and child records to Postgres

## 7. Retrieval process

`semantic_retriever.py` performs:

1. builds query from breach event context
2. creates embedding for query
3. checks Redis cache
4. searches only within the matching `contract_id`
5. optionally filters by `document_version_hash`
6. optionally filters by `clause_type`
7. returns ranked evidence with `chunk_id`, page, section, text, and similarity

Contract-scoped retrieval is mandatory. Searching across all PPAs is not allowed for financial dispute workflows.

## 8. Guardrails

### 8.1 Pre-synthesis guardrails

Before the LLM is called:

- evidence must exist
- evidence must match the breach event contract ID
- similarity must exceed threshold
- evidence must include chunk IDs

### 8.2 Post-synthesis guardrails

After the LLM responds:

- output must match structured schema
- `contract_id` must equal breach event PPA ID
- `audited_variance_usd` must match Gold event variance
- cited chunk IDs must exist in evidence pack
- dispute cannot be recommended without evidence

## 9. LLM synthesis

The LLM produces a structured JSON object:

```json
{
  "dispute_warranted": true,
  "audited_variance_usd": 6420.50,
  "contract_id": "PPA_GOOG_WILDORADO_WIND",
  "supporting_chunk_ids": [1, 2, 3],
  "compliance_justification_rationale": "...",
  "recommended_case_priority": "High"
}
```

The LLM may explain and classify. It must not invent numbers or override Gold fact values.

## 10. Human approval

Material dispute actions pause for human approval.

The approval payload should include:

- asset ID
- contract ID
- variance USD
- recommended priority
- retrieved clause evidence
- draft Salesforce case description

## 11. Salesforce case creation

`outbound_crm_connector.py` creates a Salesforce case only after approval.

The case should include:

- subject
- asset ID
- contract ID
- variance amount
- evidence references
- recommendation rationale
- audit trace ID

## 12. Operational controls

- Redis cache TTL prevents stale cache persistence.
- Cache key includes contract ID, query, embedding model, and document version hash.
- Audit logging captures breach event, evidence, guardrail results, approval decision, and CRM response.
- Max retry controls prevent runaway agent loops.

## 13. Package contents

- `stateful_ai_framework/ddl_pgvector.sql`
- `stateful_ai_framework/parse_and_vectorize.py`
- `stateful_ai_framework/semantic_retriever.py`
- `stateful_ai_framework/langgraph_orchestrator.py`
- `stateful_ai_framework/outbound_crm_connector.py`
- `sample_payloads/breach_event_sample.json`
- `stateful_ai_framework/legal_assets/sample_wildorado_google_ppa.txt`

## 14. Optional Headroom context optimization layer

The RAG runtime can use Headroom as an optional context optimizer before the LLM synthesis call.

### 14.1 Correct placement

```text
Contract-scoped retrieval
        │
        ▼
Raw evidence pack retained for audit and guardrails
        │
        ▼
Optional Headroom context optimizer
        │
        ▼
LLM synthesis
```

### 14.2 Non-authoritative role

Headroom may reduce prompt size, but it must never alter the authoritative state. The raw evidence pack, Gold breach event, deterministic guardrail inputs, human approval payload, and Salesforce audit record remain unchanged.

```text
RAG role: explain contractual support.
Gold role: compute dollars.
Headroom role: optimize non-authoritative LLM prompt context.
```

### 14.3 Enablement policy

- Default to `HEADROOM_ENABLED=false`.
- Enable only when estimated prompt size exceeds `HEADROOM_MIN_INPUT_TOKENS`.
- Preserve citations, numbers, dates, and section references.
- Log token savings to `fact_llm_usage`.
- Compare LLM output against raw evidence, not compressed prompt text.

### 14.4 Implementation artifact

The package includes:

```text
stateful_ai_framework/context_optimizer.py
architecture/headroom_context_optimization.md
```

The context optimizer returns original messages if Headroom is disabled, unavailable, or below the configured token threshold.

## 15. RAG observability and Control Tower dashboard framework

The RAG package includes telemetry needed for the VoltSentinel Control Tower dashboard.

### 15.1 RAG observability data path

```text
LangGraph node events
OpenAI usage responses
Headroom optimization metrics
Redis cache decisions
pgvector retrieval results
Salesforce responses
        │
        ▼
RAG observability logger
        │
        ▼
fact_rag_run / fact_llm_usage / fact_guardrail_event / fact_crm_dispatch
        │
        ▼
Power BI / Fabric / Streamlit Control Tower
```

### 15.2 RAG quality KPIs

- Total RAG runs
- Successful RAG runs
- Failed RAG runs
- Average retrieval latency
- Average synthesis latency
- p95 end-to-end RAG latency
- Retrieved chunk count
- Top similarity score
- No-evidence retrieval rate
- Wrong-contract retrieval blocked count
- Citation coverage percentage
- Guardrail failure rate
- Hallucination block rate
- Human override rate
- Dispute recommendation acceptance rate

### 15.3 LLM FinOps KPIs

- Prompt tokens
- Completion tokens
- Total tokens by model
- Estimated LLM cost
- Average cost per RAG run
- Cost per dispute recommendation
- Embedding tokens and embedding cost
- Cost by contract
- Cost by asset
- Headroom tokens saved
- Headroom estimated cost saved
- Redis cache hit rate
- Redis cache miss rate

### 15.4 Agent runtime KPIs

- LangGraph runs by status
- Node-level success and failure count
- Node-level retries
- Retrieval node latency
- Headroom optimization latency
- Synthesis node latency
- Guardrail node latency
- Human approval wait time
- CRM dispatch success rate
- CRM dispatch failure rate
- Most common failure reason

### 15.5 Governance KPIs

- Audit records complete percentage
- Runs with missing evidence
- Runs with missing approval
- High-dollar cases without approval
- Guardrail blocked cases
- Manual override count
- Contract version hash coverage
- Source chunk citation coverage

### 15.6 Implementation artifacts

- `observability/README.md`
- `observability/rag_event_logger.py`
- `observability/dashboard_schema.sql`
- `dashboards/control_tower_kpis.md`

## 16. RAG architecture evolution view

The package now includes an infographic showing the movement from the original CCR design to the current contract-grounded, auditable RAG architecture.

Key changes shown in the diagram:

- Clause-aware chunking and metadata added.
- Page number, section heading, clause type, and version hash preserved.
- pgvector schema expanded with source locators.
- Retrieval changed from global vector search to contract-scoped search.
- Upstash REST client corrected.
- Deterministic guardrails now check contract ID, citations, similarity, and Gold variance.
- Structured JSON schema output added.
- LangGraph human approval checkpoint added.
- Gold computes dollars; RAG explains contract support.

Diagram file:

```text
diagrams/ai_architecture_evolution_infographic.png
```

## 17. Additional implementation files added for this revision

- `stateful_ai_framework/context_optimizer.py`
- `architecture/headroom_context_optimization.md`
- `observability/README.md`
- `observability/rag_event_logger.py`
- `observability/dashboard_schema.sql`
- `dashboards/control_tower_kpis.md`
- `diagrams/ai_architecture_evolution_infographic.png`
