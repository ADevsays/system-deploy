.PHONY: help install auth validate test build up down logs restart clean

help:
	@echo "Content Processing API - Makefile Commands"
	@echo ""
	@echo "Setup & Configuration:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make auth         - Setup Google Drive authentication"
	@echo "  make validate     - Validate deployment configuration"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run local tests"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build        - Build Docker image"
	@echo "  make up           - Start containers"
	@echo "  make down         - Stop containers"
	@echo "  make logs         - View logs"
	@echo "  make restart      - Restart containers"
	@echo "  make clean        - Remove containers and volumes"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

auth:
	@echo "Setting up Google Drive authentication..."
	python scripts/setup_auth.py

validate:
	@echo "Validating deployment configuration..."
	python scripts/validate_deployment.py

test:
	@echo "Running local tests..."
	python scripts/test_local.py

build:
	@echo "Building Docker image..."
	docker-compose build

up:
	@echo "Starting containers..."
	docker-compose up -d
	@echo "API running at http://localhost:8000"

down:
	@echo "Stopping containers..."
	docker-compose down

logs:
	@echo "Viewing logs (Ctrl+C to exit)..."
	docker-compose logs -f api

restart:
	@echo "Restarting containers..."
	docker-compose restart api

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Done!"

dev:
	@echo "Starting development server..."
	uvicorn app.main:app --reload --port 8000

deploy: validate build up
	@echo "Deployment complete!"
	@echo "Run 'make logs' to view logs"
