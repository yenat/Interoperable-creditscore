FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc python3-dev libaio1 unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    curl -O https://download.oracle.com/otn_software/linux/instantclient/193000/instantclient-basic-linux.x64-19.3.0.0.0dbru.zip && \
    unzip instantclient-*.zip && \
    ln -s /opt/oracle/instantclient_19_3 /opt/oracle/instantclient && \
    echo /opt/oracle/instantclient > /etc/ld.so.conf.d/oracle.conf && \
    ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV ORACLE_HOME=/opt/oracle/instantclient

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Runtime environment variables (passed via docker run -e)
CMD ["python", "app.py"]

EXPOSE 5000