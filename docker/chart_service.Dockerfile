FROM python:3.10-slim

WORKDIR /opt/app

ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY src/chart_service/requirements.txt .
COPY pyproject.toml .

RUN pip install -r requirements.txt

COPY src/chart_service/app .

WORKDIR /opt

CMD ["uvicorn", "app.main:app", "--workers", "3", "--host", "0.0.0.0", "--port", "8005"]
