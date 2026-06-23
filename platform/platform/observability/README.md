# VoltSentinel Control Tower Observability Framework

The Control Tower is the business and technical observability layer for VoltSentinel. It collects telemetry from ingestion, lakehouse processing, RAG execution, LLM usage, Headroom optimization, human approval, and Salesforce dispatch.

## Dashboard categories

1. Executive Business KPIs
2. Asset and ISO Performance
3. Settlement Reconciliation
4. Data Pipeline Health
5. RAG Quality
6. LLM FinOps and Token Usage
7. Agent Runtime
8. Human Approval, CRM, and Audit Governance

## Architecture

```text
Kafka / ADF / Databricks / dbt / pgvector / LangGraph / OpenAI / Headroom / Salesforce
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
Power BI / Fabric / Streamlit dashboard
```

The dashboard answers two different questions:

- Business dashboards show what value VoltSentinel found.
- Observability dashboards show whether VoltSentinel itself can be trusted.
