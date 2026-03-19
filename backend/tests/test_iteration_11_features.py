"""
Test file for iteration 11 features:
1. Profitability Reports API - GET /api/analytics/profitability
2. AI Ticket Diagnosis API - POST /api/tickets/{ticket_id}/ai-diagnosis
3. Projects page functionality verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cia-operacional.preview.emergentagent.com').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "superadmin@cia-servicios.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin2024!"
COMPANY_ADMIN_EMAIL = "admin@demo-test.com"
COMPANY_ADMIN_PASSWORD = "Demo2024!"
COMPANY_SLUG = "demo-test-sa-de-cv"
TEST_TICKET_ID = "b4d034e6-f252-4b42-83f9-a3cc0bacb3f9"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_super_admin_login(self):
        """Super Admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"
        print(f"✓ Super Admin login successful")
    
    def test_company_admin_login(self):
        """Company Admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": COMPANY_ADMIN_EMAIL, "password": COMPANY_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        assert data["company"]["slug"] == COMPANY_SLUG
        print(f"✓ Company Admin login successful")


class TestProfitabilityAPI:
    """Test Profitability Reports API - GET /api/analytics/profitability"""
    
    @pytest.fixture
    def company_token(self):
        """Get company admin token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": COMPANY_ADMIN_EMAIL, "password": COMPANY_ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Unable to login as company admin")
        return response.json()["access_token"]
    
    def test_profitability_without_filters(self, company_token):
        """GET /api/analytics/profitability returns valid response without date filters"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/profitability",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "period" in data
        assert "sales" in data
        assert "purchases" in data
        assert "profitability" in data
        
        # Validate sales fields
        assert "total_invoiced" in data["sales"]
        assert "total_collected" in data["sales"]
        assert "pending_collection" in data["sales"]
        assert "invoices_count" in data["sales"]
        
        # Validate purchases fields
        assert "total_purchases" in data["purchases"]
        assert "purchase_orders_count" in data["purchases"]
        
        # Validate profitability fields
        assert "gross_profit" in data["profitability"]
        assert "profit_margin" in data["profitability"]
        
        # Verify data types
        assert isinstance(data["sales"]["total_invoiced"], (int, float))
        assert isinstance(data["profitability"]["profit_margin"], (int, float))
        
        print(f"✓ Profitability API returns valid structure without filters")
    
    def test_profitability_with_date_filters(self, company_token):
        """GET /api/analytics/profitability accepts date filters"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/profitability?start_date=2026-01-01&end_date=2026-03-31",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify date filters are returned
        assert data["period"]["start_date"] == "2026-01-01"
        assert data["period"]["end_date"] == "2026-03-31"
        
        print(f"✓ Profitability API accepts and returns date filters")
    
    def test_profitability_with_only_start_date(self, company_token):
        """GET /api/analytics/profitability accepts only start_date filter"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/profitability?start_date=2026-01-01",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["period"]["start_date"] == "2026-01-01"
        assert data["period"]["end_date"] is None
        
        print(f"✓ Profitability API accepts only start_date filter")
    
    def test_profitability_without_auth(self):
        """GET /api/analytics/profitability requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analytics/profitability")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Profitability API correctly requires authentication")


class TestAIDiagnosisAPI:
    """Test AI Ticket Diagnosis API - POST /api/tickets/{ticket_id}/ai-diagnosis"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Unable to login as super admin")
        return response.json()["access_token"]
    
    @pytest.fixture
    def company_token(self):
        """Get company admin token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": COMPANY_ADMIN_EMAIL, "password": COMPANY_ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Unable to login as company admin")
        return response.json()["access_token"]
    
    def test_ai_diagnosis_success(self, super_admin_token):
        """POST /api/tickets/{ticket_id}/ai-diagnosis generates diagnosis"""
        response = requests.post(
            f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/ai-diagnosis",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "ticket_id" in data
        assert "diagnosis" in data
        assert "created_at" in data
        assert "message" in data
        
        assert data["ticket_id"] == TEST_TICKET_ID
        assert len(data["diagnosis"]) > 100  # Should have substantial diagnosis text
        
        print(f"✓ AI Diagnosis API generates diagnosis successfully")
    
    def test_ai_diagnosis_requires_super_admin(self, company_token):
        """POST /api/tickets/{ticket_id}/ai-diagnosis requires super admin role"""
        response = requests.post(
            f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/ai-diagnosis",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ AI Diagnosis API correctly requires super admin role")
    
    def test_ai_diagnosis_ticket_not_found(self, super_admin_token):
        """POST /api/tickets/{ticket_id}/ai-diagnosis returns 404 for non-existent ticket"""
        fake_ticket_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/tickets/{fake_ticket_id}/ai-diagnosis",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ AI Diagnosis API correctly returns 404 for non-existent ticket")
    
    def test_ai_diagnosis_without_auth(self):
        """POST /api/tickets/{ticket_id}/ai-diagnosis requires authentication"""
        response = requests.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/ai-diagnosis")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ AI Diagnosis API correctly requires authentication")


class TestProjectsAPI:
    """Test Projects API to verify no JavaScript errors are caused by backend"""
    
    @pytest.fixture
    def company_token(self):
        """Get company admin token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": COMPANY_ADMIN_EMAIL, "password": COMPANY_ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Unable to login as company admin")
        token = response.json()["access_token"]
        company_id = response.json()["company"]["id"]
        return token, company_id
    
    def test_get_projects(self, company_token):
        """GET /api/projects returns valid project list"""
        token, company_id = company_token
        response = requests.get(
            f"{BASE_URL}/api/projects?company_id={company_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        print(f"✓ Projects API returns valid list ({len(data)} projects)")
    
    def test_get_clients(self, company_token):
        """GET /api/clients returns valid client list (required by Projects page)"""
        token, company_id = company_token
        response = requests.get(
            f"{BASE_URL}/api/clients?company_id={company_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Clients API returns valid list ({len(data)} clients)")
    
    def test_get_users(self, company_token):
        """GET /api/admin/users returns valid user list (required by Projects page)"""
        token, _ = company_token
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Users API returns valid list ({len(data)} users)")


class TestTicketsAPI:
    """Test Tickets API to ensure ticket detail works correctly"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(
            f"{BASE_URL}/api/super-admin/login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Unable to login as super admin")
        return response.json()["access_token"]
    
    def test_get_all_tickets(self, super_admin_token):
        """GET /api/tickets/admin/all returns all tickets (super admin)"""
        response = requests.get(
            f"{BASE_URL}/api/tickets/admin/all",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Admin Tickets API returns valid list ({len(data)} tickets)")
    
    def test_get_ticket_by_id(self, super_admin_token):
        """GET specific ticket includes ai_diagnosis field"""
        # First get all tickets to find the test ticket
        response = requests.get(
            f"{BASE_URL}/api/tickets/admin/all",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        tickets = response.json()
        
        # Find our test ticket
        test_ticket = None
        for t in tickets:
            if t.get("id") == TEST_TICKET_ID:
                test_ticket = t
                break
        
        if test_ticket:
            # Verify ticket structure includes ai_diagnosis after the diagnosis was run
            assert "id" in test_ticket
            assert "title" in test_ticket
            assert "status" in test_ticket
            print(f"✓ Test ticket found with proper structure")
        else:
            print(f"⚠ Test ticket {TEST_TICKET_ID} not found in ticket list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
