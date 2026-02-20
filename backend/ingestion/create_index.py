"""One-time Pinecone index creation."""
import time

from pinecone import Pinecone, ServerlessSpec

from backend.config import get_settings


def create_index():
    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)

    existing = pc.list_indexes().names()
    if settings.pinecone_index_name in existing:
        print(f"Index '{settings.pinecone_index_name}' already exists. Skipping creation.")
        return

    print(f"Creating index '{settings.pinecone_index_name}'...")
    pc.create_index(
        name=settings.pinecone_index_name,
        dimension=settings.embedding_dimensions,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

    # Wait for index to be ready
    while True:
        desc = pc.describe_index(settings.pinecone_index_name)
        status = desc.status
        if isinstance(status, dict):
            ready = status.get("ready", False)
        else:
            ready = getattr(status, "ready", False)
        if ready:
            break
        print("  Waiting for index to be ready...")
        time.sleep(5)

    print(f"Index '{settings.pinecone_index_name}' created successfully.")


if __name__ == "__main__":
    create_index()
