import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

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

# Test fixtures
@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "password": "employeepass123",
        "role": "employee"
    }

@pytest.fixture
def manager_user():
    """Sample manager user data"""
    return {
        "username": "testmanager",
        "password": "managerpass123", 
        "role": "manager"
    }

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


class TestUserRegistration:
    
    def test_register_new_user(self, sample_user):
        """Test successful user registration"""
        response = client.post("/users/register", json=sample_user)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User created!"
    
    def test_register_duplicate_username(self, sample_user):
        """Test registering user with existing username fails"""
        # Create first user
        client.post("/users/register", json=sample_user)
        
        # Try to create duplicate
        response = client.post("/users/register", json=sample_user)
        
        assert response.status_code == 400
        assert response.json()["detail"] == "User already registered"
    
    def test_register_invalid_data(self):
        """Test registration with missing required fields"""
        invalid_data = {
            "username": "testuser"
            # Missing password and role
        }
        
        response = client.post("/users/register", json=invalid_data)
        assert response.status_code == 422  # Validation error

class TestUserLogin:
    
    def test_login_valid_credentials(self, sample_user):
        """Test successful login with valid credentials"""
        # First register the user
        client.post("/users/register", json=sample_user)
        
        # Then try to login
        login_data = {
            "username": sample_user["username"],
            "password": sample_user["password"]
        }
        
        response = client.post("/users/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_username(self):
        """Test login with non-existent username"""
        login_data = {
            "username": "nonexistentuser",
            "password": "anypassword"
        }
        response = client.post("/users/login", data=login_data)
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    
    def test_login_invalid_password(self, sample_user):
        """Test login with wrong password"""
        # Register user first
        client.post("/users/register", json=sample_user)
        
        # Try login with wrong password
        login_data = {
            "username": sample_user["username"],
            "password": "wrongpassword"
        }
        response = client.post("/users/login", data=login_data)
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_missing_credentials(self):
        """Test login without providing credentials"""
        response = client.post("/users/login", data={})
        assert response.status_code == 422  # Validation error

class TestGetUsers:
    
    def test_get_users_default_pagination(self, sample_user):
        """Test getting users with default pagination"""
        # First register the user
        client.post("/users/register", json=sample_user)

        response = client.get("/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert "size" in data
        assert isinstance(data["users"], list)
        assert data["page"] == 1
        assert data["users"][0]["username"] == sample_user["username"]
    
    def test_get_users_custom_pagination(self):
        """Test getting users with custom page size"""
        response = client.get("/users/?page=1&size=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
    
    def test_get_users_max_page_size(self):
        """Test getting users with too big of a page size"""
        response = client.get("/users/?page=1&size=999999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] < 999999

class TestDeleteUser:
    
    def test_delete_user_requires_manager_role(self):
        """Test that deleting users requires manager authentication"""
        # Create a regular employee
        _, _ = TestHelper.create_test_user("regularuser", "employee")
        employee_token = TestHelper.get_auth_token("regularuser")
        employee_headers = TestHelper.auth_headers(employee_token)
        
        # Try to delete a user as employee (should fail)
        response = client.delete("/users/1", headers=employee_headers)
        
        assert response.status_code == 403  # Forbidden
        assert response.json()["detail"] == "Insufficient permissions"
    
    def test_delete_user_as_manager(self):
        """Test that managers can delete users"""
        # Create a manager
        _, _ = TestHelper.create_test_user("testmanager", "manager")
        manager_token = TestHelper.get_auth_token("testmanager")
        manager_headers = TestHelper.auth_headers(manager_token)
        
        # Create a user to delete
        _, _ = TestHelper.create_test_user("deleteme", "employee")
            
        # Manager deletes the user
        response = client.delete(f"/users/2", headers=manager_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted!"

    def test_delete_nonexistent_user(self):
        """Test deleting user that doesn't exist"""
        # Create a manager
        _, _ = TestHelper.create_test_user("testmanager", "manager")
        manager_token = TestHelper.get_auth_token("testmanager")
        manager_headers = TestHelper.auth_headers(manager_token)
        
        # Try to delete non-existent user
        response = client.delete("/users/99999", headers=manager_headers)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found!"
    
    def test_delete_user_without_auth(self):
        """Test deleting user without authentication"""
        response = client.delete("/users/1")
        assert response.status_code == 401  # Unauthorized

class TestUserAuthentication:
    
    def test_token_contains_user_info(self, sample_user):
        """Test that JWT token contains correct user information"""
        # Register and login
        client.post("/users/register", json=sample_user)
        login_response = client.post("/users/login", data={
            "username": sample_user["username"],
            "password": sample_user["password"]
        })
        
        assert login_response.status_code == 200
        
        # Use the token to get user info
        token = login_response.json()["access_token"]
        headers = TestHelper.auth_headers(token)
        
        me_response = client.get("/users/me", headers=headers)
        
        assert me_response.status_code == 200
        user_data = me_response.json()
        
        # Verify the token decoded to the correct user
        assert user_data["username"] == sample_user["username"]
        assert user_data["role"] == sample_user["role"]
        assert "id" in user_data
        assert "password_hash" not in user_data

class TestGetCurrentUser:

    def test_get_current_user_info(self, sample_user):
        """Test getting current user info with valid token"""
        # Register, login, get user info
        client.post("/users/register", json=sample_user)
        token = TestHelper.get_auth_token(sample_user["username"], sample_user["password"])
        
        response = client.get("/users/me", headers=TestHelper.auth_headers(token))
        
        assert response.status_code == 200
        assert response.json()["username"] == sample_user["username"]

    def test_get_current_user_without_auth(self):
        """Test that /users/me requires authentication"""
        response = client.get("/users/me")
        assert response.status_code == 401