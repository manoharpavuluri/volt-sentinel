"""Contract-scoped pgvector retrieval with Upstash REST caching."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

import psycopg2
from openai import OpenAI
from upstash_redis import Redis


RETRIEVAL_VERSION = "contract-scoped-v1"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


def vector_to_pgvector(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def build_cache_key(
    contract_id: str,
    document_version_hash: Optional[str],
    query: str,
    embedding_model: str,
    clause_type: Optional[str],
) -> str:
    cache_material = {
        "retrieval_version": RETRIEVAL_VERSION,
        "contract_id": contract_id,
        "document_version_hash": document_version_hash,
        "query": query,
        "embedding_model": embedding_model,
        "clause_type": clause_type,
    }
    return "rag:" + hashlib.sha256(json.dumps(cache_material, sort_keys=True).encode("utf-8")).hexdigest()


def get_cache_client() -> Redis:
    return Redis(
        url=require_env("UPSTASH_REDIS_REST_URL"),
        token=require_env("UPSTASH_REDIS_REST_TOKEN"),
    )


def build_retrieval_query(event_payload: dict[str, Any]) -> str:
    contract_id = event_payload.get("associated_ppa_id") or event_payload.get("contract_id")
    asset_id = event_payload.get("asset_id")
    event_type = event_payload.get("event_type", "curtailment settlement variance")
    iso_region = event_payload.get("iso_region")
    estimated_leakage = event_payload.get("estimated_leakage_revenue_usd")

    return (
        f"Find PPA clauses for {event_type}. "
        f"Contract: {contract_id}. Asset: {asset_id}. ISO region: {iso_region}. "
        f"Revenue variance from Gold table: {estimated_leakage}. "
        "Focus on curtailment compensation, settlement true-up, notice, dispute, "
        "limitations of liability, and payment adjustment language."
    )


def retrieve_contract_context(
    event_payload: dict[str, Any],
    top_k: int = 6,
    clause_type: Optional[str] = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Retrieve evidence chunks from only the matching contract/version."""
    contract_id = event_payload.get("associated_ppa_id") or event_payload.get("contract_id")
    if not contract_id:
        raise ValueError("event_payload must include associated_ppa_id or contract_id")

    document_version_hash = event_payload.get("document_version_hash")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    query_text = build_retrieval_query(event_payload)
    cache_key = build_cache_key(contract_id, document_version_hash, query_text, embedding_model, clause_type)
    ttl_seconds = int(os.getenv("RAG_CACHE_TTL_SECONDS", "3600"))

    if use_cache:
        cache = get_cache_client()
        cached = cache.get(cache_key)
        if cached:
            return json.loads(cached)

    openai_client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    embedding_response = openai_client.embeddings.create(input=[query_text], model=embedding_model)
    query_vector = vector_to_pgvector(embedding_response.data[0].embedding)

    predicates = ["c.contract_id = %s"]
    params: list[Any] = [contract_id]

    if document_version_hash:
        predicates.append("c.document_version_hash = %s")
        params.append(document_version_hash)

    if clause_type:
        predicates.append("c.clause_type = %s")
        params.append(clause_type)

    where_sql = " AND ".join(predicates)

    sql = f"""
        SELECT
            c.chunk_id,
            c.contract_id,
            c.document_version_hash,
            c.chunk_index,
            c.page_number,
            c.section_heading,
            c.clause_type,
            c.text_snippet,
            c.source_locator,
            1 - (c.embedding_vector <=> %s::vector) AS similarity
        FROM ppa_child_chunks c
        WHERE {where_sql}
        ORDER BY c.embedding_vector <=> %s::vector
        LIMIT %s;
    """

    # Query vector is used in SELECT similarity and ORDER BY.
    query_params: list[Any] = [query_vector, *params, query_vector, top_k]

    db_connection = psycopg2.connect(require_env("SUPABASE_DB_URL"))
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(sql, query_params)
            rows = cursor.fetchall()
    finally:
        db_connection.close()

    evidence = [
        {
            "chunk_id": row[0],
            "contract_id": row[1],
            "document_version_hash": row[2],
            "chunk_index": row[3],
            "page_number": row[4],
            "section_heading": row[5],
            "clause_type": row[6],
            "text_snippet": row[7],
            "source_locator": row[8],
            "similarity": float(row[9]) if row[9] is not None else None,
        }
        for row in rows
    ]

    if use_cache:
        cache = get_cache_client()
        cache.setex(cache_key, ttl_seconds, json.dumps(evidence, default=str))

    return evidence
