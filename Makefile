.PHONY: buid-owner-operator
buid-owner-operator:
	docker build -f docker/Dockerfile.owner_operator -t hemantkashniyal/k8s-owner-operator:latest .

.PHONY: push-owner-operator
push-owner-operator:
	docker push hemantkashniyal/k8s-owner-operator:latest

.PHONY: buid-owner-service
buid-owner-service:
		docker build -f docker/Dockerfile.owner_service -t hemantkashniyal/k8s-owner-service:latest .

.PHONY: push-owner-service
push-owner-service:
	docker push hemantkashniyal/k8s-owner-service:latest

.PHONY: docker-build
docker-build: buid-owner-operator buid-owner-service

.PHONY: docker-push
docker-push: push-owner-operator push-owner-service

.PHONY: docker-run
docker-run:
	docker compose -f docker/docker-compose.yaml up -d

.PHONY: run-owner-service
run-owner-service: docker-run
	fastapi dev service/owner-service/run.py --reload

.PHONY: run-prod-owner-service
run-prod-owner-service: docker-run
	ENVIRONMENT=prod fastapi run service/owner-service/run.py
