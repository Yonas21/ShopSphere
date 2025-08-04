"""
Tests for authentication endpoints and functionality.
"""
import pytest
from fastapi.testclient import TestClient

from tests.utils import (
    assert_response_success, 
    assert_response_error, 
    assert_json_contains,
    assert_json_has_fields,
    login_user,
    get_auth_headers
)


class TestUserLogin:
    """Test user login functionality."""
    
    def test_login_admin_success(self, client: TestClient, test_admin_user):
        """Test successful admin login."""
        response = client.post(
            "/api/users/login",
            json={"username": "admin", "password": "adminpass"}
        )
        
        assert_response_success(response)
        data = response.json()
        
        # Check response structure
        assert_json_has_fields(data, ["access_token", "token_type"])
        assert_json_contains(data, {"token_type": "bearer"})
        
        # Verify token is present and not empty
        assert data["access_token"]
        assert len(data["access_token"]) > 20  # JWT tokens are much longer
    
    def test_login_customer_success(self, client: TestClient, test_customer_user):
        """Test successful customer login."""
        response = client.post(
            "/api/users/login",
            json={"username": "customer", "password": "customerpass"}
        )
        
        assert_response_success(response)
        data = response.json()
        
        assert_json_has_fields(data, ["access_token", "token_type"])
        assert_json_contains(data, {"token_type": "bearer"})
        assert data["access_token"]
    
    def test_login_invalid_username(self, client: TestClient):
        """Test login with invalid username."""
        response = client.post(
            "/api/users/login",
            json={"username": "nonexistent", "password": "password"}
        )
        
        assert_response_error(response, 401)
        data = response.json()
        assert "detail" in data
    
    def test_login_invalid_password(self, client: TestClient, test_admin_user):
        """Test login with invalid password."""
        response = client.post(
            "/api/users/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        
        assert_response_error(response, 401)
        data = response.json()
        assert "detail" in data
    
    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing credentials."""
        # Missing password
        response = client.post(
            "/api/users/login",
            json={"username": "admin"}
        )
        assert_response_error(response, 422)
        
        # Missing username
        response = client.post(
            "/api/users/login",
            json={"password": "password"}
        )
        assert_response_error(response, 422)
        
        # Missing both
        response = client.post("/api/users/login", json={})
        assert_response_error(response, 422)
    
    def test_login_empty_credentials(self, client: TestClient):
        """Test login with empty credentials."""
        response = client.post(
            "/api/users/login",
            json={"username": "", "password": ""}
        )
        assert_response_error(response, 401)


class TestTokenAuthentication:
    """Test token-based authentication."""
    
    def test_access_protected_endpoint_with_valid_token(self, client: TestClient, test_admin_user):
        """Test accessing protected endpoint with valid token."""
        # Login to get token
        token = login_user(client, "admin", "adminpass")
        headers = get_auth_headers(token)
        
        # Access protected endpoint
        response = client.get("/api/users/me", headers=headers)
        assert_response_success(response)
        
        data = response.json()
        assert_json_contains(data, {
            "username": "admin",
            "email": "admin@test.com",
            "role": "admin"
        })
    
    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/users/me")
        assert_response_error(response, 401)
    
    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = get_auth_headers("invalid.token.here")
        response = client.get("/api/users/me", headers=headers)
        assert_response_error(response, 401)
    
    def test_access_protected_endpoint_with_malformed_token(self, client: TestClient):
        """Test accessing protected endpoint with malformed token."""
        headers = {"Authorization": "Bearer not-a-jwt-token"}
        response = client.get("/api/users/me", headers=headers)
        assert_response_error(response, 401)
    
    def test_access_protected_endpoint_with_wrong_auth_scheme(self, client: TestClient, test_admin_user):
        """Test accessing protected endpoint with wrong auth scheme."""
        token = login_user(client, "admin", "adminpass")
        
        # Use Basic instead of Bearer
        headers = {"Authorization": f"Basic {token}"}
        response = client.get("/api/users/me", headers=headers)
        assert_response_error(response, 401)


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_admin_can_access_admin_endpoints(self, client: TestClient, admin_headers):
        """Test that admin can access admin-only endpoints."""
        # Test creating item (admin only)
        item_data = {
            "name": "Admin Test Item",
            "description": "Item created by admin",
            "price": 99.99,
            "category": "Test",
            "stock_quantity": 5
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        # Test accessing all purchases (admin only)
        response = client.get("/api/items/purchases/all", headers=admin_headers)
        assert_response_success(response)
    
    def test_customer_cannot_access_admin_endpoints(self, client: TestClient, customer_headers):
        """Test that customer cannot access admin-only endpoints."""
        # Test creating item (admin only)
        item_data = {
            "name": "Customer Test Item",
            "description": "Item creation attempt by customer",
            "price": 99.99,
            "category": "Test",
            "stock_quantity": 5
        }
        
        response = client.post("/api/items/", json=item_data, headers=customer_headers)
        assert_response_error(response, 403)
        
        # Test accessing all purchases (admin only)
        response = client.get("/api/items/purchases/all", headers=customer_headers)
        assert_response_error(response, 403)
    
    def test_customer_can_access_customer_endpoints(self, client: TestClient, customer_headers):
        """Test that customer can access customer endpoints."""
        # Test accessing own profile
        response = client.get("/api/users/me", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        assert_json_contains(data, {"role": "customer"})
        
        # Test accessing items list
        response = client.get("/api/items/", headers=customer_headers)
        assert_response_success(response)
        
        # Test accessing own purchases
        response = client.get("/api/items/purchases/my", headers=customer_headers)
        assert_response_success(response)
    
    def test_both_roles_can_access_common_endpoints(self, client: TestClient, admin_headers, customer_headers):
        """Test that both roles can access common endpoints."""
        # Test items list access
        for headers in [admin_headers, customer_headers]:
            response = client.get("/api/items/", headers=headers)
            assert_response_success(response)
            
            # Test user profile access
            response = client.get("/api/users/me", headers=headers)
            assert_response_success(response)


class TestUserProfile:
    """Test user profile endpoint."""
    
    def test_get_admin_profile(self, client: TestClient, admin_headers, test_admin_user):
        """Test getting admin user profile."""
        response = client.get("/api/users/me", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        expected_fields = ["id", "email", "username", "role", "is_active"]
        assert_json_has_fields(data, expected_fields)
        
        assert_json_contains(data, {
            "username": "admin",
            "email": "admin@test.com",
            "role": "admin",
            "is_active": True
        })
    
    def test_get_customer_profile(self, client: TestClient, customer_headers, test_customer_user):
        """Test getting customer user profile."""
        response = client.get("/api/users/me", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        expected_fields = ["id", "email", "username", "role", "is_active"]
        assert_json_has_fields(data, expected_fields)
        
        assert_json_contains(data, {
            "username": "customer",
            "email": "customer@test.com",
            "role": "customer",
            "is_active": True
        })
    
    def test_profile_does_not_expose_sensitive_data(self, client: TestClient, admin_headers):
        """Test that profile endpoint doesn't expose sensitive data."""
        response = client.get("/api/users/me", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        
        # These fields should NOT be in the response
        sensitive_fields = ["password", "hashed_password", "hash"]
        for field in sensitive_fields:
            assert field not in data, f"Sensitive field '{field}' should not be exposed"


class TestTokenExpiration:
    """Test token expiration and refresh functionality."""
    
    def test_token_works_immediately_after_login(self, client: TestClient, test_admin_user):
        """Test that token works immediately after login."""
        token = login_user(client, "admin", "adminpass")
        headers = get_auth_headers(token)
        
        # Should work immediately
        response = client.get("/api/users/me", headers=headers)
        assert_response_success(response)
    
    # Note: Testing actual token expiration would require waiting or mocking time
    # For now, we test the structure and immediate functionality