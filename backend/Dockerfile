FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies needed for compiling psycopg2 and general tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Expose server port
EXPOSE 8000

# Set environment
ENV PYTHONPATH=/workspace
ENV ENVIRONMENT=production

# Run FastAPI app
CMD ["python", "-m", "backend.app.main"]
