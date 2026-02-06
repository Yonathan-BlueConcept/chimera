## Prerequisites
- Docker installed

## Build the image
docker build -t chimera-app .

## Run the container
docker run -it -p 8000:8000 --name chimera-container chimera-app


