FROM python:3.14.0-slim@sha256:0aecac02dc3d4c5dbb024b753af084cafe41f5416e02193f1ce345d671ec966e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/system/backend

WORKDIR /app
COPY system/backend/requirements.lock.txt /tmp/requirements.lock.txt
RUN pip install --no-cache-dir -r /tmp/requirements.lock.txt
COPY system/backend/ /app/system/backend/

EXPOSE 8000
CMD ["uvicorn", "aim.main:app", "--host", "0.0.0.0", "--port", "8000"]
