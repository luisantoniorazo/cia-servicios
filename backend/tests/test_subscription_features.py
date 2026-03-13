"""
Test suite for Super Admin Subscription Management Features:
- GET /api/super-admin/companies - days_until_expiry, subscription_end, admin_blocked fields
- POST /api/super-admin/companies/{id}/subscription/renew - subscription renewal
- POST /api/super-admin/test-mysql-connection - MySQL connection test
- POST /api/super-admin/init-mysql-schema - MySQL schema creation
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Super Admin Credentials
SUPER_ADMIN_EMAIL = "superadmin@cia-servicios.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin2024!"


class TestSuperAdminLogin:
    """Test Super Admin authentication"""
    
    def test_super_admin_login_success(self):
        """Test Super Admin login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"
        print(f"SUCCESS: Super Admin login successful, token received")
        return data["access_token"]


class TestCompaniesEndpoint:
    """Test GET /api/super-admin/companies with new fields"""
    
    @pytest.fixture
    def auth_token(self):
        """Get Super Admin auth token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Super Admin login failed")
        return response.json()["access_token"]
    
    def test_companies_list_has_days_until_expiry(self, auth_token):
        """Test that GET /api/super-admin/companies returns days_until_expiry field"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get companies: {response.text}"
        companies = response.json()
        assert isinstance(companies, list), "Response should be a list"
        
        if len(companies) > 0:
            first_company = companies[0]
            # Check days_until_expiry field exists
            assert "days_until_expiry" in first_company, f"days_until_expiry field missing. Fields: {first_company.keys()}"
            print(f"SUCCESS: days_until_expiry field found: {first_company.get('days_until_expiry')}")
            
            # The value should be an integer or None
            days = first_company.get("days_until_expiry")
            assert days is None or isinstance(days, int), f"days_until_expiry should be int or None, got {type(days)}"
        else:
            print("WARNING: No companies found to test")
    
    def test_companies_list_has_subscription_end(self, auth_token):
        """Test that GET /api/super-admin/companies returns subscription_end field"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get companies: {response.text}"
        companies = response.json()
        
        if len(companies) > 0:
            first_company = companies[0]
            assert "subscription_end" in first_company, f"subscription_end field missing. Fields: {first_company.keys()}"
            print(f"SUCCESS: subscription_end field found: {first_company.get('subscription_end')}")
        else:
            print("WARNING: No companies found to test")
    
    def test_companies_list_has_admin_blocked(self, auth_token):
        """Test that GET /api/super-admin/companies returns admin_blocked field"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get companies: {response.text}"
        companies = response.json()
        
        if len(companies) > 0:
            first_company = companies[0]
            assert "admin_blocked" in first_company, f"admin_blocked field missing. Fields: {first_company.keys()}"
            assert isinstance(first_company.get("admin_blocked"), bool), "admin_blocked should be boolean"
            print(f"SUCCESS: admin_blocked field found: {first_company.get('admin_blocked')}")
        else:
            print("WARNING: No companies found to test")
    
    def test_companies_list_all_required_fields(self, auth_token):
        """Test that all required fields are present in companies list"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get companies: {response.text}"
        companies = response.json()
        
        required_fields = [
            "id", "business_name", "slug", "subscription_status",
            "days_until_expiry", "subscription_end", "admin_blocked",
            "admin_email", "admin_name", "user_count"
        ]
        
        if len(companies) > 0:
            first_company = companies[0]
            missing_fields = [f for f in required_fields if f not in first_company]
            assert len(missing_fields) == 0, f"Missing fields: {missing_fields}"
            print(f"SUCCESS: All required fields present: {required_fields}")
        else:
            print("WARNING: No companies found to test")


class TestSubscriptionRenewal:
    """Test POST /api/super-admin/companies/{id}/subscription/renew"""
    
    @pytest.fixture
    def auth_token(self):
        """Get Super Admin auth token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Super Admin login failed")
        return response.json()["access_token"]
    
    @pytest.fixture
    def company_id(self, auth_token):
        """Get first company ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No companies available for testing")
        return response.json()[0]["id"]
    
    def test_subscription_renewal_endpoint_exists(self, auth_token, company_id):
        """Test that subscription renewal endpoint exists and accepts POST"""
        # Test with minimal renewal data
        renewal_data = {
            "months": 1,
            "payment_amount": 100,
            "payment_method": "transfer",
            "notes": "Test renewal"
        }
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/subscription/renew",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=renewal_data
        )
        # Should return 200 OK with new end date
        assert response.status_code == 200, f"Renewal failed: {response.text}"
        data = response.json()
        assert "new_end_date" in data, f"Response missing new_end_date: {data}"
        assert "days_until_expiry" in data, f"Response missing days_until_expiry: {data}"
        print(f"SUCCESS: Subscription renewed, new_end_date: {data.get('new_end_date')}")
    
    def test_subscription_renewal_returns_correct_data(self, auth_token, company_id):
        """Test renewal returns correct response structure"""
        renewal_data = {
            "months": 3,
            "payment_amount": 7500,
            "payment_method": "card",
            "notes": "Test 3-month renewal"
        }
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/subscription/renew",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=renewal_data
        )
        assert response.status_code == 200, f"Renewal failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "message" in data, "Response missing message"
        assert "new_end_date" in data, "Response missing new_end_date"
        assert "days_until_expiry" in data, "Response missing days_until_expiry"
        
        # Verify days_until_expiry is positive (since we just renewed)
        assert data["days_until_expiry"] > 0, f"days_until_expiry should be positive: {data['days_until_expiry']}"
        
        print(f"SUCCESS: Renewal response valid - message: {data['message']}, days_until_expiry: {data['days_until_expiry']}")
    
    def test_subscription_renewal_updates_company(self, auth_token, company_id):
        """Test that renewal actually updates the company subscription"""
        # Get company before renewal
        response_before = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        company_before = next((c for c in response_before.json() if c["id"] == company_id), None)
        
        # Perform renewal
        renewal_data = {
            "months": 1,
            "payment_amount": 2500,
            "payment_method": "transfer",
            "notes": "Test verify update"
        }
        response = requests.post(
            f"{BASE_URL}/api/super-admin/companies/{company_id}/subscription/renew",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=renewal_data
        )
        assert response.status_code == 200
        
        # Get company after renewal
        response_after = requests.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        company_after = next((c for c in response_after.json() if c["id"] == company_id), None)
        
        # Verify subscription_end was updated
        assert company_after["subscription_end"] is not None, "subscription_end should not be None after renewal"
        print(f"SUCCESS: Company subscription updated - subscription_end: {company_after['subscription_end']}")


class TestMySQLEndpoints:
    """Test MySQL migration endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get Super Admin auth token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Super Admin login failed")
        return response.json()["access_token"]
    
    def test_mysql_connection_endpoint_exists(self, auth_token):
        """Test POST /api/super-admin/test-mysql-connection endpoint exists"""
        # Send test config (will fail connection but endpoint should exist)
        test_config = {
            "mysql_host": "localhost",
            "mysql_port": 3306,
            "mysql_user": "test_user",
            "mysql_password": "test_pass",
            "mysql_database": "test_db"
        }
        response = requests.post(
            f"{BASE_URL}/api/super-admin/test-mysql-connection",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=test_config
        )
        # Endpoint should return 200 (even if connection fails, it returns success=false)
        assert response.status_code == 200, f"Endpoint error: {response.text}"
        data = response.json()
        assert "success" in data, f"Response missing 'success' field: {data}"
        assert "message" in data, f"Response missing 'message' field: {data}"
        print(f"SUCCESS: test-mysql-connection endpoint exists - success: {data['success']}, message: {data['message']}")
    
    def test_init_mysql_schema_endpoint_exists(self, auth_token):
        """Test POST /api/super-admin/init-mysql-schema endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/init-mysql-schema",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Endpoint should return 200 or 400 (if no config)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}, {response.text}"
        data = response.json()
        
        # If 400, should mention missing config
        if response.status_code == 400:
            assert "detail" in data or "message" in data
            print(f"SUCCESS: init-mysql-schema endpoint exists - returned 400 (no MySQL config)")
        else:
            assert "success" in data or "message" in data
            print(f"SUCCESS: init-mysql-schema endpoint exists - response: {data}")
    
    def test_server_config_get(self, auth_token):
        """Test GET /api/super-admin/server-config endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/server-config",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get server config: {response.text}"
        data = response.json()
        # Should return config with MySQL fields
        print(f"SUCCESS: server-config endpoint returns: {list(data.keys())}")
    
    def test_server_config_post(self, auth_token):
        """Test POST /api/super-admin/server-config endpoint"""
        test_config = {
            "mysql_host": "test.example.com",
            "mysql_port": 3306,
            "mysql_user": "test_user",
            "mysql_password": "",
            "mysql_database": "test_db",
            "backup_enabled": False,
            "backup_schedule": "daily",
            "cloud_provider": "mysql"
        }
        response = requests.post(
            f"{BASE_URL}/api/super-admin/server-config",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=test_config
        )
        assert response.status_code == 200, f"Failed to save server config: {response.text}"
        print(f"SUCCESS: server-config POST endpoint works")


class TestDashboardEndpoint:
    """Test dashboard endpoint that feeds the UI"""
    
    @pytest.fixture
    def auth_token(self):
        """Get Super Admin auth token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Super Admin login failed")
        return response.json()["access_token"]
    
    def test_dashboard_endpoint(self, auth_token):
        """Test GET /api/super-admin/dashboard returns companies with required fields"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Dashboard should have summary and companies
        assert "summary" in data, f"Dashboard missing summary: {data.keys()}"
        assert "companies" in data, f"Dashboard missing companies: {data.keys()}"
        
        # Check companies have required fields for UI
        if len(data["companies"]) > 0:
            company = data["companies"][0]
            ui_fields = ["days_until_expiry", "subscription_end", "admin_blocked", "subscription_status"]
            missing = [f for f in ui_fields if f not in company]
            assert len(missing) == 0, f"Dashboard companies missing fields: {missing}"
            print(f"SUCCESS: Dashboard companies have all UI required fields")
        else:
            print("WARNING: No companies in dashboard")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
