{{ config(materialized='view') }}

select
    event_id,
    timestamp_utc,
    asset_id,
    measured_generation_kw,
    expected_available_kw,
    grid_limit_kw,
    operating_status,
    telemetry_quality,
    source_system,
    kafka_topic,
    kafka_partition,
    kafka_offset,
    ingestion_ts_utc
from {{ source('bronze', 'clearway_telemetry_raw') }}
