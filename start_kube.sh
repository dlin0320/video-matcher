#!/bin/bash
MINIKUBE_STATUS=$(minikube status --format "{{.Host}}")
if [[ "$MINIKUBE_STATUS" != "Running" ]]; then
    echo "Starting Minikube..."
    minikube start --memory 4096 --cpus 2
    echo "Minikube started."
else
    echo "Minikube is already running."
fi