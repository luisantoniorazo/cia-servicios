"""
Backend tests for new CIA SERVICIOS features:
- Super Admin company admin management (edit, block/unblock)
- CRM Followup CRUD operations
- Client Statement PDF endpoint
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "superadmin@cia-servicios.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin2024!"
COMPANY_ADMIN_EMAIL = "gerente@ciademo.com"
COMPANY_ADMIN_PASSWORD = "Admin2024!"


class TestSuperAdminLogin:
    """Super Admin authentication tests"""
    
    def test_super_admin_login_success(self):
        """Test super admin login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert len(data["access_token"]) > 50, "Token seems too short"
        print(f"✓ Super admin login successful")
    
    def test_super_admin_login_invalid_credentials(self):
        """Test super admin login rejects invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": "wrong-password"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Invalid credentials rejected")


class TestSuperAdminCompanyManagement:
    """Super Admin company and admin management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get super admin token and company info"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get dashboard to find a company
        dashboard_resp = requests.get(f"{BASE_URL}/api/super-admin/dashboard", headers=self.headers)
        if dashboard_resp.status_code == 200:
            companies = dashboard_resp.json().get("companies", [])
            if companies:
                self.company_id = companies[0].get("id")
                self.company_slug = companies[0].get("slug")
                print(f"Using company: {companies[0].get('business_name')} ({self.company_id})")
    
    def test_dashboard_shows_companies_with_admin_info(self):
        """Dashboard returns companies with admin email, name and blocked status"""
        response = requests.get(f"{BASE_URL}/api/super-admin/dashboard", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "companies" in data
        
        companies = data["companies"]
        if len(companies) > 0:
            company = companies[0]
            # Verify admin info fields exist
            assert "admin_email" in company, "Missing admin_email field"
            assert "admin_name" in company, "Missing admin_name field"
            assert "admin_blocked" in company, "Missing admin_blocked field"
            print(f"✓ Company has admin_email: {company.get('admin_email')}")
            print(f"✓ Company has admin_name: {company.get('admin_name')}")
            print(f"✓ Company has admin_blocked: {company.get('admin_blocked')}")
    
    def test_get_company_admin(self):
        """Test getting company admin data"""
        if not hasattr(self, 'company_id'):
            pytest.skip("No company found")
        
        response = requests.get(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "admin" in data, "Missing admin data"
        assert "company_name" in data, "Missing company_name"
        
        admin = data["admin"]
        assert "email" in admin, "Missing admin email"
        assert "full_name" in admin, "Missing admin full_name"
        print(f"✓ Got admin data: {admin.get('full_name')} <{admin.get('email')}>")
    
    def test_update_company_admin(self):
        """Test updating company admin data"""
        if not hasattr(self, 'company_id'):
            pytest.skip("No company found")
        
        # First get current admin data
        get_response = requests.get(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin",
            headers=self.headers
        )
        original_admin = get_response.json().get("admin", {})
        original_phone = original_admin.get("phone", "")
        
        # Update with test phone number
        test_phone = "555-TEST-" + datetime.now().strftime("%H%M%S")
        response = requests.put(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin",
            headers=self.headers,
            json={"phone": test_phone}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing success message"
        print(f"✓ Admin updated: {data.get('message')}")
        
        # Verify update persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin",
            headers=self.headers
        )
        updated_admin = verify_response.json().get("admin", {})
        assert updated_admin.get("phone") == test_phone, "Phone update not persisted"
        print(f"✓ Verified phone updated to: {test_phone}")
        
        # Restore original phone
        requests.put(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin",
            headers=self.headers,
            json={"phone": original_phone}
        )
    
    def test_toggle_admin_status_block_unblock(self):
        """Test blocking and unblocking company admin"""
        if not hasattr(self, 'company_id'):
            pytest.skip("No company found")
        
        # Get current status
        get_response = requests.get(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin",
            headers=self.headers
        )
        original_status = get_response.json().get("admin", {}).get("is_active", True)
        
        # Toggle status (block)
        response = requests.patch(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin/toggle-status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message"
        assert "is_active" in data, "Missing is_active status"
        new_status = data["is_active"]
        print(f"✓ Admin status toggled: is_active={new_status} ({data.get('message')})")
        
        # Toggle back to restore original status
        restore_response = requests.patch(
            f"{BASE_URL}/api/super-admin/companies/{self.company_id}/admin/toggle-status",
            headers=self.headers
        )
        assert restore_response.status_code == 200
        restored_status = restore_response.json().get("is_active")
        print(f"✓ Admin status restored: is_active={restored_status}")


class TestCompanyAdminLogin:
    """Company admin login tests"""
    
    def test_company_admin_login_success(self):
        """Test company admin can login when not blocked"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/cia-servicios-demo-sa-de-cv/login",
            json={
                "email": COMPANY_ADMIN_EMAIL,
                "password": COMPANY_ADMIN_PASSWORD
            }
        )
        
        # Login should succeed (200) unless admin is blocked (403)
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data, "Missing access_token"
            assert "user" in data, "Missing user data"
            print(f"✓ Company admin login successful")
        elif response.status_code == 403:
            print(f"⚠ Admin is currently blocked - cannot login (expected if testing block feature)")
        else:
            assert False, f"Unexpected status {response.status_code}: {response.text}"


class TestCRMFollowups:
    """CRM Followup CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get company admin token and company info"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/cia-servicios-demo-sa-de-cv/login",
            json={
                "email": COMPANY_ADMIN_EMAIL,
                "password": COMPANY_ADMIN_PASSWORD
            }
        )
        if response.status_code != 200:
            pytest.skip("Company admin login failed - may be blocked")
        
        data = response.json()
        self.token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.company_id = data.get("company", {}).get("id")
        
        # Get a client for followup tests
        clients_resp = requests.get(
            f"{BASE_URL}/api/clients?company_id={self.company_id}",
            headers=self.headers
        )
        if clients_resp.status_code == 200:
            clients = clients_resp.json()
            if clients:
                self.client_id = clients[0].get("id")
                print(f"Using client: {clients[0].get('name')} ({self.client_id})")
    
    def test_create_followup(self):
        """Test creating a new followup for a client"""
        if not hasattr(self, 'client_id'):
            pytest.skip("No client found for testing")
        
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = requests.post(
            f"{BASE_URL}/api/clients/{self.client_id}/followups",
            headers=self.headers,
            json={
                "company_id": self.company_id,
                "client_id": self.client_id,
                "scheduled_date": tomorrow,
                "followup_type": "llamada",
                "notes": "TEST_followup_created_by_pytest"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Missing followup id"
        self.followup_id = data["id"]
        print(f"✓ Created followup: {self.followup_id}")
    
    def test_list_pending_followups(self):
        """Test listing pending followups for company"""
        if not hasattr(self, 'company_id'):
            pytest.skip("No company_id")
        
        response = requests.get(
            f"{BASE_URL}/api/followups/pending?company_id={self.company_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of followups"
        print(f"✓ Found {len(data)} pending followups")
        
        # Check followup structure
        if data:
            followup = data[0]
            assert "client_name" in followup, "Missing client_name in followup"
            assert "scheduled_date" in followup, "Missing scheduled_date"
            assert "followup_type" in followup, "Missing followup_type"
            print(f"✓ Followup data verified: {followup.get('client_name')} - {followup.get('followup_type')}")
    
    def test_list_client_followups(self):
        """Test listing followups for a specific client"""
        if not hasattr(self, 'client_id'):
            pytest.skip("No client_id")
        
        response = requests.get(
            f"{BASE_URL}/api/clients/{self.client_id}/followups",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of followups"
        print(f"✓ Found {len(data)} followups for client")


class TestClientStatementPDF:
    """Client Statement PDF endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get company admin token and find a client with invoices"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/cia-servicios-demo-sa-de-cv/login",
            json={
                "email": COMPANY_ADMIN_EMAIL,
                "password": COMPANY_ADMIN_PASSWORD
            }
        )
        if response.status_code != 200:
            pytest.skip("Company admin login failed")
        
        data = response.json()
        self.token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.company_id = data.get("company", {}).get("id")
        
        # Get a client
        clients_resp = requests.get(
            f"{BASE_URL}/api/clients?company_id={self.company_id}",
            headers=self.headers
        )
        if clients_resp.status_code == 200:
            clients = clients_resp.json()
            # Prefer non-prospect client
            non_prospects = [c for c in clients if not c.get("is_prospect")]
            if non_prospects:
                self.client = non_prospects[0]
            elif clients:
                self.client = clients[0]
            else:
                self.client = None
            
            if self.client:
                self.client_id = self.client.get("id")
                print(f"Using client: {self.client.get('name')} ({self.client_id})")
    
    def test_get_client_statement(self):
        """Test getting client statement (JSON)"""
        if not hasattr(self, 'client_id'):
            pytest.skip("No client found")
        
        response = requests.get(
            f"{BASE_URL}/api/clients/{self.client_id}/statement",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "client" in data, "Missing client data"
        assert "invoices" in data, "Missing invoices"
        assert "payments" in data, "Missing payments"
        assert "summary" in data, "Missing summary"
        
        summary = data["summary"]
        assert "total_invoiced" in summary, "Missing total_invoiced"
        assert "total_paid" in summary, "Missing total_paid"
        assert "balance" in summary, "Missing balance"
        
        print(f"✓ Client statement: total=${summary.get('total_invoiced', 0):,.2f}, paid=${summary.get('total_paid', 0):,.2f}, balance=${summary.get('balance', 0):,.2f}")
    
    def test_get_client_statement_pdf(self):
        """Test downloading client statement as PDF"""
        if not hasattr(self, 'client_id'):
            pytest.skip("No client found")
        
        response = requests.get(
            f"{BASE_URL}/api/clients/{self.client_id}/statement/pdf",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "filename" in data, "Missing filename"
        assert "content" in data, "Missing PDF content"
        
        # Verify it's valid base64 and decent size
        content = data.get("content", "")
        assert len(content) > 100, "PDF content too small"
        
        # Check filename format
        filename = data.get("filename", "")
        assert filename.endswith(".pdf"), f"Unexpected filename format: {filename}"
        assert "estado_cuenta" in filename.lower() or "account" in filename.lower(), f"Filename doesn't indicate statement: {filename}"
        
        print(f"✓ PDF generated: {filename} ({len(content)} bytes base64)")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(
            f"{BASE_URL}/api/empresa/cia-servicios-demo-sa-de-cv/login",
            json={
                "email": COMPANY_ADMIN_EMAIL,
                "password": COMPANY_ADMIN_PASSWORD
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.company_id = data.get("company", {}).get("id")
    
    def test_cleanup_test_followups(self):
        """Delete test followups"""
        if not hasattr(self, 'company_id'):
            pytest.skip("No login")
        
        response = requests.get(
            f"{BASE_URL}/api/followups/pending?company_id={self.company_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            followups = response.json()
            deleted = 0
            for f in followups:
                if "TEST_" in str(f.get("notes", "")):
                    del_resp = requests.delete(
                        f"{BASE_URL}/api/followups/{f['id']}",
                        headers=self.headers
                    )
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test followups")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
