"""RAG observability event helpers for VoltSentinel."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class RagRuntimeEvent:
    event_type: str
    rag_run_id: str
    trace_id: str
    node_name: str
    status: str
    event_id: str = field(default_factory=lambda: f"rag_evt_{uuid.uuid4().hex}")
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metrics: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)


class RagEventLogger:
    def __init__(self, sink_path: Optional[str] = None) -> None:
        self.sink_path = sink_path or os.getenv("RAG_OBSERVABILITY_JSONL", "./rag_observability_events.jsonl")
        os.makedirs(os.path.dirname(os.path.abspath(self.sink_path)), exist_ok=True)

    def emit(self, event: RagRuntimeEvent) -> None:
        with open(self.sink_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")
