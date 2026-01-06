# Production Dockerfile
FROM python:3.11-slim

# Cache buster - change this value to force rebuild
ARG CACHE_BUST=2026-01-06-v1

# Set working directory
WORKDIR /app

# Install system dependencies
# Note: npm is required because Railway dashboard has startCommand="npm start"
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Configure pip for better dependency resolution
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Upgrade pip, setuptools, and wheel for better dependency handling
RUN pip install --no-cache-dir --upgrade pip==24.3.1 setuptools==75.6.0 wheel==0.45.0

# Copy package configuration first
# Note: Railway uses repo root as build context with backend/Dockerfile
COPY backend/pyproject.toml backend/setup.py ./
# Copy package.json for Railway's "npm start" command workaround
COPY backend/package.json ./

# Copy application code
COPY backend/app ./app
COPY backend/config ./config
COPY backend/migrations ./migrations
COPY backend/entrypoint.sh ./entrypoint.sh

# Install package in editable mode with dependencies
# Increased timeout for CrewAI dependency resolution
RUN pip install --no-cache-dir -e . --timeout 300

# Create data directories
RUN mkdir -p /app/data /app/data/lancedb

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set Python path (backup measure)
ENV PYTHONPATH=/app

# Expose port (Railway will use PORT env var)
EXPOSE ${PORT:-8000}

# Use entrypoint script to determine which service to run
# Set SERVICE_TYPE=api|worker|beat via environment variable
ENTRYPOINT ["/app/entrypoint.sh"]
