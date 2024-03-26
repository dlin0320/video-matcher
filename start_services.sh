eval $(minikube docker-env)

docker build -t matching-service:latest -f matching-service.Dockerfile .

docker build -t my-redis:latest -f my-redis.Dockerfile .

docker build -t mock-producer:latest -f mock-producer.Dockerfile .

docker build -t mock-consumer:latest -f mock-consumer.Dockerfile .

kubectl apply -f matching-service-deployment.yaml

kubectl apply -f my-redis-deployment.yaml

kubectl apply -f mock-producer-deployment.yaml

kubectl apply -f mock-consumer-deployment.yaml

kubectl rollout restart deployment matching-service

kubectl rollout restart deployment mock-producer

kubectl rollout restart deployment mock-consumer

echo "Services started."