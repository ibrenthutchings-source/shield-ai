FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps and runtime requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Ensure scripts are executable
RUN chmod +x /app/scripts/wait_for_postgres.sh || true

# Entrypoint waits for Postgres to become available, then execs CMD
ENTRYPOINT ["/app/scripts/wait_for_postgres.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Container healthcheck: verifies DB connectivity via Python script
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python /app/scripts/healthcheck.py || exit 1
