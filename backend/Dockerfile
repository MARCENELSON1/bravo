# FastAPI backend image. Deterministic build (no buildpack auto-detection) so a
# monorepo subdir deploys cleanly. Migrations run via railway.json preDeploy.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=2.0"

# Install dependencies first (layer cache), then the app package.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

COPY . .
RUN poetry install --only main

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
