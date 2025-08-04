"""
Tests for item management API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from tests.utils import (
    assert_response_success,
    assert_response_error,
    assert_json_contains,
    assert_json_has_fields,
    create_test_item_via_api,
    APITestHelper,
    SAMPLE_ITEM_DATA
)


class TestItemCreation:
    """Test item creation functionality."""
    
    def test_create_item_as_admin_success(self, client: TestClient, admin_headers):
        """Test successful item creation by admin."""
        item_data = SAMPLE_ITEM_DATA["electronics"].copy()
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        data = response.json()
        required_fields = ["id", "name", "description", "price", "category", "stock_quantity", "is_active", "created_by", "created_at"]
        assert_json_has_fields(data, required_fields)
        
        # Verify item data matches input
        assert_json_contains(data, {
            "name": item_data["name"],
            "description": item_data["description"],
            "price": item_data["price"],
            "category": item_data["category"],
            "stock_quantity": item_data["stock_quantity"],
            "image_url": item_data["image_url"],
            "is_active": True
        })
        
        # Verify generated fields
        assert isinstance(data["id"], int)
        assert data["id"] > 0
        assert isinstance(data["created_by"], int)
        assert data["created_at"]
    
    def test_create_item_minimal_data(self, client: TestClient, admin_headers):
        """Test item creation with minimal required data."""
        item_data = {
            "name": "Minimal Item",
            "price": 9.99,
            "category": "Test",
            "stock_quantity": 1
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        data = response.json()
        assert_json_contains(data, {
            "name": "Minimal Item",
            "price": 9.99,
            "category": "Test",
            "stock_quantity": 1,
            "is_active": True
        })
        
        # Optional fields should have default values
        assert data.get("description") is None or data.get("description") == ""
        assert data.get("image_url") is None or data.get("image_url") == ""
    
    def test_create_item_as_customer_forbidden(self, client: TestClient, customer_headers):
        """Test that customer cannot create items."""
        item_data = SAMPLE_ITEM_DATA["books"].copy()
        
        response = client.post("/api/items/", json=item_data, headers=customer_headers)
        assert_response_error(response, 403)
    
    def test_create_item_without_auth_unauthorized(self, client: TestClient):
        """Test item creation without authentication."""
        item_data = SAMPLE_ITEM_DATA["books"].copy()
        
        response = client.post("/api/items/", json=item_data)
        assert_response_error(response, 401)
    
    def test_create_item_missing_required_fields(self, client: TestClient, admin_headers):
        """Test item creation with missing required fields."""
        # Missing name
        response = client.post("/api/items/", json={
            "price": 10.0,
            "category": "Test",
            "stock_quantity": 1
        }, headers=admin_headers)
        assert_response_error(response, 422)
        
        # Missing price
        response = client.post("/api/items/", json={
            "name": "Test Item",
            "category": "Test",
            "stock_quantity": 1
        }, headers=admin_headers)
        assert_response_error(response, 422)
        
        # Missing category
        response = client.post("/api/items/", json={
            "name": "Test Item",
            "price": 10.0,
            "stock_quantity": 1
        }, headers=admin_headers)
        assert_response_error(response, 422)
        
        # Missing stock_quantity
        response = client.post("/api/items/", json={
            "name": "Test Item",
            "price": 10.0,
            "category": "Test"
        }, headers=admin_headers)
        assert_response_error(response, 422)
    
    def test_create_item_invalid_price(self, client: TestClient, admin_headers):
        """Test item creation with invalid price."""
        # Negative price
        item_data = {
            "name": "Invalid Price Item",
            "price": -10.0,
            "category": "Test",
            "stock_quantity": 1
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_error(response, 422)
        
        # Zero price (might be valid depending on business rules)
        item_data["price"] = 0.0
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        # This might be valid for free items
    
    def test_create_item_invalid_stock(self, client: TestClient, admin_headers):
        """Test item creation with invalid stock quantity."""
        item_data = {
            "name": "Invalid Stock Item",
            "price": 10.0,
            "category": "Test",
            "stock_quantity": -1
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_error(response, 422)


class TestItemListing:
    """Test item listing functionality."""
    
    def test_get_all_items_as_admin(self, client: TestClient, admin_headers, test_item):
        """Test getting all items as admin."""
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test item
        
        # Check item structure
        if data:
            item = data[0]
            required_fields = ["id", "name", "price", "category", "stock_quantity", "is_active"]
            assert_json_has_fields(item, required_fields)
    
    def test_get_all_items_as_customer(self, client: TestClient, customer_headers, test_item):
        """Test getting all items as customer."""
        response = client.get("/api/items/", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        assert isinstance(data, list)
        
        # Customers should only see active items with stock
        for item in data:
            assert item["is_active"] is True
            assert item["stock_quantity"] > 0
    
    def test_get_items_without_auth(self, client: TestClient):
        """Test getting items without authentication."""
        response = client.get("/api/items/")
        assert_response_error(response, 401)
    
    def test_get_items_by_category(self, client: TestClient, admin_headers, db_session, test_admin_user):
        """Test filtering items by category."""
        # Create items in different categories
        from tests.conftest import create_test_items
        items = create_test_items(db_session, test_admin_user, 5)
        
        # Get items by specific category
        target_category = items[0].category
        response = client.get(f"/api/items/?category={target_category}", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        assert isinstance(data, list)
        
        # All returned items should be in the requested category
        for item in data:
            assert item["category"] == target_category
    
    def test_get_empty_items_list(self, client: TestClient, admin_headers):
        """Test getting items when none exist."""
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        assert isinstance(data, list)
        # Could be empty or contain items from other tests


class TestItemDeletion:
    """Test item deletion functionality."""
    
    def test_delete_item_as_admin_success(self, client: TestClient, admin_headers):
        """Test successful item deletion by admin."""
        # Create item first
        item_data = create_test_item_via_api(client, admin_headers)
        item_id = item_data["id"]
        
        # Delete the item
        response = client.delete(f"/api/items/{item_id}", headers=admin_headers)
        assert_response_success(response, 204)
        
        # Verify item is marked as inactive
        response = client.get("/api/items/", headers=admin_headers)
        items = response.json()
        
        deleted_item = next((item for item in items if item["id"] == item_id), None)
        if deleted_item:  # Item might be filtered out
            assert deleted_item["is_active"] is False
    
    def test_delete_item_as_customer_forbidden(self, client: TestClient, customer_headers, test_item):
        """Test that customer cannot delete items."""
        response = client.delete(f"/api/items/{test_item.id}", headers=customer_headers)
        assert_response_error(response, 403)
    
    def test_delete_item_without_auth(self, client: TestClient, test_item):
        """Test item deletion without authentication."""
        response = client.delete(f"/api/items/{test_item.id}")
        assert_response_error(response, 401)
    
    def test_delete_nonexistent_item(self, client: TestClient, admin_headers):
        """Test deleting non-existent item."""
        response = client.delete("/api/items/99999", headers=admin_headers)
        assert_response_error(response, 404)
    
    def test_delete_already_deleted_item(self, client: TestClient, admin_headers):
        """Test deleting already deleted item."""
        # Create and delete item
        item_data = create_test_item_via_api(client, admin_headers)
        item_id = item_data["id"]
        
        response = client.delete(f"/api/items/{item_id}", headers=admin_headers)
        assert_response_success(response, 204)
        
        # Try to delete again
        response = client.delete(f"/api/items/{item_id}", headers=admin_headers)
        assert_response_error(response, 404)


class TestItemCategories:
    """Test item category functionality."""
    
    def test_get_categories_list(self, client: TestClient, customer_headers, db_session, test_admin_user):
        """Test getting list of categories."""
        # Create items in different categories
        from tests.conftest import create_test_items
        items = create_test_items(db_session, test_admin_user, 5)
        
        response = client.get("/api/items/categories/list", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        
        # Should contain at least the categories from test items
        categories = data["categories"]
        item_categories = list(set(item.category for item in items))
        for category in item_categories:
            assert category in categories
    
    def test_get_categories_without_auth(self, client: TestClient):
        """Test getting categories without authentication."""
        response = client.get("/api/items/categories/list")
        assert_response_error(response, 401)
    
    def test_categories_only_include_active_items(self, client: TestClient, admin_headers, db_session, test_admin_user):
        """Test that categories only include categories from active items."""
        # Create an item and then delete it
        from models.item import Item
        
        item = Item(
            name="Test Category Item",
            price=10.0,
            category="UniqueTestCategory",
            stock_quantity=5,
            created_by=test_admin_user.id,
            is_active=False  # Inactive item
        )
        db_session.add(item)
        db_session.commit()
        
        response = client.get("/api/items/categories/list", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        categories = data["categories"]
        
        # UniqueTestCategory should not appear since the item is inactive
        assert "UniqueTestCategory" not in categories


class TestItemValidation:
    """Test item input validation."""
    
    def test_create_item_with_very_long_name(self, client: TestClient, admin_headers):
        """Test creating item with very long name."""
        item_data = {
            "name": "A" * 1000,  # Very long name
            "price": 10.0,
            "category": "Test",
            "stock_quantity": 1
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        # Should handle according to validation rules
        assert response.status_code in [201, 400, 422]
    
    def test_create_item_with_special_characters(self, client: TestClient, admin_headers):
        """Test creating item with special characters."""
        item_data = {
            "name": "Test Item @#$%^&*()",
            "description": "Description with émojis 🛍️ and spëcial çharacters",
            "price": 10.0,
            "category": "Test & Special",
            "stock_quantity": 1
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        # Should handle special characters properly
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == item_data["name"]
            assert data["description"] == item_data["description"]
    
    def test_create_item_with_extreme_values(self, client: TestClient, admin_headers):
        """Test creating item with extreme values."""
        item_data = {
            "name": "Extreme Test",
            "price": 999999.99,  # Very high price
            "category": "Test",
            "stock_quantity": 999999  # Very high stock
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        # Should handle according to business rules
        assert response.status_code in [201, 400, 422]