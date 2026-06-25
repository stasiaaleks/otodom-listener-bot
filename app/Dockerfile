FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

EXPOSE 8000

# Single worker: poll loop must not run in parallel
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
