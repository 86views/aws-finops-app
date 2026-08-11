.PHONY: help install lint test run docker-up docker-down tf-init tf-plan tf-apply report

help:
	@echo "AWS FinOps – available targets:"
	@echo "  install     Install Python deps (incl. dev)"
	@echo "  lint        Ruff + mypy"
	@echo "  test        Pytest with coverage"
	@echo "  run         Start FastAPI locally"
	@echo "  docker-up   Build & start via Compose"
	@echo "  docker-down Stop Compose stack"
	@echo "  tf-init     Terraform init (dev)"
	@echo "  tf-plan     Terraform plan (dev)"
	@echo "  tf-apply    Terraform apply (dev)"
	@echo "  report      Generate daily report"

install:
	pip install -e ".[dev]"

lint:
	ruff check app tests
	ruff format --check app tests
	mypy app

test:
	pytest

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

tf-init:
	cd terraform/environments/dev && terraform init

tf-plan:
	cd terraform/environments/dev && terraform plan -var-file=terraform.tfvars

tf-apply:
	cd terraform/environments/dev && terraform apply -var-file=terraform.tfvars

report:
	python -m app.reports.cli --period daily
