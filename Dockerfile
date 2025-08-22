FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

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

WORKDIR /app
COPY pyproject.toml ./
COPY README.md ./

# Install pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Install project dependencies (including build dependencies)
RUN pip install .[all] || pip install .

# Copy the rest of the application code
COPY syncly ./syncly
COPY data ./data


ENTRYPOINT ["syncly"]

CMD ["--help"]
