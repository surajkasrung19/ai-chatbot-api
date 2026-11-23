FROM python:3.13-slim


# Configure Python for container execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


# Set the application working directory
WORKDIR /app

# Apply available Debian security updates
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade \
        libc6 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .


RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Run the application as a non-root user
RUN useradd --create-home --uid 10001 appuser


USER appuser

# Document the application port
EXPOSE 8000

# Monitor application health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthcheck', timeout=3).close()"

# Start FastAPI with Uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]