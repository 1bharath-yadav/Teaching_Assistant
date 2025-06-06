#!/usr/bin/env python3
"""
Enhanced Discourse Processing Script with Image Processing

This script processes discourse posts and extracts image information
without embedding images as base64 to avoid polluting text embeddings.

Features:
- Processes raw scraped_posts.json
- Extracts text from images using OCR
- Stores image metadata separately
- Creates enhanced documents for indexing
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import required modules
from image_processor import ImageProcessor

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import config for embedding dimensions
try:
    from lib.config import get_config

    config = get_config()
    EMBEDDING_DIMENSIONS = (
        config.embeddings.ollama.dimensions
        if config.embeddings.provider == "ollama"
        else config.embeddings.openai.dimensions
    )
except ImportError:
    logger.warning("Could not load config, using default embedding dimensions (768)")
    EMBEDDING_DIMENSIONS = 768

# Try to import embeddings with proper path handling
try:
    # First try to import from the working directory setup
    sys.path.insert(0, str(project_root))
    from lib.embeddings import generate_embedding

    EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Embeddings not available: {e}")
    EMBEDDINGS_AVAILABLE = False


class EnhancedDiscourseProcessor:
    """Processes discourse posts with image extraction and analysis."""

    def __init__(self, enable_image_processing: bool = True, enable_ocr: bool = False):
        """
        Initialize the processor.

        Args:
            enable_image_processing: Whether to process images
            enable_ocr: Whether to use OCR (requires easyocr installation)
        """
        self.enable_image_processing = enable_image_processing
        self.enable_ocr = enable_ocr

        if self.enable_image_processing:
            try:
                self.image_processor = ImageProcessor(use_ocr=enable_ocr)
                logger.info(f"Image processor initialized (OCR: {enable_ocr})")
            except Exception as e:
                logger.error(f"Failed to initialize image processor: {e}")
                self.enable_image_processing = False
                self.image_processor = None
        else:
            self.image_processor = None

    def process_discourse_posts(
        self, scraped_file: str, processed_file: Optional[str] = None
    ) -> List[Dict]:
        """
        Process discourse posts with image extraction.

        Args:
            scraped_file: Path to scraped_posts.json
            processed_file: Optional path to existing processed.json

        Returns:
            List of processed documents with image data
        """
        # Load scraped posts
        with open(scraped_file, "r", encoding="utf-8") as f:
            scraped_posts = json.load(f)

        # Load existing processed data if available
        processed_data = {}
        if processed_file and Path(processed_file).exists():
            with open(processed_file, "r", encoding="utf-8") as f:
                existing_processed = json.load(f)
                # Create lookup by topic_id
                for doc in existing_processed:
                    processed_data[str(doc.get("topic_id", ""))] = doc

        logger.info(f"Processing {len(scraped_posts)} scraped posts")
        logger.info(f"Found {len(processed_data)} existing processed documents")

        # Group posts by topic
        topics = {}
        for post in scraped_posts:
            topic_id = post["topic_id"]
            if topic_id not in topics:
                topics[topic_id] = {
                    "topic_id": topic_id,
                    "topic_title": post["topic_title"],
                    "posts": [],
                }
            topics[topic_id]["posts"].append(post)

        logger.info(f"Found {len(topics)} unique topics")

        # Process each topic
        enhanced_documents = []
        for topic_id, topic_data in topics.items():
            try:
                enhanced_doc = self._process_topic(
                    topic_data, processed_data.get(str(topic_id))
                )
                enhanced_documents.append(enhanced_doc)
            except Exception as e:
                logger.error(f"Failed to process topic {topic_id}: {e}")
                continue

        logger.info(f"Successfully processed {len(enhanced_documents)} topics")
        return enhanced_documents

    def _process_topic(
        self, topic_data: Dict, existing_doc: Optional[Dict] = None
    ) -> Dict:
        """
        Process a single topic with all its posts.

        Args:
            topic_data: Topic data with posts
            existing_doc: Existing processed document (if any)

        Returns:
            Enhanced document with image data
        """
        topic_id = topic_data["topic_id"]
        posts = topic_data["posts"]

        # Start with existing document or create new one
        if existing_doc:
            doc = existing_doc.copy()
        else:
            # Create basic document structure
            doc = {
                "topic_id": topic_id,
                "topic_title": topic_data["topic_title"],
                "content": "",
                "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{topic_id}",
                "timestamp": posts[0]["created_at"] if posts else "",
                "metadata": {
                    "post_count": len(posts),
                    "usernames": [],
                    "mentions": [],
                    "keywords": [],
                },
            }

        # Combine all post content
        all_content = []
        all_raw_content = []  # Keep HTML for image processing
        usernames = set()

        for post in posts:
            content = post.get("post_content", "").strip()
            if content:
                all_content.append(content)
                all_raw_content.append(content)  # Keep raw HTML

            username = post.get("username", "").strip()
            if username:
                usernames.add(username)

        # Update content (clean text for embeddings)
        from bs4 import BeautifulSoup

        clean_content_parts = []
        for content in all_content:
            if content:
                soup = BeautifulSoup(content, "html.parser")
                clean_text = soup.get_text(separator=" ", strip=True)
                if clean_text:
                    clean_content_parts.append(clean_text)

        doc["content"] = "\n\n".join(clean_content_parts)

        # Update metadata
        doc["metadata"]["usernames"] = list(usernames)
        doc["metadata"]["post_count"] = len(posts)

        # Process images from all posts
        if self.enable_image_processing and self.image_processor:
            try:
                image_data = self._process_topic_images(all_raw_content)
                doc.update(image_data)

                # Add extracted text to content for better searchability
                if image_data.get("extracted_text_from_images"):
                    doc[
                        "content"
                    ] += f"\n\nExtracted from images: {image_data['extracted_text_from_images']}"

            except Exception as e:
                logger.error(f"Failed to process images for topic {topic_id}: {e}")
                # Set default image values
                doc.update(
                    {
                        "has_images": False,
                        "image_urls": [],
                        "image_descriptions": [],
                        "extracted_text_from_images": "",
                    }
                )
        else:
            # Set default image values when processing is disabled
            doc.update(
                {
                    "has_images": False,
                    "image_urls": [],
                    "image_descriptions": [],
                    "extracted_text_from_images": "",
                }
            )

        # Generate embedding if not present
        if "embedding" not in doc or not doc["embedding"]:
            if EMBEDDINGS_AVAILABLE:
                try:
                    from lib.embeddings import (
                        generate_embedding,
                    )  # Import here to avoid issues

                    embedding_text = f"{doc['topic_title']} {doc['content']}"
                    doc["embedding"] = generate_embedding(embedding_text)
                    logger.info(f"Generated embedding for topic {topic_id}")
                except Exception as e:
                    logger.error(
                        f"Failed to generate embedding for topic {topic_id}: {e}"
                    )
                    doc["embedding"] = [0.0] * EMBEDDING_DIMENSIONS  # Default embedding
            else:
                logger.warning(
                    f"Embeddings not available, using default for topic {topic_id}"
                )
                doc["embedding"] = [0.0] * EMBEDDING_DIMENSIONS  # Default embedding

        return doc

    def _process_topic_images(self, raw_content_list: List[str]) -> Dict:
        """
        Process images from all posts in a topic.

        Args:
            raw_content_list: List of raw HTML content from posts

        Returns:
            Dictionary with image data
        """
        all_image_urls = []
        all_image_descriptions = []
        all_extracted_text = []

        for content in raw_content_list:
            if not content.strip():
                continue

            try:
                image_data = self.image_processor.process_post_images(content)

                if image_data.get("has_images"):
                    all_image_urls.extend(image_data.get("image_urls", []))
                    all_image_descriptions.extend(
                        image_data.get("image_descriptions", [])
                    )

                    extracted_text = image_data.get("extracted_text_from_images", "")
                    if extracted_text:
                        all_extracted_text.append(extracted_text)

            except Exception as e:
                logger.error(f"Failed to process images in post content: {e}")
                continue

        # Remove duplicates while preserving order
        unique_urls = []
        seen_urls = set()
        for url in all_image_urls:
            if url not in seen_urls:
                unique_urls.append(url)
                seen_urls.add(url)

        return {
            "has_images": len(unique_urls) > 0,
            "image_urls": unique_urls,
            "image_descriptions": all_image_descriptions,
            "extracted_text_from_images": " | ".join(all_extracted_text),
        }


def main():
    """Main function to run the enhanced discourse processing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process discourse posts with image extraction"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="scraped_posts.json",
        help="Input file with scraped posts",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="enhanced_processed.json",
        help="Output file for processed documents",
    )
    parser.add_argument(
        "--existing",
        "-e",
        default="processed.json",
        help="Existing processed file to use as base",
    )
    parser.add_argument(
        "--no-images", action="store_true", help="Disable image processing"
    )
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR for text extraction from images",
    )

    args = parser.parse_args()

    # Setup paths
    input_file = Path(args.input)
    output_file = Path(args.output)
    existing_file = Path(args.existing) if args.existing else None

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1

    # Create processor
    processor = EnhancedDiscourseProcessor(
        enable_image_processing=not args.no_images, enable_ocr=args.enable_ocr
    )

    # Process documents
    logger.info("Starting enhanced discourse processing...")
    start_time = datetime.now()

    enhanced_docs = processor.process_discourse_posts(
        str(input_file),
        str(existing_file) if existing_file and existing_file.exists() else None,
    )

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_docs, f, indent=2, ensure_ascii=False)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"Processing complete!")
    logger.info(f"Input: {len(enhanced_docs)} topics processed")
    logger.info(f"Output: {output_file}")
    logger.info(f"Duration: {duration:.2f} seconds")

    # Show image statistics
    total_images = sum(len(doc.get("image_urls", [])) for doc in enhanced_docs)
    topics_with_images = sum(1 for doc in enhanced_docs if doc.get("has_images", False))

    logger.info(f"Image statistics:")
    logger.info(f"  Total images found: {total_images}")
    logger.info(f"  Topics with images: {topics_with_images}/{len(enhanced_docs)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
