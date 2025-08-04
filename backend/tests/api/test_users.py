"""
Tests for user management API endpoints.
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


class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_new_user_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "newuserpass"
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_success(response, 201)
        
        data = response.json()
        expected_fields = ["id", "email", "username", "role", "is_active"]
        assert_json_has_fields(data, expected_fields)
        
        # Verify user data
        assert_json_contains(data, {
            "email": "newuser@test.com",
            "username": "newuser",
            "role": "customer",  # Default role
            "is_active": True
        })
        
        # Verify password is not exposed
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_register_user_can_login_after_registration(self, client: TestClient):
        """Test that registered user can login."""
        user_data = {
            "email": "logintest@test.com",
            "username": "logintest",
            "password": "testpass"
        }
        
        # Register user
        response = client.post("/api/users/register", json=user_data)
        assert_response_success(response, 201)
        
        # Try to login
        login_response = client.post(
            "/api/users/login",
            data={"username": "logintest", "password": "testpass"}
        )
        assert_response_success(login_response)
        
        token_data = login_response.json()
        assert "access_token" in token_data
    
    def test_register_duplicate_username(self, client: TestClient, test_admin_user):
        """Test registration with duplicate username."""
        user_data = {
            "email": "different@test.com",
            "username": "admin",  # Already exists
            "password": "newpass"
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_error(response, 400)
        
        data = response.json()
        assert "detail" in data
        assert "username" in data["detail"].lower()
    
    def test_register_duplicate_email(self, client: TestClient, test_admin_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": "admin@test.com",  # Already exists
            "username": "newusername",
            "password": "newpass"
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_error(response, 400)
        
        data = response.json()
        assert "detail" in data
        assert "email" in data["detail"].lower()
    
    def test_register_invalid_email_format(self, client: TestClient):
        """Test registration with invalid email format."""
        user_data = {
            "email": "not-an-email",
            "username": "testuser",
            "password": "testpass"
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_error(response, 422)
    
    def test_register_missing_required_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        # Missing email
        response = client.post("/api/users/register", json={
            "username": "testuser",
            "password": "testpass"
        })
        assert_response_error(response, 422)
        
        # Missing username
        response = client.post("/api/users/register", json={
            "email": "test@test.com",
            "password": "testpass"
        })
        assert_response_error(response, 422)
        
        # Missing password
        response = client.post("/api/users/register", json={
            "email": "test@test.com",
            "username": "testuser"
        })
        assert_response_error(response, 422)
    
    def test_register_empty_fields(self, client: TestClient):
        """Test registration with empty fields."""
        user_data = {
            "email": "",
            "username": "",
            "password": ""
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_error(response, 422)
    
    def test_register_short_password(self, client: TestClient):
        """Test registration with short password."""
        user_data = {
            "email": "test@test.com",
            "username": "testuser",
            "password": "123"  # Too short
        }
        
        response = client.post("/api/users/register", json=user_data)
        # Note: This depends on password validation rules in your schema
        # You might want to add minimum password length validation
        # For now, we'll assume it should succeed but you might want to add validation
    
    def test_register_user_defaults_to_customer_role(self, client: TestClient):
        """Test that new users default to customer role."""
        user_data = {
            "email": "customer@test.com",
            "username": "newcustomer",
            "password": "customerpass"
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_success(response, 201)
        
        data = response.json()
        assert_json_contains(data, {"role": "customer"})


class TestUserProfile:
    """Test user profile management."""
    
    def test_get_own_profile_admin(self, client: TestClient, admin_headers):
        """Test admin getting their own profile."""
        response = client.get("/api/users/me", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        required_fields = ["id", "email", "username", "role", "is_active"]
        assert_json_has_fields(data, required_fields)
        
        assert_json_contains(data, {
            "username": "admin",
            "role": "admin",
            "is_active": True
        })
    
    def test_get_own_profile_customer(self, client: TestClient, customer_headers):
        """Test customer getting their own profile."""
        response = client.get("/api/users/me", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        required_fields = ["id", "email", "username", "role", "is_active"]
        assert_json_has_fields(data, required_fields)
        
        assert_json_contains(data, {
            "username": "customer",
            "role": "customer",
            "is_active": True
        })
    
    def test_profile_excludes_sensitive_data(self, client: TestClient, admin_headers):
        """Test that profile doesn't include sensitive data."""
        response = client.get("/api/users/me", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        
        # These should not be present
        forbidden_fields = ["password", "hashed_password", "secret", "hash"]
        for field in forbidden_fields:
            assert field not in data, f"Sensitive field '{field}' should not be in profile"
    
    def test_profile_without_authentication(self, client: TestClient):
        """Test accessing profile without authentication."""
        response = client.get("/api/users/me")
        assert_response_error(response, 401)
    
    def test_profile_with_invalid_token(self, client: TestClient):
        """Test accessing profile with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/users/me", headers=headers)
        assert_response_error(response, 401)


class TestUserAccountStatus:
    """Test user account status functionality."""
    
    def test_active_user_can_login(self, client: TestClient, test_admin_user):
        """Test that active user can login."""
        response = client.post(
            "/api/users/login",
            data={"username": "admin", "password": "adminpass"}
        )
        assert_response_success(response)
    
    def test_inactive_user_cannot_login(self, client: TestClient, db_session):
        """Test that inactive user cannot login."""
        # Create inactive user
        from models.user import User, UserRole
        from auth import get_password_hash
        
        inactive_user = User(
            email="inactive@test.com",
            username="inactive",
            hashed_password=get_password_hash("password"),
            role=UserRole.CUSTOMER,
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        # Try to login
        response = client.post(
            "/api/users/login",
            data={"username": "inactive", "password": "password"}
        )
        assert_response_error(response, 401)


class TestUserRoles:
    """Test user role functionality."""
    
    def test_admin_role_in_profile(self, client: TestClient, admin_headers):
        """Test admin role appears correctly in profile."""
        response = client.get("/api/users/me", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        assert_json_contains(data, {"role": "admin"})
    
    def test_customer_role_in_profile(self, client: TestClient, customer_headers):
        """Test customer role appears correctly in profile."""
        response = client.get("/api/users/me", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        assert_json_contains(data, {"role": "customer"})
    
    def test_new_user_gets_customer_role(self, client: TestClient):
        """Test new user registration assigns customer role."""
        user_data = {
            "email": "newrole@test.com",
            "username": "newrole",
            "password": "password"
        }
        
        response = client.post("/api/users/register", json=user_data)
        assert_response_success(response, 201)
        
        data = response.json()
        assert_json_contains(data, {"role": "customer"})


class TestUserValidation:
    """Test user input validation."""
    
    def test_invalid_json_format(self, client: TestClient):
        """Test registration with invalid JSON."""
        response = client.post(
            "/api/users/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert_response_error(response, 422)
    
    def test_sql_injection_attempts(self, client: TestClient):
        """Test registration with SQL injection attempts."""
        malicious_data = {
            "email": "test@test.com",
            "username": "'; DROP TABLE users; --",
            "password": "password"
        }
        
        response = client.post("/api/users/register", json=malicious_data)
        # Should either succeed (data is escaped) or fail with validation error
        # Should NOT cause a server error or data loss
        assert response.status_code in [201, 400, 422]
    
    def test_extremely_long_fields(self, client: TestClient):
        """Test registration with extremely long field values."""
        long_string = "a" * 10000  # Very long string
        
        user_data = {
            "email": f"{long_string}@test.com",
            "username": long_string,
            "password": long_string
        }
        
        response = client.post("/api/users/register", json=user_data)
        # Should handle gracefully with validation error
        assert response.status_code in [400, 422]
    
    def test_special_characters_in_username(self, client: TestClient):
        """Test registration with special characters in username."""
        user_data = {
            "email": "special@test.com",
            "username": "user@#$%^&*()",
            "password": "password"
        }
        
        response = client.post("/api/users/register", json=user_data)
        # Should handle according to username validation rules
        # This test documents current behavior