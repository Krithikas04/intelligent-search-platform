"""Chunk video/audio-type assets (stored as JSON with segments + full_transcript)."""
import json
from typing import List


def chunk_video(file_path: str) -> List[dict]:
    """Return a list of raw chunk dicts for a video/audio asset JSON."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    chunk_index = 0

    # Aggregate full-transcript chunk
    full_transcript = data.get("full_transcript", "").strip()
    if full_transcript:
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": full_transcript,
            "page_number": None,
            "section_id": "full_transcript",
            "heading": "Full Transcript",
            "timestamp_start": None,
            "timestamp_end": None,
        })
        chunk_index += 1

    # Per-segment chunks
    for seg in data.get("segments", []):
        speaker = seg.get("speaker", "")
        start = seg.get("start", "")
        text = seg.get("text", "").strip()
        end = seg.get("end", "")
        if not text:
            continue
        label = f"[{speaker} at {start}]: {text}" if speaker else f"[{start}]: {text}"
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": label,
            "page_number": None,
            "section_id": None,
            "heading": None,
            "timestamp_start": start,
            "timestamp_end": end,
        })
        chunk_index += 1

    return chunks
