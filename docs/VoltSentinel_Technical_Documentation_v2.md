# VoltSentinel Technical Documentation v2

This combined documentation includes the production-aligned platform architecture, the contract-grounded RAG architecture, optional Headroom context optimization, Control Tower dashboards, FinOps/observability metrics, and before/after architecture evolution diagrams.

---

# Project VoltSentinel — Full Technical Reference Architecture

## 1. System objective

Project VoltSentinel detects revenue leakage across renewable-energy assets by reconciling SCADA/operational telemetry, curtailment signals, asset metadata, Salesforce PPA mappings, market settlement records, and contract terms.

The business target is to identify cases where grid-enforced curtailment, settlement true-ups, or PPA compensation rules indicate that the organization may be underpaid or should initiate a billing dispute.

## 2. Architecture positioning

This version is a production-aligned MVP. It demonstrates the patterns expected in an enterprise deployment but does not overclaim complete private-network isolation during early development.

External SaaS services may be used during MVP:

- Upstash Kafka for simulated event streaming
- Upstash Redis for cache
- Supabase/Postgres with pgvector for RAG storage
- OpenAI for embeddings and synthesis
- Salesforce sandbox for case creation

Production hardening should replace or harden these with enterprise-approved connectivity, managed identity, private endpoints, Key Vault, controlled egress, and audit logging.

## 3. End-to-end topology

```text
[Data Sources]
  ├─ SCADA telemetry
  ├─ Curtailment instructions
  ├─ SAP asset registry
  ├─ Salesforce PPA account mapping
  ├─ ISO / market settlement records
  └─ PPA contracts
        │
        ▼
[Simulation & Edge]
  ├─ Synthetic telemetry generator
  ├─ Enterprise snapshot generator
  └─ Schema/quality tagging
        │
        ▼
[Ingestion]
  ├─ Kafka/event stream for telemetry
  └─ ADF/batch snapshots for SAP/Salesforce/settlement files
        │
        ▼
[Lakehouse]
  ├─ Bronze raw Delta tables
  ├─ Silver conformed tables
  ├─ Silver quarantine tables
  └─ Gold financial facts
        │
        ▼
[Analytics & Reconciliation]
  ├─ expected vs actual generation
  ├─ curtailment MWh
  ├─ settlement variance
  └─ estimated leakage revenue
        │
        ▼
[Cognitive RAG]
  ├─ retrieve relevant PPA clauses
  ├─ explain contract support
  ├─ cite chunk/page/section evidence
  └─ recommend dispute review
        │
        ▼
[Action]
  ├─ human approval
  ├─ Salesforce case creation
  ├─ Power BI/Fabric dashboards
  └─ audit trail
```

## 4. Repository structure

```text
volt_sentinel_platform_full/
├── terraform/
├── data_simulation/
├── data_movement_ingestion/
│   ├── adf_copy_templates/
│   └── transform_lakehouse/
└── stateful_ai_framework/
```

## 5. Data simulation layer

### 5.1 SCADA telemetry generator

`data_simulation/generate_scada_stream.py` emits simulated telemetry events for wind/solar assets.

Key fields:

- `event_id`
- `timestamp_utc`
- `asset_id`
- `measured_generation_kw`
- `expected_available_kw`
- `grid_limit_kw`
- `operating_status`
- `telemetry_quality`

The generator intentionally preserves suspicious readings so Bronze can retain auditability. Silver decides whether a record is usable or quarantined.

### 5.2 IT snapshot generator

`data_simulation/generate_it_snapshots.py` creates:

- SAP-style asset registry
- Salesforce PPA mapping
- ISO curtailment instructions
- market/settlement actuals

This fixes the earlier modeling issue where Gold used nameplate capacity as the leakage baseline. The revised model uses expected/available generation and settlement records.

## 6. Ingestion layer

### 6.1 Streaming path

`stream_bronze_landing.py` reads from Kafka and writes raw payloads to Bronze Delta storage.

Important implementation details:

- explicit SASL config
- explicit `startingOffsets`
- Kafka topic, partition, offset captured for lineage
- raw data preserved before validation

### 6.2 Batch path

ADF templates copy CSV snapshots into ADLS/Delta staging paths.

Included templates:

- `clearway_sap_assets.json`
- `clearway_sf_ppas.json`

Additional templates can follow the same pattern for ISO curtailments and settlement records.

## 7. Medallion lakehouse model

### 7.1 Bronze

Bronze is append-only raw landing. It should contain all valid and invalid incoming records.

### 7.2 Silver

Silver validates:

- timestamp parseability
- known asset IDs
- non-negative generation values
- expected generation availability
- operating status normalization
- quality flags

Bad records are routed to `quarantine_clearway_telemetry.sql`.

### 7.3 Gold

The Gold fact model calculates settlement variance using a defensible financial formula:

```text
actual_generation_mwh = sum(measured_generation_kw * sample_seconds / 3600) / 1000
expected_available_mwh = sum(expected_available_kw * sample_seconds / 3600) / 1000
grid_limited_mwh = sum(least(expected_available_kw, grid_limit_kw) * sample_seconds / 3600) / 1000
grid_curtailment_mwh = greatest(expected_available_mwh - grid_limited_mwh, 0)
eligible_compensable_mwh = contract eligibility rules applied to curtailment/settlement basis
estimated_leakage_revenue_usd = expected_settlement_usd - actual_settlement_usd
```

This avoids the incorrect shortcut of comparing actual production to nameplate capacity.

## 8. RAG integration rule

The RAG pipeline must not calculate the final dollar amount. It receives the Gold breach event and performs contract-grounded explanation.

RAG responsibilities:

- retrieve only the matching contract
- retrieve relevant clauses
- cite chunk IDs/pages/sections
- explain whether dispute review is supported
- draft human-readable case narrative

Gold responsibilities:

- calculate MWh
- calculate settlement variance
- calculate estimated leakage revenue

## 9. Governance and approvals

Salesforce case creation should be blocked unless:

- Gold variance is positive and material
- RAG returns relevant evidence
- deterministic guardrails pass
- human approval is captured

## 10. Included implementation files

- `data_simulation/generate_scada_stream.py`
- `data_simulation/generate_it_snapshots.py`
- `data_movement_ingestion/transform_lakehouse/stream_bronze_landing.py`
- `data_movement_ingestion/transform_lakehouse/models/silver/silver_clearway_telemetry.sql`
- `data_movement_ingestion/transform_lakehouse/models/silver/quarantine_clearway_telemetry.sql`
- `data_movement_ingestion/transform_lakehouse/models/gold/fact_revenue_leakage.sql`
- `terraform/*.tf`
- `.github/workflows/*.yml`

## 11. Delivery milestones

| Phase | Deliverable | Success criteria |
|---|---|---|
| 0 | Simulators | telemetry + snapshots generated locally |
| 1 | Ingestion | Kafka + ADF landing paths working |
| 2 | Lakehouse | Bronze/Silver/Gold models run successfully |
| 3 | RAG handoff | Gold breach event passed to RAG package |
| 4 | Action | human-approved Salesforce case workflow |
| 5 | Hardening | private endpoints, Key Vault, CI/CD, audit controls |

## 12. Optional Headroom context optimization layer

VoltSentinel can include Headroom as an optional context optimization layer for large RAG prompts and agent state payloads.

### 12.1 Design placement

```text
Gold breach event
+ contract-scoped evidence pack
+ guardrail context
+ runtime logs
        │
        ▼
Optional Headroom context optimizer
        │
        ▼
LLM synthesis prompt
        │
        ▼
Deterministic guardrails validate against raw evidence
```

### 12.2 Governance rule

Headroom does not become part of the authoritative evidence chain. It may compress prompt context before LLM calls, but the system must preserve raw source contract text, Gold facts, guardrail inputs, human approval payloads, and CRM audit records unchanged.

```text
Headroom optimizes prompt context. Gold and raw evidence remain the source of truth.
```

### 12.3 Recommended enablement policy

- Default `HEADROOM_ENABLED=false` for deterministic testing.
- Enable only when prompt size exceeds `HEADROOM_MIN_INPUT_TOKENS`.
- Preserve citations, numbers, dates, and section references.
- Record tokens before and after optimization in `fact_llm_usage`.

### 12.4 Repository additions

- `architecture/headroom_context_optimization.md`
- `stateful_ai_framework/context_optimizer.py` in the RAG package
- Headroom telemetry fields in `observability/dashboard_schema.sql`

## 13. VoltSentinel Control Tower dashboard framework

VoltSentinel should include a business and technical observability dashboard layer called the **VoltSentinel Control Tower**.

The dashboard has two responsibilities:

```text
Business dashboards show what value VoltSentinel found.
Observability dashboards show whether VoltSentinel itself can be trusted.
```

### 13.1 Control Tower data path

```text
Kafka / ADF / Databricks / dbt / Gold facts / pgvector / LangGraph / OpenAI / Headroom / Salesforce
        │
        ▼
Observability event logger
        │
        ▼
Bronze observability events
        │
        ▼
Silver normalized metrics
        │
        ▼
Gold KPI marts
        │
        ▼
Power BI / Fabric / Streamlit Control Tower
```

### 13.2 Dashboard pages

| Dashboard page | Primary audience | Purpose |
|---|---|---|
| Executive Overview | Leadership, finance, commercial operations | Estimated leakage, recovered value, open risk, approval backlog |
| Asset & ISO Performance | Asset management, operations | Leakage by asset, ISO, offtaker, curtailment MWh |
| Settlement Reconciliation | Commercial operations, finance | Expected vs actual generation, settlement variance, dispute value |
| Data Pipeline Health | Data engineering | Kafka, ADF, Bronze/Silver/Gold, dbt, quarantine, quality failures |
| RAG Quality | AI/data product owners | Retrieval quality, citation coverage, guardrail failures, hallucination blocks |
| LLM FinOps | Platform and finance | Tokens, cost, model usage, Headroom savings, Redis cache hit rate |
| Agent Runtime | Engineering and support | LangGraph node latency, retries, failures, approval wait time |
| Human Approval & CRM | Operations and compliance | Pending approvals, approved disputes, Salesforce case status, audit trail |

### 13.3 Business KPI examples

- Total estimated leakage revenue
- Confirmed leakage revenue
- Recovered / approved dispute amount
- Open dispute value
- Closed dispute value
- Leakage by asset
- Leakage by ISO region
- Leakage by offtaker
- Curtailment MWh
- Settlement variance USD
- Average days to dispute resolution
- Salesforce cases created
- Human approval pending count

### 13.4 Data and pipeline KPI examples

- Kafka messages received
- Kafka ingestion lag
- ADF batch snapshot success rate
- Bronze row count
- Silver clean row count
- Quarantine row count
- Data quality failure rate
- dbt model success/failure
- Last successful Gold refresh
- Schema validation failures

### 13.5 RAG, LLM, and agent KPI examples

- Total RAG runs
- Retrieval latency and p95 end-to-end RAG latency
- Top-k similarity score
- No-evidence retrieval rate
- Wrong-contract retrieval blocked count
- Citation coverage percentage
- Guardrail failure rate
- Hallucination block rate
- Human override rate
- Prompt tokens, completion tokens, and total tokens
- Estimated LLM cost
- Embedding tokens and embedding cost
- Headroom tokens saved and estimated cost saved
- Redis cache hit/miss rate
- LangGraph node-level retries and failure reason

### 13.6 Observability data model

The Control Tower introduces these tables:

- `dim_component`
- `dim_model`
- `fact_platform_run`
- `fact_pipeline_run`
- `fact_rag_run`
- `fact_llm_usage`
- `fact_retrieval_quality`
- `fact_guardrail_event`
- `fact_human_approval`
- `fact_crm_dispatch`
- `fact_cost_daily`

The DDL is included in `observability/dashboard_schema.sql`.

## 14. Architecture evolution view

The package now includes an architecture evolution infographic showing the movement from the original TRD design to the current production-aligned design.

```text
Original architecture
        │
        ▼
What changed
        │
        ▼
Current architecture
```

Key changes shown in the diagram:

- Security posture clarified: secure MVP now, full private networking later.
- Kafka ingestion hardened with SASL configuration and explicit offsets.
- True Silver layer added with clean conformed data and quarantine.
- Revenue logic corrected with expected available MWh, curtailment MWh, and settlement variance.
- Gold fact table established as the source of truth for dollars.
- Contract-grounded RAG evidence pack added.
- Deterministic guardrails and human approval gate added before CRM action.

Diagram file:

```text
diagrams/voltsentinel_platform_architecture_evolution.png
```

## 15. Additional implementation files added for this revision

- `architecture/headroom_context_optimization.md`
- `observability/README.md`
- `observability/dashboard_schema.sql`
- `observability/event_logger.py`
- `observability/sample_dashboard_metrics.json`
- `dashboards/control_tower_kpis.md`
- `diagrams/voltsentinel_platform_architecture_evolution.png`

---

# VoltSentinel Cognitive RAG Documentation

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
