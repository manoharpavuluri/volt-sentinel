from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from langgraph.graph import StateGraph, START, END

from rag.orchestrator.prompts import build_case_prompt
from rag.orchestrator.state import RAGState



from rag.orchestrator.repositories import (
    DatabricksSqlCasePackageRepository,
    DatabricksSqlRAGResultRepository,
    LocalJsonCasePackageRepository,
)

def _load_json(path: str) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_case_package(state: RAGState) -> Dict[str, Any]:
    requested_breach_event_id = state["breach_event_id"]
    case_source = state.get("case_source", "local-json")

    try:
        if case_source == "databricks-sql":
            repository = DatabricksSqlCasePackageRepository()
        elif case_source == "local-json":
            input_json_path = state["input_json_path"]
            repository = LocalJsonCasePackageRepository(input_json_path)
        else:
            return {
                "validation_errors": [f"Unsupported case_source: {case_source}"],
                "readiness_status": "BLOCKED",
            }

        selected_case = repository.get_case_package(requested_breach_event_id)

    except Exception as exc:
        return {
            "validation_errors": [f"Failed to load case package: {exc}"],
            "readiness_status": "BLOCKED",
        }

    if selected_case is None:
        return {
            "validation_errors": [f"Breach event ID not found: {requested_breach_event_id}"],
            "readiness_status": "BLOCKED",
        }

    evidence_context = selected_case.get("evidence_context") or []

    return {
        "case_package": selected_case,
        "evidence_context": evidence_context,
        "validation_errors": [],
    }


def validate_case_readiness(state: RAGState) -> Dict[str, Any]:
    case = state.get("case_package", {})
    errors: List[str] = list(state.get("validation_errors", []))

    required_fields = [
        "breach_event_id",
        "asset_id",
        "contract_id",
        "estimated_leakage_revenue_usd",
        "recommended_next_action",
    ]

    for field in required_fields:
        if case.get(field) in (None, ""):
            errors.append(f"Missing required field: {field}")

    evidence_context = state.get("evidence_context", [])

    if not evidence_context:
        errors.append("No evidence_context was supplied.")

    if errors:
        return {
            "validation_errors": errors,
            "readiness_status": "BLOCKED",
        }

    return {
        "validation_errors": [],
        "readiness_status": "READY",
    }


def route_after_readiness(state: RAGState) -> str:
    if state.get("readiness_status") == "READY":
        return "retrieve_evidence"

    return "persist_result"


def retrieve_evidence(state: RAGState) -> Dict[str, Any]:
    evidence_context = state.get("evidence_context", [])

    sorted_evidence = sorted(
        evidence_context,
        key=lambda x: (
            int(x.get("context_rank") or 999),
            -(float(x.get("evidence_score") or 0)),
        ),
    )

    top_evidence = sorted_evidence[:8]

    return {
        "evidence_context": top_evidence,
    }


def build_prompt_node(state: RAGState) -> Dict[str, Any]:
    prompt = build_case_prompt(
        case_package=state["case_package"],
        evidence_context=state["evidence_context"],
    )

    return {
        "prompt": prompt,
    }


def generate_explanation(state: RAGState) -> Dict[str, Any]:
    """
    First runnable version uses a deterministic grounded explanation.
    Later we will swap this node with Azure OpenAI / OpenAI.
    """
    case = state["case_package"]
    evidence = state.get("evidence_context", [])

    doc_types = sorted({item.get("document_type") for item in evidence if item.get("document_type")})

    ppa_available = "PPA" in doc_types
    iso_notice_available = "ISO_CURTAILMENT_NOTICE" in doc_types
    settlement_available = "ISO_SETTLEMENT_STATEMENT" in doc_types

    action = case.get("recommended_next_action")

    explanation = f"""
VoltSentinel identified a revenue leakage event for asset {case.get("asset_id")} under contract {case.get("contract_id")} with {case.get("offtaker_name")}.

The Gold case fact estimates leakage of ${case.get("estimated_leakage_revenue_usd")} and eligible compensable energy of {case.get("eligible_compensable_mwh")} MWh. This explanation does not recalculate that amount; it relies on the curated Gold calculation.

Contractual support is {'available' if ppa_available else 'not available'} from the linked PPA evidence. Operational support is {'available' if iso_notice_available else 'not available'} from the ISO curtailment notice evidence. Settlement support is {'available' if settlement_available else 'not available'} from the ISO settlement statement evidence.

SAP context shows invoice {case.get("invoice_id")} with invoice status {case.get("invoice_status")}, open amount {case.get("open_amount_usd")}, accounting document {case.get("accounting_doc_id")}, and GL account {case.get("gl_account")}. This provides finance and revenue-recognition context for the leakage case.

Salesforce context shows account {case.get("account_name")}, contract record {case.get("sf_contract_id")}, and existing open dispute flag {case.get("existing_open_dispute_flag")}. Existing dispute number is {case.get("existing_dispute_number")}.

Recommended next action: {action}. Salesforce create/update should not be automated yet because human approval is required.
""".strip()

    return {
        "rag_answer": explanation,
        "recommended_next_action": action,
    }


def validate_grounding(state: RAGState) -> Dict[str, Any]:
    errors: List[str] = list(state.get("validation_errors", []))
    answer = state.get("rag_answer", "")
    evidence = state.get("evidence_context", [])
    case = state.get("case_package", {})

    if not answer:
        errors.append("Generated answer is empty.")

    if "do not recalculate" in answer.lower():
        errors.append("Answer leaked prompt instruction text.")

    required_mentions = [
        case.get("asset_id"),
        case.get("contract_id"),
        case.get("invoice_id"),
        case.get("sf_contract_id"),
    ]

    for value in required_mentions:
        if value and str(value) not in answer:
            errors.append(f"Answer does not mention required grounded value: {value}")

    if len(evidence) == 0:
        errors.append("No evidence chunks were used.")

    readiness_status = "READY" if not errors else "BLOCKED"

    return {
        "validation_errors": errors,
        "readiness_status": readiness_status,
    }


def route_next_action(state: RAGState) -> Dict[str, Any]:
    case = state.get("case_package", {})
    action = case.get("recommended_next_action", "REVIEW_DATA_GAPS")

    if state.get("readiness_status") != "READY":
        final_route = "BLOCKED_REVIEW_REQUIRED"
    elif action == "READY_FOR_HUMAN_REVIEW":
        final_route = "HUMAN_REVIEW_QUEUE"
    elif action == "UPDATE_EXISTING_SALESFORCE_DISPUTE":
        final_route = "HUMAN_REVIEW_EXISTING_DISPUTE_UPDATE"
    else:
        final_route = "DATA_GAP_OR_THRESHOLD_REVIEW"

    return {
        "final_route": final_route,
        "approved_for_salesforce": False,
    }


def persist_result(state: RAGState) -> Dict[str, Any]:
    output_json_path = state.get("output_json_path", "rag/outputs/rag_case_result.json")

    result = {
        "breach_event_id": state.get("breach_event_id"),
        "readiness_status": state.get("readiness_status"),
        "validation_errors": state.get("validation_errors", []),
        "recommended_next_action": state.get("recommended_next_action"),
        "final_route": state.get("final_route"),
        "approved_for_salesforce": state.get("approved_for_salesforce", False),
        "rag_answer": state.get("rag_answer"),
        "case_package": state.get("case_package"),
        "evidence_used": state.get("evidence_context", []),
    }

    _write_json(output_json_path, result)

    databricks_result_id = None

    if state.get("persist_to_databricks", False):
        repository = DatabricksSqlRAGResultRepository()
        databricks_result_id = repository.save_result(result)

    result["local_output_json_path"] = output_json_path
    result["databricks_result_written"] = databricks_result_id is not None
    result["databricks_result_id"] = databricks_result_id

    return result


def build_graph():
    builder = StateGraph(RAGState)

    builder.add_node("load_case_package", load_case_package)
    builder.add_node("validate_case_readiness", validate_case_readiness)
    builder.add_node("retrieve_evidence", retrieve_evidence)
    builder.add_node("build_prompt", build_prompt_node)
    builder.add_node("generate_explanation", generate_explanation)
    builder.add_node("validate_grounding", validate_grounding)
    builder.add_node("route_next_action", route_next_action)
    builder.add_node("persist_result", persist_result)

    builder.add_edge(START, "load_case_package")
    builder.add_edge("load_case_package", "validate_case_readiness")

    builder.add_conditional_edges(
        "validate_case_readiness",
        route_after_readiness,
        {
            "retrieve_evidence": "retrieve_evidence",
            "persist_result": "persist_result",
        },
    )

    builder.add_edge("retrieve_evidence", "build_prompt")
    builder.add_edge("build_prompt", "generate_explanation")
    builder.add_edge("generate_explanation", "validate_grounding")
    builder.add_edge("validate_grounding", "route_next_action")
    builder.add_edge("route_next_action", "persist_result")
    builder.add_edge("persist_result", END)

    return builder.compile()
