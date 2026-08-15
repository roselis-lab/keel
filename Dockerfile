# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv for fast, reproducible installs from the committed lockfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY . .

# Reproducible install from uv.lock (no dev dependencies in the image).
RUN uv sync --frozen --no-dev

# Run as a non-root user; it owns /app so the entrypoint can build the SQLite DB there.
RUN chmod +x /app/docker/entrypoint.sh \
    && useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
# Default: read-only REST + browse UI at http://localhost:8000/
CMD ["uvicorn", "keel.main:app", "--host", "0.0.0.0", "--port", "8000"]
