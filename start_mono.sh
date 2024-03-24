#!/bin/bash
docker build -t matching-service:latest -f matching-service.Dockerfile .
docker run -d -p 8080:8080 matching-service:latest