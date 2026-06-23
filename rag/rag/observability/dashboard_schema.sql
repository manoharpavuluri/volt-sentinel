-- VoltSentinel Control Tower dashboard schema
-- Target: Postgres/Supabase for MVP, or Delta/Fabric tables for production.

CREATE TABLE IF NOT EXISTS dim_component (
    component_id TEXT PRIMARY KEY,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL,
    owner_team TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_model (
    model_name TEXT PRIMARY KEY,
    provider_name TEXT,
    input_price_per_1k_tokens DOUBLE PRECISION,
    output_price_per_1k_tokens DOUBLE PRECISION,
    embedding_price_per_1k_tokens DOUBLE PRECISION,
    effective_start_date DATE,
    effective_end_date DATE
);

CREATE TABLE IF NOT EXISTS fact_platform_run (
    run_id TEXT PRIMARY KEY,
    trace_id TEXT,
    run_type TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    failure_reason TEXT,
    total_latency_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_pipeline_run (
    pipeline_run_id TEXT PRIMARY KEY,
    trace_id TEXT,
    pipeline_name TEXT NOT NULL,
    layer_name TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    rows_read BIGINT DEFAULT 0,
    rows_written BIGINT DEFAULT 0,
    rows_quarantined BIGINT DEFAULT 0,
    quality_failure_count BIGINT DEFAULT 0,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_rag_run (
    rag_run_id TEXT PRIMARY KEY,
    trace_id TEXT,
    breach_event_id TEXT,
    asset_id TEXT,
    contract_id TEXT,
    document_version_hash TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    retrieval_latency_ms INT,
    context_optimization_latency_ms INT,
    synthesis_latency_ms INT,
    guardrail_latency_ms INT,
    total_latency_ms INT,
    retrieved_chunk_count INT,
    top_similarity_score DOUBLE PRECISION,
    citation_count INT,
    guardrail_passed BOOLEAN,
    human_approval_required BOOLEAN,
    human_approved BOOLEAN,
    crm_case_created BOOLEAN,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_llm_usage (
    usage_id TEXT PRIMARY KEY,
    rag_run_id TEXT,
    trace_id TEXT,
    node_name TEXT,
    model_name TEXT,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    estimated_cost_usd DOUBLE PRECISION DEFAULT 0.0,
    headroom_enabled BOOLEAN DEFAULT FALSE,
    headroom_tokens_before INT,
    headroom_tokens_after INT,
    headroom_tokens_saved INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_retrieval_quality (
    retrieval_event_id TEXT PRIMARY KEY,
    rag_run_id TEXT,
    trace_id TEXT,
    contract_id TEXT,
    document_version_hash TEXT,
    query_text TEXT,
    retrieved_chunk_count INT,
    top_similarity_score DOUBLE PRECISION,
    average_similarity_score DOUBLE PRECISION,
    no_evidence_flag BOOLEAN DEFAULT FALSE,
    wrong_contract_blocked_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_guardrail_event (
    guardrail_event_id TEXT PRIMARY KEY,
    rag_run_id TEXT,
    trace_id TEXT,
    guardrail_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    severity TEXT,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_human_approval (
    approval_id TEXT PRIMARY KEY,
    rag_run_id TEXT,
    trace_id TEXT,
    approver_id TEXT,
    approval_required BOOLEAN NOT NULL,
    approved BOOLEAN,
    decision_timestamp TIMESTAMP,
    decision_notes TEXT,
    variance_usd DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_crm_dispatch (
    crm_dispatch_id TEXT PRIMARY KEY,
    rag_run_id TEXT,
    trace_id TEXT,
    target_system TEXT DEFAULT 'Salesforce',
    status TEXT NOT NULL,
    case_id TEXT,
    http_status_code INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_cost_daily (
    cost_date DATE NOT NULL,
    component_name TEXT NOT NULL,
    model_name TEXT,
    total_tokens BIGINT DEFAULT 0,
    total_cost_usd DOUBLE PRECISION DEFAULT 0.0,
    total_runs BIGINT DEFAULT 0,
    headroom_tokens_saved BIGINT DEFAULT 0,
    redis_cache_hits BIGINT DEFAULT 0,
    redis_cache_misses BIGINT DEFAULT 0,
    PRIMARY KEY (cost_date, component_name, COALESCE(model_name, ''))
);
