"""Chunk PDF-type assets (stored as structured JSON)."""
import json
from typing import List


def chunk_pdf(file_path: str) -> List[dict]:
    """Return a list of raw chunk dicts for a PDF asset JSON."""
    with open(file_path, encoding="utf-8") as f:
        pages = json.load(f)

    chunks = []
    chunk_index = 0

    for page in pages:
        page_num = page.get("page", 1)

        # Section-level chunks
        sections = page.get("sections", [])
        if sections:
            for sec in sections:
                text = f"{sec.get('heading', '')}\n{sec.get('content', '')}".strip()
                if not text:
                    continue
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_text": text,
                    "page_number": page_num,
                    "section_id": sec.get("id"),
                    "heading": sec.get("heading"),
                    "timestamp_start": None,
                    "timestamp_end": None,
                })
                chunk_index += 1
        else:
            # Fallback: full page text
            text = page.get("text", "").strip()
            if text:
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_text": text,
                    "page_number": page_num,
                    "section_id": None,
                    "heading": None,
                    "timestamp_start": None,
                    "timestamp_end": None,
                })
                chunk_index += 1

        # Table chunks
        for table in page.get("tables", []):
            rows_text = []
            headers = table.get("headers", [])
            for row in table.get("rows", []):
                row_str = " | ".join(str(v) for v in row)
                rows_text.append(row_str)
            table_text = (
                f"{table.get('title', 'Table')}\n"
                + " | ".join(headers) + "\n"
                + "\n".join(rows_text)
            ).strip()
            if table_text:
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_text": table_text,
                    "page_number": page_num,
                    "section_id": table.get("id"),
                    "heading": table.get("title"),
                    "timestamp_start": None,
                    "timestamp_end": None,
                })
                chunk_index += 1

    return chunks
