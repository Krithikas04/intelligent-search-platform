"""
CLI entrypoint for data ingestion.
Run: python -m backend.ingestion.run_ingestion

Joins all CSV data → builds metadata → embeds → upserts to Pinecone.
"""
import os
import sys

from openai import OpenAI
from pinecone import Pinecone

from backend.config import get_settings
from backend.core.data_store import DataStore
from backend.ingestion.create_index import create_index
from backend.ingestion.chunkers.pdf_chunker import chunk_pdf
from backend.ingestion.chunkers.video_chunker import chunk_video
from backend.ingestion.chunkers.image_chunker import chunk_image
from backend.ingestion.chunkers.submission_chunker import chunk_submission
from backend.ingestion.metadata_builder import build_knowledge_metadata, build_submission_metadata
from backend.ingestion.pinecone_uploader import upsert_vectors

settings = get_settings()


ASSET_CHUNKER_MAP = {
    "pdf": chunk_pdf,
    "video": chunk_video,
    "audio": chunk_video,   # same segment structure
    "image": chunk_image,
}


def ingest_knowledge(store: DataStore, openai_client: OpenAI, index):
    """Ingest all knowledge assets (non-submission)."""
    print("\n=== Ingesting Knowledge Assets ===")
    all_vectors = []

    # Build an explicit set of asset IDs used by submissions — avoids fragile string heuristic
    submission_asset_ids = {s.asset_id for s in store.all_submissions()}

    for asset in store.all_assets():
        # Skip assets that belong to submissions
        if asset.id in submission_asset_ids:
            continue

        # Find which rep(s) reference this asset
        matching_reps = [r for r in store.all_reps() if r.asset_id == asset.id]
        if not matching_reps:
            print(f"  WARN: No rep references asset {asset.id}, skipping.")
            continue

        rep = matching_reps[0]
        play = store.get_play(rep.play_id)
        if play is None:
            print(f"  WARN: Play {rep.play_id} not found, skipping asset {asset.id}.")
            continue

        company = store.get_company(asset.company_id)
        company_name = company["name"] if company else asset.company_id

        file_path = store.asset_file_path(asset.file_name)
        if not os.path.exists(file_path):
            print(f"  WARN: Asset file not found: {file_path}")
            continue

        chunker = ASSET_CHUNKER_MAP.get(asset.type)
        if chunker is None:
            print(f"  WARN: Unknown asset type '{asset.type}' for {asset.id}")
            continue

        try:
            chunks = chunker(file_path)
        except Exception as e:
            print(f"  ERROR chunking {asset.id}: {e}")
            continue

        print(f"  [{asset.id}] {asset.type} -> {len(chunks)} chunks | play: {play.title}")

        for chunk in chunks:
            metadata = build_knowledge_metadata(
                chunk,
                company_id=asset.company_id,
                asset_id=asset.id,
                play_id=rep.play_id,
                rep_id=rep.id,
                asset_type=asset.type,
                play_title=play.title,
                rep_title=rep.prompt_title,
                company_name=company_name,
            )
            vector_id = f"{asset.id}_chunk_{chunk['chunk_index']}"
            all_vectors.append({
                "id": vector_id,
                "text": chunk["chunk_text"],
                "metadata": metadata,
            })

    print(f"\nTotal knowledge vectors to upsert: {len(all_vectors)}")
    if all_vectors:
        upsert_vectors(all_vectors, openai_client, index)
    return len(all_vectors)


def ingest_submissions(store: DataStore, openai_client: OpenAI, index):
    """Ingest all user submission assets."""
    print("\n=== Ingesting Submission Assets ===")
    all_vectors = []

    for submission in store.all_submissions():
        asset = store.get_asset(submission.asset_id)
        if asset is None:
            print(f"  WARN: Asset {submission.asset_id} not found for submission {submission.id}")
            continue

        rep = store.get_rep(submission.rep_id)
        if rep is None:
            print(f"  WARN: Rep {submission.rep_id} not found for submission {submission.id}")
            continue

        play = store.get_play(rep.play_id)
        if play is None:
            print(f"  WARN: Play {rep.play_id} not found for submission {submission.id}")
            continue

        feedback = store.get_feedback_for_submission(submission.id)
        feedback_score = feedback.score if feedback else None
        feedback_text = feedback.text if feedback else None

        company = store.get_company(submission.company_id)
        company_name = company["name"] if company else submission.company_id

        file_path = store.asset_file_path(asset.file_name)
        if not os.path.exists(file_path):
            print(f"  WARN: Submission file not found: {file_path}")
            continue

        try:
            chunks = chunk_submission(file_path, feedback_score=feedback_score, feedback_text=feedback_text)
        except Exception as e:
            print(f"  ERROR chunking submission {submission.id}: {e}")
            continue

        print(
            f"  [{submission.id}] user={submission.user_id} "
            f"-> {len(chunks)} chunks | score={feedback_score}"
        )

        for chunk in chunks:
            metadata = build_submission_metadata(
                chunk,
                company_id=submission.company_id,
                asset_id=asset.id,
                play_id=rep.play_id,
                rep_id=rep.id,
                user_id=submission.user_id,
                submission_id=submission.id,
                asset_type=asset.type,
                play_title=play.title,
                rep_title=rep.prompt_title,
                company_name=company_name,
            )
            vector_id = f"{submission.id}_chunk_{chunk['chunk_index']}"
            all_vectors.append({
                "id": vector_id,
                "text": chunk["chunk_text"],
                "metadata": metadata,
            })

    print(f"\nTotal submission vectors to upsert: {len(all_vectors)}")
    if all_vectors:
        upsert_vectors(all_vectors, openai_client, index)
    return len(all_vectors)


def main():
    print("=== Knowledge-to-Action Search: Data Ingestion ===")
    print(f"Data directory: {settings.data_dir}")
    print(f"Pinecone index: {settings.pinecone_index_name}")
    print(f"Embedding model: {settings.embedding_model} ({settings.embedding_dimensions}d)")

    # Step 1: Create Pinecone index (idempotent)
    create_index()

    # Step 2: Initialize clients
    openai_client = OpenAI(api_key=settings.openai_api_key)
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)

    # Step 3: Load data
    store = DataStore(settings.data_dir)

    # Step 4: Ingest knowledge
    k_count = ingest_knowledge(store, openai_client, index)

    # Step 5: Ingest submissions
    s_count = ingest_submissions(store, openai_client, index)

    print(f"\n=== Ingestion Complete ===")
    print(f"Knowledge vectors: {k_count}")
    print(f"Submission vectors: {s_count}")
    print(f"Total vectors: {k_count + s_count}")

    # Step 6: Print index stats
    stats = index.describe_index_stats()
    print(f"\nPinecone index stats: {stats}")


if __name__ == "__main__":
    main()
