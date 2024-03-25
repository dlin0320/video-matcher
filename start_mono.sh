#!/bin/bash
docker ps -a | awk '{ print $1,$2 }' | grep matching-service:latest | awk '{print $1 }' | xargs -I {} docker stop {}

docker ps -a | awk '{ print $1,$2 }' | grep matching-service:latest | awk '{print $1 }' | xargs -I {} docker rm {}

docker ps -a | awk '{ print $1,$2 }' | grep my-redis:latest | awk '{print $1 }' | xargs -I {} docker stop {}

docker ps -a | awk '{ print $1,$2 }' | grep my-redis:latest | awk '{print $1 }' | xargs -I {} docker rm {}

docker build -t matching-service:latest -f matching-service.Dockerfile .

docker build -t my-redis:latest -f my-redis.Dockerfile .

docker run -d -p 8000:8000 matching-service:latest

docker run -d -p 6379:6379 my-redis:latest