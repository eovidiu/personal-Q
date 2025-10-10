# Multi-stage build for production
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package configuration first
COPY pyproject.toml setup.py ./

# Copy application code
COPY app ./app
COPY config ./config
COPY migrations ./migrations

# Install package in editable mode with dependencies
RUN pip install --no-cache-dir -e .

# Create data directories
RUN mkdir -p /app/data /app/data/chromadb

# Set Python path (backup measure)
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run application using installed module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
