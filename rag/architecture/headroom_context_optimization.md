# Optional Headroom Context Optimization Layer

## Purpose

Headroom is an optional context optimization layer for the RAG synthesis prompt. It can reduce token usage when evidence packs, breach payloads, logs, and tool outputs become large.

## Placement

```text
Contract-scoped retrieval
        │
        ▼
Raw evidence pack retained for audit
        │
        ├──► deterministic guardrails use raw evidence
        │
        ▼
Optional Headroom optimizer
        │
        ▼
LLM synthesis prompt
```

## Non-negotiable rule

```text
Headroom never changes the authoritative state. It only prepares a smaller context for the LLM call.
```

## Never compress

- Source contract text stored in `ppa_child_chunks`
- Embedding input text
- Gold breach event financial fields
- Guardrail input values
- Human approval payloads
- Salesforce case audit records

## Enablement variables

```bash
HEADROOM_ENABLED="false"
HEADROOM_MIN_INPUT_TOKENS="4000"
HEADROOM_PRESERVE_CITATIONS="true"
HEADROOM_PRESERVE_NUMBERS="true"
HEADROOM_PRESERVE_DATES="true"
HEADROOM_PRESERVE_SECTION_REFERENCES="true"
```
