"""
Utility functions for testing.
"""
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient


def assert_response_success(response, expected_status=200):
    """Assert that a response is successful."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_response_error(response, expected_status=400):
    """Assert that a response is an error."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_json_contains(response_json: Dict[str, Any], expected_fields: Dict[str, Any]):
    """Assert that JSON response contains expected fields with values."""
    for field, expected_value in expected_fields.items():
        assert field in response_json, f"Field '{field}' not found in response"
        if expected_value is not None:
            assert response_json[field] == expected_value, f"Field '{field}': expected {expected_value}, got {response_json[field]}"


def assert_json_has_fields(response_json: Dict[str, Any], required_fields: list):
    """Assert that JSON response has all required fields."""
    for field in required_fields:
        assert field in response_json, f"Required field '{field}' not found in response"


def login_user(client: TestClient, username: str, password: str) -> str:
    """Login a user and return the access token."""
    response = client.post(
        "/api/users/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers with token."""
    return {"Authorization": f"Bearer {token}"}


def create_test_item_via_api(
    client: TestClient, 
    headers: Dict[str, str], 
    item_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a test item via API and return the response data."""
    if item_data is None:
        item_data = {
            "name": "API Test Item",
            "description": "Created via API for testing",
            "price": 19.99,
            "category": "Test",
            "stock_quantity": 8
        }
    
    response = client.post("/api/items/", json=item_data, headers=headers)
    assert_response_success(response, 201)
    return response.json()


def purchase_item_via_api(
    client: TestClient, 
    headers: Dict[str, str], 
    item_id: int, 
    quantity: int = 1
) -> Dict[str, Any]:
    """Purchase an item via API and return the response data."""
    purchase_data = {"item_id": item_id, "quantity": quantity}
    response = client.post("/api/items/purchase", json=purchase_data, headers=headers)
    assert_response_success(response, 201)
    return response.json()


def get_user_profile(client: TestClient, headers: Dict[str, str]) -> Dict[str, Any]:
    """Get user profile via API."""
    response = client.get("/api/users/me", headers=headers)
    assert_response_success(response)
    return response.json()


class APITestHelper:
    """Helper class for API testing."""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def login_admin(self) -> str:
        """Login as admin and return token."""
        return login_user(self.client, "admin", "adminpass")
    
    def login_customer(self) -> str:
        """Login as customer and return token."""
        return login_user(self.client, "customer", "customerpass")
    
    def create_item(self, admin_token: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create item as admin."""
        headers = get_auth_headers(admin_token)
        return create_test_item_via_api(self.client, headers, item_data)
    
    def purchase_item(self, customer_token: str, item_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Purchase item as customer."""
        headers = get_auth_headers(customer_token)
        return purchase_item_via_api(self.client, headers, item_id, quantity)
    
    def get_items(self, token: str, category: Optional[str] = None) -> list:
        """Get items list."""
        headers = get_auth_headers(token)
        params = {"category": category} if category else {}
        response = self.client.get("/api/items/", headers=headers, params=params)
        assert_response_success(response)
        return response.json()
    
    def get_purchases(self, token: str, all_purchases: bool = False) -> list:
        """Get purchases list."""
        headers = get_auth_headers(token)
        endpoint = "/api/items/purchases/all" if all_purchases else "/api/items/purchases/my"
        response = self.client.get(endpoint, headers=headers)
        assert_response_success(response)
        return response.json()
    
    def delete_item(self, admin_token: str, item_id: int) -> None:
        """Delete item as admin."""
        headers = get_auth_headers(admin_token)
        response = self.client.delete(f"/api/items/{item_id}", headers=headers)
        assert_response_success(response, 204)


# Constants for testing
TEST_USER_DATA = {
    "admin": {"username": "admin", "password": "adminpass", "email": "admin@test.com"},
    "customer": {"username": "customer", "password": "customerpass", "email": "customer@test.com"}
}

SAMPLE_ITEM_DATA = {
    "electronics": {
        "name": "Smartphone",
        "description": "Latest smartphone with advanced features",
        "price": 699.99,
        "category": "Electronics",
        "stock_quantity": 15,
        "image_url": "https://example.com/smartphone.jpg"
    },
    "books": {
        "name": "Python Programming Guide",
        "description": "Comprehensive guide to Python programming",
        "price": 29.99,
        "category": "Books",
        "stock_quantity": 20
    },
    "low_stock": {
        "name": "Limited Edition Item",
        "description": "Rare collectible item",
        "price": 199.99,
        "category": "Collectibles",
        "stock_quantity": 2
    }
}

ERROR_MESSAGES = {
    "unauthorized": "Not authenticated",
    "forbidden": "Not enough permissions",
    "not_found": "Item not found",
    "insufficient_stock": "Insufficient stock",
    "invalid_credentials": "Incorrect username or password"
}