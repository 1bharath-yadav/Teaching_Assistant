#!/usr/bin/env python3
"""
Chapters Embedding System

This script processes chapter chunks and creates embeddings for them,
then indexes them into Typesense for vector search.
"""

from pathlib import Path
from lib import (
    index_module_chunks,
)

# Configuration
CURRENT_DIR = Path(__file__).parent
MODULES_BASE_DIR = CURRENT_DIR / "tools-in-data-science-public"

MODULES = [
    "development_tools",
    "deployment_tools",
    "large_language_models",
    "data_sourcing",
    "data_preparation",
    "data_analysis",
    "data_visualization",
    "project-1",
    "project-2",
    "misc",
]


def process_module_chunks() -> None:
    """Process and index module chunks with embeddings."""
    if not MODULES_BASE_DIR.exists():
        print(f"Modules directory {MODULES_BASE_DIR} not found.")
        return

    print(f"Processing {len(MODULES)} modules...")
    for module in MODULES:
        print(f"\n=== Processing module: {module} ===")
        index_module_chunks(module, MODULES_BASE_DIR)

    print("\nChapters embedding process completed successfully!")


def main():
    """Main function to run chapters embedding."""
    print("=== Chapters Embedding System ===")
    process_module_chunks()


if __name__ == "__main__":
    main()
