from typing import List
from openai import (
    OpenAI,
)
import os
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://aipipe.org/openai/v1",
)


def generate_embedding(text: str) -> List[float]:
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


# Test the function
if __name__ == "__main__":
    test_text = "Hello, this is a test sentence for generating embeddings."
    embedding = generate_embedding(test_text)
    if embedding:
        print("Embedding generated successfully. First 5 values:")
        print(embedding[:5])
    else:
        print("Failed to generate embedding.")
