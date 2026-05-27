FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj

RUN apt-get update && apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    proj-bin \
    libproj-dev \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
COPY requirements/ requirements/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --find-links=/wheels numpy==2.3.5 && \
    pip install --no-cache-dir --timeout 300 --retries 10 -r requirements.txt

COPY . .

COPY docker/entrypoint.sh /docker/entrypoint.sh
COPY docker/worker-entrypoint.sh /docker/worker-entrypoint.sh
COPY docker/beat-entrypoint.sh /docker/beat-entrypoint.sh

RUN chmod +x /docker/entrypoint.sh /docker/worker-entrypoint.sh /docker/beat-entrypoint.sh

CMD ["/docker/entrypoint.sh"]
