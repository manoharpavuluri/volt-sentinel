# VoltSentinel Fix Pack

This pack fixes the main architecture and implementation gaps identified in the original TRD:

1. Private-networking claims are toned down for MVP and separated from true production controls.
2. SCADA generation is no longer used as a false proxy for lost revenue.
3. Bronze/Silver/Gold lakehouse layers are made explicit.
4. Kafka ingestion includes SASL JAAS config and deterministic starting offsets.
5. Revenue leakage logic uses expected generation, curtailment eligibility, settlement comparison, and PPA terms.
6. RAG retrieval is filtered to the correct contract.
7. The agent requires evidence, deterministic variance values, and human authorization before CRM dispatch.
8. Secrets are aligned across `.env`, Databricks, Redis, OpenAI, and Salesforce patterns.

Recommended implementation order:

- Apply `architecture/revised_executive_summary.md` to the TRD.
- Replace the simulation files with the versions under `data_simulation/`.
- Add the Silver models before running the Gold fact model.
- Replace the Gold leakage model with `models/gold/fact_revenue_leakage.sql`.
- Add `stateful_ai_framework/ddl_pgvector.sql` before running the contract parser.
- Replace RAG and LangGraph code with the fixed versions.
- Add Terraform private endpoint snippets only when moving beyond demo/MVP.

