from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone


PLATFORM_ROOT = Path(__file__).resolve().parents[1]

SAP_DIR = PLATFORM_ROOT / "reference_data" / "enterprise" / "sap"
SF_DIR = PLATFORM_ROOT / "reference_data" / "enterprise" / "salesforce"

SAP_DIR.mkdir(parents=True, exist_ok=True)
SF_DIR.mkdir(parents=True, exist_ok=True)


ASSETS = [
    {
        "asset_id": "CW_WIND_WILDORADO",
        "asset_name": "Wildorado Wind",
        "asset_type": "WIND",
        "iso": "ERCOT",
        "iso_region": "ERCOT_WEST",
        "settlement_point": "WILDORADO_RN",
        "resource_id": "WILDORADO_WIND_RN01",
        "contract_id": "PPA-WILDORADO-GOOGLE-001",
        "offtaker_name": "Google Energy LLC",
        "contract_rate_usd_per_mwh": 42.50,
        "contract_start_date": "2025-01-01",
        "contract_end_date": "2035-12-31",
        "sap_asset_id": "SAP-AST-100001",
        "sap_customer_number": "CUST-300001",
        "sf_account_id": "001VS000000GOOG",
        "sf_contract_id": "800VS000000WILD",
        "sf_asset_id": "02iVS000000WILD",
        "company_code": "VS01",
        "plant_code": "PL-WILD",
        "profit_center": "PC-WIND-TX",
        "cost_center": "CC-WILD-OPS",
        "invoice_id": "INV-202606-WILD-001",
        "accounting_doc_id": "SAP-GL-2026-900001",
        "market_date": "2026-06-23",
        "metered_mwh": 2190.35,
        "invoiced_mwh": 2168.00,
        "invoice_amount_usd": 92140.00,
        "open_amount_usd": 0.00,
        "payment_status": "PAID",
        "prior_dispute_status": "Closed - Paid",
        "existing_open_dispute": False,
    },
    {
        "asset_id": "CW_SOLAR_DAGGETT",
        "asset_name": "Daggett Solar",
        "asset_type": "SOLAR",
        "iso": "CAISO",
        "iso_region": "CAISO_SP15",
        "settlement_point": "DAGGETT_6_N001",
        "resource_id": "DAGGETT_SOLAR_01",
        "contract_id": "PPA-DAGGETT-UTILITY-001",
        "offtaker_name": "California Utility Offtaker",
        "contract_rate_usd_per_mwh": 38.75,
        "contract_start_date": "2024-07-01",
        "contract_end_date": "2034-06-30",
        "sap_asset_id": "SAP-AST-100002",
        "sap_customer_number": "CUST-300002",
        "sf_account_id": "001VS000000CAUT",
        "sf_contract_id": "800VS000000DAGG",
        "sf_asset_id": "02iVS000000DAGG",
        "company_code": "VS01",
        "plant_code": "PL-DAGG",
        "profit_center": "PC-SOLAR-CA",
        "cost_center": "CC-DAGG-OPS",
        "invoice_id": "INV-202606-DAGG-001",
        "accounting_doc_id": "SAP-GL-2026-900002",
        "market_date": "2026-06-23",
        "metered_mwh": 1840.75,
        "invoiced_mwh": 1826.60,
        "invoice_amount_usd": 70780.75,
        "open_amount_usd": 70780.75,
        "payment_status": "OPEN",
        "prior_dispute_status": "None",
        "existing_open_dispute": False,
    },
    {
        "asset_id": "CW_SOLAR_BLACKDUST",
        "asset_name": "Blackdust Solar",
        "asset_type": "SOLAR",
        "iso": "ERCOT",
        "iso_region": "ERCOT_NORTH",
        "settlement_point": "BLACKDUST_RN",
        "resource_id": "BLACKDUST_SOLAR_RN01",
        "contract_id": "PPA-BLACKDUST-CORP-001",
        "offtaker_name": "Corporate Renewable Buyer",
        "contract_rate_usd_per_mwh": 45.00,
        "contract_start_date": "2025-04-01",
        "contract_end_date": "2032-03-31",
        "sap_asset_id": "SAP-AST-100003",
        "sap_customer_number": "CUST-300003",
        "sf_account_id": "001VS000000CORP",
        "sf_contract_id": "800VS000000BLKD",
        "sf_asset_id": "02iVS000000BLKD",
        "company_code": "VS01",
        "plant_code": "PL-BLKD",
        "profit_center": "PC-SOLAR-TX",
        "cost_center": "CC-BLKD-OPS",
        "invoice_id": "INV-202606-BLKD-001",
        "accounting_doc_id": "SAP-GL-2026-900003",
        "market_date": "2026-06-23",
        "metered_mwh": 1288.50,
        "invoiced_mwh": 1284.90,
        "invoice_amount_usd": 57820.50,
        "open_amount_usd": 15000.00,
        "payment_status": "PARTIALLY_PAID",
        "prior_dispute_status": "In Review",
        "existing_open_dispute": True,
    },
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_sap_sources():
    asset_master_rows = []
    business_partner_rows = []
    invoice_header_rows = []
    invoice_line_rows = []
    gl_posting_rows = []
    ar_open_item_rows = []

    for asset in ASSETS:
        asset_master_rows.append({
            "sap_asset_id": asset["sap_asset_id"],
            "asset_id": asset["asset_id"],
            "asset_name": asset["asset_name"],
            "asset_type": asset["asset_type"],
            "company_code": asset["company_code"],
            "plant_code": asset["plant_code"],
            "profit_center": asset["profit_center"],
            "cost_center": asset["cost_center"],
            "asset_class": "RENEWABLE_GENERATION",
            "capitalization_date": "2024-12-31",
            "in_service_date": asset["contract_start_date"],
            "asset_status": "ACTIVE",
            "currency": "USD",
        })

        business_partner_rows.append({
            "sap_customer_number": asset["sap_customer_number"],
            "business_partner_name": asset["offtaker_name"],
            "sf_account_id": asset["sf_account_id"],
            "payment_terms": "NET_30",
            "currency": "USD",
            "credit_status": "APPROVED",
            "customer_group": "ENERGY_OFFTAKER",
            "country": "US",
        })

        invoice_header_rows.append({
            "invoice_id": asset["invoice_id"],
            "sap_customer_number": asset["sap_customer_number"],
            "offtaker_name": asset["offtaker_name"],
            "contract_id": asset["contract_id"],
            "company_code": asset["company_code"],
            "invoice_period_start": "2026-06-01",
            "invoice_period_end": "2026-06-30",
            "invoice_date": "2026-07-03",
            "due_date": "2026-08-02",
            "invoice_status": asset["payment_status"],
            "currency": "USD",
            "gross_amount_usd": f"{asset['invoice_amount_usd']:.2f}",
            "paid_amount_usd": f"{asset['invoice_amount_usd'] - asset['open_amount_usd']:.2f}",
            "open_amount_usd": f"{asset['open_amount_usd']:.2f}",
        })

        invoice_line_rows.append({
            "invoice_line_id": f"{asset['invoice_id']}-001",
            "invoice_id": asset["invoice_id"],
            "asset_id": asset["asset_id"],
            "sap_asset_id": asset["sap_asset_id"],
            "contract_id": asset["contract_id"],
            "settlement_point": asset["settlement_point"],
            "charge_type": "CONTRACT_ENERGY",
            "billing_quantity_mwh": f"{asset['invoiced_mwh']:.3f}",
            "contract_rate_usd_per_mwh": f"{asset['contract_rate_usd_per_mwh']:.2f}",
            "line_amount_usd": f"{asset['invoice_amount_usd']:.2f}",
            "revenue_recognized_flag": "true",
            "source_system": "SAP_MOCK",
        })

        gl_posting_rows.append({
            "accounting_doc_id": asset["accounting_doc_id"],
            "company_code": asset["company_code"],
            "fiscal_year": "2026",
            "posting_date": "2026-07-03",
            "gl_account": "400100",
            "gl_account_description": "Renewable Energy Revenue",
            "profit_center": asset["profit_center"],
            "cost_center": asset["cost_center"],
            "asset_id": asset["asset_id"],
            "contract_id": asset["contract_id"],
            "invoice_id": asset["invoice_id"],
            "debit_credit": "CREDIT",
            "amount_usd": f"{asset['invoice_amount_usd']:.2f}",
            "posting_type": "REVENUE_RECOGNITION",
        })

        ar_open_item_rows.append({
            "open_item_id": f"AR-{asset['invoice_id']}",
            "invoice_id": asset["invoice_id"],
            "sap_customer_number": asset["sap_customer_number"],
            "contract_id": asset["contract_id"],
            "asset_id": asset["asset_id"],
            "due_date": "2026-08-02",
            "payment_status": asset["payment_status"],
            "open_amount_usd": f"{asset['open_amount_usd']:.2f}",
            "days_past_due": "0",
            "collections_status": "NORMAL" if asset["open_amount_usd"] == 0 else "MONITOR",
        })

    write_csv(
        SAP_DIR / "sap_asset_master.csv",
        [
            "sap_asset_id",
            "asset_id",
            "asset_name",
            "asset_type",
            "company_code",
            "plant_code",
            "profit_center",
            "cost_center",
            "asset_class",
            "capitalization_date",
            "in_service_date",
            "asset_status",
            "currency",
        ],
        asset_master_rows,
    )

    write_csv(
        SAP_DIR / "sap_business_partners.csv",
        [
            "sap_customer_number",
            "business_partner_name",
            "sf_account_id",
            "payment_terms",
            "currency",
            "credit_status",
            "customer_group",
            "country",
        ],
        business_partner_rows,
    )

    write_csv(
        SAP_DIR / "sap_power_invoice_headers.csv",
        [
            "invoice_id",
            "sap_customer_number",
            "offtaker_name",
            "contract_id",
            "company_code",
            "invoice_period_start",
            "invoice_period_end",
            "invoice_date",
            "due_date",
            "invoice_status",
            "currency",
            "gross_amount_usd",
            "paid_amount_usd",
            "open_amount_usd",
        ],
        invoice_header_rows,
    )

    write_csv(
        SAP_DIR / "sap_power_invoice_lines.csv",
        [
            "invoice_line_id",
            "invoice_id",
            "asset_id",
            "sap_asset_id",
            "contract_id",
            "settlement_point",
            "charge_type",
            "billing_quantity_mwh",
            "contract_rate_usd_per_mwh",
            "line_amount_usd",
            "revenue_recognized_flag",
            "source_system",
        ],
        invoice_line_rows,
    )

    write_csv(
        SAP_DIR / "sap_gl_postings.csv",
        [
            "accounting_doc_id",
            "company_code",
            "fiscal_year",
            "posting_date",
            "gl_account",
            "gl_account_description",
            "profit_center",
            "cost_center",
            "asset_id",
            "contract_id",
            "invoice_id",
            "debit_credit",
            "amount_usd",
            "posting_type",
        ],
        gl_posting_rows,
    )

    write_csv(
        SAP_DIR / "sap_ar_open_items.csv",
        [
            "open_item_id",
            "invoice_id",
            "sap_customer_number",
            "contract_id",
            "asset_id",
            "due_date",
            "payment_status",
            "open_amount_usd",
            "days_past_due",
            "collections_status",
        ],
        ar_open_item_rows,
    )


def generate_salesforce_sources():
    account_rows = []
    contract_rows = []
    asset_rows = []
    dispute_rows = []

    for asset in ASSETS:
        account_rows.append({
            "sf_account_id": asset["sf_account_id"],
            "account_name": asset["offtaker_name"],
            "account_type": "Customer",
            "industry": "Energy",
            "sap_customer_number": asset["sap_customer_number"],
            "commercial_owner": "Alex Morgan",
            "account_status": "Active",
            "risk_tier": "Standard",
        })

        contract_rows.append({
            "sf_contract_id": asset["sf_contract_id"],
            "contract_id": asset["contract_id"],
            "sf_account_id": asset["sf_account_id"],
            "asset_id": asset["asset_id"],
            "contract_name": f"{asset['asset_name']} PPA",
            "contract_status": "Activated",
            "start_date": asset["contract_start_date"],
            "end_date": asset["contract_end_date"],
            "contract_rate_usd_per_mwh": f"{asset['contract_rate_usd_per_mwh']:.2f}",
            "governing_iso": asset["iso"],
            "ppa_document_id": f"DOC-{asset['contract_id']}",
        })

        asset_rows.append({
            "sf_asset_id": asset["sf_asset_id"],
            "sf_account_id": asset["sf_account_id"],
            "sf_contract_id": asset["sf_contract_id"],
            "asset_id": asset["asset_id"],
            "asset_name": asset["asset_name"],
            "asset_type": asset["asset_type"],
            "iso_region": asset["iso_region"],
            "settlement_point": asset["settlement_point"],
            "operations_owner": "Operations Control Center",
            "asset_status": "Operating",
        })

    # A closed historical dispute for Wildorado
    dispute_rows.append({
        "sf_dispute_id": "500VS0000001001",
        "dispute_number": "RD-0001001",
        "sf_account_id": "001VS000000GOOG",
        "sf_contract_id": "800VS000000WILD",
        "asset_id": "CW_WIND_WILDORADO",
        "contract_id": "PPA-WILDORADO-GOOGLE-001",
        "market_date": "2026-05-14",
        "dispute_type": "Revenue Leakage",
        "status": "Closed - Paid",
        "estimated_dispute_amount_usd": "486.25",
        "approved_amount_usd": "486.25",
        "owner": "Alex Morgan",
        "created_date": "2026-05-17",
        "closed_date": "2026-05-28",
        "source_system": "Salesforce_MOCK",
    })

    # An existing open dispute for Blackdust to test duplicate prevention
    dispute_rows.append({
        "sf_dispute_id": "500VS0000001002",
        "dispute_number": "RD-0001002",
        "sf_account_id": "001VS000000CORP",
        "sf_contract_id": "800VS000000BLKD",
        "asset_id": "CW_SOLAR_BLACKDUST",
        "contract_id": "PPA-BLACKDUST-CORP-001",
        "market_date": "2026-06-23",
        "dispute_type": "Revenue Leakage",
        "status": "In Review",
        "estimated_dispute_amount_usd": "183.74",
        "approved_amount_usd": "0.00",
        "owner": "Alex Morgan",
        "created_date": "2026-06-24",
        "closed_date": "",
        "source_system": "Salesforce_MOCK",
    })

    write_csv(
        SF_DIR / "sf_accounts.csv",
        [
            "sf_account_id",
            "account_name",
            "account_type",
            "industry",
            "sap_customer_number",
            "commercial_owner",
            "account_status",
            "risk_tier",
        ],
        account_rows,
    )

    write_csv(
        SF_DIR / "sf_contracts.csv",
        [
            "sf_contract_id",
            "contract_id",
            "sf_account_id",
            "asset_id",
            "contract_name",
            "contract_status",
            "start_date",
            "end_date",
            "contract_rate_usd_per_mwh",
            "governing_iso",
            "ppa_document_id",
        ],
        contract_rows,
    )

    write_csv(
        SF_DIR / "sf_assets.csv",
        [
            "sf_asset_id",
            "sf_account_id",
            "sf_contract_id",
            "asset_id",
            "asset_name",
            "asset_type",
            "iso_region",
            "settlement_point",
            "operations_owner",
            "asset_status",
        ],
        asset_rows,
    )

    write_csv(
        SF_DIR / "sf_revenue_disputes.csv",
        [
            "sf_dispute_id",
            "dispute_number",
            "sf_account_id",
            "sf_contract_id",
            "asset_id",
            "contract_id",
            "market_date",
            "dispute_type",
            "status",
            "estimated_dispute_amount_usd",
            "approved_amount_usd",
            "owner",
            "created_date",
            "closed_date",
            "source_system",
        ],
        dispute_rows,
    )


def generate_manifest():
    extract_timestamp = datetime.now(timezone.utc).isoformat()

    manifest = {
        "extract_id": "enterprise_mock_extract_20260623",
        "extract_timestamp_utc": extract_timestamp,
        "source_systems": [
            {
                "source_system": "SAP_MOCK",
                "description": "Synthetic SAP finance and accounting extracts for VoltSentinel POC",
                "landing_zone": "bronze/enterprise/sap/raw",
                "files": [
                    "sap_asset_master.csv",
                    "sap_business_partners.csv",
                    "sap_power_invoice_headers.csv",
                    "sap_power_invoice_lines.csv",
                    "sap_gl_postings.csv",
                    "sap_ar_open_items.csv",
                ],
            },
            {
                "source_system": "SALESFORCE_MOCK",
                "description": "Synthetic Salesforce commercial, contract, asset, and dispute extracts for VoltSentinel POC",
                "landing_zone": "bronze/enterprise/salesforce/raw",
                "files": [
                    "sf_accounts.csv",
                    "sf_contracts.csv",
                    "sf_assets.csv",
                    "sf_revenue_disputes.csv",
                ],
            },
        ],
    }

    with (PLATFORM_ROOT / "reference_data" / "enterprise" / "enterprise_source_manifest.json").open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(manifest, f, indent=2)


def main():
    generate_sap_sources()
    generate_salesforce_sources()
    generate_manifest()

    print("Synthetic enterprise sources generated.")
    print(f"SAP directory: {SAP_DIR}")
    print(f"Salesforce directory: {SF_DIR}")
    print(f"Manifest: {PLATFORM_ROOT / 'reference_data' / 'enterprise' / 'enterprise_source_manifest.json'}")


if __name__ == "__main__":
    main()
