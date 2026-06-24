# Test Notes

This pack does not include live tests because it depends on your Supabase, OpenAI, Azure Document Intelligence, Upstash, LangGraph, and Salesforce credentials.

Manual smoke tests:

1. Run `ddl_pgvector.sql` in Supabase.
2. Ingest one text document using `parse_and_vectorize.py`.
3. Confirm `vw_ppa_chunk_inventory` shows chunk_count > 0.
4. Run retrieval against `sample_payloads/breach_event_sample.json`.
5. Confirm all returned evidence rows have `contract_id = PPA_GOOG_WILDORADO_WIND`.
6. Run LangGraph with checkpointing and confirm execution pauses at human approval before Salesforce dispatch.
