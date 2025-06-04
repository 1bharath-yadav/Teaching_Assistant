import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from process import *
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Teaching Assistant API",
    description="API for answering student queries from TDS course",
    version="1.0.0",
)

# Add CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files for the frontend
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(frontend_build_path / "static")),
        name="static",
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# Serve the frontend at /chat
@app.get("/chat")
async def serve_chat():
    """Serve the chat frontend"""

    frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
    index_file = frontend_build_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))


# Add explicit OPTIONS handler for the API endpoint
@app.options("/api/v1/ask")
async def options_ask():
    return {"message": "OK"}


# ------------- """Main endpoint to ask questions about the TDS course""" -----------


@app.post("/api/v1/ask", response_model=QuestionResponse)
async def ask_question(request: Request, payload: QuestionRequest) -> QuestionResponse:
    start_time = time.time()
    try:
        if payload.image:
            logger.info("Image data received with question")

        classified_collections = await classify_question(payload)
        logger.info(f"Classified collections: {classified_collections['collections']}")

        # Handle image and pdf processing if image is provided
        enhanced_question = payload.question
        if payload.image:
            try:
                logger.info("Processing image with OCR...")
                ocr_text = process_image_with_ocr(payload.image)
                if ocr_text:
                    enhanced_question = (
                        f"{payload.question}\n\nText extracted from image: {ocr_text}"
                    )
                    logger.info(
                        f"Enhanced question with OCR text (length: {len(enhanced_question)})"
                    )
                else:
                    logger.warning("No text extracted from image")
            except Exception as ocr_error:
                logger.error(f"OCR processing failed: {ocr_error}")
                # Continue without OCR text

        # Create enhanced payload for search
        search_payload = QuestionRequest(
            question=enhanced_question, image=payload.image
        )

        # Step 2: Perform hybrid search and generate answer
        collections_to_search = classified_collections["collections"]
        alpha = 0.5  # Balance between keyword and vector search
        top_k = 7  # Number of top documents to retrieve

        logger.info("Starting hybrid search and answer generation...")
        search_results = await hybrid_search_and_generate_answer(
            search_payload, collections_to_search, alpha, top_k
        )

        logger.info(f"Search results type: {type(search_results)}")

        # Parse the JSON response
        try:
            parsed_response = json.loads(search_results)
            answer = parsed_response.get("answer", search_results)
            links = parsed_response.get("links", [])

            logger.info("Successfully parsed JSON response")
            logger.info(f"Answer length: {len(answer)} characters")
            logger.info(f"Number of links: {len(links)}")

            # Convert links to proper format for the response model
            link_objects = []
            source_strings = []

            for link in links:
                if isinstance(link, dict) and "url" in link and "text" in link:
                    link_objects.append({"url": link["url"], "text": link["text"]})
                    source_strings.append(
                        link["url"]
                    )  # Keep URLs as string sources for backward compatibility
                elif isinstance(link, str):
                    source_strings.append(link)

        except (json.JSONDecodeError, TypeError) as json_error:
            logger.warning(f"JSON parse error: {json_error}, using raw response")
            answer = search_results
            links = []
            link_objects = []
            source_strings = []

        # Log performance metrics
        duration = time.time() - start_time
        logger.info(f"Total request processing time: {duration:.2f} seconds")

        logger.info(f"Returning answer preview: {answer[:100]}...")

        return QuestionResponse(
            answer=answer,
            sources=source_strings if source_strings else None,
            links=link_objects if link_objects else None,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (they're already handled)
        raise

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Return a user-friendly error message
        return QuestionResponse(
            answer="I'm sorry, I encountered an error while processing your question. Please try again with a rephrased question or contact support if the issue persists.",
            sources=None,
            links=None,
        )


@app.get("/health")
async def health_check():
    """Health check endpoint with system status"""
    try:
        # Basic health checks
        status = {
            "status": "healthy",
            "service": "Teaching Assistant API",
            "version": "1.0.0",
        }
        try:
            # Test Typesense client - try to list collections
            typesense_client.collections.retrieve()
            status["typesense_connection"] = "healthy"
        except Exception as e:
            logger.warning(f"Typesense connection issue: {e}")
            status["typesense_connection"] = "unhealthy"
            status["status"] = "degraded"

        return status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Teaching Assistant API",
            "error": str(e),
        }


@app.get("/collections")
async def get_collections():
    """Get available collections with descriptions"""
    # Default collections with descriptions
    default_collections = {
        "data_sourcing": "Data collection and acquisition methods",
        "data_preparation": "Data cleaning, preprocessing, transformation",
        "data_analysis": "Statistical analysis, modeling techniques",
        "data_visualization": "Charts, graphs, plotting libraries",
        "large_language_models": "LLMs, transformers, NLP models",
        "development_tools": "IDEs, libraries, frameworks",
        "deployment_tools": "Docker, cloud platforms, CI/CD",
        "project-1": "Building an API(RAG) that answers student questions",
        "project-2": "Build LLMs to answer graded assignment questions",
        "misc": "General course information and live recordings Q&A topics",
        "discourse_posts": "Community discussions and Q&A",
    }

    try:
        # Try to get actual collections from Typesense
        try:
            collections_response = typesense_client.collections.retrieve()
            actual_collections = [col["name"] for col in collections_response]
            logger.info(
                f"Retrieved {len(actual_collections)} collections from Typesense"
            )
        except Exception as e:
            logger.warning(f"Failed to retrieve collections from Typesense: {e}")
            actual_collections = []

        return {
            "collections": list(default_collections.keys()),
            "descriptions": default_collections,
            "actual_collections": actual_collections,
            "total": len(default_collections),
        }

    except Exception as e:
        logger.error(f"Error getting collections: {e}")
        return {
            "error": "Failed to retrieve collections",
            "collections": list(default_collections.keys()),
        }


@app.post("/api/v1/debug/search")
async def debug_search(payload: QuestionRequest):
    """Debug endpoint to test hybrid search without generating final answer"""
    try:
        logger.info(f"Debug search for: {payload.question}")

        # Classify question
        classified_collections = await classify_question(payload)
        logger.info(
            f"Debug - Classified collections: {classified_collections['collections']}"
        )
        # Perform hybrid search
        search_results = await hybrid_search_across_collections(
            payload,
            classified_collections["collections"],
            top_k=5,
            alpha=0.5,
            query_embedding=None,
        )

        # Format results for debugging
        formatted_results = []
        for i, result in enumerate(search_results):
            content = result["document"].get("content", "")
            formatted_results.append(
                {
                    "rank": i + 1,
                    "content_preview": (
                        content[:200] + "..." if len(content) > 200 else content
                    ),
                    "content_length": len(content),
                    "collection": result["collection"],
                    "hybrid_score": round(result["hybrid_score"], 4),
                    "keyword_score": round(result["keyword_score"], 4),
                    "vector_similarity": round(result["vector_similarity"], 4),
                    "vector_distance": result.get("vector_distance"),
                    "text_match_raw": result.get("text_match_raw", 0),
                }
            )

        return {
            "question": payload.question,
            "question_length": len(payload.question),
            "classified_collections": classified_collections["collections"],
            "total_results": len(search_results),
            "search_results": formatted_results,
            "search_parameters": {
                "alpha": 0.5,
                "top_k": 5,
                "collections_searched": len(classified_collections["collections"]),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug search error: {e}")
        import traceback

        logger.error(f"Debug search traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "question": payload.question if payload else "No question provided",
        }


if __name__ == "__main__":
    import uvicorn

    # Check environment
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info",
    )
