#!/bin/bash
HOST="XXXXXXXXXX"
user="XXXXXXXXXX"
ssh_key="XXXXXXXXXX"
TIMEOUT=30m
HARD_TIMEOUT=30m2s
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
curl -sLS https://get.k3sup.dev | sh
sudo install k3sup /usr/local/bin/
sudo k3sup install --host $HOST --user $user --ssh-key $ssh_key
export KUBECONFIG=./kubeconfig
kubectl config use-context default
kubectl get node -o wide
curl -SLsf https://get.arkade.dev/ | sudo sh
arkade get faas-cli
arkade install openfaas --set gateway.upstreamTimeout=$TIMEOUT --set gateway.writeTimeout=$HARD_TIMEOUT --set gateway.readTimeout=$HARD_TIMEOUT --set faasnetes.writeTimeout=$HARD_TIMEOUT --set faasnetes.readTimeout=$HARD_TIMEOUT --set queueWorker.ackWait=$TIMEOUT
kubectl rollout status -n openfaas deploy/gateway
kubectl port-forward -n openfaas svc/gateway 8080:8080 &
PASSWORD=$(kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode; echo)
echo -n $PASSWORD | faas-cli login --username admin --password-stdin
