#!/bin/bash

# Check if typesense-data directory exists
if [ ! -d "typesense-data" ]; then
  mkdir typesense-data
  echo "Creating typesense-data directory..."
else
  echo "typesense-data directory already exists."
fi

# Start the Typesense container
docker run -d --name typesense \
  -p 8108:8108 \
  -v "$(pwd)/typesense-data:/data" \
  typesense/typesense:28.0 \
  --data-dir /data \
  --api-key=conscious-field \
  --enable-cors \
  --log-dir /data/logs \
  --enable-access-logging \
  --enable-search-logging \
  --api-address 0.0.0.0
