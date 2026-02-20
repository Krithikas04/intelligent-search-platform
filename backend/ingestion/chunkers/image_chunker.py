"""Chunk image-type assets (stored as JSON with alt_text + ocr_text + visual_elements)."""
import json
from typing import List


def chunk_image(file_path: str) -> List[dict]:
    """Return a single chunk combining all image descriptive fields."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    parts = []

    alt_text = data.get("alt_text", "").strip()
    if alt_text:
        parts.append(f"Description: {alt_text}")

    ocr_text = data.get("ocr_text", "").strip()
    if ocr_text:
        parts.append(f"Text visible in image: {ocr_text}")

    visual_elements = data.get("visual_elements", [])
    if visual_elements:
        ve_parts = []
        for ve in visual_elements:
            label = ve.get("label", "")
            desc = ve.get("description", "")
            ve_parts.append(f"{label}: {desc}")
        parts.append("Visual elements:\n" + "\n".join(ve_parts))

    tags = data.get("tags", [])
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")

    chunk_text = "\n\n".join(parts).strip()
    if not chunk_text:
        return []

    return [
        {
            "chunk_index": 0,
            "chunk_text": chunk_text,
            "page_number": None,
            "section_id": "image_content",
            "heading": "Image Content",
            "timestamp_start": None,
            "timestamp_end": None,
        }
    ]
