from typing import List
from .client import get_openai_client

# Constants
EMBED_BATCH_SIZE = 100


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text."""
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


def batch_generate_embeddings(
    texts: List[str], batch_size: int = EMBED_BATCH_SIZE
) -> List[List[float]]:
    """Generate embeddings for multiple texts in batches."""
    client = get_openai_client()
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            print(f"Generated embeddings for batch {i // batch_size + 1}.")
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            embeddings.extend([[] for _ in batch])
    return embeddings
