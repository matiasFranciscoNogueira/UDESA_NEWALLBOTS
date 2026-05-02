FROM python:3.12-slim

# ======================
# SYSTEM SETUP
# ======================

WORKDIR /app

RUN apt-get update && apt-get install -y \
    cron \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# ======================
# PYTHON DEPENDENCIES
# ======================

RUN pip install --no-cache-dir \
    pandas \
    matplotlib \
    "google-cloud-bigquery[pandas]" \
    db-dtypes \
    tqdm \
    openpyxl \
    google-cloud-bigquery-storage \
    pyarrow \
    plotly \
    seaborn \
    adjustText

# ======================
# APP CODE
# ======================

COPY src/ ./src/
COPY pyproject.toml ./pyproject.toml
COPY entrypoint.sh ./entrypoint.sh

# Normalize line endings + make executable
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

# ======================
# ENVIRONMENT
# ======================

ENV PYTHONPATH=/app/src
ENV SHARED_DATA_PATH=/app/data/epu

# ======================
# ENTRYPOINT
# ======================

ENTRYPOINT ["/app/entrypoint.sh"]