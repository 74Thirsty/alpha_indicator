FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
