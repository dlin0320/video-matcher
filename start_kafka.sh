#!/bin/bash
if ! helm repo list | grep -q bitnami; then
    helm repo add bitnami https://charts.bitnami.com/bitnami
    echo "Bitnami repository added."
else
    echo "Bitnami repository already exists."
fi

helm repo update

deploy_kafka_cluster() {
    release_name=$1
    if helm list -q | grep -q "^$release_name$"; then
        echo "Upgrading $release_name..."
        helm upgrade "$release_name" bitnami/kafka --set global.storageClass=standard --set replicaCount=1 --set zookeeper.replicaCount=1
    else
        echo "Installing $release_name..."
        helm install "$release_name" bitnami/kafka --set global.storageClass=standard --set replicaCount=1 --set zookeeper.replicaCount=1
    fi
}

deploy_kafka_cluster kafka-cluster-1
deploy_kafka_cluster kafka-cluster-2
deploy_kafka_cluster kafka-cluster-3

echo "Deployment process completed. Checking pods..."

kubectl get pods

echo "Remember to adjust port-forwarding or service exposure based on your access needs."
