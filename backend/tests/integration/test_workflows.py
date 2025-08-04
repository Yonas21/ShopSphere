"""
Integration tests for complete user workflows.
"""
import pytest
from fastapi.testclient import TestClient

from tests.utils import (
    assert_response_success,
    assert_response_error,
    assert_json_contains,
    assert_json_has_fields,
    login_user,
    get_auth_headers,
    APITestHelper,
    SAMPLE_ITEM_DATA
)


class TestCompleteCustomerWorkflow:
    """Test complete customer user journey."""
    
    def test_customer_registration_to_purchase_workflow(self, client: TestClient, test_admin_user):
        """Test complete workflow: registration -> login -> browse -> purchase."""
        helper = APITestHelper(client)
        
        # Step 1: Register new customer
        customer_data = {
            "email": "workflow@test.com",
            "username": "workflow",
            "password": "workflowpass"
        }
        
        response = client.post("/api/users/register", json=customer_data)
        assert_response_success(response, 201)
        
        user_data = response.json()
        assert_json_contains(user_data, {
            "username": "workflow",
            "role": "customer",
            "is_active": True
        })
        
        # Step 2: Login
        token = login_user(client, "workflow", "workflowpass")
        headers = get_auth_headers(token)
        
        # Step 3: Get user profile
        response = client.get("/api/users/me", headers=headers)
        assert_response_success(response)
        profile = response.json()
        assert_json_contains(profile, {"username": "workflow", "role": "customer"})
        
        # Step 4: Create item as admin (to have something to purchase)
        admin_token = login_user(client, "admin", "adminpass")
        admin_headers = get_auth_headers(admin_token)
        
        item_data = SAMPLE_ITEM_DATA["electronics"].copy()
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        created_item = response.json()
        
        # Step 5: Browse items as customer
        response = client.get("/api/items/", headers=headers)
        assert_response_success(response)
        items = response.json()
        
        # Find our created item
        target_item = next((item for item in items if item["id"] == created_item["id"]), None)
        assert target_item is not None
        assert target_item["is_active"] is True
        assert target_item["stock_quantity"] > 0
        
        # Step 6: Purchase item
        purchase_data = {
            "item_id": created_item["id"],
            "quantity": 2
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=headers)
        assert_response_success(response, 201)
        
        purchase = response.json()
        assert_json_contains(purchase, {
            "item_id": created_item["id"],
            "quantity": 2,
            "total_price": created_item["price"] * 2
        })
        
        # Step 7: Check purchase history
        response = client.get("/api/items/purchases/my", headers=headers)
        assert_response_success(response)
        
        purchases = response.json()
        assert len(purchases) >= 1
        
        # Find our purchase
        our_purchase = next((p for p in purchases if p["id"] == purchase["id"]), None)
        assert our_purchase is not None
        assert our_purchase["item_name"] == created_item["name"]
        
        # Step 8: Verify stock was reduced
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        updated_items = response.json()
        updated_item = next((item for item in updated_items if item["id"] == created_item["id"]), None)
        assert updated_item["stock_quantity"] == created_item["stock_quantity"] - 2
    
    def test_customer_category_filtering_workflow(self, client: TestClient, admin_headers):
        """Test customer browsing items by category."""
        helper = APITestHelper(client)
        
        # Create items in different categories
        categories = ["Electronics", "Books", "Clothing"]
        created_items = []
        
        for i, category in enumerate(categories):
            item_data = {
                "name": f"Test {category} Item",
                "description": f"Test item in {category} category",
                "price": 10.0 + i,
                "category": category,
                "stock_quantity": 5
            }
            
            response = client.post("/api/items/", json=item_data, headers=admin_headers)
            assert_response_success(response, 201)
            created_items.append(response.json())
        
        # Register and login customer
        customer_token = helper.login_customer()
        customer_headers = get_auth_headers(customer_token)
        
        # Get all categories
        response = client.get("/api/items/categories/list", headers=customer_headers)
        assert_response_success(response)
        
        category_data = response.json()
        available_categories = category_data["categories"]
        
        for category in categories:
            assert category in available_categories
        
        # Browse items by each category
        for category in categories:
            response = client.get(f"/api/items/?category={category}", headers=customer_headers)
            assert_response_success(response)
            
            items = response.json()
            
            # All items should be in the requested category
            for item in items:
                assert item["category"] == category
            
            # Should contain our created item for this category
            category_item = next((item for item in items if item["name"] == f"Test {category} Item"), None)
            assert category_item is not None


class TestCompleteAdminWorkflow:
    """Test complete admin user journey."""
    
    def test_admin_item_management_workflow(self, client: TestClient, admin_headers):
        """Test complete admin workflow: create -> list -> delete items."""
        # Step 1: Create multiple items
        created_items = []
        
        for i in range(3):
            item_data = {
                "name": f"Admin Item {i}",
                "description": f"Item {i} created by admin",
                "price": 10.0 + i,
                "category": "AdminTest",
                "stock_quantity": 5 + i
            }
            
            response = client.post("/api/items/", json=item_data, headers=admin_headers)
            assert_response_success(response, 201)
            
            created_item = response.json()
            created_items.append(created_item)
            
            # Verify item data
            assert_json_contains(created_item, {
                "name": item_data["name"],
                "price": item_data["price"],
                "category": item_data["category"],
                "is_active": True
            })
        
        # Step 2: List all items
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        all_items = response.json()
        
        # Verify all created items are in the list
        for created_item in created_items:
            found_item = next((item for item in all_items if item["id"] == created_item["id"]), None)
            assert found_item is not None
            assert found_item["is_active"] is True
        
        # Step 3: Delete one item
        item_to_delete = created_items[0]
        response = client.delete(f"/api/items/{item_to_delete['id']}", headers=admin_headers)
        assert_response_success(response, 204)
        
        # Step 4: Verify item is marked as inactive
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        updated_items = response.json()
        deleted_item = next((item for item in updated_items if item["id"] == item_to_delete["id"]), None)
        
        if deleted_item:  # Item might be filtered out
            assert deleted_item["is_active"] is False
    
    def test_admin_order_monitoring_workflow(self, client: TestClient, admin_headers, customer_headers):
        """Test admin monitoring customer orders."""
        # Step 1: Create item as admin
        item_data = SAMPLE_ITEM_DATA["books"].copy()
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        created_item = response.json()
        
        # Step 2: Customer makes purchases
        purchase_data = {
            "item_id": created_item["id"],
            "quantity": 3
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_success(response, 201)
        
        customer_purchase = response.json()
        
        # Step 3: Admin views all purchases
        response = client.get("/api/items/purchases/all", headers=admin_headers)
        assert_response_success(response)
        
        all_purchases = response.json()
        
        # Find customer's purchase
        found_purchase = next((p for p in all_purchases if p["id"] == customer_purchase["id"]), None)
        assert found_purchase is not None
        
        # Verify purchase details include customer info
        assert_json_has_fields(found_purchase, ["customer_username", "item_name"])
        assert found_purchase["customer_username"] == "customer"
        assert found_purchase["item_name"] == created_item["name"]
        
        # Step 4: Verify item stock was reduced
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        updated_items = response.json()
        updated_item = next((item for item in updated_items if item["id"] == created_item["id"]), None)
        
        assert updated_item["stock_quantity"] == created_item["stock_quantity"] - 3


class TestMultiUserScenarios:
    """Test scenarios involving multiple users."""
    
    def test_multiple_customers_purchasing_same_item(self, client: TestClient, admin_headers):
        """Test multiple customers purchasing the same item."""
        # Create item with limited stock
        item_data = {
            "name": "Popular Item",
            "description": "High demand item",
            "price": 25.99,
            "category": "Popular",
            "stock_quantity": 5
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        created_item = response.json()
        
        # Create multiple customers
        customers = []
        for i in range(3):
            customer_data = {
                "email": f"customer{i}@test.com",
                "username": f"customer{i}",
                "password": "password"
            }
            
            response = client.post("/api/users/register", json=customer_data)
            if response.status_code == 201:
                token = login_user(client, f"customer{i}", "password")
                headers = get_auth_headers(token)
                customers.append(headers)
        
        # Each customer purchases some items
        total_purchased = 0
        purchases = []
        
        for i, customer_headers in enumerate(customers):
            quantity = i + 1  # Customer 0 buys 1, customer 1 buys 2, customer 2 buys 3
            
            if total_purchased + quantity <= created_item["stock_quantity"]:
                purchase_data = {
                    "item_id": created_item["id"],
                    "quantity": quantity
                }
                
                response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
                
                if response.status_code == 201:
                    purchases.append(response.json())
                    total_purchased += quantity
        
        # Verify final stock
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        final_items = response.json()
        final_item = next((item for item in final_items if item["id"] == created_item["id"]), None)
        
        assert final_item["stock_quantity"] == created_item["stock_quantity"] - total_purchased
        
        # Verify all purchases were recorded
        response = client.get("/api/items/purchases/all", headers=admin_headers)
        assert_response_success(response)
        
        all_purchases = response.json()
        item_purchases = [p for p in all_purchases if p["item_id"] == created_item["id"]]
        
        assert len(item_purchases) == len(purchases)
    
    def test_customer_purchase_history_isolation(self, client: TestClient, admin_headers):
        """Test that customers only see their own purchase history."""
        # Create item
        item_data = SAMPLE_ITEM_DATA["electronics"].copy()
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        created_item = response.json()
        
        # Create two customers
        customers = []
        for i in range(2):
            customer_data = {
                "email": f"isolated{i}@test.com",
                "username": f"isolated{i}",
                "password": "password"
            }
            
            response = client.post("/api/users/register", json=customer_data)
            if response.status_code == 201:
                token = login_user(client, f"isolated{i}", "password")
                headers = get_auth_headers(token)
                customers.append((headers, f"isolated{i}"))
        
        if len(customers) >= 2:
            # Each customer makes a purchase
            customer_purchases = []
            
            for headers, username in customers:
                purchase_data = {
                    "item_id": created_item["id"],
                    "quantity": 1
                }
                
                response = client.post("/api/items/purchase", json=purchase_data, headers=headers)
                if response.status_code == 201:
                    customer_purchases.append((response.json(), username, headers))
            
            # Verify each customer only sees their own purchases
            for purchase, username, headers in customer_purchases:
                response = client.get("/api/items/purchases/my", headers=headers)
                assert_response_success(response)
                
                my_purchases = response.json()
                
                # Should contain their purchase
                found = any(p["id"] == purchase["id"] for p in my_purchases)
                assert found, f"Customer {username} should see their own purchase"
                
                # Should not contain other customers' purchases
                other_purchases = [p for p, u, h in customer_purchases if u != username]
                for other_purchase, _, _ in other_purchases:
                    found_other = any(p["id"] == other_purchase["id"] for p in my_purchases)
                    assert not found_other, f"Customer {username} should not see other customers' purchases"


class TestErrorHandlingWorkflows:
    """Test error handling in complete workflows."""
    
    def test_purchase_workflow_with_insufficient_stock(self, client: TestClient, admin_headers, customer_headers):
        """Test purchase workflow when stock runs out."""
        # Create item with very limited stock
        item_data = {
            "name": "Limited Stock Item",
            "description": "Only a few available",
            "price": 99.99,
            "category": "Limited",
            "stock_quantity": 2
        }
        
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        created_item = response.json()
        
        # First purchase succeeds
        purchase_data = {
            "item_id": created_item["id"],
            "quantity": 2
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_success(response, 201)
        
        # Second purchase should fail
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 400)
        
        # Verify error message mentions stock
        error_data = response.json()
        assert "stock" in error_data["detail"].lower() or "insufficient" in error_data["detail"].lower()
        
        # Verify item stock is correctly updated
        response = client.get("/api/items/", headers=admin_headers)
        assert_response_success(response)
        
        items = response.json()
        updated_item = next((item for item in items if item["id"] == created_item["id"]), None)
        assert updated_item["stock_quantity"] == 0
    
    def test_workflow_with_inactive_item(self, client: TestClient, admin_headers, customer_headers):
        """Test workflow when item becomes inactive during process."""
        # Create item
        item_data = SAMPLE_ITEM_DATA["books"].copy()
        response = client.post("/api/items/", json=item_data, headers=admin_headers)
        assert_response_success(response, 201)
        
        created_item = response.json()
        
        # Customer can see the item initially
        response = client.get("/api/items/", headers=customer_headers)
        assert_response_success(response)
        
        items = response.json()
        visible_item = next((item for item in items if item["id"] == created_item["id"]), None)
        assert visible_item is not None
        
        # Admin deletes the item
        response = client.delete(f"/api/items/{created_item['id']}", headers=admin_headers)
        assert_response_success(response, 204)
        
        # Customer tries to purchase deleted item
        purchase_data = {
            "item_id": created_item["id"],
            "quantity": 1
        }
        
        response = client.post("/api/items/purchase", json=purchase_data, headers=customer_headers)
        assert_response_error(response, 400)  # Should fail because item is inactive
        
        # Customer should no longer see the item in listings
        response = client.get("/api/items/", headers=customer_headers)
        assert_response_success(response)
        
        updated_items = response.json()
        hidden_item = next((item for item in updated_items if item["id"] == created_item["id"]), None)
        assert hidden_item is None  # Should be filtered out for customers