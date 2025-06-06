import copy
from typing import Dict
from typesense.exceptions import ObjectNotFound
from .client import get_typesense_client


def create_collection(name: str, schema) -> None:
    """Create a Typesense collection if it doesn't exist."""
    client = get_typesense_client()
    schema_with_name = copy.deepcopy(schema)
    schema_with_name["name"] = name
    try:
        client.collections[name].retrieve()
        print(f"Collection {name} already exists.")
    except ObjectNotFound:
        client.collections.create(schema_with_name)
        print(f"Created collection {name}.")
