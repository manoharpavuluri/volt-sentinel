"""
Layout-aware PPA parser and vector indexer.

Design fix:
- Stores contract_id on child chunks for safe contract-scoped retrieval.
- Stores source filename and page number for auditability.
- Uses parameterized inserts and UUIDs.
"""

import os
import uuid
from pathlib import Path

import psycopg2
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
doc_intel_client = DocumentAnalysisClient(
    endpoint=os.getenv("AZURE_DOC_INTEL_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_DOC_INTEL_KEY")),
)


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def process_and_index_clearway_ppa(file_path: str, contract_id_tag: str) -> None:
    path = Path(file_path)
    parent_id = str(uuid.uuid4())

    with open(path, "rb") as f:
        poller = doc_intel_client.begin_analyze_document("prebuilt-layout", document=f)
        result = poller.result()

    page_texts: list[tuple[int, str]] = []
    for page in result.pages:
        page_text = "\n".join(line.content for line in page.lines)
        page_texts.append((page.page_number, page_text))

    full_text = "\n\n".join(text for _, text in page_texts)

    db_conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ppa_parent_documents
                        (parent_id, contract_id, source_file_name, raw_text_content)
                    values (%s, %s, %s, %s)
                    """,
                    (parent_id, contract_id_tag, path.name, full_text),
                )

                chunk_index = 0
                for page_number, page_text in page_texts:
                    for text_snippet in chunk_text(page_text):
                        emb_res = openai_client.embeddings.create(
                            input=[text_snippet],
                            model="text-embedding-3-small",
                        )
                        vector_coordinates = emb_res.data[0].embedding
                        cursor.execute(
                            """
                            insert into ppa_child_chunks
                                (chunk_id, parent_id, contract_id, chunk_index, page_number, text_snippet, embedding_vector)
                            values (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                str(uuid.uuid4()),
                                parent_id,
                                contract_id_tag,
                                chunk_index,
                                page_number,
                                text_snippet,
                                vector_coordinates,
                            ),
                        )
                        chunk_index += 1
    finally:
        db_conn.close()

    print(f"Indexed {path.name} under contract_id={contract_id_tag}")


if __name__ == "__main__":
    process_and_index_clearway_ppa(
        "./stateful_ai_framework/legal_assets/wildorado_google_wind_ppa.txt",
        "PPA_GOOG_WILDORADO_WIND",
    )
