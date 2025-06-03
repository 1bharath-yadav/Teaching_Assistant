import os
import typesense
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client."""
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"), base_url="https://aipipe.org/openai/v1"
    )


get_typesense_client = typesense.Client(  # type: ignore
    {
        "api_key": os.getenv("TYPESENSE_API_KEY"),
        "nodes": [
            {"host": "localhost", "port": "8108", "protocol": "http"}
        ],  # type: ignore
        "connection_timeout_seconds": 10,
    }
)
