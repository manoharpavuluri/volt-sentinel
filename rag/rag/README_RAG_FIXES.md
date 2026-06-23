# VoltSentinel RAG Fix Pack

This pack replaces the current VoltSentinel Cognitive Compute Ring demo logic with a more defensible RAG implementation for PPA settlement dispute support.

## What this fixes

1. **Contract-scoped retrieval**
   - Vector search is now filtered by `contract_id` and optional `document_version_hash` before similarity ranking.
   - This prevents a breach event for one PPA from retrieving clauses from another PPA.

2. **Correct pgvector DDL**
   - Uses `CREATE EXTENSION IF NOT EXISTS vector;`.
   - Adds metadata needed for auditability: contract ID, version hash, page number, section heading, clause type, source locator, and embedding model.

3. **Better chunking model**
   - Replaces raw 512-character slicing with layout-aware page/section chunks.
   - Preserves page numbers and section headings.
   - Captures table content separately when Azure Document Intelligence returns tables.

4. **Correct Upstash Redis REST usage**
   - Replaces `redis.Redis(host=<REST URL>)` with `upstash_redis.Redis(url=..., token=...)`.

5. **Deterministic guardrails**
   - The guard checks contract match, evidence availability, similarity threshold, cited chunk IDs, and variance matching against the Gold fact payload.
   - The LLM is not allowed to invent or recalculate the official financial variance.

6. **Human approval before CRM write**
   - Any actual Salesforce case creation is routed through a human approval node.
   - High dollar values are still highlighted, but external writes require approval either way.

7. **Structured output**
   - Synthesis now requests a strict JSON schema instead of loose JSON mode.

## Suggested merge path

Copy these files into your existing repository:

```text
stateful_ai_framework/ddl_pgvector.sql
stateful_ai_framework/parse_and_vectorize.py
stateful_ai_framework/semantic_retriever.py
stateful_ai_framework/langgraph_orchestrator.py
stateful_ai_framework/outbound_crm_connector.py
.env.rag.example
requirements-rag.txt
```

Then paste the replacement TRD language from:

```text
architecture/revised_rag_trd_section.md
```

## Minimum test path

1. Run the DDL in Supabase SQL editor.
2. Configure `.env` from `.env.rag.example`.
3. Ingest one sample PPA text/PDF:

```bash
python stateful_ai_framework/parse_and_vectorize.py \
  --document ./stateful_ai_framework/legal_assets/wildorado_google_wind_ppa.txt \
  --contract-id PPA_GOOG_WILDORADO_WIND \
  --contract-name "Wildorado Google Wind PPA" \
  --offtaker-name "Google Cloud Operations LLC" \
  --asset-id CW_WIND_WILDORADO
```

4. Run a breach event through the graph with a payload like `sample_payloads/breach_event_sample.json`.
5. Confirm retrieved chunks all belong to the same contract.
6. Confirm Salesforce dispatch is blocked until human approval is true.

## Design principle

The Gold lakehouse fact table calculates money. RAG only retrieves contract language, explains whether that language supports dispute action, and drafts the human/CRM narrative.
