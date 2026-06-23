# VoltSentinel Control Tower KPI Specification

## Executive Overview

- Total estimated leakage revenue
- Confirmed leakage revenue
- Recovered / approved dispute amount
- Open dispute value
- Closed dispute value
- Average days to resolution
- Human approval pending count

## Asset and ISO Performance

- Leakage by asset
- Leakage by ISO region
- Leakage by offtaker
- Curtailment MWh by asset
- Settlement variance by region

## Data Pipeline Health

- Kafka messages received
- Kafka ingestion lag
- ADF snapshot success rate
- Bronze row count
- Silver clean row count
- Quarantine row count
- Data quality failure rate
- dbt model success/failure
- Last successful Gold refresh

## RAG Quality

- Total RAG runs
- Successful and failed RAG runs
- Average retrieval latency
- Top-k similarity score
- No-evidence retrieval rate
- Wrong-contract retrieval blocked
- Citation coverage percentage
- Guardrail failure rate
- Hallucination block rate
- Human override rate

## LLM FinOps

- Prompt tokens
- Completion tokens
- Total tokens by model
- Estimated LLM cost
- Embedding cost
- Cost per RAG run
- Cost per dispute recommendation
- Headroom tokens saved
- Headroom estimated cost saved
- Redis cache hit/miss rate

## Agent Runtime

- LangGraph runs by status
- Node-level latency
- Node-level retries
- Human approval wait time
- CRM dispatch success/failure rate
- Most common failure reason

## Governance and Audit

- Runs with complete audit records
- Runs with missing evidence
- Runs with missing approval
- High-dollar cases without approval
- Guardrail blocked cases
- Manual override count
- Contract version hash coverage
- Source chunk citation coverage
