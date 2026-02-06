# Runtime Specification

## Prerequisites
- Docker installed

## Build the image
docker build -t chimera-app .

## Run the container
docker run -it -p 8000:8000 --name chimera-container chimera-app

## Environment
- Runs inside Docker
- Exposes port 8000
- Python application

## Startup
- Entry point: `python server/orchestrator.py`
- Server binds to `8000:8000`

## Required Environment Variables
- None


