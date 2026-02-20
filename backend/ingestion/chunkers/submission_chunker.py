"""Chunk user submission assets. Same segment structure as video, with feedback embedded."""
import json
from typing import List, Optional


def chunk_submission(
    file_path: str,
    feedback_score: Optional[int] = None,
    feedback_text: Optional[str] = None,
) -> List[dict]:
    """Return chunks for a submission asset with AI feedback fields embedded."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    has_feedback = feedback_score is not None
    feedback_suffix = ""
    if has_feedback:
        feedback_suffix = f"\n[AI Feedback Score: {feedback_score}/10] {feedback_text or ''}"

    chunks = []
    chunk_index = 0

    # Full transcript
    full_transcript = data.get("full_transcript", "").strip()
    if full_transcript:
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": (full_transcript + feedback_suffix).strip(),
            "page_number": None,
            "section_id": "full_transcript",
            "heading": "Full Submission Transcript",
            "timestamp_start": None,
            "timestamp_end": None,
            "feedback_score": feedback_score,
            "feedback_text": feedback_text,
            "has_feedback": has_feedback,
        })
        chunk_index += 1

    # Per-segment chunks
    for seg in data.get("segments", []):
        speaker = seg.get("speaker", "")
        start = seg.get("start", "")
        end = seg.get("end", "")
        text = seg.get("text", "").strip()
        if not text:
            continue
        label = f"[{speaker} at {start}]: {text}" if speaker else f"[{start}]: {text}"
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": (label + feedback_suffix).strip(),
            "page_number": None,
            "section_id": None,
            "heading": None,
            "timestamp_start": start,
            "timestamp_end": end,
            "feedback_score": feedback_score,
            "feedback_text": feedback_text,
            "has_feedback": has_feedback,
        })
        chunk_index += 1

    # Text-only submissions (no segments or transcript — e.g. text type)
    if not chunks:
        text = data.get("full_text", data.get("text", data.get("content", ""))).strip()
        if text:
            chunks.append({
                "chunk_index": 0,
                "chunk_text": (text + feedback_suffix).strip(),
                "page_number": None,
                "section_id": "text_content",
                "heading": "Submission Text",
                "timestamp_start": None,
                "timestamp_end": None,
                "feedback_score": feedback_score,
                "feedback_text": feedback_text,
                "has_feedback": has_feedback,
            })

    return chunks
