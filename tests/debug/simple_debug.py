#!/usr/bin/env python3
"""
Simple debug script to understand Ollama response format
"""
import ollama

def debug_simple():
    test_question = "How can I conect to the databse?"
    
    try:
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that corrects spelling and grammar.",
                },
                {
                    "role": "user",
                    "content": f"Correct: {test_question}",
                },
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "correct_text",
                        "description": "Correct spelling and grammar",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "corrected_text": {
                                    "type": "string",
                                    "description": "The corrected text",
                                },
                            },
                            "required": ["corrected_text"],
                        },
                        "strict": True,
                    },
                }
            ],
        )

        print(f"Response type: {type(response)}")
        
        # Try different ways to access the response
        if hasattr(response, '__dict__'):
            print(f"Response __dict__: {response.__dict__}")
        
        # Check if it's a dict-like object
        try:
            message = response["message"]
            print(f"Message: {message}")
            tool_calls = message.get("tool_calls", [])
            print(f"Tool calls: {tool_calls}")
        except:
            print("Cannot access as dict")
        
        # Check if it has attributes
        try:
            message = response.message
            print(f"Message attribute: {message}")
            if hasattr(message, 'tool_calls'):
                print(f"Tool calls attribute: {message.tool_calls}")
        except:
            print("Cannot access as attributes")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_simple()
