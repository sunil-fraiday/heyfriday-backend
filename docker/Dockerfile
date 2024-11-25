FROM python:3.10-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY pyproject.toml .

RUN pip install -r requirements.txt

COPY src/backend/ .

CMD ["uvicorn", "app.main:app", "--workers", "4", "--host", "0.0.0.0", "--port", "8000"]
