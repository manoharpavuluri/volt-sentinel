import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from kafka import KafkaProducer


ASSETS = [
    {
        "asset_id": "CW_WIND_WILDORADO",
        "asset_type": "WIND",
        "iso_region": "ERCOT_WEST",
        "nameplate_mw": 160,
    },
    {
        "asset_id": "CW_SOLAR_DAGGETT",
        "asset_type": "SOLAR",
        "iso_region": "CAISO_SP15",
        "nameplate_mw": 120,
    },
    {
        "asset_id": "CW_SOLAR_BLACKDUST",
        "asset_type": "SOLAR",
        "iso_region": "ERCOT_NORTH",
        "nameplate_mw": 80,
    },
]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_event() -> dict:
    asset = random.choice(ASSETS)

    expected_kw = round(
        random.uniform(0.35, 0.95) * asset["nameplate_mw"] * 1000,
        2,
    )

    is_curtailment = random.random() < 0.25

    if is_curtailment:
        actual_kw = round(expected_kw * random.uniform(0.25, 0.65), 2)
        operating_status = "CURTAILED_BY_ISO"
        curtailment_reason = random.choice(
            ["CONGESTION", "NEGATIVE_PRICE", "TRANSMISSION_CONSTRAINT"]
        )
    else:
        actual_kw = round(expected_kw * random.uniform(0.90, 1.02), 2)
        operating_status = "NORMAL"
        curtailment_reason = None

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "scada.telemetry",
        "source_system": "mock_scada_producer",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "asset_id": asset["asset_id"],
        "asset_type": asset["asset_type"],
        "iso_region": asset["iso_region"],
        "nameplate_mw": asset["nameplate_mw"],
        "expected_available_kw": expected_kw,
        "actual_generation_kw": actual_kw,
        "operating_status": operating_status,
        "curtailment_reason": curtailment_reason,
        "market_price_usd_per_mwh": round(random.uniform(18, 85), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--messages", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    load_dotenv()

    bootstrap_server = require_env("EVENTHUB_BOOTSTRAP_SERVER")
    eventhub_name = require_env("EVENTHUB_NAME")
    connection_string = require_env("EVENTHUB_CONNECTION_STRING")

    producer = KafkaProducer(
        bootstrap_servers=[bootstrap_server],
        security_protocol="SASL_SSL",
        sasl_mechanism="PLAIN",
        sasl_plain_username="$ConnectionString",
        sasl_plain_password=connection_string,
        client_id="voltsentinel-scada-producer",
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8"),
        acks=1,
        retries=3,
        request_timeout_ms=60000,
        max_block_ms=60000,
        api_version=(1, 0, 0),
    )

    print(f"Sending {args.messages} messages to Event Hub topic: {eventhub_name}")

    try:
        for i in range(args.messages):
            event = build_event()
            future = producer.send(
                eventhub_name,
                key=event["asset_id"],
                value=event,
            )
            metadata = future.get(timeout=30)

            print(
                f"[{i + 1}/{args.messages}] sent "
                f"asset={event['asset_id']} "
                f"status={event['operating_status']} "
                f"partition={metadata.partition} "
                f"offset={metadata.offset}"
            )

            time.sleep(args.sleep)
    finally:
        producer.flush()
        producer.close()

    print("Done.")


if __name__ == "__main__":
    main()
