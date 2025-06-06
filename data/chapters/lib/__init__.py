# Chapters embedding library
from .client import get_openai_client, get_typesense_client
from .embeddings import generate_embedding
from .schemas import CHAPTERS_SCHEMA
from .collections import create_collection
from .indexing import index_module_chunks

__all__ = [
    "get_openai_client",
    "get_typesense_client",
    "generate_embedding",
    "CHAPTERS_SCHEMA",
    "create_collection",
    "index_module_chunks",
]
