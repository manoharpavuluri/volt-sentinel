-- VoltSentinel Cognitive RAG schema
-- Run in Supabase/Postgres SQL editor before ingestion.

-- pgvector extension name is "vector" in Postgres.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ppa_parent_documents (
    parent_id UUID PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    contract_name TEXT,
    offtaker_name TEXT,
    asset_id VARCHAR(100),
    document_version_hash TEXT NOT NULL,
    raw_text_content TEXT NOT NULL,
    source_file_name TEXT,
    source_mime_type TEXT,
    ingested_at_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (contract_id, document_version_hash)
);

CREATE TABLE IF NOT EXISTS ppa_child_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,
    parent_id UUID NOT NULL REFERENCES ppa_parent_documents(parent_id) ON DELETE CASCADE,
    contract_id VARCHAR(100) NOT NULL,
    document_version_hash TEXT NOT NULL,
    chunk_index INT NOT NULL,
    page_number INT,
    section_heading TEXT,
    clause_type VARCHAR(100),
    text_snippet TEXT NOT NULL,
    source_locator JSONB,
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    embedding_vector vector(1536),
    created_at_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (contract_id, document_version_hash, chunk_index)
);

CREATE TABLE IF NOT EXISTS rag_execution_audit_log (
    execution_id UUID PRIMARY KEY,
    fact_record_hash TEXT,
    contract_id VARCHAR(100) NOT NULL,
    document_version_hash TEXT,
    asset_id VARCHAR(100),
    breach_event_payload JSONB NOT NULL,
    retrieved_chunk_ids BIGINT[] DEFAULT '{}',
    synthesis_output JSONB,
    guardrail_failures JSONB DEFAULT '[]'::jsonb,
    human_authorized_release BOOLEAN DEFAULT FALSE,
    crm_case_id TEXT,
    terminal_status VARCHAR(100) NOT NULL,
    created_at_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ppa_parent_contract_idx
ON ppa_parent_documents(contract_id, document_version_hash);

CREATE INDEX IF NOT EXISTS ppa_child_contract_idx
ON ppa_child_chunks(contract_id, document_version_hash);

CREATE INDEX IF NOT EXISTS ppa_child_clause_type_idx
ON ppa_child_chunks(clause_type);

CREATE INDEX IF NOT EXISTS ppa_child_parent_idx
ON ppa_child_chunks(parent_id);

CREATE INDEX IF NOT EXISTS ppa_hnsw_vector_idx
ON ppa_child_chunks
USING hnsw (embedding_vector vector_cosine_ops);

-- Optional helper view for easier troubleshooting.
CREATE OR REPLACE VIEW vw_ppa_chunk_inventory AS
SELECT
    p.contract_id,
    p.contract_name,
    p.offtaker_name,
    p.asset_id,
    p.document_version_hash,
    COUNT(c.chunk_id) AS chunk_count,
    MIN(c.created_at_timestamp) AS first_chunk_created_at,
    MAX(c.created_at_timestamp) AS last_chunk_created_at
FROM ppa_parent_documents p
LEFT JOIN ppa_child_chunks c
    ON p.parent_id = c.parent_id
GROUP BY
    p.contract_id,
    p.contract_name,
    p.offtaker_name,
    p.asset_id,
    p.document_version_hash;
