from typing import List
from .client import get_openai_client


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text using normal (non-batch) approach."""
    client = get_openai_client()
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


def generate_embeddings_for_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts using individual calls (not batch)."""
    embeddings = []
    total = len(texts)

    for i, text in enumerate(texts, 1):
        print(f"Generating embedding {i}/{total} for chapters...")
        embedding = generate_embedding(text)
        embeddings.append(embedding)

    return embeddings
