
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt 

COPY embedding_processor.py .

ENV TORCH_NUM_THREADS=4

# Run the processor
CMD ["python", "-u", "embedding_processor.py"]