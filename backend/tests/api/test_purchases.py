"""
Tests for purchase/order management API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from tests.utils import (
    assert_response_success,
    assert_response_error,
    assert_json_contains,
    assert_json_has_fields,
    create_test_item_via_api,
    purchase_item_via_api,
    APITestHelper
)


class TestPurchaseCreation:
    """Test purchase creation functionality."""
    
    def test_purchase_item_as_customer_success(self, client: TestClient, customer_headers, test_item):
        """Test successful item purchase by customer."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 2
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_success(response, 201)
        
        data = response.json()
        required_fields = ["id", "item_id", "quantity", "total_price", "purchase_date", "item_name"]
        assert_json_has_fields(data, required_fields)
        
        # Verify purchase data
        expected_total = test_item.price * 2
        assert_json_contains(data, {
            "item_id": test_item.id,
            "quantity": 2,
            "total_price": expected_total,
            "item_name": test_item.name
        })
        
        # Verify generated fields
        assert isinstance(data["id"], int)
        assert data["id"] > 0
        assert data["purchase_date"]
    
    def test_purchase_single_item(self, client: TestClient, customer_headers, test_item):
        """Test purchasing single item (default quantity)."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_success(response, 201)
        
        data = response.json()
        assert_json_contains(data, {
            "item_id": test_item.id,
            "quantity": 1,
            "total_price": test_item.price
        })
    
    def test_purchase_multiple_items(self, client: TestClient, customer_headers, test_item):
        """Test purchasing multiple quantities of an item."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 5
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_success(response, 201)
        
        data = response.json()
        expected_total = test_item.price * 5
        assert_json_contains(data, {
            "quantity": 5,
            "total_price": expected_total
        })
    
    def test_purchase_item_as_admin_success(self, client: TestClient, admin_headers, test_item):
        """Test that admin can also purchase items."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=admin_headers)
        assert_response_success(response, 201)
    
    def test_purchase_without_auth_unauthorized(self, client: TestClient, test_item):
        """Test purchase without authentication."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data)
        assert_response_error(response, 401)
    
    def test_purchase_nonexistent_item(self, client: TestClient, customer_headers):
        """Test purchasing non-existent item."""
        purchase_data = {
            "item_id": 99999,
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 404)
    
    def test_purchase_inactive_item(self, client: TestClient, customer_headers, db_session, test_admin_user):
        """Test purchasing inactive item."""
        from models.item import Item
        
        # Create inactive item
        inactive_item = Item(
            name="Inactive Item",
            price=10.0,
            category="Test",
            stock_quantity=5,
            created_by=test_admin_user.id,
            is_active=False
        )
        db_session.add(inactive_item)
        db_session.commit()
        db_session.refresh(inactive_item)
        
        purchase_data = {
            "item_id": inactive_item.id,
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 400)
    
    def test_purchase_insufficient_stock(self, client: TestClient, customer_headers, db_session, test_admin_user):
        """Test purchasing more than available stock."""
        from models.item import Item
        
        # Create item with limited stock
        limited_item = Item(
            name="Limited Stock Item",
            price=10.0,
            category="Test",
            stock_quantity=2,
            created_by=test_admin_user.id
        )
        db_session.add(limited_item)
        db_session.commit()
        db_session.refresh(limited_item)
        
        # Try to purchase more than available
        purchase_data = {
            "item_id": limited_item.id,
            "quantity": 5  # More than the 2 available
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 400)
        
        data = response.json()
        assert "stock" in data["detail"].lower() or "insufficient" in data["detail"].lower()
    
    def test_purchase_zero_quantity(self, client: TestClient, customer_headers, test_item):
        """Test purchasing zero quantity."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 0
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 422)
    
    def test_purchase_negative_quantity(self, client: TestClient, customer_headers, test_item):
        """Test purchasing negative quantity."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": -1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 422)
    
    def test_purchase_missing_fields(self, client: TestClient, customer_headers):
        """Test purchase with missing required fields."""
        # Missing item_id
        response = client.post("/api/items/purchase", json={"quantity": 1}, headers=customer_headers)
        assert_response_error(response, 422)
        
        # Missing quantity
        response = client.post("/api/items/purchase", json={"item_id": 1}, headers=customer_headers)
        assert_response_error(response, 422)
        
        # Empty request
        response = client.post("/api/items/purchase", json={}, headers=customer_headers)
        assert_response_error(response, 422)


class TestStockManagement:
    """Test stock management during purchases."""
    
    def test_stock_decreases_after_purchase(self, client: TestClient, customer_headers, admin_headers, test_item):
        """Test that stock decreases after purchase."""
        original_stock = test_item.stock_quantity
        
        # Purchase some items
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 3
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_success(response, 201)
        
        # Check that stock has decreased
        response = client.get("/api/items/", headers=admin_headers)
        items = response.json()
        
        purchased_item = next((item for item in items if item["id"] == test_item.id), None)
        assert purchased_item is not None
        assert purchased_item["stock_quantity"] == original_stock - 3
    
    def test_multiple_purchases_reduce_stock(self, client: TestClient, customer_headers, admin_headers, test_item):
        """Test multiple purchases reduce stock correctly."""
        original_stock = test_item.stock_quantity
        
        # First purchase
        response = client.post("/api/items/purchase", json={
            "item_id": test_item.id,
            "quantity": 2
        }, headers=customer_headers)
        assert_response_success(response, 201)
        
        # Second purchase
        response = client.post("/api/items/purchase", json={
            "item_id": test_item.id,
            "quantity": 1
        }, headers=customer_headers)
        assert_response_success(response, 201)
        
        # Check final stock
        response = client.get("/api/items/", headers=admin_headers)
        items = response.json()
        
        purchased_item = next((item for item in items if item["id"] == test_item.id), None)
        assert purchased_item["stock_quantity"] == original_stock - 3
    
    def test_cannot_purchase_when_out_of_stock(self, client: TestClient, customer_headers, db_session, test_admin_user):
        """Test that purchase fails when item is out of stock."""
        from models.item import Item
        
        # Create item with zero stock
        out_of_stock_item = Item(
            name="Out of Stock Item",
            price=10.0,
            category="Test",
            stock_quantity=0,
            created_by=test_admin_user.id
        )
        db_session.add(out_of_stock_item)
        db_session.commit()
        db_session.refresh(out_of_stock_item)
        
        purchase_data = {
            "item_id": out_of_stock_item.id,
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 400)


class TestPurchaseHistory:
    """Test purchase history functionality."""
    
    def test_get_customer_own_purchases(self, client: TestClient, customer_headers, test_purchase):
        """Test customer getting their own purchase history."""
        response = client.get("/api/items/purchases/my", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test purchase
        
        # Check purchase structure
        if data:
            purchase = data[0]
            required_fields = ["id", "item_id", "quantity", "total_price", "purchase_date", "item_name"]
            assert_json_has_fields(purchase, required_fields)
    
    def test_get_admin_all_purchases(self, client: TestClient, admin_headers, test_purchase):
        """Test admin getting all purchases."""
        response = client.get("/api/items/purchases/all", headers=admin_headers)
        assert_response_success(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test purchase
        
        # Check purchase structure includes customer info
        if data:
            purchase = data[0]
            required_fields = ["id", "item_id", "quantity", "total_price", "purchase_date", "item_name", "customer_username"]
            assert_json_has_fields(purchase, required_fields)
    
    def test_customer_cannot_access_all_purchases(self, client: TestClient, customer_headers):
        """Test that customer cannot access all purchases endpoint."""
        response = client.get("/api/items/purchases/all", headers=customer_headers)
        assert_response_error(response, 403)
    
    def test_purchases_without_auth(self, client: TestClient):
        """Test accessing purchases without authentication."""
        response = client.get("/api/items/purchases/my")
        assert_response_error(response, 401)
        
        response = client.get("/api/items/purchases/all")
        assert_response_error(response, 401)
    
    def test_empty_purchase_history(self, client: TestClient):
        """Test getting purchase history when no purchases exist."""
        # Create a new customer with no purchases
        from tests.conftest import test_db
        helper = APITestHelper(client)
        
        # Register new customer
        new_customer_data = {
            "email": "newcustomer@test.com",
            "username": "newcustomer",
            "password": "password"
        }
        
        response = client.post("/api/users/register", json=new_customer_data)
        if response.status_code == 201:
            # Login as new customer
            token = helper.login_user(client, "newcustomer", "password")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Check empty purchase history
            response = client.get("/api/items/purchases/my", headers=headers)
            assert_response_success(response)
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
    
    def test_purchase_history_ordering(self, client: TestClient, customer_headers, test_item):
        """Test that purchase history is ordered by date (newest first)."""
        # Make multiple purchases
        for i in range(3):
            purchase_data = {
                "item_id": test_item.id,
                "quantity": 1
            }
            response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
            assert_response_success(response, 201)
        
        # Get purchase history
        response = client.get("/api/items/purchases/my", headers=customer_headers)
        assert_response_success(response)
        
        data = response.json()
        assert len(data) >= 3
        
        # Check that purchases are ordered by date (newest first)
        for i in range(len(data) - 1):
            current_date = data[i]["purchase_date"]
            next_date = data[i + 1]["purchase_date"]
            assert current_date >= next_date


class TestPurchaseValidation:
    """Test purchase input validation and edge cases."""
    
    def test_purchase_with_invalid_item_id_format(self, client: TestClient, customer_headers):
        """Test purchase with invalid item ID format."""
        purchase_data = {
            "item_id": "not-a-number",
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 422)
    
    def test_purchase_with_invalid_quantity_format(self, client: TestClient, customer_headers, test_item):
        """Test purchase with invalid quantity format."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": "not-a-number"
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 422)
    
    def test_purchase_with_extremely_large_quantity(self, client: TestClient, customer_headers, test_item):
        """Test purchase with extremely large quantity."""
        purchase_data = {
            "item_id": test_item.id,
            "quantity": 999999999
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 400)  # Should fail due to insufficient stock
    
    def test_concurrent_purchases_same_item(self, client: TestClient, db_session, test_admin_user):
        """Test handling concurrent purchases of the same item."""
        from models.item import Item
        from tests.utils import login_user, get_auth_headers
        
        # Create item with limited stock
        limited_item = Item(
            name="Concurrent Test Item",
            price=10.0,
            category="Test",
            stock_quantity=3,
            created_by=test_admin_user.id
        )
        db_session.add(limited_item)
        db_session.commit()
        db_session.refresh(limited_item)
        
        # Create two customers
        customers = []
        for i in range(2):
            customer_data = {
                "email": f"concurrent{i}@test.com",
                "username": f"concurrent{i}",
                "password": "password"
            }
            response = client.post("/api/users/register", json=customer_data)
            if response.status_code == 201:
                token = login_user(client, f"concurrent{i}", "password")
                headers = get_auth_headers(token)
                customers.append(headers)
        
        if len(customers) >= 2:
            # Both try to purchase 2 items (total 4, but only 3 available)
            responses = []
            for headers in customers:
                purchase_data = {
                    "item_id": limited_item.id,
                    "quantity": 2
                }
                response = client.post("/api/items/purchase", json=purchase_data, headers=headers)
                responses.append(response)
            
            # One should succeed, one should fail
            success_count = sum(1 for r in responses if r.status_code == 201)
            failure_count = sum(1 for r in responses if r.status_code == 400)
            
            assert success_count >= 1  # At least one should succeed
            assert failure_count >= 1  # At least one should fail due to insufficient stock