FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY indexer.py .

RUN mkdir -p /app/text_files

RUN mkdir -p /app/faiss_index

CMD ["python", "indexer.py", "--input-dir", "/app/text_files", "--output-dir", "/app/faiss_index"]
