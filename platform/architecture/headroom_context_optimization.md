# Optional Headroom Context Optimization Layer

## Purpose

Headroom is treated as an optional prompt-context optimization sidecar for VoltSentinel. It is not a source-of-truth component and must not mutate raw contract text, Gold financial facts, audit records, deterministic guardrail inputs, or Salesforce evidence references.

## Correct placement

```text
Contract-scoped evidence pack
+ Gold breach event
+ guardrail context
+ runtime logs
        │
        ▼
Optional Headroom context optimizer
        │
        ▼
LLM synthesis prompt
```

## Design rule

```text
Raw evidence remains authoritative. Headroom only compresses non-authoritative LLM prompt context.
```

## When to enable

Enable only when the synthesis prompt exceeds the configured threshold, typically 4,000 to 6,000 tokens. The default is disabled for deterministic testing.

## Do not compress

- Original PPA text before parsing or indexing
- Text chunks before embeddings
- Stored pgvector chunk text
- Gold breach event values
- Financial calculation fields
- Guardrail comparison values
- Human approval evidence packages
- Salesforce case audit records

## Environment variables

```bash
HEADROOM_ENABLED="false"
HEADROOM_MIN_INPUT_TOKENS="4000"
HEADROOM_PRESERVE_CITATIONS="true"
HEADROOM_PRESERVE_NUMBERS="true"
HEADROOM_PRESERVE_DATES="true"
HEADROOM_PRESERVE_SECTION_REFERENCES="true"
```
