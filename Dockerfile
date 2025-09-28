# syntax=docker/dockerfile:1

FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install .

# Copy the rest of the code
COPY . .

RUN pip install .

# Entrypoint for the CLI
ENTRYPOINT ["syncly"]
