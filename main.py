from fastapi import FastAPI
import typesense
import openai
from pydantic import BaseModel

app = FastAPI()

# Typesense client
client = typesense.Client({
    'nodes': [{'host': 'localhost', 'port': '8108', 'protocol': 'http'}],
    'api_key': 'your-api-key',
    'connection_timeout_seconds': 2
})

# OpenAI client
openai.api_key = 'your-openai-api-key'

class Query(BaseModel):
    prompt: str

async def identify_chapter(prompt_embedding):
    chapters = [
        "development_tools", "deployment_tools", "large_language_models",
        "data_sourcing", "data_preparation", "data_analysis", "data_visualization",
        "project-1", "project-2", "misc"
    ]
    max_similarity = 0
    best_chapter = None
    for chapter in chapters:
        results = client.collections[chapter].search({
            "q": "*",
            "vector_query": f"embedding:({prompt_embedding}, k:1)"
        })
        if results["hits"] and results["hits"][0]["vector_distance"] < 0.3:  # Lower distance = higher similarity
            similarity = 1 - results["hits"][0]["vector_distance"]
            if similarity > max_similarity:
                max_similarity = similarity
                best_chapter = chapter
    return best_chapter if max_similarity > 0.7 else None

@app.post("/answer")
async def answer_question(query: Query):
    # Generate embedding for prompt
    response = openai.Embedding.create(
        model="text-embedding-3-small",
        input=query.prompt
    )
    prompt_embedding = response["data"][0]["embedding"]

    # Identify chapter
    chapter = await identify_chapter(prompt_embedding)

    results = []
    if chapter:
        # Semantic search
        semantic_results = client.collections[chapter].search({
            "q": "*",
            "vector_query": f"embedding:({prompt_embedding}, k:5)"
        })
        results.extend(semantic_results["hits"])

        # Keyword search
        keyword_results = client.collections[chapter].search({
            "q": query.prompt,
            "query_by": "content",
            "per_page": 5
        })
        results.extend(keyword_results["hits"])

    # Fallback: Search all chapters if no results or no chapter identified
    if not results and not chapter:
        for chap in [
            "development_tools", "deployment_tools", "large_language_models",
            "data_sourcing", "data_preparation", "data_analysis", "data_visualization",
            "project-1", "project-2", "misc"
        ]:
            semantic_results = client.collections[chap].search({
                "q": "*",
                "vector_query": f"embedding:({prompt_embedding}, k:5)"
            })
            results.extend(semantic_results["hits"])
            keyword_results = client.collections[chap].search({
                "q": query.prompt,
                "query_by": "content",
                "per_page": 5
            })
            results.extend(keyword_results["hits"])

    # Generate answer with GPT-4o-mini
    if results:
        context = "\n".join([hit["document"]["content"] for hit in results])
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Answer the question based on the provided context."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query.prompt}"}
            ]
        )
        answer = response["choices"][0]["message"]["content"]
        source = chapter if chapter else "multiple chapters"
        return {"answer": answer, "source": source}
    else:
        return {"answer": "I couldn’t find specific information to answer your question.", "source": None}