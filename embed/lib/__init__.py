from .client import get_openai_client, get_typesense_client
from .schemas import DISCOURSE_SCHEMA, CHAPTERS_SCHEMA
from .embeddings import generate_embedding, batch_generate_embeddings
from .collections import create_collection
from .indexing import batch_upsert_documents, index_discourse_posts, index_module_chunks

__all__ = [
    "get_openai_client",
    "get_typesense_client",
    "DISCOURSE_SCHEMA",
    "CHAPTERS_SCHEMA",
    "generate_embedding",
    "batch_generate_embeddings",
    "create_collection",
    "batch_upsert_documents",
    "index_discourse_posts",
    "index_module_chunks",
]
