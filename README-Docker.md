# AI Backend Docker Setup

This document provides instructions for running the AI Backend service using Docker.

## Prerequisites

- Docker and Docker Compose installed
- API keys for the services you want to use (OpenAI, Gemini, Pinecone, etc.)

## Environment Variables

Create a `.env` file in the `ai-backend` directory with the following variables:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Pinecone Configuration
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=bakchod-ai-whatsapp

# Redis Configuration
REDIS_URL=redis://redis:6379

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
MAX_CONVERSATION_HISTORY=50
MAX_RESPONSE_LENGTH=500
```

## Quick Start

1. **Build and run with Docker Compose:**
   ```bash
   cd ai-backend
   docker-compose up --build
   ```

2. **Run in detached mode:**
   ```bash
   docker-compose up -d --build
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f ai-backend
   ```

## Individual Docker Commands

### Build the image:
```bash
docker build -t bakchod-ai-backend .
```

### Run the container:
```bash
docker run -d \
  --name bakchod-ai-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e GEMINI_API_KEY=your_key_here \
  -e PINECONE_API_KEY=your_key_here \
  bakchod-ai-backend
```

## API Endpoints

Once running, the service will be available at `http://localhost:8000`:

- **Health Check:** `GET /health`
- **API Documentation:** `GET /docs`
- **Generate AI Response:** `POST /api/v1/ai/generate-response`
- **Character Management:** `GET /api/v1/characters/`

## Health Monitoring

The container includes a health check that monitors the service every 30 seconds. You can check the health status with:

```bash
docker ps
```

Look for the `STATUS` column to see if the container is healthy.

## Troubleshooting

### Common Issues:

1. **Service not starting:**
   - Check if all required API keys are set
   - Verify the logs: `docker-compose logs ai-backend`

2. **Pinecone connection issues:**
   - Ensure your Pinecone API key is valid
   - Check if the environment region is correct

3. **Memory issues:**
   - The service requires sufficient memory for AI models
   - Consider increasing Docker memory limits

### Viewing Logs:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs ai-backend

# Follow logs in real-time
docker-compose logs -f ai-backend
```

### Stopping Services:

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Development

For development with hot reloading:

```bash
# Override the command for development
docker-compose run --rm -p 8000:8000 ai-backend uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Production Deployment

For production deployment:

1. Use environment-specific `.env` files
2. Set `DEBUG=false`
3. Configure proper logging levels
4. Set up monitoring and alerting
5. Use a reverse proxy (nginx) for SSL termination
6. Configure proper resource limits

## Security Notes

- The container runs as a non-root user for security
- API keys should be stored securely and not committed to version control
- Use Docker secrets for sensitive data in production
- Regularly update base images for security patches
