# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libaio1 && \
    rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle
ADD https://download.oracle.com/otn_software/linux/instantclient/193000/instantclient-basic-linux.x64-19.3.0.0.0dbru.zip /opt/oracle
RUN unzip /opt/oracle/instantclient-basic-linux.x64-19.3.0.0.0dbru.zip -d /opt/oracle && \
    ln -s /opt/oracle/instantclient_19_3 /opt/oracle/instantclient && \
    rm /opt/oracle/instantclient-basic-linux.x64-19.3.0.0.0dbru.zip

# Set environment variables for Oracle
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV ORACLE_HOME=/opt/oracle/instantclient

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create .env file from environment variables at runtime
RUN touch .env
CMD ["sh", "-c", "echo DB_IP=$DB_IP > .env && \
                   echo DB_PORT=$DB_PORT >> .env && \
                   echo DB_SID=$DB_SID >> .env && \
                   echo DB_USERNAME=$DB_USERNAME >> .env && \
                   echo DB_PASSWORD=$DB_PASSWORD >> .env && \
                   python app.py"]


# Use build arguments
ARG DB_IP
ARG DB_PORT
ARG DB_SID
ARG DB_USERNAME
ARG DB_PASSWORD

# Create .env file from build arguments
RUN echo DB_IP=$DB_IP > .env && \
    echo DB_PORT=$DB_PORT >> .env && \
    echo DB_SID=$DB_SID >> .env && \
    echo DB_USERNAME=$DB_USERNAME >> .env && \
    echo DB_PASSWORD=$DB_PASSWORD >> .env

CMD ["python", "app.py"]

EXPOSE 5000