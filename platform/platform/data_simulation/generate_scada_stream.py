"""
VoltSentinel SCADA simulator.

Design fix:
- Keep raw telemetry in Bronze, even when it is bad.
- Do not block negative/corrupt readings at the producer; tag them with telemetry_quality.
- Include expected/available generation so the Gold layer does not use nameplate capacity as a false leakage baseline.
"""

import json
import os
import random
import time
from datetime import datetime, timezone
from typing import Literal

from kafka import KafkaProducer
from pydantic import BaseModel, Field


class ClearwaySCADAModel(BaseModel):
    timestamp_utc: str
    asset_id: str
    measured_generation_kw: float
    expected_available_kw: float = Field(ge=0)
    grid_limit_kw: float = Field(ge=0)
    operating_status: Literal["NORMAL", "CURTAILED_BY_ERCOT", "CURTAILED_BY_CAISO", "CURTAILED_BY_PJM", "NIGHT_REST"]
    telemetry_quality: Literal["VALID", "CORRUPT_SENSOR_VALUE", "MISSING_EXPECTED_BASELINE"]
    source_system: str = "LOCAL_SCADA_SIM"


TOPIC_NAME = "clearway-scada-realtime"
ASSET_CONFIG = {
    "CW_WIND_WILDORADO": {"type": "WIND", "iso": "ERCOT", "capacity_kw": 161_000},
    "CW_SOLAR_DAGGETT": {"type": "SOLAR", "iso": "CAISO", "capacity_kw": 482_000},
    "CW_SOLAR_BLACKDUST": {"type": "SOLAR", "iso": "PJM", "capacity_kw": 120_000},
}


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=[os.getenv("UPSTASH_KAFKA_BOOTSTRAP_SERVER")],
        sasl_mechanism="SCRAM-SHA-256",
        security_protocol="SASL_SSL",
        sasl_plain_username=os.getenv("UPSTASH_KAFKA_USERNAME"),
        sasl_plain_password=os.getenv("UPSTASH_KAFKA_PASSWORD"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda v: v.encode("utf-8"),
        linger_ms=50,
    )


def simulate_asset(asset_id: str, cfg: dict) -> dict:
    now = datetime.now(timezone.utc)
    hour = now.hour
    capacity_kw = cfg["capacity_kw"]

    if cfg["type"] == "SOLAR":
        if 12 <= hour <= 22:  # UTC daylight approximation for demo only
            expected_available_kw = capacity_kw * random.uniform(0.60, 0.95)
        else:
            expected_available_kw = 0.0
    else:
        expected_available_kw = capacity_kw * random.uniform(0.20, 0.92)

    is_curtailed = random.random() < 0.10 and expected_available_kw > 0
    operating_status = "NORMAL"
    grid_limit_kw = expected_available_kw

    if is_curtailed:
        grid_limit_kw = expected_available_kw * random.uniform(0.35, 0.75)
        operating_status = f"CURTAILED_BY_{cfg['iso']}"

    measured_generation_kw = min(expected_available_kw, grid_limit_kw) * random.uniform(0.96, 1.02)
    telemetry_quality = "VALID"

    # Inject a bad value without dropping it. Silver/quarantine should handle this.
    if random.random() < 0.02:
        measured_generation_kw = -250.0
        telemetry_quality = "CORRUPT_SENSOR_VALUE"

    if expected_available_kw == 0 and cfg["type"] == "SOLAR":
        operating_status = "NIGHT_REST"

    payload = {
        "timestamp_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
        "asset_id": asset_id,
        "measured_generation_kw": round(measured_generation_kw, 2),
        "expected_available_kw": round(expected_available_kw, 2),
        "grid_limit_kw": round(grid_limit_kw, 2),
        "operating_status": operating_status,
        "telemetry_quality": telemetry_quality,
        "source_system": "LOCAL_SCADA_SIM",
    }

    # Validate structure only. Do not block business-quality anomalies at the producer.
    ClearwaySCADAModel(**payload)
    return payload


def main() -> None:
    producer = build_producer()
    print(f"VoltSentinel SCADA simulator broadcasting to Kafka topic: {TOPIC_NAME}")

    try:
        while True:
            for asset_id, cfg in ASSET_CONFIG.items():
                payload = simulate_asset(asset_id, cfg)
                producer.send(TOPIC_NAME, key=asset_id, value=payload)
                print(payload)
            producer.flush()
            time.sleep(10)
    except KeyboardInterrupt:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
