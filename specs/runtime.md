# Runtime Specification

## Prerequisites
- Docker installed

## Docker

The Dockerfile is located in `app/`.

Build the image from the repository root:

docker build -f app/Dockerfile -t chimera-app app

Run the container:

docker run -p 8000:8000 chimera-app


## Environment
- Runs inside Docker
- Exposes port 8000
- Python application

## Startup
- Entry point: `python server/orchestrator.py`
- Server binds to `8000:8000`

## Required Environment Variables
- None


