# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# RUN apt-get update && apt-get install -y \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY indexer.py .

# Create directory for input files
RUN mkdir -p /app/text_files

# Create directory for output index
RUN mkdir -p /app/faiss_index

# Default command to run the indexer
CMD ["python", "indexer.py", "--input-dir", "/app/text_files", "--output-dir", "/app/faiss_index"]
