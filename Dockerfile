# BloodLink production image (Render, Google Cloud Run, any Docker host)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

EXPOSE 8080

CMD flask --app run:app init-db && exec gunicorn "run:app" --bind :${PORT:-8080} --workers 2 --threads 4 --timeout 60
