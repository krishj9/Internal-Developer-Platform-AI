FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install dependencies
COPY pyproject.toml README.md* ./
RUN pip install --no-cache-dir .

# Copy application source code
COPY app ./api/app

EXPOSE 8080

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
