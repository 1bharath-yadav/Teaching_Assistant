# Teaching Assistant API Configuration Guide

The Teaching Assistant API is now fully configurable through the `config.yaml` file in the root directory. This guide explains how to customize the hybrid search and answer generation behavior.

## Configuration Overview

All configuration is managed through the centralized `config.yaml` file. The API automatically loads these settings and applies them to:

- Model selection (OpenAI, Ollama, Azure, etc.)
- Hybrid search parameters
- Answer generation settings
- System prompts
- Error messages
- Collection management

## Key Configuration Sections

### 1. Hybrid Search Configuration

```yaml
hybrid_search:
  # Search parameters
  alpha: 0.7                    # Balance between keyword (0.0) and semantic (1.0) search
  top_k: 10                     # Number of search results to return
  max_context_length: 50000     # Maximum context length for answer generation
  num_typos: 2                  # Number of typos allowed in search queries
  
  # Collections
  default_collections:          # Always searched collections
    - "misc"
    - "discourse_posts"
  
  available_collections:        # Collections available for classification
    - "data_sourcing"
    - "data_preparation"
    - "data_analysis"
    - "data_visualization"
    - "large_language_models"
    - "development_tools"
    - "deployment_tools"
    - "project-1"
    - "project-2"
```

### 2. Answer Generation Settings

```yaml
hybrid_search:
  answer_generation:
    enable_streaming: true        # Enable streaming responses
    enable_link_extraction: true # Extract links from content
    max_sources: 10              # Maximum number of sources to include
    deduplicate_content: true    # Remove duplicate content
    include_source_info: true    # Include source collection info
```

### 3. Model Provider Selection

```yaml
defaults:
  chat_provider: "ollama"       # Options: "openai", "ollama", "azure", "anthropic", "google"
  embedding_provider: "ollama"  # Options: "openai", "ollama", "azure"
  search_provider: "typesense"  # Options: "typesense"
```

### 4. Custom System Prompts

```yaml
hybrid_search:
  prompts:
    classification_system: "Your task is to classify the user's question..."
    assistant_system: |
      You are a helpful teaching assistant for a Tools in datascience(TDS) course...
    link_extraction_system: "Extract any URLs and links from the given content..."
```

### 5. Error Messages

```yaml
hybrid_search:
  fallback:
    error_messages:
      no_results: "I couldn't find relevant information for your question..."
      search_error: "I encountered an error while processing your question..."
      generation_error: "I found relevant information but encountered an issue..."
```

## How to Customize

### 1. Adjust Search Behavior

**To make search more semantic (AI-powered):**
```yaml
hybrid_search:
  alpha: 0.9  # Increase for more semantic search
```

**To make search more keyword-based:**
```yaml
hybrid_search:
  alpha: 0.3  # Decrease for more keyword search
```

**To get more/fewer results:**
```yaml
hybrid_search:
  top_k: 15      # Increase for more results
  max_context_length: 75000  # Increase context window
```

### 2. Change Model Providers

**Switch to OpenAI:**
```yaml
defaults:
  chat_provider: "openai"
  embedding_provider: "openai"

openai:
  default_model: "gpt-4o-mini"
  api_key: "${OPENAI_API_KEY}"
```

**Switch to Azure OpenAI:**
```yaml
defaults:
  chat_provider: "azure"
  embedding_provider: "azure"

azure:
  api_key: "${AZURE_API_KEY}"
  base_url: "${AZURE_URL}"
  deployment_name: "gpt-4"
```

### 3. Customize Collections

**Add new collections:**
```yaml
hybrid_search:
  available_collections:
    - "data_sourcing"
    - "data_preparation" 
    # ... existing collections ...
    - "new_course_module"      # Your new collection
    - "advanced_topics"        # Another new collection
```

**Change default search collections:**
```yaml
hybrid_search:
  default_collections:
    - "misc"
    - "discourse_posts"
    - "frequently_asked"       # Always search this too
```

### 4. Modify System Prompts

**Customize the teaching assistant personality:**
```yaml
hybrid_search:
  prompts:
    assistant_system: |
      You are an expert data science instructor specializing in practical applications.
      Your teaching style is:
      1. Hands-on and example-driven
      2. Clear and concise explanations
      3. Always provide code examples when relevant
      4. Encourage best practices and industry standards
      5. Connect concepts to real-world scenarios
```

### 5. Adjust Performance Settings

**For faster responses (lower quality):**
```yaml
hybrid_search:
  top_k: 5                   # Fewer results
  max_context_length: 25000  # Shorter context
  
defaults:
  chat_provider: "ollama"    # Use local model
  
ollama:
  default_model: "llama3.2:3b"  # Smaller, faster model
```

**For higher quality (slower responses):**
```yaml
hybrid_search:
  top_k: 15                  # More results
  max_context_length: 100000 # Longer context
  
defaults:
  chat_provider: "openai"    # Use GPT-4
  
openai:
  default_model: "gpt-4o"    # More capable model
```

## Environment Variables

You can override any configuration value using environment variables with the format:
`SECTION__SUBSECTION__KEY` (double underscore)

Examples:
```bash
export OPENAI__API_KEY="your-api-key"
export HYBRID_SEARCH__ALPHA="0.8"
export DEFAULTS__CHAT_PROVIDER="openai"
```

## Testing Configuration

Use the included test script to verify your configuration:

```bash
python test_config_integration.py
```

This will validate:
- Configuration loads correctly
- All required sections are present
- Functions can access configuration values
- Custom settings are applied

## Configuration Examples

### Research-Focused Setup
```yaml
hybrid_search:
  alpha: 0.9                 # Highly semantic
  top_k: 20                  # Many sources
  max_context_length: 100000 # Large context

defaults:
  chat_provider: "openai"
  
openai:
  default_model: "gpt-4o"    # Most capable model
```

### Quick Response Setup
```yaml
hybrid_search:
  alpha: 0.5                 # Balanced search
  top_k: 5                   # Few sources
  max_context_length: 25000  # Small context

defaults:
  chat_provider: "ollama"
  
ollama:
  default_model: "llama3.2:3b"  # Fast local model
```

### Keyword-Heavy Setup
```yaml
hybrid_search:
  alpha: 0.2                 # Mostly keyword search
  top_k: 8                   # Moderate sources
  num_typos: 3               # More lenient spelling
```

## Troubleshooting

1. **Configuration not loading**: Check YAML syntax and file path
2. **Model errors**: Verify API keys and model availability
3. **Search issues**: Check Typesense connection and collection names
4. **Import errors**: Ensure all dependencies are installed

The configuration system provides complete control over the Teaching Assistant API behavior while maintaining backward compatibility.
