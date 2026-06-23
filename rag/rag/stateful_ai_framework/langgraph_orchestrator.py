"""
VoltSentinel contract-grounded RAG graph.

Design principle:
- Gold fact table owns financial truth.
- RAG retrieves and explains contract evidence.
- CRM writes require human approval.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional, TypedDict

import psycopg2
from openai import OpenAI
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

try:
    from semantic_retriever import retrieve_contract_context
    from outbound_crm_connector import dispatch_dispute_ticket_to_crm
    from context_optimizer import optimize_messages_for_llm
except ImportError:  # Allows package-style imports too.
    from .semantic_retriever import retrieve_contract_context
    from .outbound_crm_connector import dispatch_dispute_ticket_to_crm
    from .context_optimizer import optimize_messages_for_llm


class AgentComputeState(TypedDict, total=False):
    execution_id: str
    breach_event_payload: Dict[str, Any]
    retrieved_contract_contexts: List[Dict[str, Any]]
    synthesis_analysis_output: Dict[str, Any]
    is_hallucination_detected: bool
    guardrail_failures: List[str]
    human_authorized_release: bool
    human_approval_payload: Dict[str, Any]
    crm_dispatch_result: Dict[str, Any]
    terminal_status: str
    system_execution_logs: List[str]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


def get_contract_id(event: Dict[str, Any]) -> str:
    contract_id = event.get("associated_ppa_id") or event.get("contract_id")
    if not contract_id:
        raise ValueError("breach_event_payload must contain associated_ppa_id or contract_id")
    return str(contract_id)


def get_logs(state: AgentComputeState) -> list[str]:
    return list(state.get("system_execution_logs", []))


def semantic_retrieval_node(state: AgentComputeState) -> Dict[str, Any]:
    event = state["breach_event_payload"]
    evidence = retrieve_contract_context(event_payload=event, top_k=6, use_cache=True)
    return {
        "retrieved_contract_contexts": evidence,
        "system_execution_logs": get_logs(state)
        + [f"Retrieved {len(evidence)} contract-scoped evidence chunks for {get_contract_id(event)}."],
    }


def build_evidence_prompt(evidence: list[dict[str, Any]]) -> str:
    lines = []
    for item in evidence:
        lines.append(
            "\n".join(
                [
                    f"CHUNK_ID: {item['chunk_id']}",
                    f"CONTRACT_ID: {item['contract_id']}",
                    f"PAGE: {item.get('page_number')}",
                    f"SECTION: {item.get('section_heading')}",
                    f"CLAUSE_TYPE: {item.get('clause_type')}",
                    f"SIMILARITY: {item.get('similarity')}",
                    f"TEXT: {item.get('text_snippet')}",
                ]
            )
        )
    return "\n\n---\n\n".join(lines)


def cognitive_synthesis_node(state: AgentComputeState) -> Dict[str, Any]:
    event = state["breach_event_payload"]
    evidence = state.get("retrieved_contract_contexts", [])
    contract_id = get_contract_id(event)
    gold_variance = float(event.get("estimated_leakage_revenue_usd", 0.0) or 0.0)

    prompt = f"""
You are a contract-grounded PPA settlement analyst for VoltSentinel.

Rules:
1. The Gold fact table is the source of truth for financial amounts.
2. Do not recalculate the official variance.
3. Use only the provided evidence chunks.
4. If evidence is weak or unrelated, set dispute_warranted=false.
5. supporting_chunk_ids must contain only CHUNK_ID values from the evidence.

Gold breach event payload:
{json.dumps(event, indent=2, default=str)}

Official Gold fact variance USD:
{gold_variance}

Contract evidence:
{build_evidence_prompt(evidence)}

Return a decision package for human approval.
"""

    schema = {
        "type": "object",
        "properties": {
            "dispute_warranted": {"type": "boolean"},
            "audited_variance_usd": {"type": "number"},
            "contract_id": {"type": "string"},
            "supporting_chunk_ids": {"type": "array", "items": {"type": "integer"}},
            "compliance_justification_rationale": {"type": "string"},
            "recommended_case_priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
            "salesforce_case_subject": {"type": "string"},
            "salesforce_case_description": {"type": "string"},
        },
        "required": [
            "dispute_warranted",
            "audited_variance_usd",
            "contract_id",
            "supporting_chunk_ids",
            "compliance_justification_rationale",
            "recommended_case_priority",
            "salesforce_case_subject",
            "salesforce_case_description",
        ],
        "additionalProperties": False,
    }

    openai_client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    model_name = os.getenv("OPENAI_SYNTHESIS_MODEL", "gpt-4o")
    optimized_context = optimize_messages_for_llm(
        messages=[{"role": "user", "content": prompt}],
        model_name=model_name,
    )
    response = openai_client.chat.completions.create(
        model=model_name,
        messages=optimized_context.messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ppa_dispute_recommendation",
                "strict": True,
                "schema": schema,
            },
        },
    )
    parsed = json.loads(response.choices[0].message.content or "{}")

    # Enforce the official variance after model output. The model can explain it, not change it.
    parsed["audited_variance_usd"] = gold_variance
    parsed["contract_id"] = contract_id

    return {
        "synthesis_analysis_output": parsed,
        "system_execution_logs": get_logs(state)
        + [
            "Synthesis completed with structured schema.",
            f"Context optimization metrics: {optimized_context.metrics}",
        ],
    }


def deterministic_guard_node(state: AgentComputeState) -> Dict[str, Any]:
    event = state["breach_event_payload"]
    evidence = state.get("retrieved_contract_contexts", [])
    verdict = state.get("synthesis_analysis_output", {})
    contract_id = get_contract_id(event)
    gold_variance = float(event.get("estimated_leakage_revenue_usd", 0.0) or 0.0)
    min_similarity = float(os.getenv("MIN_RAG_SIMILARITY", "0.62"))

    failures: list[str] = []

    if not evidence:
        failures.append("No evidence chunks were retrieved.")

    evidence_chunk_ids = {int(item["chunk_id"]) for item in evidence if item.get("chunk_id") is not None}
    supporting_ids = {int(x) for x in verdict.get("supporting_chunk_ids", []) if isinstance(x, int)}

    wrong_contract_chunks = [
        item.get("chunk_id")
        for item in evidence
        if str(item.get("contract_id")) != contract_id
    ]
    if wrong_contract_chunks:
        failures.append(f"Retrieved chunks from wrong contract: {wrong_contract_chunks}")

    best_similarity = max((float(item.get("similarity") or 0.0) for item in evidence), default=0.0)
    if best_similarity < min_similarity:
        failures.append(
            f"Best evidence similarity {best_similarity:.3f} is below threshold {min_similarity:.3f}."
        )

    if str(verdict.get("contract_id")) != contract_id:
        failures.append("Verdict contract_id does not match breach event contract_id.")

    if abs(float(verdict.get("audited_variance_usd", 0.0) or 0.0) - gold_variance) > 0.01:
        failures.append("Verdict variance does not match Gold fact variance.")

    if verdict.get("dispute_warranted") and not supporting_ids:
        failures.append("Dispute is warranted but no supporting chunk IDs were provided.")

    missing_support = sorted(supporting_ids - evidence_chunk_ids)
    if missing_support:
        failures.append(f"Verdict cites chunks not present in retrieved evidence: {missing_support}")

    return {
        "is_hallucination_detected": bool(failures),
        "guardrail_failures": failures,
        "system_execution_logs": get_logs(state) + (["Guardrail validation passed."] if not failures else failures),
    }


def route_after_guard(state: AgentComputeState) -> str:
    if state.get("is_hallucination_detected"):
        return "quarantine"
    if not state.get("synthesis_analysis_output", {}).get("dispute_warranted"):
        return "no_action"
    return "human_approval"


def human_approval_node(state: AgentComputeState) -> Dict[str, Any]:
    event = state["breach_event_payload"]
    verdict = state.get("synthesis_analysis_output", {})
    high_value_threshold = float(os.getenv("HIGH_VALUE_USD_THRESHOLD", "5000"))
    variance = float(event.get("estimated_leakage_revenue_usd", 0.0) or 0.0)

    approval_payload = {
        "approval_type": "salesforce_case_dispatch",
        "high_value_flag": variance >= high_value_threshold,
        "asset_id": event.get("asset_id"),
        "contract_id": get_contract_id(event),
        "fact_record_hash": event.get("fact_record_hash"),
        "variance_usd": variance,
        "recommended_priority": verdict.get("recommended_case_priority"),
        "case_subject": verdict.get("salesforce_case_subject"),
        "case_description": verdict.get("salesforce_case_description"),
        "evidence": state.get("retrieved_contract_contexts", []),
        "guardrail_failures": state.get("guardrail_failures", []),
        "instructions": "Approve, reject, or edit before any CRM write is executed.",
    }

    # In a LangGraph runtime with checkpointing, this pauses and waits for external input.
    decision = interrupt(approval_payload)
    approved = bool(decision.get("approved", False)) if isinstance(decision, dict) else False

    updated_verdict = dict(verdict)
    if isinstance(decision, dict):
        if decision.get("edited_case_subject"):
            updated_verdict["salesforce_case_subject"] = decision["edited_case_subject"]
        if decision.get("edited_case_description"):
            updated_verdict["salesforce_case_description"] = decision["edited_case_description"]

    return {
        "human_authorized_release": approved,
        "human_approval_payload": approval_payload,
        "synthesis_analysis_output": updated_verdict,
        "system_execution_logs": get_logs(state) + [f"Human approval captured. approved={approved}"],
    }


def route_after_human(state: AgentComputeState) -> str:
    return "dispatch" if state.get("human_authorized_release") else "quarantine"


def crm_dispatch_node(state: AgentComputeState) -> Dict[str, Any]:
    event = state["breach_event_payload"]
    verdict = state.get("synthesis_analysis_output", {})

    if not state.get("human_authorized_release"):
        return {
            "terminal_status": "blocked_missing_human_approval",
            "system_execution_logs": get_logs(state) + ["CRM dispatch blocked: missing approval."],
        }

    result = dispatch_dispute_ticket_to_crm(
        asset_id=str(event.get("asset_id")),
        dispute_value_usd=float(event.get("estimated_leakage_revenue_usd", 0.0) or 0.0),
        analytical_justification=str(verdict.get("compliance_justification_rationale", "")),
        subject=str(verdict.get("salesforce_case_subject", "PPA Settlement Dispute")),
        description=str(verdict.get("salesforce_case_description", "")),
        priority=str(verdict.get("recommended_case_priority", "High")),
        fact_record_hash=event.get("fact_record_hash"),
        contract_id=get_contract_id(event),
        evidence_chunk_ids=verdict.get("supporting_chunk_ids", []),
    )

    return {
        "crm_dispatch_result": result,
        "terminal_status": "crm_case_created" if result.get("success") else "crm_dispatch_failed",
        "system_execution_logs": get_logs(state) + [f"CRM dispatch result: {result}"],
    }


def no_action_node(state: AgentComputeState) -> Dict[str, Any]:
    return {
        "terminal_status": "no_dispute_warranted",
        "system_execution_logs": get_logs(state) + ["No dispute warranted. Graph ended without CRM write."],
    }


def quarantine_node(state: AgentComputeState) -> Dict[str, Any]:
    return {
        "terminal_status": "halted_or_quarantined",
        "system_execution_logs": get_logs(state) + ["Graph halted/quarantined before CRM write."],
    }


def save_audit_record(state: AgentComputeState) -> None:
    event = state["breach_event_payload"]
    execution_id = state.get("execution_id") or str(uuid.uuid4())
    contract_id = get_contract_id(event)
    evidence_ids = [int(item["chunk_id"]) for item in state.get("retrieved_contract_contexts", []) if item.get("chunk_id")]

    db_conn = psycopg2.connect(require_env("SUPABASE_DB_URL"))
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO rag_execution_audit_log (
                        execution_id,
                        fact_record_hash,
                        contract_id,
                        document_version_hash,
                        asset_id,
                        breach_event_payload,
                        retrieved_chunk_ids,
                        synthesis_output,
                        guardrail_failures,
                        human_authorized_release,
                        crm_case_id,
                        terminal_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                    ON CONFLICT (execution_id) DO NOTHING;
                    """,
                    (
                        execution_id,
                        event.get("fact_record_hash"),
                        contract_id,
                        event.get("document_version_hash"),
                        event.get("asset_id"),
                        json.dumps(event, default=str),
                        evidence_ids,
                        json.dumps(state.get("synthesis_analysis_output"), default=str),
                        json.dumps(state.get("guardrail_failures", []), default=str),
                        bool(state.get("human_authorized_release", False)),
                        state.get("crm_dispatch_result", {}).get("case_id"),
                        state.get("terminal_status", "unknown"),
                    ),
                )
    finally:
        db_conn.close()


def build_graph():
    graph_builder = StateGraph(AgentComputeState)

    graph_builder.add_node("retrieve_context", semantic_retrieval_node)
    graph_builder.add_node("synthesize_discrepancy", cognitive_synthesis_node)
    graph_builder.add_node("verify_deterministically", deterministic_guard_node)
    graph_builder.add_node("human_approval", human_approval_node)
    graph_builder.add_node("dispatch_crm", crm_dispatch_node)
    graph_builder.add_node("no_action", no_action_node)
    graph_builder.add_node("quarantine", quarantine_node)

    graph_builder.set_entry_point("retrieve_context")
    graph_builder.add_edge("retrieve_context", "synthesize_discrepancy")
    graph_builder.add_edge("synthesize_discrepancy", "verify_deterministically")
    graph_builder.add_conditional_edges(
        "verify_deterministically",
        route_after_guard,
        {
            "human_approval": "human_approval",
            "no_action": "no_action",
            "quarantine": "quarantine",
        },
    )
    graph_builder.add_conditional_edges(
        "human_approval",
        route_after_human,
        {
            "dispatch": "dispatch_crm",
            "quarantine": "quarantine",
        },
    )
    graph_builder.add_edge("dispatch_crm", END)
    graph_builder.add_edge("no_action", END)
    graph_builder.add_edge("quarantine", END)

    return graph_builder.compile()


runtime_application_graph = build_graph()
