#!/bin/bash

# Restart script for Mobility Synthetic Data Generator

echo "🛑 Stopping existing Docker containers..."
docker compose down

echo "🔨 Building Docker images with no cache..."
docker compose build --no-cache

echo "🚀 Starting Docker containers in detached mode..."
docker compose up -d

echo ""
echo "✅ Deployment complete."
echo "📋 You can check the logs with: docker compose logs -f"
echo "🌐 The app should be available at http://localhost:8501 (or your configured Caddy domain)"


