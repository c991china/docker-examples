# Single-stage build for the flask demo. Kept simple on purpose so you can
# diff it against ../Dockerfile.multistage and see what the multistage buys you.
#
#   docker build -t flask-demo:dev .
#   docker run --rm -p 8000:8000 -e REDIS_HOST=host.docker.internal flask-demo:dev

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# requirements first, so a code edit does not reinstall deps.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py .

# non-root user
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
