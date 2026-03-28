# ============================================
# Open Trader - Production Dockerfile
# Multi-stage build for optimized image size
# ============================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Force rebuild cache v0.3.1
RUN echo "Build version 0.3.1" > /tmp/build_version

# Stage 2: Production
FROM python:3.11-slim as production

# Security: Create non-root user
RUN groupadd -r trader && useradd -r -g trader trader

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /home/trader/.local
ENV PATH=/home/trader/.local/bin:$PATH

# Copy application code
COPY backend/ .

# Create data directory and set permissions
RUN mkdir -p /app/data && chown -R trader:trader /app

# Switch to non-root user
USER trader

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run with production server (default port 8000 if PORT not set)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --proxy-headers"]
