"""
Generates local snapshot files for SAP asset master, Salesforce PPA mappings,
ISO curtailment instructions, and actual settlement records.

Design fix:
- Adds curtailment and settlement inputs so Gold leakage logic does not rely on nameplate capacity.
- Adds contract eligibility flags and settlement method fields.
"""

import csv
import os
from datetime import datetime, timedelta, timezone

BASE_PATH = "./local_landing_zone"
SAP_OUTPUT_PATH = f"{BASE_PATH}/clearway_sap"
SF_OUTPUT_PATH = f"{BASE_PATH}/clearway_salesforce"
ISO_OUTPUT_PATH = f"{BASE_PATH}/iso_market"

for path in [SAP_OUTPUT_PATH, SF_OUTPUT_PATH, ISO_OUTPUT_PATH]:
    os.makedirs(path, exist_ok=True)


def write_csv(path: str, headers: list[str], rows: list[list]) -> None:
    with open(path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def build_clearway_enterprise_snapshots() -> None:
    write_csv(
        os.path.join(SAP_OUTPUT_PATH, "CLEARWAY_ASSET_REGISTRY.csv"),
        ["ASSET_ID", "EQUIP_NAME", "ASSET_TYPE", "RATED_CAPACITY_MW", "ISO_REGION", "COMMERCIAL_ONLINE_DATE"],
        [
            ["CW_WIND_WILDORADO", "Wildorado Wind Ranch", "WIND", 161.0, "ERCOT", "2007-04-01"],
            ["CW_SOLAR_DAGGETT", "Daggett Solar Infrastructure", "SOLAR", 482.0, "CAISO", "2024-03-15"],
            ["CW_BESS_DAGGETT", "Daggett Battery Storage Block B", "STORAGE", 394.0, "CAISO", "2024-03-15"],
            ["CW_SOLAR_BLACKDUST", "Black Dust Solar Project", "SOLAR", 120.0, "PJM", "2026-06-01"],
        ],
    )

    write_csv(
        os.path.join(SF_OUTPUT_PATH, "CLEARWAY_PPA_ACCOUNT_MAPPING.csv"),
        [
            "ACCOUNT_ID",
            "OFTAKER_NAME",
            "ASSOCIATED_PPA_ID",
            "SITE_IDENTITY_TAG",
            "CONTRACT_RATE_PER_MWH",
            "CURTAILMENT_COMPENSABLE_FLAG",
            "SETTLEMENT_METHOD",
        ],
        [
            ["ACC_TECH_GOOG", "Google Cloud Operations LLC", "PPA_GOOG_WILDORADO_WIND", "CW_WIND_WILDORADO", 42.50, "Y", "FIXED_PPA_RATE"],
            ["ACC_UTIL_SCE", "Southern California Edison", "PPA_SCE_DAGGETT_SOLAR", "CW_SOLAR_DAGGETT", 38.00, "Y", "FIXED_PPA_RATE"],
            ["ACC_CORP_AMZN", "Amazon Web Services Energy Hub", "PPA_AMZN_BLACKDUST", "CW_SOLAR_BLACKDUST", 45.10, "N", "ENERGY_ONLY"],
        ],
    )

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    hours = [now - timedelta(hours=i) for i in range(24, 0, -1)]

    curtailment_rows = []
    settlement_rows = []
    for hr in hours:
        hr_str = hr.strftime("%Y-%m-%d %H:%M:%S")
        # Curtailed examples every 6 hours for demo reproducibility.
        if hr.hour % 6 == 0:
            curtailment_rows.append([f"CURT_ERCOT_{hr.strftime('%Y%m%d%H')}", "CW_WIND_WILDORADO", hr_str, "ERCOT", "GRID_CONGESTION", 95.0])
            settlement_rows.append(["CW_WIND_WILDORADO", "PPA_GOOG_WILDORADO_WIND", hr_str, 1800.00])
        if hr.hour % 8 == 0:
            curtailment_rows.append([f"CURT_CAISO_{hr.strftime('%Y%m%d%H')}", "CW_SOLAR_DAGGETT", hr_str, "CAISO", "TRANSMISSION_CONSTRAINT", 260.0])
            settlement_rows.append(["CW_SOLAR_DAGGETT", "PPA_SCE_DAGGETT_SOLAR", hr_str, 7600.00])

    write_csv(
        os.path.join(ISO_OUTPUT_PATH, "CLEARWAY_CURTAILMENT_EVENTS.csv"),
        ["CURTAILMENT_EVENT_ID", "ASSET_ID", "RECONCILIATION_HOUR_UTC", "ISO_REGION", "CURTAILMENT_REASON", "ISO_LIMIT_MW"],
        curtailment_rows,
    )

    write_csv(
        os.path.join(ISO_OUTPUT_PATH, "CLEARWAY_MARKET_SETTLEMENTS.csv"),
        ["ASSET_ID", "ASSOCIATED_PPA_ID", "RECONCILIATION_HOUR_UTC", "ACTUAL_SETTLEMENT_USD"],
        settlement_rows,
    )

    print("VoltSentinel local SAP, Salesforce, ISO curtailment, and settlement snapshots generated.")


if __name__ == "__main__":
    build_clearway_enterprise_snapshots()
