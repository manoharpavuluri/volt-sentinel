# RAG Observability and FinOps Dashboard Framework

This folder defines the telemetry captured from the VoltSentinel Cognitive RAG runtime.

## Metric groups

- Retrieval quality
- Contract citation quality
- Guardrail outcomes
- LLM token usage and cost
- Optional Headroom token savings
- Redis cache hit/miss rate
- LangGraph node latency and retries
- Human approval state
- Salesforce dispatch outcome

## Data path

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
