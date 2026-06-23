"""Lightweight observability event logger for VoltSentinel MVP.

This logger writes JSONL events locally by default. In production, replace the
sink with Event Hub, Log Analytics, Postgres, Delta, or Fabric Real-Time Intelligence.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class ObservabilityEvent:
    event_type: str
    component_name: str
    status: str
    trace_id: str = field(default_factory=lambda: f"trace_{uuid.uuid4().hex}")
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metrics: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)


class EventLogger:
    def __init__(self, sink_path: Optional[str] = None) -> None:
        self.sink_path = sink_path or os.getenv(
            "VOLTSENTINEL_OBSERVABILITY_JSONL", "./observability_events.jsonl"
        )
        os.makedirs(os.path.dirname(os.path.abspath(self.sink_path)), exist_ok=True)

    def emit(self, event: ObservabilityEvent) -> None:
        with open(self.sink_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")

    def timed_event(self, event_type: str, component_name: str, trace_id: str, **attrs: Any):
        return _TimedEvent(self, event_type, component_name, trace_id, attrs)


class _TimedEvent:
    def __init__(self, logger: EventLogger, event_type: str, component_name: str, trace_id: str, attrs: Dict[str, Any]) -> None:
        self.logger = logger
        self.event_type = event_type
        self.component_name = component_name
        self.trace_id = trace_id
        self.attrs = attrs
        self.started = time.perf_counter()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        latency_ms = int((time.perf_counter() - self.started) * 1000)
        self.logger.emit(
            ObservabilityEvent(
                event_type=self.event_type,
                component_name=self.component_name,
                trace_id=self.trace_id,
                status="failure" if exc else "success",
                metrics={"latency_ms": latency_ms},
                attributes={**self.attrs, "error": str(exc) if exc else None},
            )
        )
        return False
