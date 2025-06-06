# Discourse embedding library
from .client import get_openai_client, get_typesense_client
from .schemas import DISCOURSE_SCHEMA
from .collections import create_collection
from .indexing import index_discourse_posts

__all__ = [
    "get_openai_client",
    "get_typesense_client",
    "DISCOURSE_SCHEMA",
    "create_collection",
    "index_discourse_posts",
]
