"""Salesforce sandbox connector for approved VoltSentinel dispute cases."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import requests


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


def get_salesforce_token() -> str:
    payload = {
        "grant_type": "client_credentials",
        "client_id": require_env("SF_CONSUMER_KEY"),
        "client_secret": require_env("SF_CONSUMER_SECRET"),
    }
    response = requests.post(require_env("SALESFORCE_OAUTH_TOKEN_URL"), data=payload, timeout=30)
    if response.status_code != 200:
        raise ConnectionRefusedError(f"Salesforce OAuth token failure: {response.status_code} {response.text}")

    token = response.json().get("access_token")
    if not token:
        raise ConnectionRefusedError("Salesforce OAuth response did not include access_token")
    return token


def dispatch_dispute_ticket_to_crm(
    asset_id: str,
    dispute_value_usd: float,
    analytical_justification: str,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    priority: str = "High",
    fact_record_hash: Optional[str] = None,
    contract_id: Optional[str] = None,
    evidence_chunk_ids: Optional[list[int]] = None,
) -> dict[str, Any]:
    """
    Create a Salesforce Case after LangGraph human approval.

    This function does not decide whether a case should be created. It only executes
    the already-approved action.
    """
    token = get_salesforce_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    evidence_ids = evidence_chunk_ids or []
    case_description = description or analytical_justification
    case_description += "\n\nVoltSentinel audit metadata:\n"
    case_description += json.dumps(
        {
            "asset_id": asset_id,
            "contract_id": contract_id,
            "fact_record_hash": fact_record_hash,
            "dispute_value_usd": dispute_value_usd,
            "evidence_chunk_ids": evidence_ids,
        },
        indent=2,
        default=str,
    )

    case_record = {
        "Subject": subject or f"PPA Settlement Dispute: {asset_id}",
        "Priority": priority if priority in {"Low", "Medium", "High"} else "High",
        "Origin": "VoltSentinel Platform",
        "Description": case_description,
        "Status": "New",
    }

    endpoint = f"{require_env('SALESFORCE_SANDBOX_URL').rstrip('/')}/services/data/v60.0/sobjects/Case"
    response = requests.post(endpoint, headers=headers, json=case_record, timeout=30)

    if response.status_code == 201:
        payload = response.json()
        return {
            "success": True,
            "case_id": payload.get("id"),
            "status_code": response.status_code,
            "response": payload,
        }

    return {
        "success": False,
        "case_id": None,
        "status_code": response.status_code,
        "response": response.text,
    }
