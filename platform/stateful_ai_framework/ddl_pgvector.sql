-- Supabase/Postgres pgvector schema for contract-grounded retrieval.
-- Run once before parse_and_vectorize.py.

create extension if not exists vector;

create table if not exists ppa_parent_documents (
    parent_id uuid primary key,
    contract_id text not null,
    source_file_name text not null,
    raw_text_content text not null,
    created_at timestamptz not null default now()
);

create table if not exists ppa_child_chunks (
    chunk_id uuid primary key,
    parent_id uuid not null references ppa_parent_documents(parent_id) on delete cascade,
    contract_id text not null,
    chunk_index integer not null,
    page_number integer,
    text_snippet text not null,
    embedding_vector vector(1536) not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_ppa_child_contract_id
    on ppa_child_chunks(contract_id);

create index if not exists idx_ppa_child_embedding
    on ppa_child_chunks
    using ivfflat (embedding_vector vector_cosine_ops)
    with (lists = 100);
