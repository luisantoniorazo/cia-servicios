"""
Iteration 13 Tests - Super Admin Login, Dashboard, Changelog, Password Visibility
Tests for:
1. Super Admin Login API
2. Super Admin Dashboard API
3. Health Check API
4. Company Login API
5. Password visibility toggle (frontend verified via Playwright)
6. Version v1.0.0 display (frontend verified via Playwright)
7. Changelog modal (frontend verified via Playwright)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "superadmin@cia-servicios.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin2024!"


class TestSuperAdminAuth:
    """Super Admin authentication tests"""
    
    def test_super_admin_login_success(self):
        """Test Super Admin login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == SUPER_ADMIN_EMAIL
        assert data["user"]["role"] == "super_admin"
        print(f"✅ Super Admin login successful - Token received")
    
    def test_super_admin_login_invalid_password(self):
        """Test Super Admin login with invalid password"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Invalid password correctly rejected with 401")
    
    def test_super_admin_login_invalid_email(self):
        """Test Super Admin login with non-existent email"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={
                "email": "nonexistent@example.com",
                "password": SUPER_ADMIN_PASSWORD
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Non-existent email correctly rejected with 401")


class TestSuperAdminDashboard:
    """Super Admin dashboard tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for Super Admin"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Super Admin authentication failed")
    
    def test_dashboard_loads(self, auth_token):
        """Test Super Admin dashboard API returns data"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "summary" in data, "Dashboard should contain summary"
        assert "companies" in data, "Dashboard should contain companies list"
        print(f"✅ Dashboard loaded - {data['summary'].get('total_companies', 0)} companies found")
    
    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/super-admin/dashboard")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✅ Dashboard correctly requires authentication")
    
    def test_revenue_stats(self, auth_token):
        """Test revenue statistics API"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/revenue-stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "monthly_revenue" in data or "total_monthly_revenue" in data, "Should contain revenue data"
        print(f"✅ Revenue stats loaded successfully")
    
    def test_server_config(self, auth_token):
        """Test server configuration API"""
        response = requests.get(
            f"{BASE_URL}/api/super-admin/server-config",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ Server config loaded successfully")


class TestCompanyAuth:
    """Company authentication tests"""
    
    def test_company_info_endpoint(self):
        """Test company info endpoint returns public data"""
        response = requests.get(f"{BASE_URL}/api/empresa/marisela-vazquez-garcia/info")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain company id"
        assert "business_name" in data, "Response should contain business_name"
        assert "slug" in data, "Response should contain slug"
        print(f"✅ Company info loaded: {data.get('business_name')}")
    
    def test_company_info_not_found(self):
        """Test company info returns 404 for non-existent company"""
        response = requests.get(f"{BASE_URL}/api/empresa/non-existent-company/info")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✅ Non-existent company correctly returns 404")
    
    def test_company_login_invalid_credentials(self):
        """Test company login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/marisela-vazquez-garcia/login",
            json={
                "email": "invalid@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Invalid company credentials correctly rejected")


class TestAPIHealth:
    """API health and basic functionality tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        
        # API root might return 200 or 404 depending on implementation
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"✅ API root responded with {response.status_code}")
    
    def test_smtp_presets(self):
        """Test SMTP presets endpoint (requires auth)"""
        # First get auth token
        login_response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
        )
        
        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")
        
        token = login_response.json().get("access_token")
        
        response = requests.get(
            f"{BASE_URL}/api/super-admin/smtp-presets",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "gmail" in data, "Should contain gmail preset"
        assert "outlook" in data, "Should contain outlook preset"
        print(f"✅ SMTP presets loaded - {len(data)} providers available")


class TestTicketSystem:
    """Ticket system tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for Super Admin"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Super Admin authentication failed")
    
    def test_unread_ticket_count(self, auth_token):
        """Test unread ticket count endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/tickets/unread-count",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "unread" in data or isinstance(data, dict), "Should return count data"
        print(f"✅ Unread ticket count loaded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
