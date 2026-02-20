"""
Tests for orchestrator helper functions.
"""
import pytest
from backend.pipeline.orchestrator import _apply_mode, _play_id_set_from_chunks
from backend.models.api_schemas import IntentResult, SourceChunk


def _make_intent(intent: str = "assigned_knowledge") -> IntentResult:
    return IntentResult(intent=intent, confidence=0.9, reasoning="test")


def _make_chunk(play_id: str | None = "play-001", play_title: str = "Test Play") -> SourceChunk:
    return SourceChunk(
        asset_id="asset-001",
        asset_type="pdf",
        play_id=play_id,
        play_title=play_title,
        rep_title="Test Rep",
        chunk_text="some content",
    )


class TestApplyMode:
    def test_no_mode_leaves_intent_unchanged(self):
        ir = _make_intent("assigned_knowledge")
        _apply_mode(ir, None)
        assert ir.intent == "assigned_knowledge"

    def test_auto_mode_leaves_intent_unchanged(self):
        ir = _make_intent("general_professional")
        _apply_mode(ir, "auto")
        assert ir.intent == "general_professional"

    def test_knowledge_mode_overrides_to_assigned_knowledge(self):
        ir = _make_intent("out_of_scope")
        _apply_mode(ir, "knowledge")
        assert ir.intent == "assigned_knowledge"

    def test_performance_mode_overrides_to_performance_history(self):
        ir = _make_intent("assigned_knowledge")
        _apply_mode(ir, "performance")
        assert ir.intent == "performance_history"


class TestPlayIdSetFromChunks:
    def test_extracts_play_ids_from_chunks(self):
        chunks = [_make_chunk("play-001"), _make_chunk("play-002"), _make_chunk("play-001")]
        result = _play_id_set_from_chunks(chunks)
        assert result == {"play-001", "play-002"}

    def test_skips_chunks_with_no_play_id(self):
        chunks = [_make_chunk(None), _make_chunk("play-003")]
        result = _play_id_set_from_chunks(chunks)
        assert result == {"play-003"}

    def test_empty_chunks_returns_empty_set(self):
        assert _play_id_set_from_chunks([]) == set()

    def test_all_none_play_ids_returns_empty_set(self):
        chunks = [_make_chunk(None), _make_chunk(None)]
        assert _play_id_set_from_chunks(chunks) == set()
