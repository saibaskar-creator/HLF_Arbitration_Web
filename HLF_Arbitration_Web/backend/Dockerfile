# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2 and other libs
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
# We assume the build context is the HLF_Arbitration_Web root directory
COPY backend/requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# We copy specific directories to avoid cluttering /app with unrelated files (like frontend)
COPY backend/ /app/backend/
COPY src/ /app/src/
COPY prompts/ /app/prompts/

# Set environment variable for Google Cloud functionality if needed
# ENV GOOGLE_APPLICATION_CREDENTIALS=/app/backend/service-account-key.json
# (Note: In Cloud Run, we usually use Workload Identity, but for dev we might mount secrets)

# Set working directory to backend to match local dev execution path
WORKDIR /app/backend

# Make sure the app listens on port 8080 (Cloud Run default)
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
