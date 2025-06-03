#!/bin/bash

# Check if typesense-data file exists else create dir and logs directory
if [ ! -d "typesense-data" ]; then
  mkdir -p typesense-data 
  echo "Creating typesense-data..."
else
  echo "typesense-data directory already exists."
fi

source .env

typesense-server  \
  -p 8108:8108 \
  -v "$(pwd)/typesense-data" \
  typesense/typesense:28.0 \
  --data-dir $(pwd)/typesense-data \
  --api-key=$TYPESENSE_API_KEY \
  --enable-cors \
  --enable-access-logging \
  --enable-search-logging \
  --api-address 0.0.0.0




# Start the Typesense container for production server

# docker run -d --name typesense \
#   -p 8108:8108 \
#   -v "$(pwd)/typesense-data:/data" \
#   typesense/typesense:28.0 \
#   --data-dir /data \
#   --api-key=conscious-field \
#   --enable-cors \
#   --log-dir /data/logs \
#   --enable-access-logging \
#   --enable-search-logging \
#   --api-address 0.0.0.0
