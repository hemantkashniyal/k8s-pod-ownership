# k8s-pod-ownership
This project is a Kubernetes operator that manages ownership records for pods in a database. It provides an API to get and set ownership records for pods, and a job to update the ownership records periodically.

Any deleted pod's (from the k8s cluster) will have its ownership record kept for 7 days, after which it will be deleted.

Sample record looks like this:
```
{
    "namespace": "k8s-ownership",
    "pod_name": "k8s-owner-job-cronjob-28797352-9fk2z",
    "owner": "Job",
    "owner_name": "k8s-owner-job-cronjob-28797352",
    "updated_at": "1727841305.496536",
    "deleted": "true"
}
```

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [API Reference](#api-reference)
- [Local Development](#local-development)
## Overview

This project is designed to help manage ownership of Kubernetes pods in a Redis database. It provides an API to get and set ownership records for pods, and a job to update the ownership records periodically.

## Prerequisites

- Kubernetes cluster
  - Set up a Kubernetes cluster using Minikube, Docker Desktop or any other Kubernetes cluster.
  - Install `kubectl` CLI for your cluster.
- Redis database
  - Set up a Redis database using [docker compose](./docker/docker-compose.yaml) (for local development)
  - Or set up a Redis database in your [cluster](./k8s/redis-datastore.yaml) (for deployment)
- Python 3.10 or later
- pip
- kubectl
- docker

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/k8s-pod-owner.git
   ```

1. Set up the Kubernetes cluster and Redis database.
    ```
    kubectl create namespace k8s-ownership
    ```
    ```
    kubectl apply -f k8s/redis-datastore.yaml -n k8s-ownership
    ```
1. Apply the Kubernetes configuration:

    Either apply all the files in the `k8s/` directory:
    ```
    kubectl apply -f k8s/ -n k8s-ownership
    ```
    Or apply each file separately:
    ```
    kubectl apply -f k8s/k8s-ownership-roles.yaml -n k8s-ownership
    ```
    ```
    kubectl apply -f k8s/k8s-ownership-config.yaml -n k8s-ownership
    ```
    ```
    kubectl apply -f k8s/k8s-ownership-job.yaml -n k8s-ownership
    ```
    ```
    kubectl apply -f k8s/k8s-ownership-service.yaml -n k8s-ownership
    ```

1. Portforward the service to your local machine:
    ```
    kubectl port-forward svc/ownership-service 8003:8000 -n k8s-ownership
    ```

## API Reference

http://localhost:8003/docs is the link to the API reference:


## Local Development

Running service and job locally will first spin a Redis database in a container and then run the service and job. Job script will connect to the default K8S cluster and update the ownership records in the Redis database.

1. Create a virtual environment and install the dependencies:

    ```
    python3 -m venv .venv
    source venv/bin/activate
    pip install -r service/owner-service/requirements.txt job/owner-job/requirements.txt
    ```

1. Run the service:
    ```
    make run-owner-service
    ```

1. Run the job:
    ```
    make run-owner-job
    ```
1. Access the API at http://localhost:8000/docs

1. To package the job and push it to the docker hub:
   - Requires docker login
   - Update `DOCKER_USERNAME` in Makefile
   - Update docker image path in corresponsding files in `k8s/` directory
    ```
    make docker-build docker-push
    ```
