#!/bin/bash
HOST="XXXXXXXXXX"
user="XXXXXXXXXX"
ssh_key="XXXXXXXXXX"
TIMEOUT=48h
HARD_TIMEOUT=48h2s
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -r kubectl
curl -sLS https://get.k3sup.dev | sh
sudo mv k3sup /usr/local/bin/k3sup
curl -SLsf https://get.arkade.dev/ | sudo sh
arkade get faas-cli
sudo mv $HOME/.arkade/bin/faas-cli /usr/local/bin/
k3sup install --host $HOST --user $user --ssh-key $ssh_key --local-path $HOME/serverless-workflow-reduction/scripts/kubeconfig
export KUBECONFIG=$HOME/serverless-workflow-reduction/scripts/kubeconfig
kubectl config use-context default
kubectl get node -o wide
arkade install openfaas --load-balancer true --set queueWorker.maxInflight=10000000 --set gateway.upstreamTimeout=$TIMEOUT --set gateway.writeTimeout=$HARD_TIMEOUT --set gateway.readTimeout=$HARD_TIMEOUT --set faasnetes.writeTimeout=$HARD_TIMEOUT --set faasnetes.readTimeout=$HARD_TIMEOUT --set queueWorker.ackWait=$TIMEOUT
kubectl rollout status -n openfaas deploy/gateway
kubectl port-forward -n openfaas svc/gateway 8080:8080 &
sleep 30s
PASSWORD=$(kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode; echo)
echo -n $PASSWORD | faas-cli login --username admin --password-stdin
arkade install mongodb
export MONGODB_ROOT_PASSWORD=$(sudo k3s kubectl get secret --namespace default mongodb -o jsonpath="{.data.mongodb-root-password}" | base64 --decode)
kubectl port-forward --namespace default svc/mongodb 27017:27017 &
arkade install redis
export REDIS_PASSWORD=$(sudo k3s kubectl get secret --namespace redis redis -o jsonpath="{.data.redis-password}" | base64 --decode)
kubectl port-forward --namespace redis svc/redis-master 6379:6379 &
faas-cli secret create mongo-db-password --from-literal $MONGODB_ROOT_PASSWORD
faas-cli secret create redis-password --from-literal $REDIS_PASSWORD
faas-cli store deploy shasum
faas-cli store deploy SentimentAnalysis
python3 set-redis.py $REDIS_PASSWORD
