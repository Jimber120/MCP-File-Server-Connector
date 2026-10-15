FROM python:3.11-slim

# Install git so git_status and git_commit tools function properly
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Expose port 8000 for Streamable HTTP
EXPOSE 8000

CMD ["python", "server.py"]