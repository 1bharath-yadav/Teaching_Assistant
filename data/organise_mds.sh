#!/bin/bash

# Base directory
BASE_DIR="/home/archer/projects/llm_tests/Teaching_Assistant/data/tools-in-data-science-public"

# Create directories
mkdir -p "$BASE_DIR"/{development_tools,deployment_tools,large_language_models,data_sourcing,data_preparation,data_analysis,data_visualization}

# Move files to corresponding directories
mv "$BASE_DIR"/{development-tools.md,devtools.md,bash.md,colab.md,css-selectors.md,docker.md,fastapi.md,git.md,github-actions.md,github-codespaces.md,github-copilot.md,github-pages.md,marimo.md,markdown.md,marp.md,npx.md,uv.md,vscode.md} "$BASE_DIR/development_tools/"

mv "$BASE_DIR"/{deployment-tools.md,ngrok.md,vercel.md} "$BASE_DIR/deployment_tools/"

mv "$BASE_DIR"/{large-language-models.md,llm*.md,embeddings.md,multimodal-embeddings.md,prompt-engineering.md,retrieval-augmented-generation.md,vector-databases.md,vision-models.md,fine-tuning-gemini.md,hybrid-rag-typesense.md,llamafile.md,ollama.md,tds-gpt-reviewer.md,tds-ta-instructions.md} "$BASE_DIR/large_language_models/"

mv "$BASE_DIR"/{data-sourcing.md,bbc-weather-api-with-python.md,crawling-cli.md,nominatim-api-with-python.md,scraping*.md,wikipedia-data-with-python.md} "$BASE_DIR/data_sourcing/"

mv "$BASE_DIR"/{data-preparation.md,data-preparation-in-the-editor.md,data-preparation-in-the-shell.md,data-cleansing-in-excel.md,data-transformation-in-excel.md,cleaning-data-with-openrefine.md,convert-html-to-markdown.md,convert-pdfs-to-markdown.md,parsing-json.md,splitting-text-in-excel.md} "$BASE_DIR/data_preparation/"

mv "$BASE_DIR"/{data-analysis.md,data-analysis-with-*.md,correlation-with-excel.md,geospatial-analysis-with-*.md,network-analysis-in-python.md,outlier-detection-with-excel.md,profiling-data-with-python.md,regression-with-excel.md,topic-modeling.md} "$BASE_DIR/data_analysis/"

mv "$BASE_DIR"/{data-visualization.md,data-visualization-with-*.md,actor-network-visualization.md,data-storytelling.md,google-charts.md,google-data-studio.md,narratives-with-*.md,rawgraphs.md,revealjs.md,transforming-images.md,visualizing-*.md} "$BASE_DIR/data_visualization/"

# Move project-related files to respective project directories
mkdir -p "$BASE_DIR/project-1" "$BASE_DIR/project-2"
mv "$BASE_DIR"/project-1.md "$BASE_DIR/project-1/"
mv "$BASE_DIR"/project-2.md "$BASE_DIR/project-2/"
mv "$BASE_DIR"/project-tds-virtual-ta* "$BASE_DIR/project-1/"

# Move remaining files to misc directory
mkdir -p "$BASE_DIR/misc"
mv "$BASE_DIR"/{*.md,*.html,*.yaml,*.py,*.webp,.gitignore,.nojekyll,CNAME,2025-01,images} "$BASE_DIR/misc/"
