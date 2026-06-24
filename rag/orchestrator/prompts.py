from __future__ import annotations

from typing import Any, Dict, List


def build_case_prompt(case_package: Dict[str, Any], evidence_context: List[Dict[str, Any]]) -> str:
    evidence_lines = []

    for item in evidence_context:
        evidence_lines.append(
            f"""
Evidence Rank: {item.get("context_rank")}
Document Type: {item.get("document_type")}
Evidence Role: {item.get("evidence_role")}
Document ID: {item.get("document_id")}
Text:
{item.get("chunk_text")}
"""
        )

    evidence_text = "\n---\n".join(evidence_lines)

    return f"""
You are VoltSentinel's revenue leakage explanation agent.

Task:
Explain whether this renewable-energy revenue leakage event is contractually and operationally supportable.

Rules:
- Use only the supplied case facts and evidence chunks.
- Do not recalculate the estimated leakage dollars.
- Mention SAP invoice/payment context.
- Mention Salesforce account/contract/dispute context.
- Mention PPA evidence.
- Mention ISO curtailment notice evidence.
- Mention settlement evidence.
- Do not approve Salesforce action automatically.
- End with the recommended next action.

Case Facts:
Breach Event ID: {case_package.get("breach_event_id")}
Asset ID: {case_package.get("asset_id")}
Asset Name: {case_package.get("asset_name")}
Contract ID: {case_package.get("contract_id")}
Offtaker: {case_package.get("offtaker_name")}
Curtailment Reason: {case_package.get("curtailment_reason")}
Eligible Compensable MWh: {case_package.get("eligible_compensable_mwh")}
Estimated Leakage USD: {case_package.get("estimated_leakage_revenue_usd")}
Breach Severity: {case_package.get("breach_severity")}

SAP Context:
Invoice ID: {case_package.get("invoice_id")}
Invoice Status: {case_package.get("invoice_status")}
Open Amount USD: {case_package.get("open_amount_usd")}
Accounting Doc ID: {case_package.get("accounting_doc_id")}
GL Account: {case_package.get("gl_account")}
Profit Center: {case_package.get("profit_center")}

Salesforce Context:
Account Name: {case_package.get("account_name")}
SF Account ID: {case_package.get("sf_account_id")}
SF Contract ID: {case_package.get("sf_contract_id")}
Existing Open Dispute: {case_package.get("existing_open_dispute_flag")}
Existing Dispute Number: {case_package.get("existing_dispute_number")}
Recommended Next Action: {case_package.get("recommended_next_action")}

Evidence:
{evidence_text}
""".strip()
