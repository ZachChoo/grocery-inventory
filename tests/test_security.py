import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_current_user,
    require_role
)
from app.config import settings
from app.main import app

client = TestClient(app)

class TestPasswordHashing:
    
    def test_hash_password_creates_hash(self):
        """Test that password hashing creates a hash different from original"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert password not in hashed
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed.startswith('$2b$')  # bcrypt hash format
    
    def test_hash_password_different_hashes_for_same_password(self):
        """Test that same password creates different hashes (salt works)"""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different due to salt
    
    def test_verify_password_correct_password(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

class TestJWTTokens:
    
    def test_create_access_token_structure(self):
        """Test that JWT token is created with correct structure"""
        data = {"sub": "testuser", "user_id": 123}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts separated by dots
    
    def test_create_access_token_contains_data(self):
        """Test that JWT token contains the provided data"""
        data = {"sub": "testuser", "user_id": 123}
        token = create_access_token(data)
        
        # Decode token to verify contents
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == 123
        assert "exp" in decoded  # Expiration should be added
    
    def test_create_access_token_has_expiration(self):
        """Test that JWT token has expiration time"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        # Should expire in approximately ACCESS_TOKEN_EXPIRE_MINUTES
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        
        assert time_diff < 60  # Should be within 1 minute of expected
    
    def test_create_access_token_empty_data(self):
        """Test creating token with empty data"""
        token = create_access_token({})
        
        assert isinstance(token, str)
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in decoded  # Should still have expiration

class TestGetCurrentUser:
    
    def setup_method(self):
        """Create a test user for authentication tests"""
        user_data = {
            "username": "authtest",
            "password": "testpass123",
            "role": "employee"
        }
        client.post("/users/register", json=user_data)
    
    def test_get_current_user_valid_token(self):
        """Test getting current user with valid token"""
        # Login to get a valid token
        login_data = {"username": "authtest", "password": "testpass123"}
        login_response = client.post("/users/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Use the token to get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "authtest"
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_get_current_user_expired_token(self):
        """Test getting current user with expired token"""
        # Create an expired token manually
        expired_data = {
            "sub": "authtest",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired 1 minute ago
        }
        expired_token = jwt.encode(expired_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_malformed_token(self):
        """Test getting current user with malformed token"""
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_no_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/users/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_nonexistent_user(self):
        """Test token with username that doesn't exist in database"""
        # Create token for non-existent user
        fake_data = {"sub": "nonexistentuser"}
        fake_token = create_access_token(fake_data)
        
        headers = {"Authorization": f"Bearer {fake_token}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_token_missing_username(self):
        """Test token that's valid but missing 'sub' field"""
        # Create token without 'sub' field
        token_data = {
            "user_id": 123,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        token = jwt.encode(token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

class TestRequireRole:
    
    def setup_method(self):
        """Create test users with different roles"""
        employee_data = {
            "username": "roleemployee",
            "password": "testpass123",
            "role": "employee"
        }
        manager_data = {
            "username": "rolemanager", 
            "password": "testpass123",
            "role": "manager"
        }
        
        client.post("/users/register", json=employee_data)
        client.post("/users/register", json=manager_data)
    
    def get_auth_token(self, username: str) -> str:
        """Helper to get auth token for user"""
        login_data = {"username": username, "password": "testpass123"}
        response = client.post("/users/login", data=login_data)
        return response.json()["access_token"]
    
    def test_require_role_correct_role(self):
        """Test that user with correct role can access endpoint"""
        manager_token = self.get_auth_token("rolemanager")
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Try to delete a user (requires manager role)
        response = client.delete("/users/999", headers=headers)
        
        # Should not be a 404 Forbidden as user doesn't exist
        assert response.status_code == 404
    
    def test_require_role_incorrect_role(self):
        """Test that user with incorrect role cannot access endpoint"""
        employee_token = self.get_auth_token("roleemployee")
        headers = {"Authorization": f"Bearer {employee_token}"}
        
        # Try to delete a user (requires manager role)
        response = client.delete("/users/999", headers=headers)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions"
    
    def test_require_role_no_authentication(self):
        """Test that unauthenticated users cannot access role-protected endpoints"""
        response = client.delete("/users/999")
        
        assert response.status_code == 401  # Should be unauthorized, not forbidden

class TestSecurityIntegration:
    
    def test_full_auth_flow(self):
        """Test complete authentication flow from registration to protected access"""
        # 1. Register user
        user_data = {
            "username": "integrationtest",
            "password": "securepass123",
            "role": "manager"
        }
        reg_response = client.post("/users/register", json=user_data)
        assert reg_response.status_code == 200
        
        # 2. Login and get token
        login_response = client.post("/users/login", data={
            "username": "integrationtest",
            "password": "securepass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/users/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "integrationtest"
        
        # 4. Use token to access role-protected endpoint
        delete_response = client.delete("/users/999", headers=headers)
        assert delete_response.status_code != 403  # Has correct role