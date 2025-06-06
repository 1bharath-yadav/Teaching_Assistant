#!/usr/bin/env python3

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add the embed/lib directory to Python path
curr_dir = Path(__file__).parent
embed_lib_path = curr_dir / "embed" / "lib"
sys.path.insert(0, str(embed_lib_path))

from embed.lib import get_openai_client

def debug_ollama_connection():
    """Debug the Ollama connection by showing configuration."""
    try:
        print("Environment variables:")
        print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
        print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
        
        client = get_openai_client()
        print("✓ OpenAI client initialized successfully")
        print(f"Client base_url: {client.base_url}")
        print(f"Client api_key: {client.api_key}")
        
        # Test a simple completion
        response = client.chat.completions.create(
            model="gemma3:4b",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10
        )
        
        print("✓ Successfully got response from Ollama")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"✗ Error testing Ollama connection: {e}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    print("Debugging Ollama connection...")
    success = debug_ollama_connection()
    sys.exit(0 if success else 1)
