# Revised VoltSentinel Cognitive RAG Framework Section

## Corrected Objective

VoltSentinel-CCR is a contract-grounded reasoning layer that connects Power Purchase Agreement language to structured revenue leakage events already calculated in the Gold lakehouse. The Gold fact table remains the financial system of record. The RAG layer does not calculate official settlement variance; it retrieves relevant contract evidence, determines whether the contract language supports dispute review, drafts a human-readable explanation, and prepares a Salesforce case only after human approval.

## Corrected Runtime Flow

```text
[Raw PPA PDF/Text]
  -> Azure AI Document Intelligence / text fallback
  -> layout-aware page, heading, and table extraction
  -> parent document table with contract/version metadata
  -> child chunk table with page, heading, clause type, source locator
  -> OpenAI embeddings
  -> Supabase Postgres + pgvector HNSW index

[Gold fact_revenue_leakage event]
  -> contract_id + optional document_version_hash
  -> contract-scoped vector retrieval
  -> evidence pack with chunk IDs, page numbers, similarity scores
  -> deterministic guardrails
  -> LLM synthesis with strict JSON schema
  -> deterministic output validation
  -> human approval interrupt
  -> Salesforce sandbox case creation
  -> audit trail record
```

## Key Governance Rule

The RAG system may explain and classify, but it must not become the source of truth for money.

Allowed RAG responsibilities:

- identify contract clauses relevant to curtailment, payment, settlement, limitation, notice, or dispute rights;
- summarize why a breach event may or may not justify dispute review;
- produce cited evidence using chunk IDs, page numbers, and section headings;
- draft a Salesforce case description;
- package the decision for human approval.

Not allowed RAG responsibilities:

- independently recalculating official revenue leakage;
- overriding Gold fact table variance;
- opening CRM tickets without approval;
- citing chunks from a different contract;
- using cached results without contract/version awareness.

## Retrieval Contract

Every retrieval must apply this order:

1. Filter by `contract_id`.
2. Filter by `document_version_hash` when provided.
3. Optionally filter or boost by `clause_type`.
4. Rank by vector similarity.
5. Return chunk IDs, page numbers, section headings, snippet text, similarity score, and source locator.

## Guardrail Contract

Before CRM dispatch, the graph must confirm:

- all retrieved chunks match the event contract;
- at least one evidence chunk passes the minimum similarity threshold;
- the LLM output includes supporting chunk IDs;
- every supporting chunk ID exists in the retrieved evidence pack;
- `audited_variance_usd` equals the Gold fact value within tolerance;
- `contract_id` in the verdict equals the breach event contract;
- human approval has been captured.

## Human Approval Pattern

All Salesforce writes require human approval. High value cases above the configured threshold are marked as high risk in the approval payload, but even lower-value dispute cases are not written externally until approved.

## Corrected FinOps Claim

Redis caching reduces repeated vector searches for identical contract/query/version combinations. Do not claim a fixed cost reduction percentage unless measured in telemetry. Cache keys must include `contract_id`, `document_version_hash`, query text, embedding model, and retrieval version.

## Corrected Security Claim

For the MVP, Supabase, Upstash, OpenAI, Azure Document Intelligence, and Salesforce are external SaaS endpoints governed by credentials, TLS, and service-level access policies. Do not claim they are inside an Azure Private VNet unless private connectivity, private endpoints, DNS, firewall, and egress controls are actually implemented.
