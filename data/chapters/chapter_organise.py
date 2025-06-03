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
        "devtools.md",
        "bash.md",
        "colab.md",
        "css-selectors.md",
        "docker.md",
        "fastapi.md",
        "git.md",
        "github-actions.md",
        "github-codespaces.md",
        "github-copilot.md",
        "github-pages.md",
        "marimo.md",
        "markdown.md",
        "marp.md",
        "npx.md",
        "uv.md",
        "vscode.md",
    ],
    "deployment_tools": ["deployment-tools.md", "ngrok.md", "vercel.md"],
    "large_language_models": [
        "large-language-models.md",
        "embeddings.md",
        "multimodal-embeddings.md",
        "prompt-engineering.md",
        "retrieval-augmented-generation.md",
        "vector-databases.md",
        "vision-models.md",
        "fine-tuning-gemini.md",
        "hybrid-rag-typesense.md",
        "llamafile.md",
        "ollama.md",
        "tds-gpt-reviewer.md",
        "tds-ta-instructions.md",
    ],
    "data_sourcing": [
        "data-sourcing.md",
        "bbc-weather-api-with-python.md",
        "crawling-cli.md",
        "nominatim-api-with-python.md",
        "wikipedia-data-with-python.md",
    ],
    "data_preparation": [
        "data-preparation.md",
        "data-preparation-in-the-editor.md",
        "data-preparation-in-the-shell.md",
        "data-cleansing-in-excel.md",
        "data-transformation-in-excel.md",
        "cleaning-data-with-openrefine.md",
        "convert-html-to-markdown.md",
        "convert-pdfs-to-markdown.md",
        "parsing-json.md",
        "splitting-text-in-excel.md",
    ],
    "data_analysis": [
        "data-analysis.md",
        "correlation-with-excel.md",
        "network-analysis-in-python.md",
        "outlier-detection-with-excel.md",
        "profiling-data-with-python.md",
        "regression-with-excel.md",
        "topic-modeling.md",
    ],
    "data_visualization": [
        "data-visualization.md",
        "actor-network-visualization.md",
        "data-storytelling.md",
        "google-charts.md",
        "google-data-studio.md",
        "rawgraphs.md",
        "revealjs.md",
        "transforming-images.md",
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
