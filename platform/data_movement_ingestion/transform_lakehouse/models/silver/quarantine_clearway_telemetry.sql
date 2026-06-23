{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge'
) }}

with src as (
    select
        event_id,
        to_timestamp(timestamp_utc, 'yyyy-MM-dd HH:mm:ss') as event_ts_utc,
        asset_id,
        measured_generation_kw,
        expected_available_kw,
        grid_limit_kw,
        operating_status,
        telemetry_quality,
        source_system,
        raw_payload,
        kafka_topic,
        kafka_partition,
        kafka_offset,
        bronze_ingested_at
    from {{ source('bronze', 'clearway_telemetry') }}
    {% if is_incremental() %}
      where bronze_ingested_at >= current_timestamp() - interval 72 hours
    {% endif %}
),

validated as (
    select
        *,
        case
            when event_ts_utc is null then 'INVALID_TIMESTAMP'
            when asset_id is null then 'MISSING_ASSET'
            when asset_id not in ('CW_WIND_WILDORADO', 'CW_SOLAR_DAGGETT', 'CW_SOLAR_BLACKDUST') then 'UNKNOWN_ASSET'
            when measured_generation_kw < 0 then 'NEGATIVE_GENERATION'
            when expected_available_kw < 0 then 'NEGATIVE_EXPECTED_BASELINE'
            when grid_limit_kw < 0 then 'NEGATIVE_GRID_LIMIT'
            when operating_status not in ('NORMAL', 'CURTAILED_BY_ERCOT', 'CURTAILED_BY_CAISO', 'CURTAILED_BY_PJM', 'NIGHT_REST') then 'UNKNOWN_STATUS'
            when telemetry_quality <> 'VALID' then telemetry_quality
            else null
        end as validation_error_code
    from src
)

select *
from validated
where validation_error_code is not null
