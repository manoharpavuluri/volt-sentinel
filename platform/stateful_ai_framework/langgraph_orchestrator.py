"""
VoltSentinel stateful agent orchestration.

Design fix:
- Retrieves clauses only from the matching PPA contract.
- Requires deterministic leakage values from the Gold fact payload.
- Requires clause evidence with page/chunk metadata.
- Does not dispatch CRM records unless human_authorized is true.
- Aligns Redis usage with UPSTASH_REDIS_REST_URL/TOKEN from .env.example.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, TypedDict

import psycopg2
import requests
from langgraph.graph import END, StateGraph
from openai import OpenAI


class RetrievedClause(TypedDict):
    contract_id: str
    page_number: int | None
    chunk_index: int
    text_snippet: str


class ClearwayAgentState(TypedDict):
    leakage_record_payload: Dict[str, Any]
    retrieved_clauses: List[RetrievedClause]
    synthesis_verdict_json: Dict[str, Any]
    is_hallucination: bool
    human_authorized: bool
    runtime_logs: List[str]


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vector) + "]"


def _cache_get(key: str) -> list[dict] | None:
    redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
    redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not redis_url or not redis_token:
        return None

    response = requests.get(
        f"{redis_url}/get/{key}",
        headers={"Authorization": f"Bearer {redis_token}"},
        timeout=10,
    )
    response.raise_for_status()
    value = response.json().get("result")
    return json.loads(value) if value else None


def _cache_set(key: str, value: list[dict], ttl_seconds: int = 3600) -> None:
    redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
    redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not redis_url or not redis_token:
        return

    encoded_value = json.dumps(value)
    response = requests.post(
        f"{redis_url}/set/{key}",
        headers={"Authorization": f"Bearer {redis_token}"},
        json={"value": encoded_value, "ex": ttl_seconds},
        timeout=10,
    )
    response.raise_for_status()


def semantic_retrieval_node(state: ClearwayAgentState) -> Dict[str, Any]:
    payload = state["leakage_record_payload"]
    contract_id = payload["associated_ppa_id"]

    search_context = (
        "Curtailment compensation, deemed energy, billing dispute rights, "
        f"settlement true-up terms for contract {contract_id}."
    )
    cache_key = hashlib.sha256(f"{contract_id}|{search_context}".encode("utf-8")).hexdigest()

    cached_hit = _cache_get(cache_key)
    if cached_hit:
        return {
            "retrieved_clauses": cached_hit,
            "runtime_logs": state["runtime_logs"] + ["Contract-scoped context resolved from Redis cache."],
        }

    emb = openai_client.embeddings.create(input=[search_context], model="text-embedding-3-small")
    query_vector = _vector_literal(emb.data[0].embedding)

    db_conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
    try:
        with db_conn.cursor() as cursor:
            cursor.execute(
                """
                select contract_id, page_number, chunk_index, text_snippet
                from ppa_child_chunks
                where contract_id = %s
                order by embedding_vector <=> %s::vector
                limit 5
                """,
                (contract_id, query_vector),
            )
            rows = cursor.fetchall()
    finally:
        db_conn.close()

    clauses = [
        {
            "contract_id": row[0],
            "page_number": row[1],
            "chunk_index": row[2],
            "text_snippet": row[3],
        }
        for row in rows
    ]

    _cache_set(cache_key, clauses)
    return {
        "retrieved_clauses": clauses,
        "runtime_logs": state["runtime_logs"] + ["Fresh contract-scoped context retrieved from pgvector."],
    }


def evaluation_synthesis_node(state: ClearwayAgentState) -> Dict[str, Any]:
    payload = state["leakage_record_payload"]
    clauses = state["retrieved_clauses"]

    evidence = "\n\n".join(
        f"[contract={c['contract_id']}, page={c['page_number']}, chunk={c['chunk_index']}]\n{c['text_snippet']}"
        for c in clauses
    )

    prompt = f"""
You are reviewing a renewable-energy PPA settlement discrepancy.

Use only the deterministic payload values and the retrieved contract evidence.
Do not invent rates, MWh values, settlement amounts, contract clauses, or legal conclusions.

Gold fact payload:
{json.dumps(payload, indent=2)}

Retrieved contract evidence:
{evidence}

Return JSON with exactly these fields:
- dispute_required: boolean
- variance_confirmed_usd: number; must equal payload.estimated_leakage_revenue_usd when dispute_required is true
- contract_id: string
- evidence: array of objects with page_number, chunk_index, and short_supporting_summary
- justification_text: string; explain why the variance is or is not dispute-worthy
- missing_information: array of strings
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    verdict = json.loads(response.choices[0].message.content)

    return {
        "synthesis_verdict_json": verdict,
        "runtime_logs": state["runtime_logs"] + ["Evidence-grounded synthesis finished."],
    }


def deterministic_guard_node(state: ClearwayAgentState) -> Dict[str, Any]:
    payload = state["leakage_record_payload"]
    verdict = state["synthesis_verdict_json"]
    clauses = state["retrieved_clauses"]

    errors = []
    if verdict.get("contract_id") != payload.get("associated_ppa_id"):
        errors.append("Verdict contract_id does not match payload associated_ppa_id.")

    if verdict.get("dispute_required"):
        expected_variance = round(float(payload.get("estimated_leakage_revenue_usd", 0.0)), 2)
        verdict_variance = round(float(verdict.get("variance_confirmed_usd", -1.0)), 2)
        if expected_variance != verdict_variance:
            errors.append("Verdict variance does not match deterministic Gold fact variance.")

    if verdict.get("dispute_required") and not clauses:
        errors.append("No retrieved contract evidence was available.")

    allowed_chunks = {(c["page_number"], c["chunk_index"]) for c in clauses}
    for item in verdict.get("evidence", []):
        evidence_key = (item.get("page_number"), item.get("chunk_index"))
        if evidence_key not in allowed_chunks:
            errors.append(f"Evidence reference {evidence_key} was not retrieved from the contract store.")

    failed = bool(errors)
    return {
        "is_hallucination": failed,
        "runtime_logs": state["runtime_logs"] + [f"Deterministic guard errors: {errors if errors else 'none'}"],
    }


def crm_webhook_dispatch_node(state: ClearwayAgentState) -> Dict[str, Any]:
    if state["is_hallucination"]:
        return {"runtime_logs": state["runtime_logs"] + ["CRM dispatch halted by deterministic guard."]}

    if not state["human_authorized"]:
        return {"runtime_logs": state["runtime_logs"] + ["CRM dispatch halted pending human approval."]}

    # Replace with outbound_crm_connector.create_salesforce_case(...)
    return {"runtime_logs": state["runtime_logs"] + ["Approved discrepancy ready for Salesforce case dispatch."]}


def pipeline_router(state: ClearwayAgentState) -> str:
    if state["is_hallucination"]:
        return "halt"
    if state["synthesis_verdict_json"].get("dispute_required"):
        return "trigger_dispute"
    return "halt"


workflow = StateGraph(ClearwayAgentState)
workflow.add_node("retrieve_context", semantic_retrieval_node)
workflow.add_node("synthesize_discrepancy", evaluation_synthesis_node)
workflow.add_node("verify_deterministic_faithfulness", deterministic_guard_node)
workflow.add_node("dispatch_ticket", crm_webhook_dispatch_node)

workflow.set_entry_point("retrieve_context")
workflow.add_edge("retrieve_context", "synthesize_discrepancy")
workflow.add_edge("synthesize_discrepancy", "verify_deterministic_faithfulness")
workflow.add_conditional_edges(
    "verify_deterministic_faithfulness",
    pipeline_router,
    {"trigger_dispute": "dispatch_ticket", "halt": END},
)
workflow.add_edge("dispatch_ticket", END)

app = workflow.compile()
