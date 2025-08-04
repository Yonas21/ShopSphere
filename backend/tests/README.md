# Test Suite Documentation

This directory contains comprehensive tests for the FastAPI React E-commerce application backend.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── utils.py                 # Testing utility functions and helpers
├── api/                     # API endpoint tests
│   ├── test_auth.py         # Authentication and authorization tests
│   ├── test_users.py        # User management API tests
│   ├── test_items.py        # Item management API tests
│   └── test_purchases.py    # Purchase/order API tests
├── integration/             # Integration tests
│   └── test_workflows.py    # End-to-end workflow tests
├── unit/                    # Unit tests
│   └── test_auth_utils.py   # Authentication utility function tests
└── README.md               # This file
```

## Running Tests

### Prerequisites

Make sure you have all testing dependencies installed:

```bash
pip install -r requirements.txt
```

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/api/                    # API tests only
pytest tests/unit/                   # Unit tests only
pytest tests/integration/           # Integration tests only

# Run specific test file
pytest tests/api/test_auth.py

# Run specific test function
pytest tests/api/test_auth.py::TestUserLogin::test_login_admin_success

# Run tests matching a pattern
pytest -k "test_login"              # All tests with "login" in the name
pytest -k "admin"                   # All tests with "admin" in the name
```

### Using Make Commands

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-api

# Run with coverage
make test-coverage

# Run without coverage (faster)
make test-fast

# Run specific file
make test-file FILE=tests/api/test_auth.py

# Run tests matching pattern
make test-pattern PATTERN=test_login
```

### Test Markers

Tests are categorized using markers:

```bash
# Run authentication tests
pytest -m auth

# Run security tests
pytest -m security

# Run slow tests
pytest -m slow
```

## Test Categories

### API Tests (`tests/api/`)

Test all API endpoints with various scenarios:

- **Authentication Tests** (`test_auth.py`)
  - User login/logout
  - Token validation
  - Role-based access control
  - Password verification

- **User Management Tests** (`test_users.py`)
  - User registration
  - Profile management
  - Account validation
  - Security checks

- **Item Management Tests** (`test_items.py`)
  - Item creation (admin only)
  - Item listing and filtering
  - Item deletion
  - Category management

- **Purchase Tests** (`test_purchases.py`)
  - Purchase creation
  - Stock management
  - Purchase history
  - Order validation

### Integration Tests (`tests/integration/`)

Test complete user workflows:

- **Complete Customer Workflow**
  - Registration → Login → Browse → Purchase
  - Category filtering
  - Purchase history

- **Complete Admin Workflow**
  - Item creation and management
  - Order monitoring
  - Stock tracking

- **Multi-User Scenarios**
  - Multiple customers purchasing same item
  - Purchase history isolation
  - Concurrent purchase handling

### Unit Tests (`tests/unit/`)

Test individual components in isolation:

- **Authentication Utilities**
  - Password hashing and verification
  - JWT token creation and validation
  - Security edge cases

## Test Data and Fixtures

### Shared Fixtures (conftest.py)

- `test_db`: Temporary SQLite database for each test
- `client`: FastAPI test client
- `test_admin_user`: Pre-created admin user
- `test_customer_user`: Pre-created customer user
- `admin_headers`/`customer_headers`: Authentication headers
- `test_item`: Sample item for testing
- `test_purchase`: Sample purchase for testing

### Test Utilities (utils.py)

Helper functions for common test operations:

- `assert_response_success()`: Assert successful HTTP responses
- `assert_response_error()`: Assert error HTTP responses
- `login_user()`: Login and get access token
- `create_test_item_via_api()`: Create test items via API
- `APITestHelper`: Class with common API operations

## Writing New Tests

### Basic Test Structure

```python
def test_something(self, client: TestClient, admin_headers):
    """Test description."""
    # Arrange
    test_data = {"key": "value"}
    
    # Act
    response = client.post("/api/endpoint", json=test_data, headers=admin_headers)
    
    # Assert
    assert_response_success(response, 201)
    data = response.json()
    assert data["key"] == "value"
```

### Using Fixtures

```python
def test_with_fixtures(self, client: TestClient, test_item, customer_headers):
    """Test using existing fixtures."""
    response = client.get(f"/api/items/{test_item.id}", headers=customer_headers)
    assert_response_success(response)
```

### Creating Test Data

```python
def test_with_custom_data(self, client: TestClient, admin_headers):
    """Test with custom test data."""
    item_data = {
        "name": "Test Item",
        "price": 19.99,
        "category": "Test",
        "stock_quantity": 5
    }
    
    response = client.post("/api/items/", json=item_data, headers=admin_headers)
    assert_response_success(response, 201)
```

## Test Coverage

The test suite aims for high coverage of:

- All API endpoints
- Authentication and authorization
- Business logic
- Error handling
- Edge cases
- Security scenarios

View coverage reports:

```bash
# Generate HTML coverage report
make test-coverage

# Open coverage report
open htmlcov/index.html
```

## Best Practices

### Test Naming

- Use descriptive test names: `test_customer_cannot_delete_items`
- Group related tests in classes: `TestItemCreation`
- Use action-oriented names: `test_login_with_invalid_credentials`

### Test Structure

- Follow AAA pattern: Arrange, Act, Assert
- One assertion per test when possible
- Test both success and failure cases
- Include edge cases and boundary conditions

### Test Data

- Use fixtures for common test data
- Create minimal test data for each test
- Clean up after tests (handled automatically by fixtures)
- Don't rely on external services

### Assertions

- Use helper functions for common assertions
- Provide clear error messages
- Test both data and structure
- Verify side effects (like database changes)

## Debugging Tests

### Verbose Output

```bash
# See detailed test output
pytest -v -s

# See print statements
pytest -s tests/api/test_auth.py::test_login_admin_success
```

### Debugging Specific Tests

```bash
# Add breakpoint in test
import pdb; pdb.set_trace()

# Run single test with debugger
pytest --pdb tests/api/test_auth.py::test_login_admin_success
```

### Database Inspection

```bash
# Check database state during tests
pytest --pdb -s tests/api/test_items.py
# In debugger:
# (Pdb) from database.sql_database import SessionLocal
# (Pdb) db = SessionLocal()
# (Pdb) db.query(Item).all()
```

## Continuous Integration

Tests are designed to run in CI environments:

- Use temporary databases
- No external dependencies
- Deterministic test data
- Reasonable timeouts
- Clear success/failure indicators

## Common Issues

### Database Connection Errors
- Ensure test database is properly isolated
- Check fixture dependencies
- Verify database cleanup

### Authentication Errors
- Check token expiration
- Verify user fixtures are created
- Ensure correct headers format

### Timing Issues
- Use proper async handling
- Add timeouts where needed
- Don't rely on exact timing

### Test Isolation
- Each test should be independent
- Use fixtures for test data
- Clean up after tests

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Include both success and failure cases
3. Test edge cases and security implications
4. Update documentation
5. Ensure good test coverage
6. Follow existing patterns and conventions