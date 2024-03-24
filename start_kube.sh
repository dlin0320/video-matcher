#!/bin/bash
eval $(minikube docker-env)
docker build -t matching-service:latest -f matching-service.Dockerfile .
kubectl apply -f matching-service-deployment.yaml
kubectl rollout restart deployment/matching-service