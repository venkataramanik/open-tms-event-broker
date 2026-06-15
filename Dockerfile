# Tells Hugging Face to use the official Docker Compose plugin
FROM lucasalt/tesserae:latest

# Copies your cluster configuration files into the execution environment
COPY docker-compose.yml /app/docker-compose.yml
COPY api/ /app/api/
COPY workers/ /app/workers/

WORKDIR /app

# Commands Hugging Face to launch your entire multi-container network
CMD ["docker-compose", "up", "--build"]
