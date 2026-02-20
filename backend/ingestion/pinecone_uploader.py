"""Batched Pinecone upsert with OpenAI embeddings."""
import time
from typing import List

from openai import OpenAI
from pinecone import Pinecone

from backend.config import get_settings

settings = get_settings()


def embed_texts(texts: List[str], client: OpenAI) -> List[List[float]]:
    """Embed a batch of texts using OpenAI text-embedding-3-large."""
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        dimensions=settings.embedding_dimensions,
    )
    return [item.embedding for item in response.data]


def upsert_vectors(
    vectors: List[dict],
    openai_client: OpenAI,
    pinecone_index,
    batch_size: int = 50,
):
    """
    vectors: list of {"id": str, "text": str, "metadata": dict}
    Embeds texts and upserts in batches.
    """
    total = len(vectors)
    print(f"  Upserting {total} vectors in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = vectors[i : i + batch_size]
        texts = [v["text"] for v in batch]
        embeddings = embed_texts(texts, openai_client)

        upsert_payload = [
            {
                "id": batch[j]["id"],
                "values": embeddings[j],
                "metadata": batch[j]["metadata"],
            }
            for j in range(len(batch))
        ]
        pinecone_index.upsert(vectors=upsert_payload)
        print(f"    Upserted {min(i + batch_size, total)}/{total}")
        time.sleep(0.5)  # rate limit courtesy pause
