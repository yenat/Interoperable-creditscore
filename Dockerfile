# Stage 1: Build stage
FROM python:3.9-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc python3-dev libaio1 unzip curl && \
    rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client (minimal approach)
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
# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Stage 2: Final stage
FROM python:3.9-slim

WORKDIR /app

# Copy Oracle Instant Client from builder stage
COPY --from=builder /opt/oracle /opt/oracle
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV ORACLE_HOME=/opt/oracle/instantclient
# Copy application files
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--lifespan", "off"]

EXPOSE 5000
