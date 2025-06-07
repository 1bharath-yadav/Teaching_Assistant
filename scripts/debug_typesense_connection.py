#!/usr/bin/env python3
# filepath: /home/archer/projects/llm_tests/Teaching_Assistant/scripts/debug_typesense_connection.py
"""
Debug the connection to Typesense by printing the configuration used.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to path so we can import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from lib.config import get_config
import typesense

def main():
    """Debug Typesense connection configuration."""
    try:
        # Get the full configuration
        config = get_config()
        
        print("Typesense Configuration:")
        print(f"API Key: {config.typesense.api_key}")
        print("Nodes:")
        for node in config.typesense.nodes:
            print(f"  - Host: {node.host}, Port: {node.port}, Protocol: {node.protocol}")
            
        print("\nEnvironment variables:")
        print(f"TYPESENSE_API_KEY: {os.getenv('TYPESENSE_API_KEY')}")
        print(f"TYPESENSE_HOST: {os.getenv('TYPESENSE_HOST')}")
        print(f"TYPESENSE_PORT: {os.getenv('TYPESENSE_PORT')}")
        print(f"TYPESENSE_PROTOCOL: {os.getenv('TYPESENSE_PROTOCOL')}")
        
        # Try direct connection with environment variables
        direct_client = typesense.Client({
            "api_key": os.getenv('TYPESENSE_API_KEY', 'xyz'),
            "nodes": [{
                "host": os.getenv('TYPESENSE_HOST', 'localhost'),
                "port": os.getenv('TYPESENSE_PORT', '8108'),
                "protocol": os.getenv('TYPESENSE_PROTOCOL', 'http')
            }],
            "connection_timeout_seconds": 10
        })
        
        try:
            print("\nAttempting direct connection using environment variables:")
            collections = direct_client.collections.retrieve()
            print(f"Success! Found {len(collections)} collections.")
        except Exception as e:
            print(f"Direct connection failed: {e}")
        
        # Try connecting with hardcoded API key
        hardcoded_client = typesense.Client({
            "api_key": "xyz",
            "nodes": [{
                "host": "localhost",
                "port": "8108",
                "protocol": "http"
            }],
            "connection_timeout_seconds": 10
        })
        
        try:
            print("\nAttempting connection with hardcoded 'xyz' API key:")
            collections = hardcoded_client.collections.retrieve()
            print(f"Success! Found {len(collections)} collections.")
        except Exception as e:
            print(f"Hardcoded connection failed: {e}")
        
    except Exception as e:
        print(f"Error during configuration debug: {e}")

if __name__ == "__main__":
    main()
