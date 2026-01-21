# Save as: Dockerfile

# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy package configuration and source code
COPY pyproject.toml .
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Install the caspar package
# This makes 'from caspar.agent import ...' work properly
RUN pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose the API port (documentation only, Railway ignores this)
EXPOSE 8000

# Health check for local Docker (Railway uses its own)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the API server
# IMPORTANT: Use $PORT for Railway compatibility (they set this env var)
CMD uvicorn caspar.api.main:app --host 0.0.0.0 --port ${PORT}
