.PHONY: buid-owner-job
buid-owner-job:
	docker build -f docker/Dockerfile.owner_job -t hemantkashniyal/k8s-owner-job:latest .

.PHONY: push-owner-job
push-owner-job:
	docker push hemantkashniyal/k8s-owner-job:latest

.PHONY: buid-owner-service
buid-owner-service:
		docker build -f docker/Dockerfile.owner_service -t hemantkashniyal/k8s-owner-service:latest .

.PHONY: push-owner-service
push-owner-service:
	docker push hemantkashniyal/k8s-owner-service:latest

.PHONY: docker-build
docker-build: buid-owner-job buid-owner-service

.PHONY: docker-push
docker-push: push-owner-job push-owner-service

.PHONY: docker-run
docker-run:
	docker compose -f docker/docker-compose.yaml up -d

.PHONY: run-owner-service
run-owner-service: docker-run
	fastapi dev service/owner-service/run.py --reload

.PHONY: run-owner-job
run-owner-job: docker-run
	python3 job/owner-job/run.py


.PHONY: run-prod-owner-service
run-prod-owner-service: docker-run
	ENVIRONMENT=prod fastapi run --workers 4 service/owner-service/run.py
