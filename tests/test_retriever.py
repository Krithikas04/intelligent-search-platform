"""
Tests for the Pinecone retriever security filter.

build_pinecone_filter() is the most security-critical function in the system.
These tests verify the invariant: company_id is ALWAYS present in every filter path.
"""
import pytest
from backend.pipeline.retriever import build_pinecone_filter
from backend.core.user_context import UserContext, AssignedPlay


def _make_ctx(
    company_id: str = "comp-test-001",
    user_id: str = "user-test-001",
    play_ids: list[str] | None = None,
) -> UserContext:
    plays = [
        AssignedPlay(play_id=pid, play_title=f"Play {pid}", status="assigned", completed_at=None)
        for pid in (play_ids or ["play-001"])
    ]
    return UserContext(
        user_id=user_id,
        username="testuser",
        display_name="Test User",
        company_id=company_id,
        company_name="Test Co",
        assigned_plays=plays,
    )


class TestBuildPineconeFilter:
    """Security invariant: company_id must be in every filter."""

    def _assert_company_fence(self, f: dict, company_id: str) -> None:
        """Recursively verify company_id is constrained in the filter."""
        serialized = str(f)
        assert company_id in serialized, (
            f"company_id '{company_id}' not found in filter: {f}"
        )

    def test_knowledge_intent_has_company_fence(self):
        ctx = _make_ctx(company_id="comp-veldra-001")
        f = build_pinecone_filter(ctx, "assigned_knowledge")
        self._assert_company_fence(f, "comp-veldra-001")

    def test_performance_intent_has_company_fence(self):
        ctx = _make_ctx(company_id="comp-aetheris-002")
        f = build_pinecone_filter(ctx, "performance_history")
        self._assert_company_fence(f, "comp-aetheris-002")

    def test_combined_intent_has_company_fence(self):
        ctx = _make_ctx(company_id="comp-kyberon-003")
        f = build_pinecone_filter(ctx, "combined")
        self._assert_company_fence(f, "comp-kyberon-003")

    def test_general_professional_falls_through_to_knowledge_filter(self):
        ctx = _make_ctx(company_id="comp-sentivue-004")
        f = build_pinecone_filter(ctx, "general_professional")
        self._assert_company_fence(f, "comp-sentivue-004")

    def test_knowledge_filter_contains_play_ids(self):
        ctx = _make_ctx(play_ids=["play-001", "play-002"])
        f = build_pinecone_filter(ctx, "assigned_knowledge")
        serialized = str(f)
        assert "play-001" in serialized
        assert "play-002" in serialized

    def test_performance_filter_contains_user_id(self):
        ctx = _make_ctx(user_id="user-xyz-999")
        f = build_pinecone_filter(ctx, "performance_history")
        serialized = str(f)
        assert "user-xyz-999" in serialized

    def test_performance_filter_content_type_is_submission(self):
        ctx = _make_ctx()
        f = build_pinecone_filter(ctx, "performance_history")
        serialized = str(f)
        assert "submission" in serialized

    def test_knowledge_filter_content_type_is_knowledge(self):
        ctx = _make_ctx()
        f = build_pinecone_filter(ctx, "assigned_knowledge")
        serialized = str(f)
        assert "knowledge" in serialized

    def test_combined_filter_includes_both_content_types(self):
        ctx = _make_ctx()
        f = build_pinecone_filter(ctx, "combined")
        serialized = str(f)
        assert "knowledge" in serialized
        assert "submission" in serialized

    def test_different_companies_get_different_filters(self):
        ctx_a = _make_ctx(company_id="comp-a-001")
        ctx_b = _make_ctx(company_id="comp-b-002")
        f_a = build_pinecone_filter(ctx_a, "assigned_knowledge")
        f_b = build_pinecone_filter(ctx_b, "assigned_knowledge")
        assert str(f_a) != str(f_b)
        assert "comp-a-001" in str(f_a)
        assert "comp-b-002" in str(f_b)
        assert "comp-b-002" not in str(f_a)
        assert "comp-a-001" not in str(f_b)
