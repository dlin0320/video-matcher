#!/bin/bash
MINIKUBE_STATUS=$(minikube status --format "{{.Host}}")
if [[ "$MINIKUBE_STATUS" != "Running" ]]; then
    echo "Starting Minikube..."
    minikube start
else
    echo "Minikube is already running."
fi

eval $(minikube docker-env)

docker build -t matching-service:latest -f matching-service.Dockerfile .

docker build -t my-redis:latest -f my-redis.Dockerfile .

kubectl apply -f matching-service-deployment.yaml

kubectl apply -f my-redis-deployment.yaml