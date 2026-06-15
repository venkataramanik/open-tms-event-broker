# Use a clean, official open-source Python base image
FROM python:3.11-slim

# Install system dependencies required for PostgreSQL and network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root system user for security compliance on Hugging Face
RUN useradd -m -u 1000 user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy and install API Gateway requirements
COPY api/requirements.txt ./api_requirements.txt
RUN pip install --no-cache-dir -r ./api_requirements.txt

# Copy and install background worker requirements
COPY workers/requirements.txt ./worker_requirements.txt
RUN pip install --no-cache-dir -r ./worker_requirements.txt

# Copy all application code into the container
COPY --chown=user:user api/ ./api/
COPY --chown=user:user workers/ ./workers/

# Secure the application directory recursively using the correct -R flag
RUN chown -R user:user /app
USER user

EXPOSE 7860

# Command the container to run your API gateway on the required port
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
