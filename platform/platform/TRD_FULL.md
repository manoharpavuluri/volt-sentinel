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
