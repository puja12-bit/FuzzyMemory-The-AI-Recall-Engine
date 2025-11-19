FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# FIX: Google Cloud Run expects port 8080, not 8000
ENV PORT=8080
EXPOSE 8080

# FIX: Use 'exec' for better signal handling and listen on the $PORT variable
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT}
