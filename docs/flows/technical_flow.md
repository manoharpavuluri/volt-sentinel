# VoltSentinel Technical Flow

This document explains the technical implementation flow for VoltSentinel.

VoltSentinel is a renewable-energy revenue assurance proof of concept that combines streaming telemetry, lakehouse processing, data quality checks, enterprise context, document evidence, RAG orchestration, human approval, and mocked Salesforce workflow execution.

The technical design supports the business goal of detecting potential revenue leakage from curtailment, settlement mismatches, and contract interpretation gaps.

---

## High-Level Technical Architecture

    Synthetic SCADA Producer
        -> Azure Event Hubs Kafka-Compatible Endpoint
        -> Databricks Structured Streaming
        -> ADLS Gen2 Bronze Delta
        -> Silver Cleaned Telemetry Delta
        -> Gold Revenue Leakage Delta
        -> Soda Core Quality Gate
        -> Breach Event Export
        -> Synthetic PPA / ISO / Settlement Evidence
        -> Synthetic SAP Finance Context
        -> Synthetic Salesforce Commercial Context
        -> Gold RAG Case Package
        -> Databricks SQL Table
        -> LangGraph RAG Orchestrator
        -> Databricks RAG Result Table
        -> Human Approval Queue
        -> Mocked Salesforce Action Table

---

## Design Principles

VoltSentinel follows several enterprise architecture principles:

1. Separate raw, cleaned, and business-ready data using Bronze, Silver, and Gold layers.
2. Use streaming ingestion for operational telemetry.
3. Preserve raw source events for auditability.
4. Apply data quality checks before downstream AI or workflow processing.
5. Curate enterprise data before using it in RAG.
6. Keep AI grounded in governed Gold data and linked evidence.
7. Require human approval before customer-facing workflow actions.
8. Persist AI results and approval decisions for traceability.
9. Avoid direct AI access to raw SAP, Salesforce, or document repositories.
10. Treat RAG as an explanation and workflow-support layer, not the system of financial record.

---

## Main Technical Components

| Component | Purpose |
|---|---|
| Python SCADA producer | Generates synthetic renewable telemetry events |
| Azure Event Hubs | Managed Kafka-compatible streaming ingestion layer |
| Databricks Structured Streaming | Reads Event Hubs telemetry and lands Bronze Delta |
| ADLS Gen2 | Stores Bronze, Silver, Gold, Quarantine, and Observability zones |
| Delta Lake | Provides ACID table format over lakehouse data |
| Soda Core | Validates Silver and Gold data quality |
| Synthetic document generator | Creates PPA, ISO curtailment, and settlement evidence |
| Synthetic enterprise generator | Creates SAP-style and Salesforce-style source data |
| Databricks notebooks | Transform Bronze to Silver and Gold business outputs |
| Databricks SQL | Exposes Gold RAG case packages to the LangGraph orchestrator |
| LangGraph | Orchestrates RAG case explanation and routing |
| Human approval table | Stores pending and approved workflow decisions |
| Mock Salesforce table | Simulates approved downstream Salesforce actions |

---

## Azure Foundation

The Azure foundation includes:

- Resource group
- ADLS Gen2 storage account
- Storage containers or filesystems
- Azure Event Hubs namespace
- Event Hub topic for telemetry
- Event Hub consumer group for Databricks
- Databricks workspace
- Key Vault
- Key Vault-backed Databricks secret scope

Logical storage zones:

    bronze
    silver
    gold
    quarantine
    observability

Purpose of each zone:

| Zone | Purpose |
|---|---|
| Bronze | Raw source data and raw event landing |
| Silver | Cleaned, typed, validated, source-aligned data |
| Gold | Business-ready facts, dimensions, evidence links, and RAG case packages |
| Quarantine | Invalid records that failed validation |
| Observability | Soda results, quality summaries, and pipeline monitoring artifacts |

---

## Event Streaming Flow

The SCADA producer uses the Kafka client protocol to publish telemetry events into Azure Event Hubs.

Important distinction:

    This project does not operate a self-managed Apache Kafka cluster.
    Azure Event Hubs is used as a managed Kafka-compatible broker.

Logical mapping:

| Kafka Concept | VoltSentinel Implementation |
|---|---|
| Kafka broker | Azure Event Hubs namespace |
| Kafka topic | Event Hub |
| Kafka producer | Python SCADA telemetry producer |
| Kafka consumer | Databricks Structured Streaming |
| Consumer group | Databricks Bronze ingestion consumer group |

Technical flow:

    Python SCADA producer
        -> Kafka protocol
        -> Event Hubs namespace
        -> telemetry Event Hub
        -> Databricks Structured Streaming consumer
        -> Bronze Delta table

Telemetry event examples include:

- asset_id
- asset_type
- timestamp_utc
- expected_available_kw
- actual_generation_kw
- operating_status
- curtailment_reason
- market_price_usd_per_mwh
- source_system
- event_id

---

## Bronze Telemetry Flow

Bronze is the raw ingestion layer.

The Databricks streaming notebook reads from Event Hubs using Spark's Kafka source and writes raw events to Delta.

Bronze stores:

- Kafka topic
- Kafka partition
- Kafka offset
- Kafka timestamp
- Kafka key
- Raw JSON payload
- Ingestion timestamp

Technical purpose:

    Bronze preserves what arrived from the source stream.
    It is append-only and audit-friendly.
    It allows replay, debugging, and downstream reprocessing.

Bronze telemetry path pattern:

    abfss://bronze@<storage-account>.dfs.core.windows.net/scada/telemetry

Checkpoint path pattern:

    abfss://bronze@<storage-account>.dfs.core.windows.net/_checkpoints/scada/telemetry

Why checkpointing matters:

    Event Hubs stores events by partition and offset.
    Databricks checkpoints the last processed offsets.
    If the streaming job restarts, it resumes from the checkpoint instead of rereading or skipping events.

---

## Silver Telemetry Flow

Silver converts raw Bronze telemetry into cleaned and typed telemetry records.

Silver processing performs:

- JSON parsing
- Schema enforcement
- Timestamp conversion
- Numeric type casting
- Required field checks
- Asset ID validation
- Non-negative metric validation
- Duplicate event handling
- Derived metric calculation
- Quarantine routing for invalid records

Derived Silver fields include:

- source_timestamp_utc_ts
- source_date
- expected_available_mwh
- actual_generation_mwh
- curtailed_mwh
- is_curtailment_event
- silver_processed_timestamp_utc
- dq_status
- dq_error_reason

Silver valid telemetry path pattern:

    abfss://silver@<storage-account>.dfs.core.windows.net/scada/telemetry

Quarantine telemetry path pattern:

    abfss://quarantine@<storage-account>.dfs.core.windows.net/scada/telemetry

Technical purpose:

    Silver represents trusted operational telemetry.
    It is clean enough for revenue calculations and quality checks.
    Invalid records are not silently dropped; they are written to quarantine.

---

## Gold Revenue Leakage Flow

Gold transforms Silver telemetry into business-ready revenue leakage facts.

The Gold revenue leakage process joins telemetry with asset-contract mapping.

Gold logic calculates:

- curtailed MWh
- compensable curtailment eligibility
- eligible compensable MWh
- estimated leakage revenue
- contract mapping status
- revenue leakage flag
- fact record hash

Example logic:

    If the asset was curtailed
    and the curtailment reason is compensable
    and the asset is mapped to a PPA
    then calculate estimated revenue leakage.

Gold revenue leakage fact path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/facts/revenue_leakage

Gold asset-contract dimension path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/dimensions/asset_contract

Technical purpose:

    Gold converts operational telemetry into business financial risk signals.

---

## Soda Core Quality Gate

Soda Core is used as a data quality gate before downstream RAG and workflow processing.

Soda validates:

- Silver telemetry
- Gold revenue leakage facts

Example checks include:

- row count greater than zero
- missing event_id checks
- duplicate event_id checks
- non-negative expected generation
- non-negative actual generation
- non-negative curtailed MWh
- valid dq_status values
- missing fact_record_hash checks
- duplicate fact_record_hash checks
- non-negative estimated leakage revenue
- compensable MWh consistency checks

Quality result path pattern:

    abfss://observability@<storage-account>.dfs.core.windows.net/soda/check_results

Technical purpose:

    RAG and workflow processing should not run on unvalidated business data.
    Soda creates an explicit quality gate between Gold calculation and downstream case generation.

Quality gate rule:

    If Soda passes:
        continue to breach event and RAG processing

    If Soda fails:
        block downstream processing and investigate data quality issues

---

## Breach Event Export Flow

After Gold revenue leakage facts pass the Soda gate, qualifying leakage records are exported as breach events.

Breach events represent candidate business cases.

Breach event fields include:

- breach_event_id
- breach_event_type
- asset_id
- contract_id
- estimated_leakage_revenue_usd
- severity
- rag_task
- contract_lookup_required
- requires_human_approval
- salesforce_dispatch_allowed
- dq_gate_status

Breach event path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/events/revenue_leakage_breach_events

JSON export path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/exports/rag/revenue_leakage_breach_events_json

Technical purpose:

    Breach events decouple revenue leakage detection from downstream RAG processing.
    Each breach event becomes a case candidate.

---

## Document Evidence Flow

VoltSentinel generates synthetic evidence documents to simulate real energy-market documentation.

Document categories include:

- PPA documents
- ISO curtailment notices
- ISO settlement statements

Document generation produces:

- PDF files
- text files
- document manifest
- structured reference data

Raw document landing pattern:

    abfss://bronze@<storage-account>.dfs.core.windows.net/documents/raw/pdf
    abfss://bronze@<storage-account>.dfs.core.windows.net/documents/raw/text

Reference data landing pattern:

    abfss://bronze@<storage-account>.dfs.core.windows.net/reference_data/energy_evidence

Technical purpose:

    Documents are landed and curated before RAG runtime.
    RAG does not scan random PDFs directly at runtime.
    The lakehouse creates governed evidence chunks and evidence links.

---

## Silver Document Processing Flow

Raw document text is processed into Silver document tables.

Silver document outputs include:

- document registry
- document chunks
- extracted metadata

Document registry stores:

- document_id
- document_type
- asset_id
- contract_id
- source_path
- document_title
- effective date or event date
- processing timestamp

Document chunks store:

- chunk_id
- document_id
- document_type
- asset_id
- contract_id
- chunk_text
- chunk_sequence
- source_path

Silver document registry path pattern:

    abfss://silver@<storage-account>.dfs.core.windows.net/documents/document_registry

Silver document chunks path pattern:

    abfss://silver@<storage-account>.dfs.core.windows.net/documents/document_chunks

Technical purpose:

    Silver document chunks become governed RAG evidence.
    They can later be embedded into vector search, but the current POC uses deterministic evidence selection.

---

## Gold Evidence Link Flow

Gold evidence links connect breach events to supporting documents.

Each breach event can be linked to:

- PPA contractual support
- ISO operational support
- ISO settlement support

Evidence link output path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/evidence/breach_event_document_links

Evidence link examples:

| Evidence Type | Purpose |
|---|---|
| CONTRACTUAL_SUPPORT | Links breach event to PPA clauses |
| OPERATIONAL_SUPPORT | Links breach event to ISO curtailment notice |
| SETTLEMENT_SUPPORT | Links breach event to ISO settlement statement |

Technical purpose:

    The RAG workflow should know which evidence belongs to each case.
    Evidence links prevent broad, uncontrolled retrieval.

---

## Synthetic SAP Source Flow

VoltSentinel simulates SAP-style finance data.

Synthetic SAP files include:

- asset master
- business partners
- invoice headers
- invoice lines
- GL postings
- AR open items

Bronze landing pattern:

    abfss://bronze@<storage-account>.dfs.core.windows.net/enterprise/sap/raw

Silver SAP output examples:

    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/sap/asset_master
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/sap/business_partners
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/sap/power_invoice_headers
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/sap/power_invoice_lines
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/sap/gl_postings
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/sap/ar_open_items

Technical purpose:

    SAP-style data provides the finance truth:
    invoice status, GL posting, AR status, and payment status.

---

## Synthetic Salesforce Source Flow

VoltSentinel simulates Salesforce-style commercial workflow data.

Synthetic Salesforce files include:

- accounts
- contracts
- assets
- revenue disputes

Bronze landing pattern:

    abfss://bronze@<storage-account>.dfs.core.windows.net/enterprise/salesforce/raw

Silver Salesforce output examples:

    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/salesforce/accounts
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/salesforce/contracts
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/salesforce/assets
    abfss://silver@<storage-account>.dfs.core.windows.net/enterprise/salesforce/revenue_disputes

Technical purpose:

    Salesforce-style data provides the commercial workflow truth:
    customer, contract, asset, dispute, and approval context.

---

## Gold Case-Ready Revenue Leakage Flow

Gold case-ready revenue leakage joins:

- Gold revenue leakage facts
- SAP invoice and payment context
- Salesforce account, contract, asset, and dispute context

Output path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/enterprise/case_ready_revenue_leakage

Recommended action values include:

- READY_FOR_HUMAN_REVIEW
- UPDATE_EXISTING_SALESFORCE_DISPUTE
- REVIEW_DATA_GAPS

Technical purpose:

    This layer converts raw leakage facts into commercial case candidates.
    It determines whether the issue should become a new review case, update an existing dispute, or be held for further data review.

---

## Gold RAG Case Package Flow

The RAG case package combines:

- case-ready revenue leakage
- evidence links
- document chunks

Output path pattern:

    abfss://gold@<storage-account>.dfs.core.windows.net/rag/case_explanation_package

Each RAG case package includes:

- breach_event_id
- asset_id
- contract_id
- offtaker
- leakage amount
- eligible compensable MWh
- SAP invoice/payment context
- Salesforce dispute context
- linked evidence chunks
- recommended next action
- RAG instruction

Technical purpose:

    The RAG case package is the governed input to the LangGraph orchestrator.
    It prevents the AI workflow from pulling arbitrary raw data.

---

## Databricks SQL Registration Flow

The Gold RAG case package is registered as a Databricks SQL table.

Managed table example:

    voltsentinel_gold.case_explanation_package

RAG result table example:

    voltsentinel_gold.rag_case_explanations

Human approval queue example:

    voltsentinel_gold.human_approval_queue

Mock Salesforce action table example:

    voltsentinel_gold.mock_salesforce_actions

Technical purpose:

    Databricks SQL provides a clean query interface for the local LangGraph orchestrator.
    The orchestrator can fetch one case package by breach_event_id.

---

## LangGraph RAG Orchestrator Flow

The LangGraph orchestrator is implemented in the rag/orchestrator package.

Main files:

| File | Purpose |
|---|---|
| state.py | Defines workflow state |
| graph.py | Defines LangGraph nodes and routing |
| repositories.py | Handles local JSON, Databricks SQL, approval, and mock Salesforce persistence |
| prompts.py | Builds case explanation prompts |
| run_case.py | Runs a RAG case workflow |
| approve_case.py | Approves or rejects a pending approval request |
| execute_mock_salesforce_action.py | Executes a mocked Salesforce action after approval |
| visualize_graph.py | Generates graph visualization output |

Workflow nodes:

    START
        -> load_case_package
        -> validate_case_readiness
        -> retrieve_evidence
        -> build_prompt
        -> generate_explanation
        -> validate_grounding
        -> route_next_action
        -> persist_result
        -> END

Conditional behavior:

    If case package is ready:
        retrieve evidence and generate explanation

    If case package is blocked:
        persist blocked result and stop

Technical purpose:

    LangGraph provides explicit workflow state, routing, validation, and persistence.
    It makes the RAG process explainable and auditable.

---

## RAG Explanation Flow

For each breach_event_id, the orchestrator:

1. Loads the Gold RAG case package.
2. Validates readiness.
3. Retrieves linked evidence context.
4. Builds a grounded prompt.
5. Generates a case explanation.
6. Validates that required evidence was used.
7. Routes the case to the appropriate next action.
8. Persists the result locally and optionally to Databricks.

The explanation includes:

- asset and contract context
- estimated leakage value
- curtailment and compensable MWh details
- PPA evidence
- ISO curtailment evidence
- settlement evidence
- SAP invoice/payment status
- Salesforce dispute status
- recommended next action

Technical purpose:

    RAG turns structured leakage data and linked evidence into a human-readable case explanation.

---

## Human Approval Flow

VoltSentinel does not allow AI to directly create or update customer-facing Salesforce workflow records.

Instead:

    RAG result
        -> human approval queue
        -> approver decision
        -> approved or rejected
        -> mocked Salesforce action only if approved

Approval table example:

    voltsentinel_gold.human_approval_queue

Approval statuses:

- PENDING
- APPROVED
- REJECTED

Technical purpose:

    This implements human-in-the-loop AI governance.
    The AI can recommend, but a human must approve external workflow action.

---

## Mock Salesforce Action Flow

After approval, VoltSentinel executes a mocked Salesforce action.

Mock action table example:

    voltsentinel_gold.mock_salesforce_actions

Possible mocked actions:

- MOCK_CREATE_SALESFORCE_DISPUTE
- MOCK_UPDATE_SALESFORCE_DISPUTE
- MOCK_REVIEW_ONLY

Technical purpose:

    The POC demonstrates workflow integration without connecting to a real Salesforce org.
    In production, this layer could be replaced with Salesforce API integration.

---

## End-to-End Technical Flow

    1. Python producer generates SCADA telemetry
          ↓
    2. Producer sends telemetry to Azure Event Hubs using Kafka protocol
          ↓
    3. Databricks Structured Streaming reads Event Hubs offsets
          ↓
    4. Raw events land in Bronze Delta
          ↓
    5. Bronze telemetry is parsed, typed, validated, and written to Silver
          ↓
    6. Invalid records are written to Quarantine
          ↓
    7. Silver telemetry is joined to contract mapping
          ↓
    8. Gold revenue leakage facts are calculated
          ↓
    9. Soda Core validates Silver and Gold outputs
          ↓
    10. Passing Gold leakage facts are exported as breach events
          ↓
    11. Synthetic PPA, ISO, and settlement documents are landed in Bronze
          ↓
    12. Documents are converted to Silver registry and chunk tables
          ↓
    13. Breach events are linked to relevant document evidence
          ↓
    14. Synthetic SAP and Salesforce data are landed in Bronze
          ↓
    15. SAP and Salesforce data are curated into Silver enterprise tables
          ↓
    16. Gold case-ready revenue leakage records are created
          ↓
    17. Gold RAG case explanation packages are built
          ↓
    18. RAG case packages are registered as Databricks SQL tables
          ↓
    19. LangGraph fetches a case package by breach_event_id
          ↓
    20. LangGraph generates grounded case explanation
          ↓
    21. RAG result is persisted to Databricks Gold
          ↓
    22. Human approval request is created
          ↓
    23. Human approves or rejects the case
          ↓
    24. Mock Salesforce action is executed if approved

---

## Data Layer Summary

| Layer | Contains | Main Purpose |
|---|---|---|
| Bronze | Raw telemetry, raw documents, raw SAP/Salesforce extracts | Preserve source data |
| Silver | Clean telemetry, document chunks, curated enterprise tables | Create trusted source-aligned data |
| Gold | Revenue leakage facts, evidence links, case packages, RAG results | Create business-ready outputs |
| Quarantine | Invalid telemetry records | Preserve failed records for investigation |
| Observability | Soda check results | Monitor quality and pipeline health |

---

## Why This Is Not a Generic RAG Chatbot

VoltSentinel does not allow the RAG workflow to search across uncontrolled documents at runtime.

Instead, the system creates a governed RAG input:

    Gold revenue leakage case
        + linked PPA evidence
        + linked ISO evidence
        + linked settlement evidence
        + SAP finance context
        + Salesforce commercial context
        = RAG case explanation package

This means the RAG workflow is:

- case-specific
- evidence-linked
- auditable
- quality-gated
- human-reviewed
- aligned to business workflow

---

## Why This Is Not Just a Databricks Pipeline

The lakehouse is only one part of the solution.

The full solution includes:

- revenue leakage detection
- enterprise context enrichment
- document evidence grounding
- AI explanation generation
- approval workflow
- mocked downstream CRM action

The business outcome is not just a Gold table.

The business outcome is:

    evidence-backed revenue recovery case readiness

---

## Production Hardening Considerations

A production version would likely add:

- Real SAP CDC or incremental ingestion
- Real Salesforce API integration
- Real ISO/RTO data feeds
- Managed identity authentication
- Databricks Asset Bundles
- Databricks Workflows or Azure Data Factory orchestration
- CI/CD deployment
- Unity Catalog external locations and permissions
- Vector search over document chunks
- Real LLM integration
- Token, cost, latency, and grounding metrics
- Model evaluation and RAG quality dashboards
- Role-based approval workflow
- Full audit logging
- Exception handling and retry framework
- Data retention and compliance policies

---

## Security Notes

Secrets should not be committed to Git.

Local credentials should be stored in:

    .env

The repository should only include:

    .env.example

Databricks and Azure secrets should be stored in:

    Azure Key Vault
    Databricks secret scopes

Never commit:

- Azure keys
- Event Hub connection strings
- Databricks tokens
- Salesforce credentials
- SAP credentials
- .env files
- Terraform state files

---

## Interview Explanation

VoltSentinel uses Azure Event Hubs and Databricks to process renewable asset telemetry into Bronze, Silver, and Gold lakehouse layers. Gold revenue leakage facts are quality-gated with Soda Core before they are enriched with SAP-style finance data, Salesforce-style commercial data, and linked PPA/ISO/settlement evidence.

A Gold RAG case package is then exposed through Databricks SQL and processed by a LangGraph orchestrator. The RAG workflow generates a grounded explanation, persists the result back to Databricks, creates a human approval request, and only after approval executes a mocked Salesforce dispute action.

The technical design supports an enterprise revenue assurance workflow rather than a generic data pipeline or generic chatbot.
