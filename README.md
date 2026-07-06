# VoltSentinel

VoltSentinel is a renewable-energy revenue leakage detection and explanation platform built as a hands-on lakehouse, streaming, and RAG architecture proof of concept.

The project simulates how renewable-energy operational data, enterprise finance data, commercial workflow data, and contractual evidence can be combined to detect potential revenue leakage and prepare human-reviewable dispute cases.

## Architecture Overview

SCADA telemetry producer
  -> Azure Event Hubs Kafka-compatible endpoint
  -> Databricks Structured Streaming
  -> ADLS Bronze Delta
  -> Silver cleaned telemetry
  -> Gold revenue leakage facts
  -> Soda quality checks
  -> PPA / ISO / settlement evidence layer
  -> SAP + Salesforce enterprise context
  -> Gold RAG case package
  -> LangGraph RAG workflow
  -> Human approval queue
  -> Mocked Salesforce action

## Key Capabilities

- Simulates renewable-energy SCADA telemetry.
- Uses Azure Event Hubs as a Kafka-compatible streaming layer.
- Processes telemetry with Databricks Structured Streaming.
- Implements Bronze, Silver, and Gold lakehouse layers on ADLS Gen2 using Delta Lake.
- Adds SAP-style finance context such as invoices, GL postings, and AR status.
- Adds Salesforce-style commercial context such as accounts, contracts, assets, and dispute workflow.
- Generates synthetic PPA, ISO curtailment notice, and settlement evidence documents.
- Applies Soda data quality checks before downstream processing.
- Uses LangGraph to orchestrate RAG case explanation, validation, routing, and persistence.
- Enforces human approval before any Salesforce-style action.
- Writes RAG results, approval records, and mocked Salesforce actions back to Databricks Gold tables.

## Project Structure

docs/
  Technical documentation and architecture notes

platform/
  Infrastructure, producers, Databricks pipeline code, synthetic source generation, and reference data

rag/
  Synthetic legal/evidence assets and LangGraph RAG orchestrator

## Status

This is a proof of concept designed for learning, architecture validation, and interview discussion. It is not intended to connect to real SAP, Salesforce, market, or utility systems without additional production hardening.

## Security Notes

Secrets are not committed to this repository. Local environment variables should be stored in .env, which is intentionally excluded from Git. Use .env.example as the template.
