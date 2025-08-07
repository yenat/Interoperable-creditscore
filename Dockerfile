FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc python3-dev libaio1 unzip curl && \
    rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    curl -O https://download.oracle.com/otn_software/linux/instantclient/193000/instantclient-basiclite-linux.x64-19.3.0.0.0dbru.zip && \
    unzip instantclient-*.zip && \
    ln -s /opt/oracle/instantclient_19_3 /opt/oracle/instantclient && \
    echo /opt/oracle/instantclient > /etc/ld.so.conf.d/oracle.conf && \
    ldconfig && \
    rm instantclient-*.zip

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV ORACLE_HOME=/opt/oracle/instantclient

# Install Python packages with production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn && \
    pip cache purge

COPY . .

# Production server configuration
ENV GUNICORN_CMD_ARGS="--workers=4 --bind=0.0.0.0:5050 --timeout 120 --access-logfile - --error-logfile -"

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:5050/health || exit 1

CMD ["gunicorn", "app:app"]

EXPOSE 5050