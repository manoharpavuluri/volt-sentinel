"""
VoltSentinel layout-aware PPA ingestion.

Purpose:
- Parse PPA PDF/text documents.
- Preserve contract/page/section metadata.
- Store parent document + child chunks in Postgres pgvector.

This version is intentionally conservative: it keeps RAG as evidence retrieval,
not a financial calculation engine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

import psycopg2
from openai import OpenAI
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


SECTION_HEADING_PATTERN = re.compile(
    r"^\s*((section|article|exhibit|schedule|appendix)\s+[\w\-.]+|\d+(\.\d+)*\s+)[\):.\-\s]+(.{3,120})$",
    re.IGNORECASE,
)

CLAUSE_KEYWORDS = {
    "curtailment": ["curtail", "curtailment", "dispatch down", "reduction", "limited by grid"],
    "settlement": ["settlement", "invoice", "payment", "true-up", "billing"],
    "price": ["price", "rate", "$", "mwh", "megawatt-hour"],
    "limitation": ["liability", "limit", "cap", "exclusion", "damages"],
    "notice": ["notice", "dispute", "claim", "cure", "days after"],
    "force_majeure": ["force majeure", "uncontrollable", "emergency", "iso order"],
}


@dataclass
class LayoutLine:
    page_number: int
    text: str


@dataclass
class ChunkRecord:
    chunk_index: int
    page_number: Optional[int]
    section_heading: Optional[str]
    clause_type: Optional[str]
    text_snippet: str
    source_locator: dict[str, Any]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def vector_to_pgvector(values: list[float]) -> str:
    """Postgres pgvector accepts text in '[1,2,3]' vector literal form."""
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def detect_section_heading(line: str, previous_heading: Optional[str]) -> Optional[str]:
    clean = " ".join(line.strip().split())
    if not clean:
        return previous_heading

    match = SECTION_HEADING_PATTERN.match(clean)
    if match:
        return clean[:200]

    # Simple legal drafting heuristic: short uppercase lines are often headings.
    if len(clean) <= 120 and clean.upper() == clean and any(ch.isalpha() for ch in clean):
        return clean[:200]

    return previous_heading


def detect_clause_type(text: str) -> Optional[str]:
    lower = text.lower()
    scores: dict[str, int] = {}
    for clause_type, keywords in CLAUSE_KEYWORDS.items():
        scores[clause_type] = sum(1 for keyword in keywords if keyword in lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def split_long_text(text: str, max_chars: int = 1400, overlap_chars: int = 200) -> Iterable[str]:
    """Split long section text at sentence-ish boundaries with overlap."""
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        yield clean
        return

    start = 0
    while start < len(clean):
        end = min(start + max_chars, len(clean))
        if end < len(clean):
            boundary = max(clean.rfind(". ", start, end), clean.rfind("; ", start, end), clean.rfind("\n", start, end))
            if boundary > start + int(max_chars * 0.55):
                end = boundary + 1
        yield clean[start:end].strip()
        if end >= len(clean):
            break
        start = max(end - overlap_chars, start + 1)


def parse_text_file(path: Path) -> tuple[str, list[LayoutLine], list[dict[str, Any]]]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = [LayoutLine(page_number=1, text=line.strip()) for line in raw.splitlines() if line.strip()]
    return raw, lines, []


def parse_with_azure_document_intelligence(path: Path) -> tuple[str, list[LayoutLine], list[dict[str, Any]]]:
    doc_client = DocumentAnalysisClient(
        require_env("AZURE_DOC_INTEL_ENDPOINT"),
        AzureKeyCredential(require_env("AZURE_DOC_INTEL_KEY")),
    )

    with path.open("rb") as target_file:
        poller = doc_client.begin_analyze_document("prebuilt-layout", document=target_file)
        result = poller.result()

    layout_lines: list[LayoutLine] = []
    for page in getattr(result, "pages", []) or []:
        page_no = getattr(page, "page_number", None) or getattr(page, "pageNumber", None) or 0
        for line in getattr(page, "lines", []) or []:
            content = getattr(line, "content", "").strip()
            if content:
                layout_lines.append(LayoutLine(page_number=int(page_no), text=content))

    table_blocks: list[dict[str, Any]] = []
    for table_index, table in enumerate(getattr(result, "tables", []) or []):
        cells = []
        page_number = None
        for cell in getattr(table, "cells", []) or []:
            content = getattr(cell, "content", "").strip()
            if not content:
                continue
            row_index = getattr(cell, "row_index", None)
            col_index = getattr(cell, "column_index", None)
            cells.append({"row": row_index, "column": col_index, "content": content})
            if page_number is None:
                regions = getattr(cell, "bounding_regions", []) or []
                if regions:
                    page_number = getattr(regions[0], "page_number", None)
        if cells:
            table_text = " | ".join(cell["content"] for cell in cells)
            table_blocks.append(
                {
                    "table_index": table_index,
                    "page_number": page_number,
                    "text": table_text,
                    "cells": cells,
                }
            )

    full_text = "\n".join(line.text for line in layout_lines)
    if table_blocks:
        full_text += "\n\n[TABLES]\n" + "\n".join(block["text"] for block in table_blocks)

    return full_text, layout_lines, table_blocks


def build_chunks(lines: list[LayoutLine], table_blocks: list[dict[str, Any]]) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    current_heading: Optional[str] = None
    current_page: Optional[int] = None
    section_buffer: list[str] = []
    section_start_page: Optional[int] = None

    def flush_section() -> None:
        nonlocal section_buffer, section_start_page, current_heading
        if not section_buffer:
            return
        section_text = " ".join(section_buffer).strip()
        for part in split_long_text(section_text):
            chunks.append(
                ChunkRecord(
                    chunk_index=len(chunks),
                    page_number=section_start_page,
                    section_heading=current_heading,
                    clause_type=detect_clause_type(part),
                    text_snippet=part,
                    source_locator={
                        "kind": "text_section",
                        "page_number": section_start_page,
                        "section_heading": current_heading,
                    },
                )
            )
        section_buffer = []
        section_start_page = None

    for line in lines:
        detected_heading = detect_section_heading(line.text, current_heading)
        is_new_heading = detected_heading != current_heading and detected_heading == line.text[:200]

        if is_new_heading:
            flush_section()
            current_heading = detected_heading
            current_page = line.page_number
            section_start_page = line.page_number
            section_buffer.append(line.text)
        else:
            current_page = line.page_number
            if section_start_page is None:
                section_start_page = line.page_number
            section_buffer.append(line.text)

    flush_section()

    for table in table_blocks:
        table_text = table.get("text", "").strip()
        if not table_text:
            continue
        chunks.append(
            ChunkRecord(
                chunk_index=len(chunks),
                page_number=table.get("page_number"),
                section_heading="TABLE",
                clause_type=detect_clause_type(table_text) or "table",
                text_snippet=table_text,
                source_locator={
                    "kind": "table",
                    "page_number": table.get("page_number"),
                    "table_index": table.get("table_index"),
                    "cells": table.get("cells", []),
                },
            )
        )

    return [chunk for chunk in chunks if chunk.text_snippet]


def embed_texts(client: OpenAI, texts: list[str], model: str, batch_size: int = 64) -> list[list[float]]:
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(input=batch, model=model)
        all_embeddings.extend(item.embedding for item in response.data)
    return all_embeddings


def ingest_contract(
    document_path: str,
    contract_id: str,
    contract_name: Optional[str] = None,
    offtaker_name: Optional[str] = None,
    asset_id: Optional[str] = None,
    document_version_hash: Optional[str] = None,
) -> str:
    path = Path(document_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    version_hash = document_version_hash or sha256_file(path)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    if path.suffix.lower() in {".txt", ".md"}:
        raw_text, layout_lines, table_blocks = parse_text_file(path)
    else:
        raw_text, layout_lines, table_blocks = parse_with_azure_document_intelligence(path)

    chunks = build_chunks(layout_lines, table_blocks)
    if not chunks:
        raise ValueError("No chunks were created from the document.")

    openai_client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    embeddings = embed_texts(openai_client, [chunk.text_snippet for chunk in chunks], embedding_model)

    parent_id = str(uuid.uuid4())
    db_conn = psycopg2.connect(require_env("SUPABASE_DB_URL"))
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ppa_parent_documents (
                        parent_id,
                        contract_id,
                        contract_name,
                        offtaker_name,
                        asset_id,
                        document_version_hash,
                        raw_text_content,
                        source_file_name,
                        source_mime_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (contract_id, document_version_hash)
                    DO UPDATE SET
                        contract_name = EXCLUDED.contract_name,
                        offtaker_name = EXCLUDED.offtaker_name,
                        asset_id = EXCLUDED.asset_id,
                        raw_text_content = EXCLUDED.raw_text_content,
                        source_file_name = EXCLUDED.source_file_name,
                        source_mime_type = EXCLUDED.source_mime_type,
                        ingested_at_timestamp = CURRENT_TIMESTAMP
                    RETURNING parent_id;
                    """,
                    (
                        parent_id,
                        contract_id,
                        contract_name,
                        offtaker_name,
                        asset_id,
                        version_hash,
                        raw_text,
                        path.name,
                        mime_type,
                    ),
                )
                parent_id = str(cursor.fetchone()[0])

                # Idempotent re-ingestion for the same contract/version.
                cursor.execute("DELETE FROM ppa_child_chunks WHERE parent_id = %s;", (parent_id,))

                for chunk, embedding in zip(chunks, embeddings):
                    cursor.execute(
                        """
                        INSERT INTO ppa_child_chunks (
                            parent_id,
                            contract_id,
                            document_version_hash,
                            chunk_index,
                            page_number,
                            section_heading,
                            clause_type,
                            text_snippet,
                            source_locator,
                            embedding_model,
                            embedding_vector
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::vector);
                        """,
                        (
                            parent_id,
                            contract_id,
                            version_hash,
                            chunk.chunk_index,
                            chunk.page_number,
                            chunk.section_heading,
                            chunk.clause_type,
                            chunk.text_snippet,
                            json.dumps(chunk.source_locator),
                            embedding_model,
                            vector_to_pgvector(embedding),
                        ),
                    )
    finally:
        db_conn.close()

    print(
        json.dumps(
            {
                "status": "success",
                "parent_id": parent_id,
                "contract_id": contract_id,
                "document_version_hash": version_hash,
                "chunk_count": len(chunks),
                "embedding_model": embedding_model,
            },
            indent=2,
        )
    )
    return parent_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and vectorize a PPA document.")
    parser.add_argument("--document", required=True, help="Path to PPA PDF/TXT/MD file.")
    parser.add_argument("--contract-id", required=True, help="PPA contract identifier.")
    parser.add_argument("--contract-name", default=None)
    parser.add_argument("--offtaker-name", default=None)
    parser.add_argument("--asset-id", default=None)
    parser.add_argument("--document-version-hash", default=None)
    args = parser.parse_args()

    ingest_contract(
        document_path=args.document,
        contract_id=args.contract_id,
        contract_name=args.contract_name,
        offtaker_name=args.offtaker_name,
        asset_id=args.asset_id,
        document_version_hash=args.document_version_hash,
    )


if __name__ == "__main__":
    main()
