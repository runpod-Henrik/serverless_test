FROM python:3.12-slim

# Install system dependencies and curl for Node.js setup
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (LTS) for TypeScript/JavaScript tests
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Go 1.22 for Go tests
RUN wget -q https://go.dev/dl/go1.22.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz && \
    rm go1.22.0.linux-amd64.tar.gz

# Set Go environment variables
ENV PATH="/usr/local/go/bin:${PATH}" \
    GOPATH="/go" \
    GOBIN="/go/bin"

# Create Go workspace
RUN mkdir -p ${GOPATH}/src ${GOPATH}/bin

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Verify installations
RUN python --version && \
    node --version && \
    npm --version && \
    go version && \
    echo "All runtimes installed successfully"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import runpod; print('healthy')" || exit 1

# Start the worker
CMD ["./run.sh"]