from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class RAGState(TypedDict, total=False):
    case_source: str
    persist_to_databricks: bool

    input_json_path: str
    output_json_path: str
    breach_event_id: str

    case_package: Dict[str, Any]
    evidence_context: List[Dict[str, Any]]

    readiness_status: str
    validation_errors: List[str]

    prompt: str
    rag_answer: str
    recommended_next_action: str
    final_route: str

    approved_for_salesforce: bool

    local_output_json_path: str
    databricks_result_written: bool
    databricks_result_id: str
