#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# Base directory

BASE_DIR = "/home/archer/projects/llm_tests/Teaching_Assistant/data/chapters/tools-in-data-science-public"

# Create directories
directories = [
    "development_tools",
    "deployment_tools",
    "large_language_models",
    "data_sourcing",
    "data_preparation",
    "data_analysis",
    "data_visualization",
]

for directory in directories:
    os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True)

# Move files to corresponding directories
files_to_move = {
    "development_tools": [
        "development-tools.md",
        "vscode.md",
        "github-copilot.md",
        "uv.md",
        "npx.md",
        "unicode.md",
        "devtools.md",
        "css-selectors.md",
        "json.md",
        "bash.md",
        "llm.md",
        "spreadsheets.md",
        "sqlite.md",
        "git.md",
    ],
    "deployment_tools": [
        "deployment-tools.md",
        "markdown.md",
        "image-compression.md",
        "github-pages.md",
        "colab.md",
        "vercel.md",
        "github-actions.md",
        "docker.md",
        "github-codespaces.md",
        "ngrok.md",
        "cors.md",
        "rest-apis.md",
        "fastapi.md",
        "google-auth.md",
        "ollama.md",
    ],
    "large_language_models": [
        "large-language-models.md",
        "prompt-engineering.md",
        "tds-ta-instructions.md",
        "tds-gpt-reviewer.md",
        "llm-sentiment-analysis.md",
        "llm-text-extraction.md",
        "base64-encoding.md",
        "vision-models.md",
        "embeddings.md",
        "multimodal-embeddings.md",
        "topic-modeling.md",
        "vector-databases.md",
        "rag-cli.md",
        "hybrid-rag-typesense.md",
        "function-calling.md",
        "llm-agents.md",
        "llm-image-generation.md",
        "llm-speech.md",
        "llm-evals.md",
    ],
    "data_sourcing": [
        "data-sourcing.md",
        "scraping-with-excel.md",
        "scraping-with-google-sheets.md",
        "crawling-cli.md",
        "bbc-weather-api-with-python.md",
        "scraping-imdb-with-javascript.md",
        "nominatim-api-with-python.md",
        "wikipedia-data-with-python.md",
        "scraping-pdfs-with-tabula.md",
        "convert-pdfs-to-markdown.md",
        "convert-html-to-markdown.md",
        "llm-website-scraping.md",
        "llm-video-screen-scraping.md",
        "web-automation-with-playwright.md",
        "scheduled-scraping-with-github-actions.md",
        "scraping-emarketer.md",
        "scraping-live-sessions.md",
    ],
    "data_preparation": [
        "data-preparation.md",
        "data-cleansing-in-excel.md",
        "data-transformation-in-excel.md",
        "splitting-text-in-excel.md",
        "data-aggregation-in-excel.md",
        "data-preparation-in-the-shell.md",
        "data-preparation-in-the-editor.md",
        "cleaning-data-with-openrefine.md",
        "profiling-data-with-python.md",
        "parsing-json.md",
        "dbt.md",
        "transforming-images.md",
        "extracting-audio-and-transcripts.md",
    ],
    "data_analysis": [
        "data-analysis.md",
        "correlation-with-excel.md",
        "regression-with-excel.md",
        "forecasting-with-excel.md",
        "outlier-detection-with-excel.md",
        "data-analysis-with-python.md",
        "data-analysis-with-sql.md",
        "data-analysis-with-datasette.md",
        "data-analysis-with-duckdb.md",
        "data-analysis-with-chatgpt.md",
        "geospatial-analysis-with-excel.md",
        "geospatial-analysis-with-python.md",
        "geospatial-analysis-with-qgis.md",
        "network-analysis-in-python.md",
    ],
    "data_visualization": [
        "data-visualization.md",
        "visualizing-forecasts-with-excel.md",
        "visualizing-animated-data-with-powerpoint.md",
        "visualizing-animated-data-with-flourish.md",
        "visualizing-network-data-with-kumu.md",
        "visualizing-charts-with-excel.md",
        "data-visualization-with-seaborn.md",
        "data-visualization-with-chatgpt.md",
        "actor-network-visualization.md",
        "rawgraphs.md",
        "data-storytelling.md",
        "narratives-with-llms.md",
        "marimo.md",
        "revealjs.md",
        "marp.md",
    ],
}

# Move files and handle patterns
for target_dir, files in files_to_move.items():
    for file_pattern in files:
        if "*" in file_pattern:
            # Handle wildcard patterns
            base_path = Path(BASE_DIR)
            for file_path in base_path.glob(file_pattern):
                if file_path.is_file():
                    shutil.move(str(file_path), os.path.join(BASE_DIR, target_dir))
        else:
            file_path = os.path.join(BASE_DIR, file_pattern)
            if os.path.exists(file_path):
                shutil.move(file_path, os.path.join(BASE_DIR, target_dir))

# Handle patterns for specific categories
patterns = {
    "large_language_models": ["llm*.md"],
    "data_sourcing": ["scraping*.md"],
    "data_analysis": ["data-analysis-with-*.md", "geospatial-analysis-with-*.md"],
    "data_visualization": [
        "data-visualization-with-*.md",
        "narratives-with-*.md",
        "visualizing-*.md",
    ],
}

for target_dir, pattern_list in patterns.items():
    for pattern in pattern_list:
        base_path = Path(BASE_DIR)
        for file_path in base_path.glob(pattern):
            if file_path.is_file():
                shutil.move(str(file_path), os.path.join(BASE_DIR, target_dir))

# Move project-related files to respective project directories
os.makedirs(os.path.join(BASE_DIR, "project-1"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "project-2"), exist_ok=True)

project_files = [("project-1.md", "project-1"), ("project-2.md", "project-2")]

for file_name, project_dir in project_files:
    file_path = os.path.join(BASE_DIR, file_name)
    if os.path.exists(file_path):
        shutil.move(file_path, os.path.join(BASE_DIR, project_dir))

# Move project-tds-virtual-ta* files to project-1
base_path = Path(BASE_DIR)
for file_path in base_path.glob("project-tds-virtual-ta*"):
    if file_path.exists():
        shutil.move(str(file_path), os.path.join(BASE_DIR, "project-1"))

# Move remaining files to misc directory
os.makedirs(os.path.join(BASE_DIR, "misc"), exist_ok=True)

remaining_patterns = [
    "*.md",
    "*.html",
    "*.yaml",
    "*.py",
    "*.webp",
    ".gitignore",
    ".nojekyll",
    "CNAME",
    "2025-01",
    "images",
]

for pattern in remaining_patterns:
    base_path = Path(BASE_DIR)
    for item_path in base_path.glob(pattern):
        if item_path.exists() and item_path.name not in [
            "organise_mds.py"
        ]:  # Don't move this script
            shutil.move(str(item_path), os.path.join(BASE_DIR, "misc"))
