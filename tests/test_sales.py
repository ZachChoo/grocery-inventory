import pytest
import random
from fastapi.testclient import TestClient
from datetime import date, timedelta

from app.main import app

client = TestClient(app)

class TestHelper:
    @staticmethod
    def create_test_user(username: str, role: str = "employee"):
        """Create a test user and return their data"""
        user_data = {
            "username": username,
            "password": "testpassword123",
            "role": role
        }
        response = client.post("/users/register", json=user_data)
        return user_data, response
    
    @staticmethod
    def get_auth_token(username: str, password: str = "testpassword123"):
        """Login and get JWT token"""
        login_data = {"username": username, "password": password}
        response = client.post("/users/login", data=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @staticmethod
    def auth_headers(token: str):
        """Create authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def create_test_product(auth_headers: dict):
        """Create a test product and return product data"""
        product_data = {
            "upc": random.randint(0, 999_999_999),  # Unique UPC
            "name": "Test Product for Sales",
            "price": 19.99,
            "quantity": 100,
            "report_code": 123,
            "reorder_threshold": 10
        }
        response = client.post("/products/", json=product_data, headers=auth_headers)
        if response.status_code == 200:
            # Get the created product to return its ID
            products_response = client.get("/products/")
            products = products_response.json()["products"]
            created_product = next(p for p in products if p["upc"] == product_data["upc"])
            return created_product
        return None

# Test fixtures
@pytest.fixture
def employee_token():
    """Create employee user and return auth token"""
    TestHelper.create_test_user("employee", "employee")
    return TestHelper.get_auth_token("employee")

@pytest.fixture
def manager_token():
    """Create manager user and return auth token"""
    TestHelper.create_test_user("manager", "manager")
    return TestHelper.get_auth_token("manager")

@pytest.fixture
def sample_sale():
    """Sample sale data for testing"""
    return {
        "product_id": 1,  # Will be updated in tests with actual product ID
        "sale_price": 15.99,
        "sale_start": str(date.today()),
        "sale_end": str(date.today() + timedelta(days=7))
    }

class TestGetSales:
    
    def test_get_sales_default_pagination(self):
        """Test getting sales with default pagination"""
        response = client.get("/sales/")
        
        assert response.status_code == 200
        data = response.json()
        assert "sales" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["sales"], list)
        assert data["page"] == 1
    
    def test_get_sales_custom_pagination(self):
        """Test getting sales with custom pagination"""
        response = client.get("/sales/?page=2&size=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 5

    def test_get_sales_max_page_size(self):
        """Test getting sales with too big of a page size"""
        response = client.get("/sales/?page=1&size=999999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] < 999999

class TestCreateSale:
    
    def test_create_sale_requires_auth(self, sample_sale):
        """Test that creating sale requires authentication"""
        response = client.post("/sales/", json=sample_sale)
        
        assert response.status_code == 401  # Unauthorized
    
    def test_create_sale_with_valid_product(self, employee_token, sample_sale):
        """Test creating sale for existing product"""
        headers = TestHelper.auth_headers(employee_token)
        
        # First create a product
        product = TestHelper.create_test_product(headers)
        assert product is not None
        
        # Update sale data with real product ID
        sample_sale["product_id"] = product["id"]
        
        # Create the sale
        response = client.post("/sales/", json=sample_sale, headers=headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Sale created!"
    
    def test_create_sale_with_invalid_product(self, employee_token, sample_sale):
        """Test creating sale for non-existent product fails"""
        headers = TestHelper.auth_headers(employee_token)
        
        # Use non-existent product ID
        sample_sale["product_id"] = 99999
        
        response = client.post("/sales/", json=sample_sale, headers=headers)
        
        # Should fail due to foreign key constraint
        assert response.status_code == 400
    
    def test_create_sale_invalid_dates(self, employee_token):
        """Test creating sale with invalid date range"""
        headers = TestHelper.auth_headers(employee_token)
        
        # Create product first
        product = TestHelper.create_test_product(headers)
        
        # Sale with end date before start date
        invalid_sale = {
            "product_id": product["id"],
            "sale_price": 15.99,
            "sale_start": str(date.today() + timedelta(days=7)),
            "sale_end": str(date.today())  # End before start!
        }
        
        response = client.post("/sales/", json=invalid_sale, headers=headers)
        assert response.status_code == 422


class TestDeleteSale:
    
    def test_delete_sale_requires_manager(self, employee_token, manager_token):
        """Test that only managers can delete sales"""
        employee_headers = TestHelper.auth_headers(employee_token)
        manager_headers = TestHelper.auth_headers(manager_token)
        
        # Manager creates product and sale
        product = TestHelper.create_test_product(manager_headers)
        sale_data = {
            "product_id": product["id"],
            "sale_price": 15.99,
            "sale_start": str(date.today()),
            "sale_end": str(date.today() + timedelta(days=7))
        }
        sale_response = client.post("/sales/", json=sale_data, headers=manager_headers)
        assert sale_response.status_code == 200
        
        # Get the created sale ID
        sales_response = client.get("/sales/")
        sales = sales_response.json()["sales"]
        test_sale = next((s for s in sales if s["product_id"] == product["id"]), None)
        
        if test_sale:
            sale_id = test_sale["id"]
            
            # Employee tries to delete (should fail)
            employee_delete = client.delete(f"/sales/{sale_id}", headers=employee_headers)
            assert employee_delete.status_code == 403
            
            # Manager deletes (should work)
            manager_delete = client.delete(f"/sales/{sale_id}", headers=manager_headers)
            assert manager_delete.status_code == 200
    
    def test_delete_nonexistent_sale(self, manager_token):
        """Test deleting sale that doesn't exist"""
        headers = TestHelper.auth_headers(manager_token)
        
        response = client.delete("/sales/99999", headers=headers)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Sale not found!"
    
    def test_delete_sale_without_auth(self):
        """Test deleting sale without authentication"""
        response = client.delete("/sales/1")
        assert response.status_code == 401


class TestCascadeDelete:
    
    def test_product_delete_cascades_to_sales(self, manager_token):
        """Test that deleting a product also deletes its associated sales"""
        headers = TestHelper.auth_headers(manager_token)
        
        # Create a product
        product = TestHelper.create_test_product(headers)
        assert product is not None
        product_id = product["id"]
        product_upc = product["upc"]
        
        # Create multiple sales for this product
        sale_data_1 = {
            "product_id": product_id,
            "sale_price": 15.99,
            "sale_start": str(date.today()),
            "sale_end": str(date.today() + timedelta(days=7))
        }
        sale_data_2 = {
            "product_id": product_id,
            "sale_price": 12.99,
            "sale_start": str(date.today() + timedelta(days=8)),
            "sale_end": str(date.today() + timedelta(days=14))
        }
        
        sale1_response = client.post("/sales/", json=sale_data_1, headers=headers)
        sale2_response = client.post("/sales/", json=sale_data_2, headers=headers)
        
        assert sale1_response.status_code == 200
        assert sale2_response.status_code == 200
        
        # Verify sales were created
        sales_check = client.get("/sales/").json()["sales"]
        assert len(sales_check) >= 2  # At least our 2 sales
        
        # Delete the product
        delete_response = client.delete(f"/products/{product_upc}", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify product is gone
        product_check = client.get("/products/").json()["products"]
        assert len(product_check) == 0
        
        # Verify all sales for this product are also gone (cascade delete)
        sales_after = client.get("/sales/").json()["sales"]
        assert len(sales_after) == 0  # Should be empty due to cascade
    
    def test_sale_delete_does_not_affect_product(self, manager_token):
        """Test that deleting a sale doesn't delete the product"""
        headers = TestHelper.auth_headers(manager_token)
        
        # Create product and sale
        product = TestHelper.create_test_product(headers)
        sale_data = {
            "product_id": product["id"],
            "sale_price": 15.99,
            "sale_start": str(date.today()),
            "sale_end": str(date.today() + timedelta(days=7))
        }
        
        sale_response = client.post("/sales/", json=sale_data, headers=headers)
        assert sale_response.status_code == 200
        
        # Get the sale ID
        sales = client.get("/sales/").json()["sales"]
        test_sale = next(s for s in sales if s["product_id"] == product["id"])
        
        # Delete the sale
        delete_response = client.delete(f"/sales/{test_sale['id']}", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify product still exists
        product_check = client.get("/products/")
        assert product_check.status_code == 200
        assert len(product_check.json()["products"]) > 0