.PHONY: help start backend frontend test migrate install docker-up docker-down

PYTHON ?= ./.venv/Scripts/python.exe
ifeq ($(wildcard $(PYTHON)),)
	PYTHON := python3
endif

help:
	@echo "SafeRoute AI - Micro Project 14 Makefile"
	@echo "Commands:"
	@echo "  make start       - Start both backend and frontend servers"
	@echo "  make backend     - Run Django REST backend on port 8000"
	@echo "  make frontend    - Run Vite frontend on port 5173"
	@echo "  make test        - Run Django REST API test suite"
	@echo "  make migrate     - Run database migrations"
	@echo "  make install     - Install Python and Node dependencies"
	@echo "  make docker-up   - Launch containers using Docker Compose"
	@echo "  make docker-down - Stop Docker Compose containers"

install:
	pip install -r requirements.txt
	npm --prefix frontend install

migrate:
	$(PYTHON) backend/manage.py migrate

test:
	$(PYTHON) backend/manage.py test api

backend:
	$(PYTHON) backend/manage.py runserver 0.0.0.0:8000

frontend:
	npm --prefix frontend run dev

start:
	@echo "Starting SafeRoute AI backend and frontend..."
	powershell -ExecutionPolicy Bypass -File ./start.ps1

docker-up:
	docker compose up --build

docker-down:
	docker compose down
