FROM python:3.11-slim

WORKDIR /app

# Install deps first for layer caching
COPY k9_backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend + core (so `src.*` imports work inside the container)
COPY k9_backend /app/k9_backend
COPY k9_core /app/k9_core

ENV K9API_K9_CORE_DIR=/app/k9_core

EXPOSE 8000

WORKDIR /app/k9_backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
