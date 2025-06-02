### base image
FROM python:3.11-slim  AS runtime

### Set environment variables
# PYTHONUNBUFFERED=1 -- Disable output buffering for easier logging
# PYTHONDONTWRITEBYTECODE=1 -- Disable writing .pyc files
# PIP_NO_CACHE_DIR=1 -- Disable pip cache to reduce image size
# DOCKER_CONTAINER=1 -- Indicate that the application is running inside a Docker container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DOCKER_CONTAINER=1

### Install system dependencies(ssl / gcc for uvicorn) and clean up apt cache
RUN apt-get update && apt-get install -y build-essential gcc &&  rm -rf /var/lib/apt/lists/*

### Ensure logs directory is writable
RUN mkdir -p /tests/logs && chmod -R 777 /tests/logs

### Set working directory for pytest execution
WORKDIR /tests

### 1. install Python requirements first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

###  Define default entry point
# --junitxml ...  : save JUnit compatible results      --> /app/results/junit.xml
# --cov --cov-... : save coverage report (optional)    --> /app/results/coverage.xml
ENTRYPOINT ["/bin/bash"]

# Define default command to run on container start (Needs to be commenter in case if you want to use container in detached mode).
# CMD ["python3 -m pytest -sv --log-level=INFO" tests]
