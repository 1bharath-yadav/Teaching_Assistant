#!/bin/bash

# Enable recursive globbing
shopt -s globstar

# Base directory
BASE_DIR="/home/archer/projects/llm_tests/Teaching_Assistant/data/tools-in-data-science-public"

# Directories to process
DIRS=("development_tools" "deployment_tools" "large_language_models" "data_sourcing" "data_preparation" "data_analysis" "data_visualization" "project-1" "project-2" "misc")



# Process each directory
for dir in "${DIRS[@]}"; do
    # Create output directory if it doesn't exist
    mkdir -p "$BASE_DIR/$dir"
    
    # Initialize chunks.json for the directory
    echo "[]" > "$dir/chunks.json"
    
    # Process all .md files in the directory
    for f in "$BASE_DIR/$dir"/*.md; do
        if [[ -f "$f" ]]; then
            relative_path="${f#$BASE_DIR/}"
            uvx --from split_markdown4gpt mdsplit4gpt "$f" --model gpt-4o --limit 4096 --separator "===SPLIT===" \
            | sed '1s/^/===SPLIT===\n/' \
            | jq -R -s -c --arg file "$relative_path" '
              split("===SPLIT===")[1:]
              | to_entries
              | map({
                  id: ($file + "#" + (.key | tostring)),
                  content: .value
                })[]
            ' >> "$BASE_DIR/$dir/chunks.json.tmp" || {
                echo "Error processing $f"
                continue
            }
            echo "Processed $f"
        fi
    done
    
    # Combine temporary chunks into final chunks.json
    if [[ -f "$BASE_DIR/$dir/chunks.json.tmp" ]]; then
        jq -s 'flatten' "$BASE_DIR/$dir/chunks.json.tmp" > "$BASE_DIR/$dir/chunks.json"
        rm "$BASE_DIR/$dir/chunks.json.tmp"
    fi
done