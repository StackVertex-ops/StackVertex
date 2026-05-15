# Multi-stage build for OverCloud Backend
FROM python:3.11-slim AS builder

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi --no-root --only main

# ============================================================================
# Runtime stage
# ============================================================================
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash overcloud && \
    mkdir -p /app && \
    chown -R overcloud:overcloud /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=overcloud:overcloud /app/.venv /app/.venv

# Copy application code
COPY --chown=overcloud:overcloud . /app/

# Switch to non-root user
USER overcloud

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
