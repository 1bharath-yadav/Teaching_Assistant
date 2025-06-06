# ******************** AI tool definitions ********************#
"""
Function definitions for AI tools and structured outputs.
"""

from .clients import config


# ******************** function definitions for AI tools ********************#
classification_function = {
    "type": "function",
    "function": {
        "name": "classify_question",
        "description": "Classify a student's query into one or more relevant TDS course collections.",
        "parameters": {
            "type": "object",
            "properties": {
                "collections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": config.hybrid_search.available_collections,
                    },
                }
            },
            "required": ["collections"],
            "additionalProperties": False,
        },
    },
    "strict": True,  # Ensure strict validation of function parameters
}
