from __future__ import annotations

import argparse
from pathlib import Path

from rag.orchestrator.graph import build_graph


def main():
    parser = argparse.ArgumentParser(description="Run VoltSentinel LangGraph RAG case workflow.")
    parser.add_argument("--input-json", required=True, help="Path to RAG case package JSON.")
    parser.add_argument("--breach-event-id", required=True, help="Breach event ID to explain.")
    parser.add_argument("--output-json", default="rag/outputs/rag_case_result.json", help="Output JSON path.")

    args = parser.parse_args()

    if not Path(args.input_json).exists():
        raise FileNotFoundError(f"Input JSON not found: {args.input_json}")

    graph = build_graph()

    result = graph.invoke(
        {
            "input_json_path": args.input_json,
            "breach_event_id": args.breach_event_id,
            "output_json_path": args.output_json,
        }
    )

    print("Workflow complete.")
    print("Breach Event ID:", result.get("breach_event_id"))
    print("Readiness Status:", result.get("readiness_status"))
    print("Final Route:", result.get("final_route"))
    print("Approved for Salesforce:", result.get("approved_for_salesforce"))
    print()
    print("RAG Answer:")
    print(result.get("rag_answer"))
    print()
    print("Output written to:", args.output_json)


if __name__ == "__main__":
    main()
