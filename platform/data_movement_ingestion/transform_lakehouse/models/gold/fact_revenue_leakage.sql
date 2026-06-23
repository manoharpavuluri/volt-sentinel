{{ config(
    materialized='incremental',
    unique_key='fact_record_hash',
    incremental_strategy='merge'
) }}

/*
Design fix:
- Converts 10-second kW samples to MWh correctly.
- Uses expected_available_kw/grid_limit_kw as the curtailment baseline.
- Applies PPA compensability rules.
- Compares expected settlement to actual settlement records.
*/

with telemetry_hourly as (
    select
        reconciliation_hour_utc,
        asset_id,
        max(case when operating_status like 'CURTAILED_BY_%' then operating_status else null end) as curtailment_status,
        count(*) as sample_count,

        -- Each sample represents a 10-second interval. kW * seconds / 3600 = kWh; /1000 = MWh.
        sum(measured_generation_kw * 10.0 / 3600.0) / 1000.0 as actual_generation_mwh,
        sum(expected_available_kw * 10.0 / 3600.0) / 1000.0 as expected_available_mwh,
        sum(grid_limit_kw * 10.0 / 3600.0) / 1000.0 as grid_limited_mwh
    from {{ ref('silver_clearway_telemetry') }}
    {% if is_incremental() %}
    where reconciliation_hour_utc >= current_timestamp() - interval 72 hours
    {% endif %}
    group by 1, 2
),

sap_assets as (
    select
        asset_id,
        equip_name,
        asset_type,
        rated_capacity_mw,
        iso_region
    from {{ source('clearway_sap', 'asset_registry') }}
),

sf_ppas as (
    select
        account_id,
        oftaker_name,
        associated_ppa_id,
        site_identity_tag,
        cast(contract_rate_per_mwh as double) as contract_rate_per_mwh,
        curtailment_compensable_flag,
        settlement_method
    from {{ source('clearway_salesforce', 'ppa_mapping') }}
),

curtailment_events as (
    select
        curtailment_event_id,
        asset_id,
        to_timestamp(reconciliation_hour_utc, 'yyyy-MM-dd HH:mm:ss') as reconciliation_hour_utc,
        iso_region,
        curtailment_reason,
        cast(iso_limit_mw as double) as iso_limit_mw
    from {{ source('iso_market', 'curtailment_events') }}
),

actual_settlements as (
    select
        asset_id,
        associated_ppa_id,
        to_timestamp(reconciliation_hour_utc, 'yyyy-MM-dd HH:mm:ss') as reconciliation_hour_utc,
        cast(actual_settlement_usd as double) as actual_settlement_usd
    from {{ source('iso_market', 'market_settlements') }}
),

joined as (
    select
        t.reconciliation_hour_utc,
        t.asset_id,
        sap.equip_name,
        sap.asset_type,
        sap.iso_region,
        sf.account_id,
        sf.oftaker_name,
        sf.associated_ppa_id,
        sf.contract_rate_per_mwh,
        sf.curtailment_compensable_flag,
        sf.settlement_method,
        ce.curtailment_event_id,
        ce.curtailment_reason,
        t.sample_count,
        t.actual_generation_mwh,
        t.expected_available_mwh,
        t.grid_limited_mwh,
        greatest(t.expected_available_mwh - t.actual_generation_mwh, 0.0) as physical_shortfall_mwh,
        case
            when ce.curtailment_event_id is not null then greatest(t.expected_available_mwh - t.grid_limited_mwh, 0.0)
            else 0.0
        end as grid_curtailment_mwh,
        coalesce(s.actual_settlement_usd, 0.0) as actual_settlement_usd
    from telemetry_hourly t
    inner join sap_assets sap
        on t.asset_id = sap.asset_id
    inner join sf_ppas sf
        on t.asset_id = sf.site_identity_tag
    left join curtailment_events ce
        on t.asset_id = ce.asset_id
       and t.reconciliation_hour_utc = ce.reconciliation_hour_utc
    left join actual_settlements s
        on t.asset_id = s.asset_id
       and sf.associated_ppa_id = s.associated_ppa_id
       and t.reconciliation_hour_utc = s.reconciliation_hour_utc
)

select
    sha2(concat_ws('|', cast(reconciliation_hour_utc as string), asset_id, associated_ppa_id), 256) as fact_record_hash,
    reconciliation_hour_utc,
    asset_id,
    equip_name,
    asset_type,
    iso_region,
    account_id,
    oftaker_name,
    associated_ppa_id,
    contract_rate_per_mwh,
    curtailment_compensable_flag,
    settlement_method,
    curtailment_event_id,
    curtailment_reason,
    sample_count,
    actual_generation_mwh,
    expected_available_mwh,
    grid_limited_mwh,
    physical_shortfall_mwh,
    grid_curtailment_mwh,
    case
        when curtailment_compensable_flag = 'Y'
         and curtailment_event_id is not null
        then grid_curtailment_mwh
        else 0.0
    end as eligible_compensable_mwh,
    case
        when curtailment_compensable_flag = 'Y'
         and curtailment_event_id is not null
        then grid_curtailment_mwh * contract_rate_per_mwh
        else 0.0
    end as expected_settlement_usd,
    actual_settlement_usd,
    greatest(
        case
            when curtailment_compensable_flag = 'Y'
             and curtailment_event_id is not null
            then grid_curtailment_mwh * contract_rate_per_mwh
            else 0.0
        end - actual_settlement_usd,
        0.0
    ) as estimated_leakage_revenue_usd,
    current_timestamp() as gold_calculated_at
from joined
