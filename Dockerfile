FROM python:3.12-slim

# Pillow (qrcode), reportlab, bcrypt derlemesi icin sistem bagimliliklari
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY mysite/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY mysite/ ./mysite/

WORKDIR /app/mysite

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/mysite

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
