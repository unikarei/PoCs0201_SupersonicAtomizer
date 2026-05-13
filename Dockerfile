# Dockerfile for SupersonicAtomizer FastAPI application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv (lightweight package manager)
RUN pip install --no-cache-dir uv

# Copy project files for dependency installation
COPY pyproject.toml uv.lock ./

# Sync dependencies
RUN uv sync --no-dev

# Copy source code
COPY src ./src

# Expose port
EXPOSE 8502

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8502/health').close()" || exit 1

# Run FastAPI application
CMD ["uv", "run", "uvicorn", "supersonic_atomizer.gui.fastapi_app:app", "--host", "0.0.0.0", "--port", "8502"]
