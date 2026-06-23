# Revised Executive Summary & Topology Language

## Executive Summary

Project VoltSentinel is a production-aligned proof-of-concept for detecting renewable asset revenue leakage by reconciling operational telemetry, curtailment events, asset master data, PPA contract terms, and market settlement records.

The MVP demonstrates an end-to-end enterprise data pattern: synthetic SCADA and IT-system feeds land into a Medallion Lakehouse, Silver validation separates trusted telemetry from quarantined records, Gold models calculate expected-versus-actual settlement variance, and a contract-grounded AI workflow recommends dispute actions only when evidence and deterministic calculations support the claim.

The system is intentionally designed as an MVP first, with a clear path to production hardening through private networking, managed identities, Key Vault-backed secrets, Databricks workspace hardening, controlled egress, and human-approved Salesforce case creation.

## Revised Security Positioning

For the MVP, external SaaS services such as Upstash Kafka, Upstash Redis, Supabase/Postgres, OpenAI, and Salesforce are treated as approved external service boundaries. Production deployment must replace or harden these connections using enterprise-approved connectivity, identity, and egress-control patterns.

The production target architecture should include:

- ADLS Gen2 private endpoints for `dfs` and `blob` subresources.
- Public network access disabled for storage accounts after private endpoint validation.
- Private DNS zones linked to the data platform VNet.
- Databricks VNet injection, secure cluster connectivity, and no-public-IP controls where supported.
- Azure Key Vault references through managed identity and Databricks secret scopes.
- Restricted outbound egress through firewall/NAT with approved FQDN rules.
- Human approval before any CRM/billing action is created.

## Revised Data Flow

```text
[Local SCADA + IT Simulators]
        │
        ├── telemetry stream → Kafka topic → Bronze Delta raw telemetry
        ├── curtailment events → batch snapshot → Bronze/Silver curtailment events
        ├── SAP asset registry → batch snapshot → Silver asset dimension
        ├── Salesforce PPA map → batch snapshot → Silver PPA dimension
        └── ISO/settlement records → batch snapshot → Silver settlement facts

[Silver Validation Layer]
        ├── valid telemetry
        ├── quarantined telemetry
        ├── normalized curtailment events
        ├── normalized PPA/account mapping
        └── normalized settlement records

[Gold Financial Model]
        └── expected settlement vs actual settlement variance by asset, PPA, hour

[Contract-Grounded AI Review]
        ├── retrieves only clauses from matching PPA
        ├── checks deterministic variance values
        ├── emits citation-backed recommendation
        └── creates CRM dispute case only after human authorization
```
