from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


PLATFORM_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLATFORM_ROOT.parent
RAG_ROOT = REPO_ROOT / "rag"

PDF_DIR = RAG_ROOT / "legal_assets" / "pdf"
TEXT_DIR = RAG_ROOT / "legal_assets" / "text"
REFERENCE_DIR = PLATFORM_ROOT / "reference_data"

for path in [PDF_DIR, TEXT_DIR, REFERENCE_DIR]:
    path.mkdir(parents=True, exist_ok=True)


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
        "seller_name": "VoltSentinel Renewables Wind Holdings LLC",
        "contract_rate_usd_per_mwh": 42.50,
        "notice_id": "ERCOT-CN-2026-0623-001",
        "statement_id": "ERCOT-STMT-2026-0623-WILDORADO",
        "curtailment_reason": "CONGESTION",
        "constraint_name": "WEST_EXPORT_LIMIT_345KV",
        "start_time_utc": "2026-06-23T19:20:00Z",
        "end_time_utc": "2026-06-23T19:55:00Z",
        "expected_available_mw": 72.4,
        "actual_output_mw": 42.1,
        "curtailed_mwh": 17.675,
        "eligible_compensable_mwh": 17.675,
        "estimated_leakage_revenue_usd": 751.19,
        "market_price_usd_per_mwh": 29.84,
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
        "seller_name": "VoltSentinel Solar Daggett LLC",
        "contract_rate_usd_per_mwh": 38.75,
        "notice_id": "CAISO-CN-2026-0623-014",
        "statement_id": "CAISO-STMT-2026-0623-DAGGETT",
        "curtailment_reason": "TRANSMISSION_CONSTRAINT",
        "constraint_name": "SP15_IMPORT_CONSTRAINT",
        "start_time_utc": "2026-06-23T20:05:00Z",
        "end_time_utc": "2026-06-23T20:40:00Z",
        "expected_available_mw": 64.8,
        "actual_output_mw": 40.6,
        "curtailed_mwh": 14.117,
        "eligible_compensable_mwh": 14.117,
        "estimated_leakage_revenue_usd": 547.03,
        "market_price_usd_per_mwh": 31.22,
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
        "seller_name": "VoltSentinel Solar Blackdust LLC",
        "contract_rate_usd_per_mwh": 45.00,
        "notice_id": "ERCOT-CN-2026-0623-002",
        "statement_id": "ERCOT-STMT-2026-0623-BLACKDUST",
        "curtailment_reason": "CONGESTION",
        "constraint_name": "NORTH_HUB_EXPORT_LIMIT",
        "start_time_utc": "2026-06-23T21:10:00Z",
        "end_time_utc": "2026-06-23T21:35:00Z",
        "expected_available_mw": 38.2,
        "actual_output_mw": 28.4,
        "curtailed_mwh": 4.083,
        "eligible_compensable_mwh": 4.083,
        "estimated_leakage_revenue_usd": 183.74,
        "market_price_usd_per_mwh": 27.91,
    },
]


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Small",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
    )
)
styles.add(
    ParagraphStyle(
        name="Clause",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        spaceAfter=6,
    )
)


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.65 * inch, 0.45 * inch, "SYNTHETIC DOCUMENT — VoltSentinel POC — Not a real contract, invoice, or ISO record")
    canvas.drawRightString(7.85 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def write_pdf(path: Path, title: str, subtitle: str, sections: list[tuple[str, list[str] | list[list[str]]]]):
    doc = SimpleDocTemplate(
        str(path),
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    story = []
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(subtitle, styles["Heading3"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("SYNTHETIC SAMPLE FOR DEMONSTRATION ONLY", styles["Heading2"]))
    story.append(Paragraph("This document was generated for the VoltSentinel proof of concept. It is not a real contract, settlement statement, market notice, invoice, legal document, or operational instruction.", styles["Small"]))
    story.append(Spacer(1, 0.2 * inch))

    for heading, body in sections:
        story.append(Paragraph(heading, styles["Heading2"]))

        if body and isinstance(body[0], list):
            table = Table(body, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.15 * inch))
        else:
            for para in body:
                story.append(Paragraph(para, styles["Clause"]))
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)


def write_text(path: Path, title: str, sections: list[tuple[str, list[str] | list[list[str]]]]):
    lines = [title, "SYNTHETIC SAMPLE FOR DEMONSTRATION ONLY", ""]
    for heading, body in sections:
        lines.append(heading)
        lines.append("-" * len(heading))
        if body and isinstance(body[0], list):
            for row in body:
                lines.append(" | ".join(str(x) for x in row))
        else:
            for para in body:
                lines.append(para)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def ppa_sections(asset: dict) -> list[tuple[str, list[str] | list[list[str]]]]:
    return [
        ("1. Agreement Summary", [
            f"This Synthetic Power Purchase Agreement is entered into between {asset['seller_name']} as Seller and {asset['offtaker_name']} as Buyer.",
            f"Contract ID: {asset['contract_id']}. Facility: {asset['asset_name']} ({asset['asset_id']}). ISO Region: {asset['iso_region']}. Settlement Point: {asset['settlement_point']}.",
            "This Agreement is created solely for testing document parsing, retrieval-augmented generation, and revenue leakage workflow automation.",
        ]),
        ("2. Facility and Delivery", [
            f"Seller shall deliver energy generated by the {asset['asset_type']} facility to the agreed Point of Delivery and shall maintain operational data sufficient to support settlement, metering, and curtailment verification.",
            "The Facility shall provide interval telemetry, metered generation, expected available output, and operating status information at five-minute or finer granularity where available.",
        ]),
        ("3. Contract Price", [
            f"Buyer shall pay Seller for delivered Contract Energy at a fixed contract rate of ${asset['contract_rate_usd_per_mwh']:.2f} per MWh, subject to the terms and exclusions in this Agreement.",
            "The contract price is used by the commercial settlement system as the authoritative rate for estimating compensable curtailment value. The language in this document supports explanation; it is not the computational source of truth.",
        ]),
        ("4. Compensable Curtailment", [
            "A Compensable Curtailment means a reduction in Facility output caused by an ISO, RTO, transmission provider, or Buyer instruction for congestion management, transmission constraint management, or similar grid reliability reasons, provided that the reduction is not caused by Seller fault, planned outage, equipment failure, Force Majeure, or failure to follow dispatch.",
            "For a Compensable Curtailment, the eligible MWh shall equal the positive difference between expected available MWh and actual delivered MWh during the affected interval, using SCADA, meter, ISO notice, and settlement evidence.",
            f"For this contract, congestion and transmission-constraint curtailments are compensable. Negative-price economic curtailments are not compensable unless separately approved in writing. Contract ID: {asset['contract_id']}.",
        ]),
        ("5. Non-Compensable Curtailment", [
            "A Non-Compensable Curtailment includes curtailment caused by Seller equipment outage, Seller failure to follow dispatch, insufficient permits, Force Majeure, emergency conditions, negative price economic dispatch, or any outage not caused by Buyer, ISO, RTO, or transmission provider action.",
            "Seller is not entitled to payment for Non-Compensable Curtailment unless Buyer later determines through dispute resolution that the event was misclassified.",
        ]),
        ("6. Lost Production Evidence", [
            "Seller shall provide supporting documentation for any compensable curtailment claim, including: ISO notice or dispatch instruction, five-minute SCADA intervals, expected available output, actual delivered output, metering data, settlement statement details, and calculation support.",
            "Expected available output shall be based on best available telemetry and resource conditions during the affected interval. Actual delivered output shall be measured at or adjusted to the Point of Delivery.",
        ]),
        ("7. Billing, Dispute, and Approval", [
            "Claims for compensable curtailment shall be reviewed as part of the monthly settlement process. Either Party may dispute settlement values by providing a written explanation and supporting documentation.",
            "No external dispute case, invoice adjustment, or CRM workflow may be submitted without human commercial approval. Automated systems may prepare evidence packages but may not approve claims independently.",
        ]),
    ]


def notice_sections(asset: dict) -> list[tuple[str, list[str] | list[list[str]]]]:
    table = [
        ["Field", "Value"],
        ["Notice ID", asset["notice_id"]],
        ["ISO", asset["iso"]],
        ["Resource ID", asset["resource_id"]],
        ["Asset ID", asset["asset_id"]],
        ["Settlement Point", asset["settlement_point"]],
        ["Issue Time UTC", "2026-06-23T19:15:00Z"],
        ["Start Time UTC", asset["start_time_utc"]],
        ["End Time UTC", asset["end_time_utc"]],
        ["Curtailment Reason", asset["curtailment_reason"]],
        ["Constraint", asset["constraint_name"]],
        ["Expected Available MW", str(asset["expected_available_mw"])],
        ["Actual Output MW", str(asset["actual_output_mw"])],
        ["Estimated Curtailed MWh", str(asset["curtailed_mwh"])],
    ]

    return [
        ("1. Operational Curtailment Notice", [
            f"{asset['iso']} issues this synthetic operational notice for {asset['resource_id']} at settlement point {asset['settlement_point']}.",
            "The instruction reflects a grid or market operating condition and is provided as evidence for operational reconciliation. This synthetic notice is not an actual ISO notice.",
        ]),
        ("2. Notice Details", table),
        ("3. Operator Notes", [
            f"Resource output was limited due to {asset['constraint_name']}. The resource was instructed to reduce output for the stated operating interval.",
            "This notice should be reconciled against SCADA telemetry, settlement statements, and applicable contract provisions before any commercial dispute is created.",
        ]),
    ]


def settlement_sections(asset: dict) -> list[tuple[str, list[str] | list[list[str]]]]:
    gross_value = round(asset["eligible_compensable_mwh"] * asset["contract_rate_usd_per_mwh"], 2)

    table = [
        ["Charge Code", "Description", "MWh", "Rate / Price", "Amount"],
        [
            "MTR_ENERGY",
            "Metered energy settlement quantity",
            str(round(asset["actual_output_mw"] * 0.5, 3)),
            f"${asset['market_price_usd_per_mwh']:.2f}/MWh",
            f"${round(asset['actual_output_mw'] * 0.5 * asset['market_price_usd_per_mwh'], 2):.2f}",
        ],
        [
            "CURT_SHORTFALL",
            "Potential compensable curtailment shortfall",
            str(asset["eligible_compensable_mwh"]),
            f"${asset['contract_rate_usd_per_mwh']:.2f}/MWh",
            f"${gross_value:.2f}",
        ],
        [
            "DISPUTE_HOLD",
            "Amount pending commercial review",
            str(asset["eligible_compensable_mwh"]),
            "N/A",
            f"${asset['estimated_leakage_revenue_usd']:.2f}",
        ],
    ]

    return [
        ("1. Settlement Statement Summary", [
            f"Statement ID: {asset['statement_id']}. Market: {asset['iso']}. Resource: {asset['resource_id']}. Settlement point: {asset['settlement_point']}.",
            "This synthetic settlement statement summarizes interval settlement values and a potential revenue leakage item detected by VoltSentinel.",
        ]),
        ("2. Settlement Line Items", table),
        ("3. Reconciliation Notes", [
            "The CURT_SHORTFALL line is not an approved invoice adjustment. It represents a potential claim requiring contract review, data quality validation, and human approval.",
            f"Related Contract ID: {asset['contract_id']}. Related Notice ID: {asset['notice_id']}. Related Asset ID: {asset['asset_id']}.",
        ]),
    ]


def safe_file_fragment(value: str) -> str:
    return value.lower().replace("ppa-", "").replace("_", "-").replace(" ", "-").replace(".", "").replace("/", "-")


def generate_documents():
    manifest_rows = []

    for asset in ASSETS:
        contract_fragment = safe_file_fragment(asset["contract_id"])

        # PPA
        ppa_title = f"Synthetic Power Purchase Agreement — {asset['asset_name']}"
        ppa_pdf = PDF_DIR / f"synthetic_{contract_fragment}_ppa.pdf"
        ppa_txt = TEXT_DIR / f"synthetic_{contract_fragment}_ppa.txt"
        ppa_sections_data = ppa_sections(asset)
        write_pdf(ppa_pdf, ppa_title, asset["contract_id"], ppa_sections_data)
        write_text(ppa_txt, ppa_title, ppa_sections_data)

        manifest_rows.append({
            "document_id": f"DOC-{asset['contract_id']}",
            "document_type": "PPA",
            "contract_id": asset["contract_id"],
            "asset_id": asset["asset_id"],
            "pdf_path": str(ppa_pdf.relative_to(REPO_ROOT)),
            "text_path": str(ppa_txt.relative_to(REPO_ROOT)),
        })

        # ISO notice
        notice_title = f"Synthetic {asset['iso']} Curtailment Notice — {asset['asset_name']}"
        notice_pdf = PDF_DIR / f"synthetic_{asset['iso'].lower()}_curtailment_notice_{safe_file_fragment(asset['asset_name'])}.pdf"
        notice_txt = TEXT_DIR / f"synthetic_{asset['iso'].lower()}_curtailment_notice_{safe_file_fragment(asset['asset_name'])}.txt"
        notice_sections_data = notice_sections(asset)
        write_pdf(notice_pdf, notice_title, asset["notice_id"], notice_sections_data)
        write_text(notice_txt, notice_title, notice_sections_data)

        manifest_rows.append({
            "document_id": f"DOC-{asset['notice_id']}",
            "document_type": "ISO_CURTAILMENT_NOTICE",
            "contract_id": asset["contract_id"],
            "asset_id": asset["asset_id"],
            "pdf_path": str(notice_pdf.relative_to(REPO_ROOT)),
            "text_path": str(notice_txt.relative_to(REPO_ROOT)),
        })

        # ISO settlement
        settlement_title = f"Synthetic {asset['iso']} Settlement Statement — {asset['asset_name']}"
        settlement_pdf = PDF_DIR / f"synthetic_{asset['iso'].lower()}_settlement_statement_{safe_file_fragment(asset['asset_name'])}.pdf"
        settlement_txt = TEXT_DIR / f"synthetic_{asset['iso'].lower()}_settlement_statement_{safe_file_fragment(asset['asset_name'])}.txt"
        settlement_sections_data = settlement_sections(asset)
        write_pdf(settlement_pdf, settlement_title, asset["statement_id"], settlement_sections_data)
        write_text(settlement_txt, settlement_title, settlement_sections_data)

        manifest_rows.append({
            "document_id": f"DOC-{asset['statement_id']}",
            "document_type": "ISO_SETTLEMENT_STATEMENT",
            "contract_id": asset["contract_id"],
            "asset_id": asset["asset_id"],
            "pdf_path": str(settlement_pdf.relative_to(REPO_ROOT)),
            "text_path": str(settlement_txt.relative_to(REPO_ROOT)),
        })

    # Structured reference data
    with (REFERENCE_DIR / "asset_contract_mapping.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "asset_id",
                "asset_name",
                "asset_type",
                "iso",
                "iso_region",
                "settlement_point",
                "resource_id",
                "contract_id",
                "offtaker_name",
                "contract_rate_usd_per_mwh",
                "congestion_curtailment_compensable",
                "transmission_constraint_compensable",
                "negative_price_curtailment_compensable",
            ],
        )
        writer.writeheader()
        for asset in ASSETS:
            writer.writerow({
                "asset_id": asset["asset_id"],
                "asset_name": asset["asset_name"],
                "asset_type": asset["asset_type"],
                "iso": asset["iso"],
                "iso_region": asset["iso_region"],
                "settlement_point": asset["settlement_point"],
                "resource_id": asset["resource_id"],
                "contract_id": asset["contract_id"],
                "offtaker_name": asset["offtaker_name"],
                "contract_rate_usd_per_mwh": asset["contract_rate_usd_per_mwh"],
                "congestion_curtailment_compensable": True,
                "transmission_constraint_compensable": True,
                "negative_price_curtailment_compensable": False,
            })

    with (REFERENCE_DIR / "iso_curtailment_notices.json").open("w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "notice_id": asset["notice_id"],
                    "iso": asset["iso"],
                    "asset_id": asset["asset_id"],
                    "resource_id": asset["resource_id"],
                    "settlement_point": asset["settlement_point"],
                    "curtailment_reason": asset["curtailment_reason"],
                    "constraint_name": asset["constraint_name"],
                    "start_time_utc": asset["start_time_utc"],
                    "end_time_utc": asset["end_time_utc"],
                    "expected_available_mw": asset["expected_available_mw"],
                    "actual_output_mw": asset["actual_output_mw"],
                    "curtailed_mwh": asset["curtailed_mwh"],
                    "related_contract_id": asset["contract_id"],
                }
                for asset in ASSETS
            ],
            f,
            indent=2,
        )

    with (REFERENCE_DIR / "iso_settlement_statement_rows.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "statement_id",
                "iso",
                "market_date",
                "asset_id",
                "resource_id",
                "settlement_point",
                "contract_id",
                "charge_code",
                "eligible_compensable_mwh",
                "market_price_usd_per_mwh",
                "contract_rate_usd_per_mwh",
                "estimated_leakage_revenue_usd",
            ],
        )
        writer.writeheader()
        for asset in ASSETS:
            writer.writerow({
                "statement_id": asset["statement_id"],
                "iso": asset["iso"],
                "market_date": "2026-06-23",
                "asset_id": asset["asset_id"],
                "resource_id": asset["resource_id"],
                "settlement_point": asset["settlement_point"],
                "contract_id": asset["contract_id"],
                "charge_code": "CURT_SHORTFALL",
                "eligible_compensable_mwh": asset["eligible_compensable_mwh"],
                "market_price_usd_per_mwh": asset["market_price_usd_per_mwh"],
                "contract_rate_usd_per_mwh": asset["contract_rate_usd_per_mwh"],
                "estimated_leakage_revenue_usd": asset["estimated_leakage_revenue_usd"],
            })

    with (REFERENCE_DIR / "document_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["document_id", "document_type", "contract_id", "asset_id", "pdf_path", "text_path"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print("Synthetic documents generated.")
    print(f"PDF directory: {PDF_DIR}")
    print(f"Text directory: {TEXT_DIR}")
    print(f"Reference data directory: {REFERENCE_DIR}")


if __name__ == "__main__":
    generate_documents()
