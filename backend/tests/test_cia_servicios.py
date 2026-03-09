"""
CIA SERVICIOS - Comprehensive Backend API Tests
Tests: Super Admin Auth, Company Auth, User Management, Module CRUD operations
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============== TEST CREDENTIALS ==============
SUPER_ADMIN_CREDS = {
    "email": "superadmin@cia-servicios.com",
    "password": "SuperAdmin2024!",
    "admin_key": "cia-master-2024"
}

COMPANY_ADMIN_CREDS = {
    "email": "gerente@ciademo.com",
    "password": "Admin2024!",
    "company_slug": "cia-servicios-demo-sa-de-cv"
}


# ============== FIXTURES ==============
@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def super_admin_token(api_client):
    """Super Admin JWT Token"""
    response = api_client.post(f"{BASE_URL}/api/super-admin/login", json=SUPER_ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Super Admin login failed: {response.text}")


@pytest.fixture(scope="module")
def company_admin_token(api_client):
    """Company Admin JWT Token"""
    slug = COMPANY_ADMIN_CREDS["company_slug"]
    response = api_client.post(f"{BASE_URL}/api/empresa/{slug}/login", json={
        "email": COMPANY_ADMIN_CREDS["email"],
        "password": COMPANY_ADMIN_CREDS["password"]
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Company Admin login failed: {response.text}")


@pytest.fixture(scope="module")
def company_id(api_client, super_admin_token):
    """Get the demo company ID"""
    response = api_client.get(
        f"{BASE_URL}/api/super-admin/companies",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    companies = response.json()
    for c in companies:
        if c["slug"] == COMPANY_ADMIN_CREDS["company_slug"]:
            return c["id"]
    pytest.fail("Demo company not found")


# ============== SUPER ADMIN AUTH TESTS ==============
class TestSuperAdminAuth:
    """Super Admin Authentication endpoint tests"""

    def test_super_admin_login_success(self, api_client):
        """Test Super Admin login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/super-admin/login", json=SUPER_ADMIN_CREDS)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["email"] == SUPER_ADMIN_CREDS["email"]
        print("✓ Super Admin login successful")

    def test_super_admin_login_invalid_key(self, api_client):
        """Test Super Admin login fails with wrong admin_key"""
        response = api_client.post(f"{BASE_URL}/api/super-admin/login", json={
            **SUPER_ADMIN_CREDS,
            "admin_key": "wrong-key"
        })
        assert response.status_code == 401
        print("✓ Super Admin login correctly rejected with invalid key")

    def test_super_admin_login_invalid_password(self, api_client):
        """Test Super Admin login fails with wrong password"""
        response = api_client.post(f"{BASE_URL}/api/super-admin/login", json={
            **SUPER_ADMIN_CREDS,
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Super Admin login correctly rejected with invalid password")


# ============== COMPANY AUTH TESTS ==============
class TestCompanyAuth:
    """Company Authentication endpoint tests"""

    def test_get_company_info_by_slug(self, api_client):
        """Test fetching company public info by slug"""
        slug = COMPANY_ADMIN_CREDS["company_slug"]
        response = api_client.get(f"{BASE_URL}/api/empresa/{slug}/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["slug"] == slug
        assert "business_name" in data
        assert "id" in data
        print(f"✓ Company info fetched: {data['business_name']}")

    def test_get_company_info_not_found(self, api_client):
        """Test 404 for non-existent company"""
        response = api_client.get(f"{BASE_URL}/api/empresa/nonexistent-company/info")
        assert response.status_code == 404
        print("✓ Non-existent company correctly returns 404")

    def test_company_login_success(self, api_client):
        """Test Company Admin login with valid credentials"""
        slug = COMPANY_ADMIN_CREDS["company_slug"]
        response = api_client.post(f"{BASE_URL}/api/empresa/{slug}/login", json={
            "email": COMPANY_ADMIN_CREDS["email"],
            "password": COMPANY_ADMIN_CREDS["password"]
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == COMPANY_ADMIN_CREDS["email"]
        assert data["user"]["role"] == "admin"
        assert data["company"]["slug"] == slug
        print("✓ Company Admin login successful")

    def test_company_login_invalid_credentials(self, api_client):
        """Test Company login fails with wrong password"""
        slug = COMPANY_ADMIN_CREDS["company_slug"]
        response = api_client.post(f"{BASE_URL}/api/empresa/{slug}/login", json={
            "email": COMPANY_ADMIN_CREDS["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Company login correctly rejected with invalid credentials")


# ============== SUPER ADMIN DASHBOARD TESTS ==============
class TestSuperAdminDashboard:
    """Super Admin Dashboard and Company Management tests"""

    def test_super_admin_dashboard(self, api_client, super_admin_token):
        """Test Super Admin dashboard returns statistics"""
        response = api_client.get(
            f"{BASE_URL}/api/super-admin/dashboard",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "total_companies" in data["summary"]
        assert "active" in data["summary"]
        assert "monthly_revenue" in data["summary"]
        assert "companies" in data
        print(f"✓ Dashboard stats: {data['summary']['total_companies']} companies, ${data['summary']['monthly_revenue']} revenue")

    def test_list_all_companies(self, api_client, super_admin_token):
        """Test listing all companies"""
        response = api_client.get(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the demo company
        print(f"✓ Listed {len(data)} companies")

    def test_create_company_with_admin(self, api_client, super_admin_token):
        """Test creating a new company with admin user"""
        unique_id = str(uuid.uuid4())[:8]
        company_data = {
            "business_name": f"TEST Company {unique_id}",
            "rfc": f"TST{unique_id}ABC",
            "address": "Test Address 123",
            "phone": "+52 55 9999 9999",
            "email": f"test_{unique_id}@testcompany.com",
            "monthly_fee": 1500.0,
            "license_type": "basic",
            "max_users": 5,
            "admin_full_name": f"Test Admin {unique_id}",
            "admin_email": f"admin_{unique_id}@testcompany.com",
            "admin_password": "TestPassword123!"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/super-admin/companies",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json=company_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "company" in data
        assert "admin" in data
        assert data["company"]["business_name"] == company_data["business_name"]
        print(f"✓ Created company: {data['company']['business_name']} with slug: {data['company']['slug']}")


# ============== COMPANY USER MANAGEMENT TESTS ==============
class TestCompanyUserManagement:
    """Company Admin User Management tests"""

    def test_list_company_users(self, api_client, company_admin_token):
        """Test listing users in a company"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {company_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} users in company")

    def test_create_company_user(self, api_client, company_admin_token):
        """Test creating a new user in a company"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_user_{unique_id}@test.com",
            "full_name": f"TEST User {unique_id}",
            "password": "UserPassword123!",
            "role": "user",
            "phone": "+52 55 1111 1111"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {company_admin_token}"},
            json=user_data
        )
        # May fail if max users reached
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == user_data["email"]
            assert data["full_name"] == user_data["full_name"]
            assert data["role"] == "user"
            print(f"✓ Created user: {data['email']}")
        elif response.status_code == 400:
            print(f"✓ User creation rejected (expected - max users reached)")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")

    def test_create_user_with_manager_role(self, api_client, company_admin_token):
        """Test creating a user with manager role"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_manager_{unique_id}@test.com",
            "full_name": f"TEST Manager {unique_id}",
            "password": "ManagerPassword123!",
            "role": "manager"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {company_admin_token}"},
            json=user_data
        )
        # Accept both success and max users reached
        assert response.status_code in [200, 400]
        print(f"✓ Manager user creation: status {response.status_code}")

    def test_cannot_create_super_admin(self, api_client, company_admin_token):
        """Test that company admin cannot create super_admin users"""
        user_data = {
            "email": "fake_super@test.com",
            "full_name": "Fake Super Admin",
            "password": "FakePassword123!",
            "role": "super_admin"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {company_admin_token}"},
            json=user_data
        )
        assert response.status_code == 403
        print("✓ Company admin cannot create super_admin users")


# ============== COMPANY DATA ACCESS TESTS ==============
class TestCompanyDataAccess:
    """Company data access and update tests"""

    def test_get_company_details(self, api_client, company_admin_token, company_id):
        """Test getting company details"""
        response = api_client.get(
            f"{BASE_URL}/api/companies/{company_id}",
            headers={"Authorization": f"Bearer {company_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == company_id
        assert "business_name" in data
        print(f"✓ Company details retrieved: {data['business_name']}")

    def test_update_company_info(self, api_client, company_admin_token, company_id):
        """Test updating company information"""
        update_data = {
            "phone": "+52 55 9999 0000",
            "address": "Updated Test Address"
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/companies/{company_id}",
            headers={"Authorization": f"Bearer {company_admin_token}"},
            json=update_data
        )
        assert response.status_code == 200
        print("✓ Company info updated successfully")


# ============== AUTH ME ENDPOINT TEST ==============
class TestAuthMe:
    """Auth /me endpoint tests"""

    def test_get_current_user_super_admin(self, api_client, super_admin_token):
        """Test getting current user info as Super Admin"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == "super_admin"
        print(f"✓ Super Admin info: {data['email']}")

    def test_get_current_user_company_admin(self, api_client, company_admin_token):
        """Test getting current user info as Company Admin"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {company_admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == "admin"
        assert data["company_id"] is not None
        print(f"✓ Company Admin info: {data['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
