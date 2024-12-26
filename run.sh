#!/bin/bash
set -e  # Exit on error

echo "Building Docker image..."
docker build -t reddit-bot-01 .

echo "Starting container..."
docker run \
    --cap-add=NET_ADMIN \
    --device=/dev/net/tun \
    --env-file .env \
    -v "${PWD}/logs:/app/logs" \
    reddit-bot-01
