import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

class TestHelper:
    @staticmethod
    def create_test_user(username: str, role: str = "employee"):
        """Create a test user and return their data"""
        user_data = {
            "username": username,
            "password": "testpassword",
            "role": role
        }
        client.post("/users/register", json=user_data)
        return user_data
    
    @staticmethod
    def get_auth_token(username: str, password: str = "testpassword"):
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

# Test fixtures
@pytest.fixture
def employee_token():
    """Create employee user and return auth token"""
    TestHelper.create_test_user("testemployee", "employee")
    return TestHelper.get_auth_token("testemployee")

@pytest.fixture
def manager_token():
    """Create manager user and return auth token"""
    TestHelper.create_test_user("testmanager", "manager")
    return TestHelper.get_auth_token("testmanager")

@pytest.fixture
def sample_product():
    """Sample product data for testing"""
    return {
        "upc": 123,
        "name": "Test Product",
        "price": 9.99,
        "quantity": 50,
        "report_code": 1234,
        "reorder_threshold": 10
    }

class TestGetProducts:
    def test_get_products_no_auth_required(self):
        """Test getting products (should work without authentication)"""
        response = client.get("/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert isinstance(data["products"], list)

    def test_get_products_max_page_size(self):
        """Test getting products with too big of a page size"""
        response = client.get("/products/?page=1&size=999999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] < 999999

    def test_get_product_after_creation(self, employee_token, sample_product):
        """Test creating product can be gotten"""
        headers = TestHelper.auth_headers(employee_token)
        response = client.post("/products/", json=sample_product, headers=headers)
        
        assert response.status_code == 200  # Created
        assert response.json()["message"] == "Product created!"

        response = client.get("/products/")
        assert response.status_code == 200
        product = response.json()["products"][0]
        del product["id"]
        assert product == sample_product

class TestCreateProducts:
    def test_create_product_requires_auth(self, sample_product):
        """Test creating product without authentication fails"""
        response = client.post("/products/", json=sample_product)
        
        assert response.status_code == 401  # Unauthorized
        assert response.json()["detail"] == "Not authenticated"
    
    def test_create_product_with_auth(self, employee_token, sample_product):
        """Test creating product with valid authentication"""
        headers = TestHelper.auth_headers(employee_token)
        response = client.post("/products/", json=sample_product, headers=headers)
        
        assert response.status_code == 200  # Created
        assert response.json()["message"] == "Product created!"

    @pytest.mark.parametrize("upc", [None, "string"])
    def test_create_product_invalid_upc(self, upc, employee_token, sample_product):
        """Test creating product with invalid fields - upc as an string and None"""
        headers = TestHelper.auth_headers(employee_token)
        product = sample_product.copy()
        product["upc"] = upc
        response = client.post("/products/", json=product, headers=headers)

        assert response.status_code == 422

    def test_create_product_duplicate_upc(self, employee_token, sample_product):
        """Test creating product with duplicate UPC fails"""
        headers = TestHelper.auth_headers(employee_token)
        
        # Create first product
        client.post("/products/", json=sample_product, headers=headers)
        
        # Try to create duplicate
        response = client.post("/products/", json=sample_product, headers=headers)
        
        assert response.status_code == 400  # Bad Request
        assert response.json()["detail"] == "Invalid product"

class TestDeleteProducts:
    def test_delete_product_requires_manager(self, employee_token, manager_token, sample_product):
        """Test that only managers can delete products"""
        manager_headers = TestHelper.auth_headers(manager_token)
        employee_headers = TestHelper.auth_headers(employee_token)
        
        # Manager creates a product
        create_response = client.post("/products/", json=sample_product, headers=manager_headers)
        assert create_response.status_code == 200
        
        # Employee tries to delete (should fail)
        employee_delete = client.delete(f"/products/{sample_product['upc']}", headers=employee_headers)
        assert employee_delete.status_code == 403  # Forbidden
        assert employee_delete.json()["detail"] == "Insufficient permissions"
        
        # Manager deletes (should work)
        manager_delete = client.delete(f"/products/{sample_product['upc']}", headers=manager_headers)
        assert manager_delete.status_code == 200
        assert manager_delete.json()["message"] == "Product deleted!"
        
    def test_delete_nonexistent_product(self, manager_token):
        """Test deleting product that doesn't exist"""
        headers = TestHelper.auth_headers(manager_token)
        
        response = client.delete("/products/99999", headers=headers)
        assert response.status_code == 404  # Not Found
        assert response.json()["detail"] == "Product not found!"