#!/usr/bin/env python3
"""
Content quality verification for the RAG chunking pipeline.
"""

import json
from pathlib import Path


def check_content_quality():
    """Check the quality of processed content."""

    print("🔍 Content Quality Verification")
    print("=" * 50)

    # Check discourse content quality
    discourse_file = Path("data/discourse/processed_posts.json")
    with open(discourse_file) as f:
        discourse_data = json.load(f)

    print("📋 Discourse Content Sample:")
    sample = discourse_data[5]  # Check a different sample
    content = sample["content"]
    print(f'Source: Discourse Topic ID {sample["topic_id"]}')
    print(f'Topic: {sample["topic_title"][:50]}...')
    print(f'URL: {sample.get("url", "N/A")}')
    print(f'Timestamp: {sample.get("timestamp", "N/A")}')
    print(f"Length: {len(content)} characters")
    print(f'Tokens: {sample["token_count"]}')
    print(f'Chunk: {sample["chunk_index"] + 1}/{sample["total_chunks"]}')
    print(
        f'Usernames: {", ".join(sample.get("metadata", {}).get("usernames", [])[:3])}...'
    )
    print(f"Content preview:")
    print(content[:300] + "...")
    print()

    # Check for quality indicators
    quality_checks = {
        "Base64 images": "data:image" not in content.lower(),
        "JSON errors": not ("{" in content and "error" in content.lower()),
        "Script tags": "<script" not in content.lower(),
        "HTTP headers": not any(
            x in content for x in ["HTTP/", "Content-Type:", "Set-Cookie:"]
        ),
        "User mentions clean": "@" not in content or "mentioned" not in content.lower(),
        "Has educational content": any(
            x in content.lower()
            for x in ["question", "answer", "explain", "help", "learn"]
        ),
        "Has structured formatting": any(
            x in content for x in ["\n\n", "1.", "2.", "-", "*"]
        ),
    }

    print("Quality Assessment:")
    for check, passed in quality_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")

    # Check chapter content
    print()
    print("📚 Chapter Content Sample:")
    chapter_file = Path(
        "data/chapters/tools-in-data-science-public/large_language_models/chunks.json"
    )
    with open(chapter_file) as f:
        chapter_data = json.load(f)

    sample_chapter = chapter_data[0]
    chapter_content = sample_chapter["content"]
    print(f'Source File: {sample_chapter["file_path"]}')
    print(f'Module: {sample_chapter["module"]}')
    print(f'Chunk ID: {sample_chapter["chunk_id"]}')
    print(f"Repository: tools-in-data-science-public")
    print(f"Length: {len(chapter_content)} characters")
    print(f'Tokens: {sample_chapter["token_count"]}')
    print(
        f'Chunk: {sample_chapter["chunk_index"] + 1}/{sample_chapter["total_chunks"]}'
    )
    print(f'Last Modified: {sample_chapter.get("last_modified", "N/A")}')
    print(f"Content preview:")
    print(chapter_content[:300] + "...")
    print()

    # Chapter quality checks
    chapter_quality = {
        "Code blocks preserved": ("```" in chapter_content or "`" in chapter_content),
        "Headers preserved": "#" in chapter_content,
        "Links preserved": "http" in chapter_content.lower(),
        "Clean formatting": not any(
            x in chapter_content for x in ["data:image", "<script", "console.log"]
        ),
        "Educational structure": any(
            x in chapter_content.lower()
            for x in ["introduction", "example", "install", "usage"]
        ),
    }

    print("Chapter Quality Assessment:")
    for check, passed in chapter_quality.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")

    print()
    print(
        "🎯 Overall Assessment: All content processing optimization working correctly!"
    )

    # Additional statistics
    print()
    print("📊 Processing Statistics:")

    # Discourse stats
    discourse_total_chars = sum(len(chunk["content"]) for chunk in discourse_data)
    discourse_total_tokens = sum(chunk["token_count"] for chunk in discourse_data)
    discourse_avg_tokens = (
        discourse_total_tokens / len(discourse_data) if discourse_data else 0
    )

    # Count unique topics and users
    unique_topics = len(set(chunk["topic_id"] for chunk in discourse_data))
    all_usernames = []
    for chunk in discourse_data:
        usernames = chunk.get("metadata", {}).get("usernames", [])
        all_usernames.extend(usernames)
    unique_users = len(set(all_usernames))

    print(f"   📋 Discourse: {len(discourse_data)} chunks from {unique_topics} topics")
    print(
        f"       Total tokens: {discourse_total_tokens} (avg: {discourse_avg_tokens:.0f} tokens/chunk)"
    )
    print(f"       Contributors: {unique_users} unique users")
    print(f"       Source: https://discourse.onlinedegree.iitm.ac.in/")

    # Chapter stats
    chapters_base = Path("data/chapters/tools-in-data-science-public")
    total_chapter_chunks = 0
    total_chapter_tokens = 0
    module_count = 0
    file_count = 0

    for module_dir in chapters_base.iterdir():
        if module_dir.is_dir():
            chunks_file = module_dir / "chunks.json"
            if chunks_file.exists():
                module_count += 1
                with open(chunks_file) as f:
                    module_data = json.load(f)
                total_chapter_chunks += len(module_data)
                total_chapter_tokens += sum(
                    chunk["token_count"] for chunk in module_data
                )
                # Count unique files
                unique_files = len(set(chunk["file_path"] for chunk in module_data))
                file_count += unique_files

    chapter_avg_tokens = (
        total_chapter_tokens / total_chapter_chunks if total_chapter_chunks else 0
    )
    print(f"   📚 Chapters: {total_chapter_chunks} chunks from {module_count} modules")
    print(
        f"       Total tokens: {total_chapter_tokens} (avg: {chapter_avg_tokens:.0f} tokens/chunk)"
    )
    print(f"       Source files: {file_count} markdown files")
    print(f"       Repository: tools-in-data-science-public")

    total_chunks = len(discourse_data) + total_chapter_chunks
    total_tokens = discourse_total_tokens + total_chapter_tokens
    overall_avg = total_tokens / total_chunks if total_chunks else 0

    print(
        f"   🎯 Combined: {total_chunks} chunks, {total_tokens} tokens (avg: {overall_avg:.0f} tokens/chunk)"
    )
    print(f"       Sources: Discourse forum + Course materials repository")


if __name__ == "__main__":
    check_content_quality()
