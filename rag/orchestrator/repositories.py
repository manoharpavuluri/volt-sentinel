from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from databricks import sql

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_json_safe(v) for v in value]

    return value


def _require_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def _validate_table_name(table_name: str) -> str:
    """
    Allows identifiers like:
      schema.table
      catalog.schema.table
    """
    pattern = r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){1,2}$"

    if not re.match(pattern, table_name):
        raise ValueError(f"Unsafe or invalid table name: {table_name}")

    return table_name


class LocalJsonCasePackageRepository:
    def __init__(self, input_json_path: str):
        self.input_json_path = input_json_path

    def get_case_package(self, breach_event_id: str) -> Optional[Dict[str, Any]]:
        with Path(self.input_json_path).open("r", encoding="utf-8") as f:
            payload = json.load(f)

        if isinstance(payload, dict) and "cases" in payload:
            cases = payload["cases"]
        elif isinstance(payload, list):
            cases = payload
        elif isinstance(payload, dict):
            cases = [payload]
        else:
            raise ValueError(
                "Input JSON must be a case object, list of cases, or object with a cases array."
            )

        for case in cases:
            if case.get("breach_event_id") == breach_event_id:
                return _json_safe(case)

        return None


class DatabricksSqlCasePackageRepository:
    def __init__(self):
        self.server_hostname = _require_env("DATABRICKS_SERVER_HOSTNAME")
        self.http_path = _require_env("DATABRICKS_HTTP_PATH")
        self.access_token = _require_env("DATABRICKS_TOKEN")
        self.table_name = _validate_table_name(
            os.getenv(
                "DATABRICKS_RAG_PACKAGE_TABLE",
                "voltsentinel_gold.case_explanation_package",
            )
        )

    def get_case_package(self, breach_event_id: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT
                *,
                to_json(evidence_context) AS evidence_context_json
            FROM {self.table_name}
            WHERE breach_event_id = ?
            LIMIT 1
        """

        with sql.connect(
            server_hostname=self.server_hostname,
            http_path=self.http_path,
            access_token=self.access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, [breach_event_id])
                row = cursor.fetchone()

                if row is None:
                    return None

                columns = [description[0] for description in cursor.description]
                data = dict(zip(columns, row))

        evidence_context_json = data.pop("evidence_context_json", None)

        # Remove native complex column if the connector returned it separately.
        data.pop("evidence_context", None)

        if evidence_context_json:
            data["evidence_context"] = json.loads(evidence_context_json)
        else:
            data["evidence_context"] = []

        return _json_safe(data)


import hashlib
from datetime import timezone


class DatabricksSqlRAGResultRepository:
    def __init__(self):
        self.server_hostname = _require_env("DATABRICKS_SERVER_HOSTNAME")
        self.http_path = _require_env("DATABRICKS_HTTP_PATH")
        self.access_token = _require_env("DATABRICKS_TOKEN")
        self.table_name = _validate_table_name(
            os.getenv(
                "DATABRICKS_RAG_RESULT_TABLE",
                "voltsentinel_gold.rag_case_explanations",
            )
        )

    def save_result(self, result: Dict[str, Any]) -> str:
        breach_event_id = result.get("breach_event_id") or "UNKNOWN"
        result_seed = f"{breach_event_id}|{datetime.now(timezone.utc).isoformat()}"
        result_id = hashlib.sha256(result_seed.encode("utf-8")).hexdigest()

        validation_errors_json = json.dumps(
            _json_safe(result.get("validation_errors", [])),
            default=str,
        )

        case_package_json = json.dumps(
            _json_safe(result.get("case_package", {})),
            default=str,
        )

        evidence_used_json = json.dumps(
            _json_safe(result.get("evidence_used", [])),
            default=str,
        )

        query = f"""
            INSERT INTO {self.table_name} (
                result_id,
                run_timestamp_utc,
                breach_event_id,
                readiness_status,
                recommended_next_action,
                final_route,
                approved_for_salesforce,
                validation_errors_json,
                rag_answer,
                case_package_json,
                evidence_used_json,
                source_system
            )
            VALUES (
                ?,
                current_timestamp(),
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
        """

        params = [
            result_id,
            breach_event_id,
            result.get("readiness_status"),
            result.get("recommended_next_action"),
            result.get("final_route"),
            bool(result.get("approved_for_salesforce", False)),
            validation_errors_json,
            result.get("rag_answer"),
            case_package_json,
            evidence_used_json,
            "LANGGRAPH_LOCAL_ORCHESTRATOR",
        ]

        with sql.connect(
            server_hostname=self.server_hostname,
            http_path=self.http_path,
            access_token=self.access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)

        return result_id