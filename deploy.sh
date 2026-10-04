#!/bin/sh

set -e

echo "================================"
echo "Starting deployment"
echo "================================"

echo "Image tag: $IMAGE_TAG"

echo
echo "Pulling API image..."

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  pull api

echo
echo "Starting production services..."

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d

echo
echo "Checking production services..."

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  ps

echo
echo "================================"
echo "Deployment completed"
echo "================================"
