DiffSyncLibrary/Dockerfile
# syntax=docker/dockerfile:1

# Use a slim Python base image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for building and running Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        libwebp-dev \
        tcl8.6-dev \
        tk8.6-dev \
        python3-tk \
        git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy only dependency files first for better caching
COPY pyproject.toml ./
COPY DiffSyncLibrary/README.md ./README.md

# Install pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Install project dependencies (including build dependencies)
RUN pip install .[all] || pip install .

# Copy the rest of the application code
COPY diffsync_cli ./diffsync_cli
COPY data ./data

# Copy config YAMLs if not included by setuptools
COPY diffsync_cli/config/perfion ./diffsync_cli/config/perfion

# Optionally copy tests if you want to run them in the container
# COPY tests ./tests

# Set the entrypoint for the CLI (can be overridden in Kubernetes job spec)
ENTRYPOINT ["diffsync"]

# Default command (prints help)
CMD ["--help"]
