# ******************** pydantic models ********************#
"""
Data models for the Teaching Assistant API.
Defines request/response schemas and validation.
"""

from typing import List, Optional
from pydantic import BaseModel


# ******************** request models ********************#
class QuestionRequest(BaseModel):
    """Request model for questions submitted to the API."""

    question: str
    image: Optional[str] = None  # base64-encoded
    # Optional model parameters
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None


# ******************** response models ********************#
class LinkObject(BaseModel):
    """Model for structured link objects in responses."""

    url: str
    text: str


class QuestionResponse(BaseModel):
    """Response model for answered questions."""

    answer: str
    sources: Optional[List[str]] = None  # Keep for backward compatibility
    links: Optional[List[LinkObject]] = None  # New field for structured links
