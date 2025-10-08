.PHONY: help start stop restart logs clean test init-db

help:
	@echo "Personal-Q AI Agent Management System"
	@echo ""
	@echo "Available commands:"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs"
	@echo "  make clean      - Remove volumes and data"
	@echo "  make test       - Run tests"
	@echo "  make init-db    - Initialize database with sample data"

start:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/api/v1/docs"

stop:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -rf backend/data

test:
	cd backend && pytest

init-db:
	docker-compose exec backend python app/db/init_db.py
