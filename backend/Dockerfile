# Multi-stage build for production
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configure pip for better dependency resolution
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Upgrade pip, setuptools, and wheel for better dependency handling
RUN pip install --no-cache-dir --upgrade pip==24.3.1 setuptools==75.6.0 wheel==0.45.0

# Copy package configuration first
COPY pyproject.toml setup.py ./

# Copy application code
COPY app ./app
COPY config ./config
COPY migrations ./migrations

# Install package in editable mode with dependencies
# Increased timeout for CrewAI dependency resolution
RUN pip install --no-cache-dir -e . --timeout 300

# Create data directories
RUN mkdir -p /app/data /app/data/chromadb

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set Python path (backup measure)
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run application using installed module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
