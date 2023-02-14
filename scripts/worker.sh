#!/bin/bash
WORKER="XXXXXXXXXX"
HOST="XXXXXXXXXX"
user="XXXXXXXXXX"
ssh_key="XXXXXXXXXX"
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -r kubectl
curl -sLS https://get.k3sup.dev | sh
sudo mv k3sup /usr/local/bin/k3sup
k3sup join --ip $WORKER --server-ip $HOST --user $user --ssh-key $ssh_key
