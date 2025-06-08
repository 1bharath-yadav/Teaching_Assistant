#!/usr/bin/env python3
"""
Example script demonstrating integrated chunking for both markdown and discourse content.
"""

import json
from pathlib import Path
from optimized_chunker import OptimizedChunker, main_integrated


def load_sample_discourse_data():
    """Load sample discourse data for testing."""
    sample_data = {
        "123": {
            "topic_title": "Introduction to Data Science",
            "timestamp": "2024-01-15T10:30:00.000Z",
            "posts": [
                {
                    "post_number": 1,
                    "post_content": "Welcome to this comprehensive introduction to data science. In this course, we'll cover various aspects including data collection, cleaning, analysis, and visualization. Let's start with understanding what data science is and why it's important in today's world.",
                },
                {
                    "post_number": 2,
                    "post_content": "Great introduction! I'm particularly interested in the data visualization part. Could you elaborate on the tools we'll be using? I've heard about Python libraries like matplotlib and seaborn.",
                },
            ],
        },
        "456": {
            "topic_title": "Machine Learning Fundamentals",
            "timestamp": "2024-01-20T14:15:00.000Z",
            "posts": [
                {
                    "post_number": 1,
                    "post_content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. We'll explore supervised learning, unsupervised learning, and reinforcement learning approaches.",
                }
            ],
        },
    }
    return sample_data


def example_integrated_processing():
    """Example of processing both types of content."""
    print("=== Integrated Chunking Example ===\n")

    # Load sample discourse data
    discourse_data = load_sample_discourse_data()
    print(f"Loaded {len(discourse_data)} discourse topics")

    # Process with custom discourse chunk size
    results = main_integrated(
        discourse_data=discourse_data,
        markdown_repo_dir=None,  # Skip markdown for this example
        discourse_max_tokens=500,  # Smaller chunks for discourse
    )

    print(f"\nProcessing Results:")
    print(f"- Discourse Success: {results['discourse_success']}")
    print(f"- Discourse Chunks: {results['discourse_chunks']}")
    print(f"- Total Chunks: {results['total_chunks']}")

    # Check if output files were created
    current_dir = Path(__file__).parent
    discourse_chunks_file = current_dir / "discourse_chunks.json"
    discourse_summary_file = current_dir / "discourse_summary.json"

    if discourse_chunks_file.exists():
        print(f"\nDiscourse chunks saved to: {discourse_chunks_file}")
        with open(discourse_chunks_file, "r") as f:
            chunks = json.load(f)
            print(f"Sample chunk:")
            if chunks:
                sample_chunk = chunks[0]
                print(f"  ID: {sample_chunk['topic_id']}")
                print(f"  Title: {sample_chunk['topic_title']}")
                print(f"  Content length: {len(sample_chunk['content'])} chars")
                print(f"  Content preview: {sample_chunk['content'][:100]}...")

    if discourse_summary_file.exists():
        print(f"\nSummary saved to: {discourse_summary_file}")


def example_discourse_only():
    """Example of processing only discourse content."""
    print("\n=== Discourse-Only Processing ===\n")

    chunker = OptimizedChunker()
    discourse_data = load_sample_discourse_data()

    # Process discourse data with different chunk sizes
    chunk_sizes = [300, 500, 800]

    for chunk_size in chunk_sizes:
        print(f"\nProcessing with chunk size: {chunk_size}")
        discourse_chunks = chunker.process_discourse_data(discourse_data, chunk_size)
        print(f"Generated {len(discourse_chunks)} chunks")

        # Show chunk size distribution
        chunk_lengths = [len(chunk["content"]) for chunk in discourse_chunks]
        if chunk_lengths:
            avg_length = sum(chunk_lengths) / len(chunk_lengths)
            max_length = max(chunk_lengths)
            min_length = min(chunk_lengths)
            print(f"  Average chunk length: {avg_length:.1f} chars")
            print(f"  Min/Max chunk length: {min_length}/{max_length} chars")


def main():
    """Main function to run examples."""
    try:
        # Example 1: Integrated processing
        example_integrated_processing()

        # Example 2: Discourse-only processing with different chunk sizes
        example_discourse_only()

        print("\n=== Examples completed successfully! ===")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
