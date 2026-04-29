FROM python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies frozen
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY backend/ backend/
COPY frontend/ frontend/

# Set Python path to find the backend module
ENV PYTHONPATH=/app

EXPOSE 8000

# Run the FastAPI application using uv and uvicorn
CMD ["uv", "run", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
