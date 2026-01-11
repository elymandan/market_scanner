# name=Dockerfile
FROM python:3.11-slim

# Prevents Python from buffering stdout/stderr (useful for logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only requirements first to maximize layer cache
COPY requirements.txt /app/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && apt-get remove -y gcc build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Expose webhook port (if used)
EXPOSE 8000

# Default command (runs your scanner + webhook as implemented in src/main.py)
CMD ["python", "-m", "src.main"]