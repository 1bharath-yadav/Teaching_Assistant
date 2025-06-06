"""
Image Processing Module for Discourse Posts

This module processes images found in discourse posts to extract useful information
without embedding the images as base64 data to avoid polluting text embeddings.

Features:
- Extract image URLs and metadata from HTML content
- Extract text from images using OCR (Optical Character Recognition)
- Generate image descriptions using AI models
- Store image metadata separately from text content
"""

import re
import requests
from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup
import base64
from PIL import Image
import io
import os
import logging
from urllib.parse import urljoin, urlparse
import time
import hashlib
import json
from pathlib import Path

# OCR libraries
try:
    import easyocr

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: easyocr not installed. OCR functionality will be disabled.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processes images from discourse posts to extract useful information."""

    def __init__(self, use_ocr: bool = True, ocr_languages: List[str] = ["en"]):
        """
        Initialize the image processor.

        Args:
            use_ocr: Whether to use OCR for text extraction
            ocr_languages: List of languages for OCR processing
        """
        self.use_ocr = use_ocr and OCR_AVAILABLE
        self.ocr_languages = ocr_languages

        if self.use_ocr:
            try:
                self.ocr_reader = easyocr.Reader(ocr_languages)
                logger.info(f"OCR initialized with languages: {ocr_languages}")
            except Exception as e:
                logger.error(f"Failed to initialize OCR: {e}")
                self.use_ocr = False

        # Create cache directory for images
        self.cache_dir = "image_cache"
        self.downloads_dir = Path(self.cache_dir) / "downloads"
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)

        # Image tracking
        self.image_registry_file = Path(self.cache_dir) / "image_registry.json"
        self.image_registry = self._load_image_registry()

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def _load_image_registry(self) -> Dict:
        """Load the image registry from file or create a new one."""
        if self.image_registry_file.exists():
            try:
                with open(self.image_registry_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load image registry: {e}")
        return {}

    def _save_image_registry(self):
        """Save the image registry to file."""
        try:
            with open(self.image_registry_file, "w") as f:
                json.dump(self.image_registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save image registry: {e}")

    def _generate_image_id(self, url: str) -> str:
        """Generate a unique ID for an image based on its URL."""
        # Create a hash of the URL for a unique but deterministic ID
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"img_{url_hash}"

    def _get_file_extension(self, url: str, content_type: str = None) -> str:
        """Get appropriate file extension for the image."""
        # Try to get extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()

        if path.endswith((".jpg", ".jpeg")):
            return ".jpg"
        elif path.endswith(".png"):
            return ".png"
        elif path.endswith(".gif"):
            return ".gif"
        elif path.endswith(".webp"):
            return ".webp"
        elif path.endswith(".bmp"):
            return ".bmp"
        elif path.endswith(".svg"):
            return ".svg"

        # Try to get from content type
        if content_type:
            if "jpeg" in content_type or "jpg" in content_type:
                return ".jpg"
            elif "png" in content_type:
                return ".png"
            elif "gif" in content_type:
                return ".gif"
            elif "webp" in content_type:
                return ".webp"
            elif "bmp" in content_type:
                return ".bmp"
            elif "svg" in content_type:
                return ".svg"

        # Default to jpg
        return ".jpg"

    def extract_images_from_html(self, html_content: str) -> List[Dict]:
        """
        Extract image information from HTML content.

        Args:
            html_content: HTML content containing images

        Returns:
            List of dictionaries containing image metadata
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        images = []

        # Find all img tags
        img_tags = soup.find_all("img")

        for img in img_tags:
            src = img.get("src", "")
            alt = img.get("alt", "")
            title = img.get("title", "")
            width = img.get("width", "")
            height = img.get("height", "")

            # Skip emoji images
            if "emoji" in src.lower() or "emoji" in alt.lower():
                continue

            # Skip very small images (likely icons)
            try:
                if width and height:
                    w, h = int(width), int(height)
                    if w < 50 and h < 50:
                        continue
            except ValueError:
                pass

            image_info = {
                "url": src,
                "alt_text": alt,
                "title": title,
                "width": width,
                "height": height,
                "context": self._extract_context(img),
                "type": self._classify_image_type(src, alt, title),
            }

            images.append(image_info)

        # Also look for lightbox wrappers (discourse-specific)
        lightbox_wrappers = soup.find_all("div", class_="lightbox-wrapper")
        for wrapper in lightbox_wrappers:
            a_tag = wrapper.find("a", class_="lightbox")
            if a_tag:
                href = a_tag.get("href", "")
                title = a_tag.get("title", "")

                img_tag = wrapper.find("img")
                if img_tag:
                    src = img_tag.get("src", "")
                    alt = img_tag.get("alt", "")

                    image_info = {
                        "url": href,  # Use high-res URL from lightbox
                        "thumbnail_url": src,
                        "alt_text": alt,
                        "title": title,
                        "width": img_tag.get("width", ""),
                        "height": img_tag.get("height", ""),
                        "context": self._extract_context(wrapper),
                        "type": self._classify_image_type(href, alt, title),
                    }

                    images.append(image_info)

        return images

    def _extract_context(self, element) -> str:
        """Extract surrounding text context for an image."""
        context_text = ""

        # Get preceding text
        prev_sibling = element.previous_sibling
        if prev_sibling and hasattr(prev_sibling, "get_text"):
            context_text += prev_sibling.get_text(strip=True)[-100:]  # Last 100 chars

        # Get following text
        next_sibling = element.next_sibling
        if next_sibling and hasattr(next_sibling, "get_text"):
            context_text += (
                " " + next_sibling.get_text(strip=True)[:100]
            )  # First 100 chars

        # Get parent context
        parent = element.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            if len(parent_text) < 500:  # Only if parent text is not too long
                context_text = parent_text

        return context_text.strip()

    def _classify_image_type(self, url: str, alt: str, title: str) -> str:
        """Classify the type of image based on URL and metadata."""
        text = f"{url} {alt} {title}".lower()

        if "screenshot" in text or "screen" in text:
            return "screenshot"
        elif "error" in text or "exception" in text:
            return "error"
        elif "code" in text or "terminal" in text or "console" in text:
            return "code"
        elif "diagram" in text or "chart" in text or "graph" in text:
            return "diagram"
        elif "email" in text or "mail" in text:
            return "email"
        elif "assignment" in text or "homework" in text:
            return "assignment"
        else:
            return "general"

    def download_image(self, url: str, max_size_mb: int = 5) -> Optional[bytes]:
        """
        Download an image from a URL and save it locally.

        Args:
            url: Image URL
            max_size_mb: Maximum size in MB

        Returns:
            Image bytes or None if failed
        """
        if not url:
            return None

        # Generate image ID and check if already processed
        image_id = self._generate_image_id(url)

        # Check if we already have this image
        if image_id in self.image_registry:
            cached_info = self.image_registry[image_id]
            local_path = Path(cached_info.get("local_path", ""))

            if local_path.exists():
                logger.debug(f"Using cached image: {image_id}")
                try:
                    with open(local_path, "rb") as f:
                        return f.read()
                except Exception as e:
                    logger.warning(f"Failed to read cached image {image_id}: {e}")
                    # Continue to download again

        try:
            # Check if it's a data URL
            if url.startswith("data:image/"):
                # Extract base64 data
                header, data = url.split(",", 1)
                image_bytes = base64.b64decode(data)

                # Save to local file
                content_type = (
                    header.split(";")[0].split(":")[1]
                    if ";" in header
                    else "image/jpeg"
                )
                extension = self._get_file_extension(url, content_type)
                local_path = self.downloads_dir / f"{image_id}{extension}"

                with open(local_path, "wb") as f:
                    f.write(image_bytes)

                # Update registry
                self.image_registry[image_id] = {
                    "url": url,
                    "local_path": str(local_path),
                    "size_bytes": len(image_bytes),
                    "content_type": content_type,
                    "is_valid": True,
                    "downloaded_at": time.time(),
                }
                self._save_image_registry()

                return image_bytes

            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()

            # Check content length
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > max_size_mb * 1024 * 1024:
                logger.warning(f"Image too large: {url} ({content_length} bytes)")
                return None

            # Get content type and file extension
            content_type = response.headers.get("content-type", "image/jpeg")
            extension = self._get_file_extension(url, content_type)
            local_path = self.downloads_dir / f"{image_id}{extension}"

            # Download in chunks
            content = b""
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    content += chunk
                    f.write(chunk)
                    if len(content) > max_size_mb * 1024 * 1024:
                        logger.warning(f"Image too large during download: {url}")
                        # Remove incomplete file
                        try:
                            local_path.unlink()
                        except:
                            pass
                        return None

            # Validate the image
            is_valid = self._validate_image(local_path)

            # Update registry
            self.image_registry[image_id] = {
                "url": url,
                "local_path": str(local_path),
                "size_bytes": len(content),
                "content_type": content_type,
                "is_valid": is_valid,
                "downloaded_at": time.time(),
            }
            self._save_image_registry()

            if not is_valid:
                logger.warning(f"Downloaded image is not valid: {url}")
                return None

            return content

        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            # Update registry with error info
            self.image_registry[image_id] = {
                "url": url,
                "local_path": None,
                "size_bytes": 0,
                "content_type": None,
                "is_valid": False,
                "error": str(e),
                "downloaded_at": time.time(),
            }
            self._save_image_registry()
            return None

    def _validate_image(self, file_path: Path) -> bool:
        """Validate that a file is a proper image."""
        try:
            with Image.open(file_path) as img:
                # Try to load the image
                img.verify()

            # Re-open to check dimensions (verify() closes the file)
            with Image.open(file_path) as img:
                width, height = img.size
                if width < 10 or height < 10:
                    return False
                if width > 5000 or height > 5000:
                    logger.warning(f"Very large image: {width}x{height}")

                return True

        except Exception as e:
            logger.error(f"Image validation failed for {file_path}: {e}")
            return False

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from an image using OCR.

        Args:
            image_bytes: Image data as bytes

        Returns:
            Extracted text
        """
        if not self.use_ocr:
            return ""

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Check if image is valid and not too small/large
            width, height = image.size
            if width < 50 or height < 50:
                logger.debug(f"Image too small for OCR: {width}x{height}")
                return ""
            if width > 2000 or height > 2000:
                logger.debug(f"Image too large for OCR: {width}x{height}")
                return ""

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Convert PIL Image to numpy array for EasyOCR
            import numpy as np

            image_array = np.array(image)

            # Use OCR to extract text with timeout protection
            try:
                results = self.ocr_reader.readtext(image_array)
            except Exception as ocr_error:
                logger.error(f"OCR processing failed: {ocr_error}")
                return ""

            # Extract text from results
            extracted_text = []
            for bbox, text, confidence in results:
                # Check if confidence is a number and above threshold
                try:
                    conf_score = (
                        float(confidence)
                        if isinstance(confidence, (int, float, str))
                        else 0.0
                    )
                    if conf_score > 0.5:  # Only include high-confidence text
                        extracted_text.append(text.strip())
                except (ValueError, TypeError):
                    # If confidence is not a valid number, skip
                    continue

            return " ".join(extracted_text)

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            return ""

    def get_image_registry_info(self) -> Dict:
        """Get information about tracked images."""
        total_images = len(self.image_registry)
        valid_images = sum(
            1 for info in self.image_registry.values() if info.get("is_valid", False)
        )
        invalid_images = total_images - valid_images
        total_size_mb = sum(
            info.get("size_bytes", 0) for info in self.image_registry.values()
        ) / (1024 * 1024)

        return {
            "total_images": total_images,
            "valid_images": valid_images,
            "invalid_images": invalid_images,
            "total_size_mb": round(total_size_mb, 2),
            "cache_directory": str(self.cache_dir),
            "downloads_directory": str(self.downloads_dir),
        }

    def process_post_images(self, post_content: str) -> Dict:
        """
        Process all images in a discourse post.

        Args:
            post_content: HTML content of the post

        Returns:
            Dictionary containing processed image information
        """
        images = self.extract_images_from_html(post_content)

        if not images:
            return {
                "has_images": False,
                "image_urls": [],
                "image_descriptions": [],
                "extracted_text_from_images": "",
                "image_ids": [],
                "image_registry_summary": self.get_image_registry_info(),
            }

        image_urls = []
        image_descriptions = []
        image_ids = []
        all_extracted_text = []

        for img_info in images:
            url = img_info["url"]
            if not url:
                continue

            # Generate image ID for tracking
            image_id = self._generate_image_id(url)

            image_urls.append(url)
            image_ids.append(image_id)

            # Create description from metadata
            description_parts = []
            description_parts.append(f"ID: {image_id}")
            if img_info["alt_text"]:
                description_parts.append(f"Alt: {img_info['alt_text']}")
            if img_info["title"]:
                description_parts.append(f"Title: {img_info['title']}")
            if img_info["type"]:
                description_parts.append(f"Type: {img_info['type']}")
            if img_info["context"]:
                description_parts.append(f"Context: {img_info['context'][:200]}...")

            description = " | ".join(description_parts)
            image_descriptions.append(description)

            # Extract text from image if OCR is enabled
            if self.use_ocr:
                logger.info(f"Processing image {image_id}: {url}")
                image_bytes = self.download_image(url)
                if image_bytes:
                    extracted_text = self.extract_text_from_image(image_bytes)
                    if extracted_text:
                        all_extracted_text.append(
                            f"From {img_info['type']} image ({image_id}): {extracted_text}"
                        )
                        logger.info(
                            f"Extracted text from {image_id}: {extracted_text[:100]}..."
                        )
                    else:
                        logger.debug(f"No text extracted from {image_id}")
                else:
                    logger.warning(f"Failed to download image {image_id}")

                # Add a small delay to avoid overwhelming servers
                time.sleep(0.5)

        return {
            "has_images": True,
            "image_urls": image_urls,
            "image_descriptions": image_descriptions,
            "extracted_text_from_images": " | ".join(all_extracted_text),
            "image_ids": image_ids,
            "image_registry_summary": self.get_image_registry_info(),
        }


def main():
    """Test the image processor with sample HTML content."""
    processor = ImageProcessor()

    # Test HTML with images
    test_html = """
    <p>Here's a screenshot of the error:</p>
    <div class="lightbox-wrapper">
        <a class="lightbox" href="https://example.com/error.png" title="Error Screenshot">
            <img src="https://example.com/error_thumb.png" alt="Error Screenshot" width="690" height="388">
        </a>
    </div>
    <p>As you can see, the system is throwing an exception.</p>
    """

    result = processor.process_post_images(test_html)
    print("Processed images:", result)


if __name__ == "__main__":
    main()
