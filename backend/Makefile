# Makefile for FastAPI backend development and testing

.PHONY: help install test test-unit test-integration test-api test-coverage clean lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-api         Run API tests only"
	@echo "  test-coverage    Run tests with detailed coverage report"
	@echo "  test-fast        Run tests without coverage"
	@echo "  lint             Run code linting"
	@echo "  format           Format code"
	@echo "  clean            Clean test artifacts"
	@echo "  run              Run the development server"

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	pytest

# Run only unit tests
test-unit:
	pytest tests/unit/ -v

# Run only integration tests
test-integration:
	pytest tests/integration/ -v

# Run only API tests
test-api:
	pytest tests/api/ -v

# Run tests with detailed coverage
test-coverage:
	pytest --cov=. --cov-branch --cov-report=html --cov-report=term-missing

# Run tests without coverage (faster)
test-fast:
	pytest --no-cov

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=tests/api/test_auth.py"; \
	else \
		pytest $(FILE) -v; \
	fi

# Run tests matching a pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=test_login"; \
	else \
		pytest -k "$(PATTERN)" -v; \
	fi

# Run tests with specific markers
test-auth:
	pytest -m auth -v

test-security:
	pytest -m security -v

test-slow:
	pytest -m slow -v

# Code quality
lint:
	@echo "Running flake8..."
	@if command -v flake8 > /dev/null; then \
		flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

format:
	@echo "Running black..."
	@if command -v black > /dev/null; then \
		black . --line-length 100; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi

# Clean up
clean:
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f app.db
	rm -f test_*.db

# Development server
run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Database operations
reset-db:
	rm -f app.db
	python -c "from database.sql_database import engine; from models.user import Base; Base.metadata.create_all(bind=engine)"

# Create test data
create-test-data:
	python -c "
from database.sql_database import SessionLocal, engine
from models.user import Base, User, UserRole
from auth import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Create admin user
admin = User(
    email='admin@test.com',
    username='admin',
    hashed_password=get_password_hash('adminpass'),
    role=UserRole.ADMIN
)
db.add(admin)

# Create customer user
customer = User(
    email='customer@test.com',
    username='customer',
    hashed_password=get_password_hash('customerpass'),
    role=UserRole.CUSTOMER
)
db.add(customer)

try:
    db.commit()
    print('Test users created successfully!')
except Exception as e:
    print(f'Error creating test users: {e}')
finally:
    db.close()
"

# Test database setup
setup-test-db:
	@echo "Setting up test database..."
	python -c "
from sqlalchemy import create_engine
from models.user import Base
from models.item import Base as ItemBase

engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(bind=engine)
print('Test database created successfully!')
"

# Check test setup
check-setup:
	@echo "Checking test setup..."
	@python -c "
import sys
try:
    import pytest
    import httpx
    import sqlalchemy
    import fastapi
    print('✓ All required packages installed')
except ImportError as e:
    print(f'✗ Missing package: {e}')
    sys.exit(1)
"
	@echo "✓ Test setup is ready"

# Continuous testing (requires pytest-watch)
watch:
	@if command -v ptw > /dev/null; then \
		ptw --runner "pytest --no-cov"; \
	else \
		echo "pytest-watch not installed. Install with: pip install pytest-watch"; \
	fi