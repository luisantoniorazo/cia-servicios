"""
Tests for CIA SERVICIOS new features (Iteration 4):
- Super Admin login without admin_key
- Quote to Invoice conversion
- Payment registration with proof
- Client account statement
- Overdue invoices tracking
- Project tasks CRUD
- User permissions update
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
COMPANY_SLUG = "cia-servicios-demo-sa-de-cv"

# Test client IDs provided in review request
TEST_CLIENT_ID_1 = "70d541c7-72cd-4a55-9606-2447132b202d"  # Grupo Industrial Monterrey
TEST_CLIENT_ID_2 = "cc07f103-c62e-4f45-bd33-f74dc29bb03a"  # Constructora Norte S.A.


@pytest.fixture(scope="session")
def super_admin_token():
    """Get Super Admin token via new login endpoint (no admin_key)"""
    response = requests.post(f"{BASE_URL}/api/super-admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Super Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="session")
def company_admin_token():
    """Get Company Admin token"""
    response = requests.post(f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login", json={
        "email": COMPANY_ADMIN_EMAIL,
        "password": COMPANY_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token"), data.get("company", {}).get("id")
    pytest.skip(f"Company Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def authenticated_admin_client(api_client, company_admin_token):
    """Session with Company Admin auth header"""
    token, company_id = company_admin_token
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    return api_client, company_id


# ============= SUPER ADMIN LOGIN TESTS =============
class TestSuperAdminLogin:
    """Tests for Super Admin login without admin_key"""
    
    def test_super_admin_login_success(self, api_client):
        """Super Admin can login with just email/password (no admin_key required)"""
        response = api_client.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["email"] == SUPER_ADMIN_EMAIL
        print("✓ Super Admin login SUCCESS without admin_key")
    
    def test_super_admin_login_invalid_credentials(self, api_client):
        """Super Admin login fails with wrong password"""
        response = api_client.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": "WrongPassword123"
        })
        assert response.status_code == 401
        print("✓ Super Admin login correctly rejects invalid credentials")
    
    def test_super_admin_login_non_super_admin_email(self, api_client):
        """Super Admin login fails for non-super-admin user"""
        response = api_client.post(f"{BASE_URL}/api/super-admin/login", json={
            "email": COMPANY_ADMIN_EMAIL,
            "password": COMPANY_ADMIN_PASSWORD
        })
        assert response.status_code == 401
        print("✓ Super Admin login correctly rejects non-super-admin users")


# ============= QUOTE TO INVOICE CONVERSION TESTS =============
class TestQuoteToInvoice:
    """Tests for Quote to Invoice conversion"""
    
    def test_convert_quote_to_invoice_requires_auth(self, api_client):
        """Quote conversion requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/quotes/fake-id/to-invoice")
        assert response.status_code in [401, 403]
        print("✓ Quote to Invoice requires authentication")
    
    def test_convert_non_authorized_quote_fails(self, authenticated_admin_client):
        """Can't convert a quote that isn't authorized status"""
        client, company_id = authenticated_admin_client
        
        # First get existing quotes
        quotes_response = client.get(f"{BASE_URL}/api/quotes?company_id={company_id}")
        if quotes_response.status_code != 200:
            pytest.skip("Could not fetch quotes")
        
        quotes = quotes_response.json()
        non_authorized = [q for q in quotes if q.get("status") != "authorized"]
        
        if non_authorized:
            quote = non_authorized[0]
            response = client.post(f"{BASE_URL}/api/quotes/{quote['id']}/to-invoice?due_days=30")
            assert response.status_code == 400, f"Expected 400 for non-authorized quote, got {response.status_code}"
            print(f"✓ Cannot convert non-authorized quote (status: {quote.get('status')})")
        else:
            print("✓ Skipped - no non-authorized quotes found to test")
    
    def test_convert_authorized_quote_creates_invoice(self, authenticated_admin_client):
        """Converting an authorized quote creates an invoice"""
        client, company_id = authenticated_admin_client
        
        # First, create a new quote
        quote_data = {
            "company_id": company_id,
            "client_id": TEST_CLIENT_ID_1,
            "quote_number": f"TEST-QTI-{datetime.now().strftime('%H%M%S')}",
            "title": "TEST Quote for Invoice Conversion",
            "description": "Test quote to be converted",
            "items": [{"description": "Test Item", "quantity": 2, "unit": "pza", "unit_price": 1000, "total": 2000}],
            "subtotal": 2000,
            "tax": 320,
            "total": 2320,
            "status": "authorized"  # Create as authorized
        }
        
        create_response = client.post(f"{BASE_URL}/api/quotes", json=quote_data)
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test quote: {create_response.text}")
        
        quote_id = create_response.json().get("id")
        
        # Now convert to invoice
        convert_response = client.post(f"{BASE_URL}/api/quotes/{quote_id}/to-invoice?due_days=30")
        assert convert_response.status_code == 200, f"Expected 200, got {convert_response.status_code}: {convert_response.text}"
        
        data = convert_response.json()
        assert "invoice_id" in data
        assert "invoice_number" in data
        assert data["invoice_number"].startswith("FAC-")
        print(f"✓ Quote converted to invoice: {data['invoice_number']}")
        
        # Verify quote status changed to 'invoiced'
        quote_response = client.get(f"{BASE_URL}/api/quotes/{quote_id}")
        if quote_response.status_code == 200:
            quote = quote_response.json()
            assert quote.get("status") == "invoiced", f"Expected 'invoiced', got {quote.get('status')}"
            print("✓ Quote status updated to 'invoiced'")
        
        # Clean up - delete the test invoice and quote
        if data.get("invoice_id"):
            client.delete(f"{BASE_URL}/api/invoices/{data['invoice_id']}")
        client.delete(f"{BASE_URL}/api/quotes/{quote_id}")


# ============= PAYMENT REGISTRATION TESTS =============
class TestPaymentRegistration:
    """Tests for Payment (Abono) registration with proof"""
    
    def test_payment_requires_auth(self, api_client):
        """Payment registration requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/payments", json={
            "company_id": "fake",
            "invoice_id": "fake",
            "client_id": "fake",
            "amount": 100,
            "payment_date": "2025-01-01",
            "payment_method": "transferencia"
        })
        assert response.status_code in [401, 403]
        print("✓ Payment registration requires authentication")
    
    def test_create_payment_updates_invoice(self, authenticated_admin_client):
        """Creating a payment updates invoice paid_amount"""
        client, company_id = authenticated_admin_client
        
        # First, create a test invoice
        invoice_data = {
            "company_id": company_id,
            "client_id": TEST_CLIENT_ID_1,
            "invoice_number": f"TEST-PAY-{datetime.now().strftime('%H%M%S')}",
            "concept": "TEST Invoice for Payment Testing",
            "subtotal": 10000,
            "tax": 1600,
            "total": 11600,
            "paid_amount": 0,
            "status": "pending",
            "due_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test invoice: {create_response.text}")
        
        invoice = create_response.json()
        invoice_id = invoice.get("id")
        
        # Create a partial payment
        payment_data = {
            "company_id": company_id,
            "invoice_id": invoice_id,
            "client_id": TEST_CLIENT_ID_1,
            "amount": 5000,
            "payment_date": datetime.now().isoformat(),
            "payment_method": "transferencia",
            "reference": "TEST-REF-001",
            "notes": "Test partial payment",
            "proof_file": None
        }
        
        payment_response = client.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert payment_response.status_code == 200, f"Payment failed: {payment_response.text}"
        
        data = payment_response.json()
        assert "payment_id" in data
        assert data.get("new_balance") == 6600  # 11600 - 5000
        print(f"✓ Payment created, new balance: {data.get('new_balance')}")
        
        # Verify invoice updated to partial status
        invoice_check = client.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        if invoice_check.status_code == 200:
            updated_invoice = invoice_check.json()
            assert updated_invoice.get("paid_amount") == 5000
            assert updated_invoice.get("status") == "partial"
            print("✓ Invoice updated to 'partial' status")
        
        # Clean up
        client.delete(f"{BASE_URL}/api/invoices/{invoice_id}")
    
    def test_full_payment_marks_invoice_paid(self, authenticated_admin_client):
        """Full payment marks invoice as paid"""
        client, company_id = authenticated_admin_client
        
        # Create a test invoice
        invoice_data = {
            "company_id": company_id,
            "client_id": TEST_CLIENT_ID_2,
            "invoice_number": f"TEST-FULL-{datetime.now().strftime('%H%M%S')}",
            "concept": "TEST Invoice for Full Payment",
            "subtotal": 1000,
            "tax": 160,
            "total": 1160,
            "paid_amount": 0,
            "status": "pending"
        }
        
        create_response = client.post(f"{BASE_URL}/api/invoices", json=invoice_data)
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test invoice: {create_response.text}")
        
        invoice_id = create_response.json().get("id")
        
        # Pay full amount
        payment_data = {
            "company_id": company_id,
            "invoice_id": invoice_id,
            "client_id": TEST_CLIENT_ID_2,
            "amount": 1160,
            "payment_date": datetime.now().isoformat(),
            "payment_method": "efectivo",
        }
        
        payment_response = client.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert payment_response.status_code == 200
        
        # Verify invoice status is 'paid'
        invoice_check = client.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        if invoice_check.status_code == 200:
            assert invoice_check.json().get("status") == "paid"
            print("✓ Full payment marks invoice as 'paid'")
        
        # Clean up
        client.delete(f"{BASE_URL}/api/invoices/{invoice_id}")


# ============= CLIENT STATEMENT TESTS =============
class TestClientStatement:
    """Tests for Client account statement"""
    
    def test_client_statement_requires_auth(self, api_client):
        """Client statement requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/clients/{TEST_CLIENT_ID_1}/statement")
        assert response.status_code in [401, 403]
        print("✓ Client statement requires authentication")
    
    def test_get_client_statement(self, authenticated_admin_client):
        """Get client account statement with invoices and payments"""
        client, company_id = authenticated_admin_client
        
        response = client.get(f"{BASE_URL}/api/clients/{TEST_CLIENT_ID_1}/statement")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "client" in data
        assert "summary" in data
        assert "invoices" in data
        assert "payments" in data
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_invoiced" in summary
        assert "total_paid" in summary
        assert "balance" in summary
        assert "overdue_count" in summary
        
        print(f"✓ Client statement retrieved: {data['client'].get('name')}")
        print(f"  - Total invoiced: ${summary.get('total_invoiced', 0):,.2f}")
        print(f"  - Balance: ${summary.get('balance', 0):,.2f}")
        print(f"  - Invoices: {len(data['invoices'])}, Payments: {len(data['payments'])}")
    
    def test_client_statement_404_for_invalid_client(self, authenticated_admin_client):
        """Client statement returns 404 for non-existent client"""
        client, _ = authenticated_admin_client
        response = client.get(f"{BASE_URL}/api/clients/non-existent-id-12345/statement")
        assert response.status_code == 404
        print("✓ Client statement returns 404 for invalid client")


# ============= OVERDUE INVOICES TESTS =============
class TestOverdueInvoices:
    """Tests for Overdue invoices tracking"""
    
    def test_overdue_invoices_requires_auth(self, api_client):
        """Overdue invoices endpoint requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/invoices/overdue?company_id=fake")
        assert response.status_code in [401, 403]
        print("✓ Overdue invoices requires authentication")
    
    def test_get_overdue_invoices(self, authenticated_admin_client):
        """Get overdue and upcoming invoices"""
        client, company_id = authenticated_admin_client
        
        response = client.get(f"{BASE_URL}/api/invoices/overdue?company_id={company_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "overdue" in data
        assert "upcoming" in data
        assert "total_overdue_amount" in data
        
        print(f"✓ Overdue invoices retrieved:")
        print(f"  - Overdue count: {len(data['overdue'])}")
        print(f"  - Upcoming count: {len(data['upcoming'])}")
        print(f"  - Total overdue amount: ${data['total_overdue_amount']:,.2f}")
        
        # Verify overdue invoices have days_overdue field
        if data['overdue']:
            assert "days_overdue" in data['overdue'][0]
            print(f"  - First overdue: {data['overdue'][0].get('invoice_number')} ({data['overdue'][0].get('days_overdue')} days)")


# ============= PROJECT TASKS TESTS =============
class TestProjectTasks:
    """Tests for Project tasks CRUD"""
    
    def test_project_tasks_requires_auth(self, api_client):
        """Project tasks endpoint requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/projects/fake-id/tasks")
        assert response.status_code in [401, 403]
        print("✓ Project tasks requires authentication")
    
    def test_create_and_list_project_tasks(self, authenticated_admin_client):
        """Create and list tasks for a project"""
        client, company_id = authenticated_admin_client
        
        # Get existing projects
        projects_response = client.get(f"{BASE_URL}/api/projects?company_id={company_id}")
        if projects_response.status_code != 200:
            pytest.skip("Could not fetch projects")
        
        projects = projects_response.json()
        if not projects:
            pytest.skip("No projects to test tasks with")
        
        project = projects[0]
        project_id = project["id"]
        
        # Create a task
        task_data = {
            "project_id": project_id,
            "company_id": company_id,
            "name": f"TEST Task {datetime.now().strftime('%H%M%S')}",
            "description": "Test task for automation testing",
            "estimated_hours": 8.0,
            "estimated_cost": 2500.00,
            "status": "pending",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        create_response = client.post(f"{BASE_URL}/api/projects/{project_id}/tasks", json=task_data)
        assert create_response.status_code == 200, f"Task creation failed: {create_response.text}"
        
        task = create_response.json()
        assert task.get("name") == task_data["name"]
        assert task.get("estimated_hours") == 8.0
        task_id = task.get("id")
        print(f"✓ Task created: {task['name']}")
        
        # List tasks
        list_response = client.get(f"{BASE_URL}/api/projects/{project_id}/tasks")
        assert list_response.status_code == 200
        tasks = list_response.json()
        assert any(t["id"] == task_id for t in tasks)
        print(f"✓ Task appears in project task list ({len(tasks)} tasks total)")
        
        # Clean up
        client.delete(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}")
    
    def test_update_task_status(self, authenticated_admin_client):
        """Update task status"""
        client, company_id = authenticated_admin_client
        
        # Get existing projects and create a task
        projects_response = client.get(f"{BASE_URL}/api/projects?company_id={company_id}")
        if projects_response.status_code != 200 or not projects_response.json():
            pytest.skip("No projects available")
        
        project_id = projects_response.json()[0]["id"]
        
        # Create task
        task_data = {
            "project_id": project_id,
            "company_id": company_id,
            "name": f"TEST Status Update {datetime.now().strftime('%H%M%S')}",
            "status": "pending"
        }
        create_response = client.post(f"{BASE_URL}/api/projects/{project_id}/tasks", json=task_data)
        if create_response.status_code != 200:
            pytest.skip("Could not create task")
        
        task_id = create_response.json().get("id")
        
        # Update status to in_progress
        update_response = client.put(
            f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}",
            json={"status": "in_progress"}
        )
        assert update_response.status_code == 200
        
        # Verify update
        task_check = client.get(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}")
        if task_check.status_code == 200:
            assert task_check.json().get("status") == "in_progress"
            print("✓ Task status updated to 'in_progress'")
        
        # Clean up
        client.delete(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}")
    
    def test_delete_task(self, authenticated_admin_client):
        """Delete a project task"""
        client, company_id = authenticated_admin_client
        
        projects_response = client.get(f"{BASE_URL}/api/projects?company_id={company_id}")
        if projects_response.status_code != 200 or not projects_response.json():
            pytest.skip("No projects available")
        
        project_id = projects_response.json()[0]["id"]
        
        # Create task
        task_data = {
            "project_id": project_id,
            "company_id": company_id,
            "name": f"TEST Delete Task {datetime.now().strftime('%H%M%S')}",
            "status": "pending"
        }
        create_response = client.post(f"{BASE_URL}/api/projects/{project_id}/tasks", json=task_data)
        if create_response.status_code != 200:
            pytest.skip("Could not create task")
        
        task_id = create_response.json().get("id")
        
        # Delete task
        delete_response = client.delete(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        verify_response = client.get(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}")
        assert verify_response.status_code == 404
        print("✓ Task deleted successfully")


# ============= USER PERMISSIONS TESTS =============
class TestUserPermissions:
    """Tests for User module permissions"""
    
    def test_permissions_update_requires_admin(self, api_client):
        """User permissions update requires admin role"""
        response = api_client.put(f"{BASE_URL}/api/admin/users/fake-id/permissions", json=["dashboard"])
        assert response.status_code in [401, 403]
        print("✓ User permissions update requires authentication")
    
    def test_update_user_permissions(self, authenticated_admin_client):
        """Update user module permissions"""
        client, company_id = authenticated_admin_client
        
        # Get users
        users_response = client.get(f"{BASE_URL}/api/admin/users")
        if users_response.status_code != 200:
            pytest.skip("Could not fetch users")
        
        users = users_response.json()
        # Find a non-admin user
        non_admin_users = [u for u in users if u.get("role") != "admin"]
        
        if not non_admin_users:
            # Create a test user
            test_user_data = {
                "email": f"test_perm_{datetime.now().strftime('%H%M%S')}@test.com",
                "full_name": "TEST Permission User",
                "password": "TestPass123!",
                "role": "user"
            }
            create_response = client.post(f"{BASE_URL}/api/admin/users", json=test_user_data)
            if create_response.status_code != 200:
                pytest.skip("Could not create test user")
            user = create_response.json()
            user_id = user.get("id")
            created_user = True
        else:
            user = non_admin_users[0]
            user_id = user.get("id")
            created_user = False
        
        # Update permissions
        new_permissions = ["dashboard", "projects", "invoices"]
        update_response = client.put(
            f"{BASE_URL}/api/admin/users/{user_id}/permissions",
            json=new_permissions
        )
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        data = update_response.json()
        assert data.get("permissions") == new_permissions
        print(f"✓ User permissions updated: {new_permissions}")
        
        # Clean up if we created a test user
        if created_user:
            client.delete(f"{BASE_URL}/api/admin/users/{user_id}")


# ============= PAYMENTS LIST TESTS =============
class TestPaymentsList:
    """Tests for listing payments"""
    
    def test_list_payments_by_company(self, authenticated_admin_client):
        """List all payments for a company"""
        client, company_id = authenticated_admin_client
        
        response = client.get(f"{BASE_URL}/api/payments?company_id={company_id}")
        assert response.status_code == 200
        
        payments = response.json()
        assert isinstance(payments, list)
        print(f"✓ Retrieved {len(payments)} payments for company")
    
    def test_list_payments_by_client(self, authenticated_admin_client):
        """List payments filtered by client"""
        client, company_id = authenticated_admin_client
        
        response = client.get(f"{BASE_URL}/api/payments?company_id={company_id}&client_id={TEST_CLIENT_ID_1}")
        assert response.status_code == 200
        
        payments = response.json()
        assert isinstance(payments, list)
        print(f"✓ Retrieved {len(payments)} payments for client {TEST_CLIENT_ID_1}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
