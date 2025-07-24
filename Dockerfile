# === Stage 1: Build dependencies ===
FROM python:3.9-alpine AS builder

WORKDIR /build

# System deps for building Python packages
RUN apk add --no-cache \
    build-base \
    libpq \
    postgresql-dev \
    musl-dev \
    gcc \
    python3-dev \
    linux-headers

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# === Stage 2: Final runtime image ===
FROM python:3.9-alpine

ENV PYTHONPATH="/install/lib/python3.9/site-packages"

WORKDIR /app

# Only runtime deps (lighter image)
RUN apk add --no-cache \
    libpq \
    rsync

COPY --from=builder /install /install

COPY /static/ static/
COPY /templates/ templates/
COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]