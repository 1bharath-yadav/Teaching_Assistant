#!/usr/bin/env python3
"""
Optimized Chapter Chunking Script

This script replaces the bash createchunks.sh script with a more robust Python implementation.
It processes markdown files from the tools-in-data-science-public repository and creates
optimized chunks for embedding.

Features:
- Intelligent markdown-aware chunking
- Configurable chunk sizes based on embedding provider
- Better content validation and cleaning
- Metadata extraction
- Resume capability for interrupted processing
"""

import json
import sys
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import time

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from lib.config import get_config
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for chunking parameters."""

    chunk_size: int
    chunk_overlap: int
    min_chunk_size: int
    max_chunk_size: int

    @classmethod
    def from_embedding_provider(cls, provider: str, dimensions: int):
        """Create chunking config optimized for embedding provider."""
        if provider == "openai":
            if dimensions >= 3000:  # large model
                return cls(1500, 300, 100, 8000)
            else:  # small model
                return cls(1000, 200, 50, 6000)
        elif provider == "ollama":
            if dimensions >= 1000:  # large model
                return cls(1200, 250, 80, 7000)
            else:  # small model
                return cls(800, 150, 50, 4000)
        else:
            # Default safe values
            return cls(1000, 200, 50, 6000)


class OptimizedChunker:
    """Optimized markdown chunker for tools-in-data-science content."""

    def __init__(self):
        """Initialize the chunker with configuration."""
        self.config = get_config()
        self.embedding_config = self._get_embedding_config()
        self.chunking_config = ChunkingConfig.from_embedding_provider(
            self.embedding_config["provider"], self.embedding_config["dimensions"]
        )

        logger.info(
            f"Initialized chunker for {self.embedding_config['provider']} embeddings"
        )
        logger.info(
            f"Chunk size: {self.chunking_config.chunk_size}, overlap: {self.chunking_config.chunk_overlap}"
        )

        # Setup text splitters
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
            ]
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunking_config.chunk_size,
            chunk_overlap=self.chunking_config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def _get_embedding_config(self) -> Dict:
        """Get embedding configuration."""
        provider = self.config.embeddings.provider
        if provider == "openai":
            return {
                "provider": "openai",
                "model": self.config.embeddings.openai.model,
                "dimensions": self.config.embeddings.openai.dimensions,
            }
        elif provider == "ollama":
            return {
                "provider": "ollama",
                "model": self.config.embeddings.ollama.model,
                "dimensions": self.config.embeddings.ollama.dimensions,
            }
        else:
            return {"provider": "unknown", "model": "unknown", "dimensions": 1000}

    def clean_markdown_content(self, content: str) -> str:
        """Clean and normalize markdown content."""
        # Remove excessive whitespace
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        # Fix common markdown issues
        content = re.sub(
            r"```(\w+)?\n", r"```\1\n", content
        )  # Fix code block languages
        content = re.sub(
            r"\n```\n", "\n```\n\n", content
        )  # Add spacing after code blocks

        # Remove HTML comments
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # Normalize headers
        content = re.sub(
            r"^#{1,6}\s*(.+?)#*$",
            lambda m: "#" * len(m.group(0).split()[0]) + " " + m.group(1).strip(),
            content,
            flags=re.MULTILINE,
        )

        return content.strip()

    def extract_metadata(self, content: str, file_path: str) -> Dict:
        """Extract metadata from markdown content."""
        metadata = {
            "has_code": bool(re.search(r"```|`[^`]+`", content)),
            "has_images": bool(re.search(r"!\[.*?\]\(.*?\)", content)),
            "has_links": bool(re.search(r"\[.*?\]\(.*?\)", content)),
            "has_tables": bool(re.search(r"\|.*?\|", content)),
            "word_count": len(content.split()),
            "char_count": len(content),
            "header_count": len(re.findall(r"^#+\s", content, re.MULTILINE)),
            "file_path": file_path,
        }

        # Extract first header as title
        title_match = re.search(r"^#+\s+(.+?)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        else:
            metadata["title"] = Path(file_path).stem

        return metadata

    def validate_chunk(self, chunk: Dict) -> bool:
        """Validate chunk quality."""
        content = chunk.get("page_content", "")

        # Skip very short chunks
        if len(content) < self.chunking_config.min_chunk_size:
            return False

        # Skip very long chunks
        if len(content) > self.chunking_config.max_chunk_size:
            return False

        # Skip chunks that are mostly special characters
        alpha_count = sum(c.isalnum() for c in content)
        if alpha_count / len(content) < 0.3:
            return False

        # Skip chunks that are just headers
        if re.match(r"^\s*#+\s+.+?\s*$", content.strip()):
            return False

        return True

    def create_chunk_id(self, file_path: str, chunk_index: int, content: str) -> str:
        """Create a unique, stable ID for a chunk."""
        # Create content hash for stability
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

        # Clean file path for ID
        clean_path = file_path.replace("/", "_").replace(".md", "")

        return f"{clean_path}#{chunk_index}#{content_hash}"

    def process_file(self, file_path: Path, base_dir: Path) -> List[Dict]:
        """Process a single markdown file into chunks."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Clean content
            clean_content = self.clean_markdown_content(content)

            if not clean_content or len(clean_content) < 100:
                logger.warning(f"Skipping file with insufficient content: {file_path}")
                return []

            # Extract file metadata
            relative_path = str(file_path.relative_to(base_dir))
            file_metadata = self.extract_metadata(clean_content, relative_path)

            # First split by headers to preserve structure
            header_splits = self.header_splitter.split_text(clean_content)

            # Then chunk each section
            all_chunks = []
            for header_doc in header_splits:
                # Add header context to each chunk
                header_context = ""
                if header_doc.metadata:
                    headers = []
                    for level in ["h1", "h2", "h3", "h4"]:
                        if level in header_doc.metadata:
                            headers.append(
                                f"{'#' * int(level[1:])} {header_doc.metadata[level]}"
                            )
                    if headers:
                        header_context = "\n".join(headers) + "\n\n"

                # Split the content
                content_chunks = self.text_splitter.split_text(header_doc.page_content)

                for chunk_content in content_chunks:
                    full_chunk_content = header_context + chunk_content

                    chunk = {
                        "page_content": full_chunk_content,
                        "metadata": {
                            **file_metadata,
                            **header_doc.metadata,
                            "chunk_type": "text_with_context",
                        },
                    }

                    if self.validate_chunk(chunk):
                        all_chunks.append(chunk)

            # Create final chunk documents with IDs
            final_chunks = []
            for i, chunk in enumerate(all_chunks):
                chunk_id = self.create_chunk_id(relative_path, i, chunk["page_content"])

                final_chunk = {
                    "id": chunk_id,
                    "content": chunk["page_content"],
                    "metadata": chunk["metadata"],
                }

                final_chunks.append(final_chunk)

            logger.info(f"Processed {file_path.name}: {len(final_chunks)} chunks")
            return final_chunks

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []

    def process_module(self, module_dir: Path, base_dir: Path) -> List[Dict]:
        """Process all markdown files in a module directory."""
        chunks = []

        # Find all markdown files
        md_files = list(module_dir.glob("*.md"))

        if not md_files:
            logger.warning(f"No markdown files found in {module_dir}")
            return []

        logger.info(f"Processing {len(md_files)} files in {module_dir.name}")

        for md_file in md_files:
            file_chunks = self.process_file(md_file, base_dir)
            chunks.extend(file_chunks)

        return chunks

    def process_repository(self, repo_dir: Optional[str] = None) -> bool:
        """Process the entire tools-in-data-science-public repository."""
        if repo_dir is None:
            repo_dir = current_dir / "chapters" / "tools-in-data-science-public"

        repo_path = Path(repo_dir)

        if not repo_path.exists():
            logger.error(f"Repository directory not found: {repo_path}")
            return False

        # Define modules to process
        modules = [
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

        # Process each module
        all_results = {}
        total_chunks = 0

        for module in modules:
            module_dir = repo_path / module

            if not module_dir.exists():
                logger.warning(f"Module directory not found: {module_dir}")
                continue

            logger.info(f"Processing module: {module}")

            # Process module
            chunks = self.process_module(module_dir, repo_path)

            if chunks:
                # Save module chunks
                output_file = module_dir / "chunks.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, indent=2, ensure_ascii=False)

                logger.info(f"Saved {len(chunks)} chunks to {output_file}")
                all_results[module] = len(chunks)
                total_chunks += len(chunks)
            else:
                logger.warning(f"No valid chunks generated for module: {module}")

        # Save summary
        summary = {
            "total_chunks": total_chunks,
            "modules_processed": len(all_results),
            "chunks_per_module": all_results,
            "embedding_provider": self.embedding_config["provider"],
            "embedding_model": self.embedding_config["model"],
            "chunking_config": {
                "chunk_size": self.chunking_config.chunk_size,
                "chunk_overlap": self.chunking_config.chunk_overlap,
                "min_chunk_size": self.chunking_config.min_chunk_size,
                "max_chunk_size": self.chunking_config.max_chunk_size,
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        summary_file = repo_path / "chunking_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Processing complete! Total chunks: {total_chunks}")
        logger.info(f"Summary saved to: {summary_file}")

        return True


def main():
    """Main function to run the optimized chunker."""
    chunker = OptimizedChunker()

    # Clone repository if it doesn't exist
    repo_dir = current_dir / "chapters" / "tools-in-data-science-public"
    if not repo_dir.exists():
        logger.info("Cloning tools-in-data-science-public repository...")
        import subprocess

        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/sanand0/tools-in-data-science-public.git",
                    str(repo_dir),
                ],
                check=True,
            )
            logger.info("Repository cloned successfully!")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            return False

    # Process the repository
    success = chunker.process_repository()

    if success:
        logger.info("Chunking completed successfully!")
    else:
        logger.error("Chunking failed!")

    return success


if __name__ == "__main__":
    main()
