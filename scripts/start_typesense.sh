#!/bin/bash

# ******************** Typesense Server Startup Script ********************#
# Set the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if typesense-data file exists else create dir and logs directory
if [ ! -d "$PROJECT_ROOT/typesense-data" ]; then
  mkdir -p "$PROJECT_ROOT/typesense-data"
  echo "Creating typesense-data..."
else
  echo "typesense-data directory already exists."
fi

# ******************** environment configuration ********************#
source "$PROJECT_ROOT/.env"

# ******************** typesense server startup ********************#
echo "Starting Typesense server..."
typesense-server  \
  -p 8108:8108 \
  -v "$PROJECT_ROOT/typesense-data" \
  typesense/typesense:28.0 \
  --data-dir "$PROJECT_ROOT/typesense-data" \
  --api-key=$TYPESENSE_API_KEY \
  --enable-cors \
  --enable-access-logging \
  --enable-search-logging \
  --api-address 0.0.0.0

echo "Typesense server started on port 8108"


# ******************** production docker configuration (commented) ********************#
# Start the Typesense container for production server

# docker run -d --name typesense \
#   -p 8108:8108 \
#   -v "$(pwd)/typesense-data:/data" \
#   typesense/typesense:28.0 \
#   --data-dir /data \
#   --api-key=xyz \
#   --enable-cors \
#   --log-dir /data/logs \
#   --enable-access-logging \
#   --enable-search-logging \
#   --api-address 0.0.0.0
