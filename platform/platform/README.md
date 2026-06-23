# Project VoltSentinel — Full Platform Package

VoltSentinel is a production-aligned proof-of-concept for detecting renewable asset revenue leakage caused by congestion curtailment, settlement variance, and PPA compensation mismatches.

This full package includes the complete end-to-end scaffold, not just patch files:

- synthetic SCADA and enterprise snapshot generators
- Kafka/event and ADF/batch ingestion examples
- ADLS/Databricks/dbt Medallion lakehouse models
- Silver validation and quarantine logic
- Gold settlement/revenue leakage fact model
- private endpoint Terraform hardening snippets
- RAG integration handoff points
- CI/CD workflow examples
- architecture diagrams and original source TRD

## Primary architecture flow

1. **Data Sources**: SCADA telemetry, curtailment signals, SAP asset registry, Salesforce PPA mapping, ISO/market settlements, and PPA documents.
2. **Simulation & Edge**: local generators create realistic telemetry, expected-generation baselines, curtailment instructions, and settlement records.
3. **Ingestion**: Kafka captures high-velocity telemetry; ADF copies snapshot files.
4. **Storage & Lakehouse**: Bronze raw, Silver conformed/quarantine, Gold financial fact models.
5. **Analytics & Reconciliation**: expected-vs-actual generation, curtailment MWh, settlement variance, estimated leakage revenue.
6. **Cognitive RAG**: contract evidence explains whether the PPA supports dispute action; Gold remains source of truth for dollars.
7. **Action**: human approval, Salesforce case creation, Power BI/Fabric consumption, audit trail.

See `diagrams/project_voltsentinel_platform_flow_diagram.png` for the visual version.

## Folder structure

```text
volt_sentinel_platform_full/
├── README.md
├── TRD_FULL.md
├── .env.example
├── requirements.txt
├── .gitignore
├── diagrams/
├── source_originals/
├── terraform/
├── .github/workflows/
├── data_simulation/
├── data_movement_ingestion/
│   ├── adf_copy_templates/
│   └── transform_lakehouse/
│       ├── dbt_project.yml
│       ├── data_observability/
│       └── models/
│           ├── bronze/
│           ├── silver/
│           └── gold/
└── stateful_ai_framework/
```

## Recommended build order

### 1. Generate local data

```bash
python data_simulation/generate_it_snapshots.py
python data_simulation/generate_scada_stream.py
```

For a local-only MVP, you can write telemetry to file instead of Kafka. For the cloud path, configure Upstash Kafka credentials in `.env.example`, copy it to `.env`, and keep `.env` out of Git.

### 2. Land raw data

Use either:

- `data_movement_ingestion/transform_lakehouse/stream_bronze_landing.py` for Kafka to Delta Bronze.
- `data_movement_ingestion/adf_copy_templates/*.json` for batch snapshot files to ADLS.

### 3. Run dbt models

```bash
cd data_movement_ingestion/transform_lakehouse
# Configure profiles.yml for Databricks first.
dbt deps
dbt run --select silver+
dbt test
```

### 4. Review Gold model output

The Gold fact table calculates:

```text
actual_generation_mwh
expected_available_mwh
grid_curtailment_mwh
eligible_compensable_mwh
expected_settlement_usd
actual_settlement_usd
estimated_leakage_revenue_usd
```

The RAG pipeline should not recalculate these values. It should explain whether contract language supports a dispute.

### 5. Connect to the RAG package

Use the companion package `volt_sentinel_rag_full.zip` for the complete contract-grounded RAG engine.

## Security positioning

This package is a **secure MVP scaffold**, not a fully locked-down enterprise deployment. External services such as Upstash, Supabase, OpenAI, and Salesforce are treated as approved external SaaS boundaries in MVP mode. Production hardening should add:

- ADLS private endpoints for `blob` and `dfs`
- private DNS zones
- public-network access restrictions
- managed identities and Key Vault-backed secrets
- Databricks VNet injection and controlled egress
- explicit approval before external CRM writes

## Important design rules

- Bronze preserves raw records, even bad telemetry.
- Silver validates and quarantines records.
- Gold is the financial source of truth.
- RAG explains contract support only.
- Human approval is required before Salesforce case creation.

## Added in v2: Headroom + Control Tower + evolution diagram

This package now includes the optional Headroom context optimization layer and the VoltSentinel Control Tower dashboard framework.

New additions:

```text
architecture/headroom_context_optimization.md
observability/README.md
observability/dashboard_schema.sql
observability/event_logger.py
observability/sample_dashboard_metrics.json
dashboards/control_tower_kpis.md
diagrams/voltsentinel_platform_architecture_evolution.png
```

### Headroom role

Headroom is optional and only optimizes prompt context before LLM synthesis. It does not change raw contract evidence, Gold facts, guardrail inputs, or audit records.

### Control Tower role

The Control Tower gives business and technical visibility into:

- revenue leakage KPIs
- settlement reconciliation KPIs
- data pipeline health
- RAG quality
- LLM token and cost usage
- Headroom token savings
- LangGraph agent runtime
- human approval and Salesforce dispatch
- governance and audit completeness

### Architecture evolution view

The new evolution diagram shows:

```text
Original architecture → What changed → Current production-aligned architecture
```
