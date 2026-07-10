FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev tesseract-ocr ghostscript qpdf \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
RUN pip install --upgrade pip setuptools wheel \
    && pip install -e ".[dev]"
