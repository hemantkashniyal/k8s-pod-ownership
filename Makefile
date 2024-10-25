DOCKER_USERNAME=hemantkashniyal

.PHONY: buid-owner-job
buid-owner-job:
	docker build -f docker/Dockerfile.owner_job -t ${DOCKER_USERNAME}/k8s-owner-job:latest .

.PHONY: push-owner-job
push-owner-job:
	docker push ${DOCKER_USERNAME}/k8s-owner-job:latest

.PHONY: buid-owner-service
buid-owner-service:
	docker build -f docker/Dockerfile.owner_service -t ${DOCKER_USERNAME}/k8s-owner-service:latest .

.PHONY: push-owner-service
push-owner-service:
	docker push ${DOCKER_USERNAME}/k8s-owner-service:latest

.PHONY: docker-build
docker-build: buid-owner-job buid-owner-service

.PHONY: docker-push
docker-push: push-owner-job push-owner-service


.PHONY: docker-restart
docker-restart: docker-stop docker-start

.PHONY: docker-stop
docker-stop:
	docker compose -f docker/docker-compose.yaml down

.PHONY: docker-start
docker-start:
	docker compose -f docker/docker-compose.yaml up -d

.PHONY: run-owner-service
run-owner-service: docker-start
	OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
	OTEL_RESOURCE_ATTRIBUTES="service.name=unnamed-service" \
	OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
	OTEL_SERVICE_NAME=ownership-service \
	OTEL_TRACES_EXPORTER=otlp \
	OTEL_METRICS_EXPORTER=otlp \
	OTEL_LOGS_EXPORTER=none \
	opentelemetry-instrument \
	fastapi run service/owner-service/run.py

.PHONY: run-owner-job
run-owner-job: docker-start
	python3 job/owner-job/run.py

.PHONY: run-prod-owner-service
run-prod-owner-service: docker-start
	OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
	OTEL_RESOURCE_ATTRIBUTES="service.name=unnamed-service" \
	OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
	OTEL_SERVICE_NAME=ownership-service \
	OTEL_TRACES_EXPORTER=otlp \
	OTEL_METRICS_EXPORTER=otlp \
	OTEL_LOGS_EXPORTER=none \
	opentelemetry-instrument \
	ENVIRONMENT=prod fastapi run --workers 4 service/owner-service/run.py
