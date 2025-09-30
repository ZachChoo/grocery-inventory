import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch

from app.main import app

client = TestClient(app)

class TestHelper:
    @staticmethod
    def create_test_user(username: str, role: str = "employee", email: str = None):
        """Create a test user and return their data"""
        if email is None:
            email = f"{username}@test.com"
        
        user_data = {
            "username": username,
            "password": "testpassword",
            "role": role,
            "email": email
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
def manager_token():
    """Create manager user and return auth token"""
    TestHelper.create_test_user("testmanager", "manager", "manager@test.com")
    return TestHelper.get_auth_token("testmanager")

@pytest.fixture
def employee_token():
    """Create employee user and return auth token"""
    TestHelper.create_test_user("testemployee", "employee", "employee@test.com")
    return TestHelper.get_auth_token("testemployee")

@pytest.fixture
def sample_product(employee_token):
    """Create a sample product for testing"""
    headers = TestHelper.auth_headers(employee_token)
    product_data = {
        "upc": 123456,
        "name": "Test Product",
        "price": 9.99,
        "quantity": 50,
        "report_code": 1234,
        "reorder_threshold": 10
    }
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    return product_data

@pytest.fixture
def sample_sale(employee_token, sample_product):
    """Create a sample sale for testing"""
    headers = TestHelper.auth_headers(employee_token)
    
    # Create sale ending tomorrow
    tomorrow = datetime.now().date() + timedelta(days=1)
    sale_data = {
        "product_upc": 123456,
        "sale_price": 7.99,
        "sale_start": datetime.now().date().isoformat(),
        "sale_end": tomorrow.isoformat()
    }
    response = client.post("/sales/", json=sale_data, headers=headers)
    assert response.status_code == 200
    return sale_data


class TestEmailNotifications:
    
    def test_manual_sale_check_endpoint_exists(self):
        """Test that the manual sale check endpoint exists"""
        response = client.post("/admin/notify-sales")
        assert response.status_code == 200
        assert "message" in response.json()
    
    @patch('app.services.emails.EmailService.send_sale_notification_email')
    def test_manual_sale_check_with_expiring_sale(self, mock_email, manager_token, sample_sale):
        """Test manual sale check finds expiring sales and sends email"""
        # Mock successful email sending
        mock_email.return_value = True
        
        # Trigger the manual check
        response = client.post("/admin/notify-sales")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have sent notification
        assert "1 notifications sent" in data["message"] or "1 notification sent" in data["message"]
        
        # Email service should have been called
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        # Should have sent to manager
        assert "manager@test.com" in call_args[0][0]  # Email recipients
        assert len(call_args[0][1]) == 1  # Sales list should have 1 sale
    
    def test_manual_sale_check_no_expiring_sales(self, manager_token):
        """Test manual sale check with no expiring sales"""
        response = client.post("/admin/notify-sales")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate no notifications sent
        assert "0 notifications sent" in data["message"]
    
    @patch('app.services.emails.EmailService.send_sale_notification_email')
    def test_manual_sale_check_no_managers(self, mock_email, employee_token, sample_sale):
        """Test manual sale check when no managers exist to notify"""
        # Only employee exists, no managers
        mock_email.return_value = True
        
        response = client.post("/admin/notify-sales")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate no notifications sent (no managers to notify)
        assert "0 notifications sent" in data["message"]
        
        # Email service should not have been called
        mock_email.assert_not_called()
    
    @patch('app.services.emails.EmailService.send_sale_notification_email')
    def test_email_content_includes_product_details(self, mock_email, manager_token, sample_sale):
        """Test that email notifications include proper product details"""
        mock_email.return_value = True
        
        response = client.post("/admin/notify-sales")
        assert response.status_code == 200
        
        # Verify email service was called with proper data
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        # Check recipients
        recipients = call_args[0][0]
        assert "manager@test.com" in recipients
        
        # Check sales data
        sales_list = call_args[0][1]
        assert len(sales_list) == 1

        # The sale should have product relationship loaded
        sale = sales_list[0]
        assert sale["product"]["name"] == "Test Product"
        assert sale["sale_price"] == 7.99