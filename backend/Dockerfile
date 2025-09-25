FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy the entire project to get access to ea_analyzer modules
COPY ../src /app/src
COPY ../backend /app/backend

# Set working directory to backend
WORKDIR /app/backend

# Install dependencies with uv
RUN uv sync

# Set Python path
ENV PYTHONPATH=/app/src:/app/backend

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
