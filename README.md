# VoltSentinel

VoltSentinel is a renewable-energy revenue assurance platform that detects potential revenue leakage from curtailment, settlement mismatches, and contract interpretation gaps.

The project simulates how an energy company can combine operational telemetry, market/ISO events, finance records, commercial account data, and contractual evidence to identify under-recovered revenue and prepare human-reviewable dispute cases.

## Business Problem

Renewable-energy operators often lose revenue when generation is curtailed, settlements do not fully reflect contractual rights, or commercial teams lack a unified view across operations, finance, contracts, and customer systems.

The challenge is not just detecting an operational event. The real challenge is answering:

* Was the asset available to generate?
* Was the curtailment compensable under the contract?
* Was the revenue already invoiced or paid?
* Is there an existing customer dispute?
* What evidence supports the claim?
* Should this become a human-reviewed commercial case?

VoltSentinel addresses that business workflow end to end.

## What the Platform Does

VoltSentinel creates a case-ready revenue leakage workflow:

1. Detects curtailment and generation shortfall from telemetry.
2. Calculates estimated revenue leakage.
3. Validates the data quality before downstream use.
4. Links operational events to PPA, ISO notice, and settlement evidence.
5. Adds SAP-style invoice, GL, AR, and payment context.
6. Adds Salesforce-style account, contract, asset, and dispute context.
7. Generates a grounded explanation using a governed RAG workflow.
8. Routes the case to human approval.
9. Executes a Salesforce dispute action only after approval.

## Business Value

VoltSentinel demonstrates how an energy company could improve:

* Revenue assurance
* Curtailment compensation review
* Settlement dispute readiness
* Contract compliance analysis
* Finance and commercial workflow alignment
* Human-in-the-loop AI governance
* Auditability of AI-generated recommendations

## Architecture Summary

Operational data, finance data, commercial data, and document evidence are curated into a governed lakehouse. A LangGraph workflow then retrieves one case package at a time, generates a grounded explanation, validates routing, and writes the result back for human review.

The system is designed so that AI does not directly query raw SAP, Salesforce, or contract repositories. Instead, it uses curated Gold case packages and linked evidence.

## Technology Used

The technical stack includes Azure Event Hubs, ADLS Gen2, Databricks, Delta Lake, Soda data quality checks, synthetic SAP/Salesforce source data, and LangGraph-based RAG orchestration.

These tools are used to support the business use case of renewable-energy revenue leakage detection and dispute workflow automation.

## Repository Structure

| Folder | Purpose |
|---|---|
| `platform/` | Azure infrastructure, producers, Databricks lakehouse pipeline, synthetic SAP/Salesforce data |
| `rag/` | LangGraph RAG orchestrator, evidence assets, human approval workflow |
| `docs/` | Architecture notes, build steps, and technical documentation |

## Current Implementation Status

Implemented:

- SCADA telemetry simulation
- Event Hubs Kafka-compatible ingestion
- Databricks Bronze, Silver, and Gold Delta layers
- Revenue leakage calculation
- Soda data quality checks
- Synthetic PPA, ISO curtailment notice, and settlement evidence
- Synthetic SAP and Salesforce source context
- Gold case-ready leakage records
- LangGraph RAG case explanation workflow
- Databricks Gold RAG result persistence
- Human approval queue
- Salesforce action workflow

## Demo Flow

1. Generate or stream telemetry events.
2. Process telemetry into Bronze, Silver, and Gold Delta tables.
3. Enrich leakage events with SAP, Salesforce, and document evidence.
4. Build a Gold RAG case package.
5. Run LangGraph for a selected `breach_event_id`.
6. Persist the RAG explanation back to Databricks.
7. Create a human approval request.
8. Approve the case.
9. Execute a Salesforce dispute action.

## Security Notes

Secrets are not committed to this repository. Local credentials should be stored in `.env`, which is excluded from Git. Use `.env.example` as the template.

## Production Enhancements

Future enhancements could include:

- Real SAP CDC or incremental ingestion
- Real Salesforce API integration
- Databricks Asset Bundles
- CI/CD deployment
- Managed identity authentication
- Real LLM integration with token and cost tracking
- Vector search over contract and settlement evidence
- Databricks SQL or Power BI dashboard
