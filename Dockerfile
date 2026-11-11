
# ==========================================
# Stage 1: Build Python dependencies
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt


# ==========================================
# Stage 2: Production application image
# ==========================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install prepared dependencies
COPY --from=builder /wheels /wheels

RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Create non-root application user
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup appuser

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/

# Copy Alembic configuration and migrations
COPY --chown=appuser:appgroup alembic.ini ./alembic.ini
COPY --chown=appuser:appgroup migrations/ ./migrations/

# Run application without root privileges
USER appuser

EXPOSE 8000

# Container health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
