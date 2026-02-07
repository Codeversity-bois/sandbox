# Code Sandbox - Multi-stage Docker Build with Docker-in-Docker
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI (for docker-in-docker capability)
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py ./
COPY config.py ./
COPY models/ ./models/
COPY routes/ ./routes/
COPY services/ ./services/

# Create necessary directories
RUN mkdir -p logs

# Create non-root user (docker group already exists from docker.io installation)
RUN useradd -m -u 1000 appuser && \
    usermod -aG docker appuser && \
    chown -R appuser:appuser /app
# Don't switch user - needs root for Docker access
# USER appuser

# Environment variables
ENV PORT=8082
ENV PYTHONUNBUFFERED=1

EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8082/health', timeout=5)" || exit 1

# Run FastAPI app
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8082}
