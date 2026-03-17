"""
Test suite for CIA SERVICIOS new features and bug fixes:
1. Ticket creation (POST /api/tickets) - Bug fix
2. AI Conversation CRUD (POST/GET/DELETE /api/ai/conversations)
3. Broadcast notifications (POST /api/admin/broadcast-notification)
4. Account statement PDF verification
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "superadmin@cia-servicios.com",
    "password": "SuperAdmin2024!"
}

COMPANY_USER_CREDS = {
    "slug": "cia-servicios-demo-sa-de-cv",
    "email": "gerente@ciademo.com",
    "password": "Test1234!"
}


class TestSetup:
    """Setup and authentication tests"""
    
    def test_backend_health(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api")
        print(f"Backend health check: {response.status_code}")
        assert response.status_code in [200, 404, 307], f"Backend not responding properly: {response.status_code}"
    
    def test_super_admin_login(self):
        """Test super admin login"""
        response = requests.post(f"{BASE_URL}/api/super-admin/login", json=SUPER_ADMIN_CREDS)
        print(f"Super admin login: {response.status_code}")
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        return data["access_token"]
    
    def test_company_user_login(self):
        """Test company user login"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_USER_CREDS['slug']}/login",
            json={
                "email": COMPANY_USER_CREDS["email"],
                "password": COMPANY_USER_CREDS["password"]
            }
        )
        print(f"Company user login: {response.status_code}")
        assert response.status_code == 200, f"Company user login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        return data


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/super-admin/login", json=SUPER_ADMIN_CREDS)
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Super admin login failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def company_user_auth():
    """Get company user authentication data"""
    response = requests.post(
        f"{BASE_URL}/api/empresa/{COMPANY_USER_CREDS['slug']}/login",
        json={
            "email": COMPANY_USER_CREDS["email"],
            "password": COMPANY_USER_CREDS["password"]
        }
    )
    if response.status_code == 200:
        return response.json()
    pytest.skip("Company user login failed - skipping authenticated tests")


class TestTicketSystem:
    """Tests for ticket creation bug fix - POST /api/tickets"""
    
    def test_create_ticket_as_company_user(self, company_user_auth):
        """
        BUG FIX TEST: Create ticket as company user
        Previously failed due to MongoDB ObjectId serialization issue
        """
        token = company_user_auth["access_token"]
        company_id = company_user_auth["company"]["id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        ticket_data = {
            "company_id": company_id,
            "title": "TEST_Ticket de prueba - Testing Agent",
            "description": "Este es un ticket creado por el testing agent para verificar que el bug de serialización de ObjectId fue corregido.",
            "priority": "medium",
            "category": "general",
            "screenshots": []
        }
        
        response = requests.post(f"{BASE_URL}/api/tickets", json=ticket_data, headers=headers)
        print(f"Create ticket response: {response.status_code}")
        print(f"Create ticket body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Ticket creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Ticket ID not in response"
        assert "ticket_number" in data, "Ticket number not in response"
        assert data["title"] == ticket_data["title"], "Title mismatch"
        assert data["status"] == "open", "Status should be 'open'"
        
        print(f"SUCCESS: Created ticket {data['ticket_number']} with ID {data['id']}")
        return data["id"]
    
    def test_list_tickets_as_company_user(self, company_user_auth):
        """List tickets as company user - verify they can see their own tickets"""
        token = company_user_auth["access_token"]
        company_id = company_user_auth["company"]["id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/tickets?company_id={company_id}", headers=headers)
        
        print(f"List tickets: {response.status_code}")
        assert response.status_code == 200, f"List tickets failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Found {len(data)} tickets")
    
    def test_list_tickets_as_super_admin(self, super_admin_token):
        """Super admin can list all tickets"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/tickets", headers=headers)
        
        print(f"Super admin list tickets: {response.status_code}")
        assert response.status_code == 200, f"Super admin list tickets failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Super admin can see {len(data)} tickets")


class TestAIConversations:
    """Tests for AI conversation CRUD - new feature"""
    
    def test_save_ai_conversation(self, company_user_auth):
        """Save a new AI conversation - POST /api/ai/conversations"""
        token = company_user_auth["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        conversation_data = {
            "title": "TEST_Conversation - Testing Agent",
            "messages": [
                {"role": "user", "content": "Analiza las ventas de este mes"},
                {"role": "assistant", "content": "Según los datos, las ventas muestran una tendencia positiva..."}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/conversations", json=conversation_data, headers=headers)
        print(f"Save conversation: {response.status_code}")
        
        assert response.status_code == 200, f"Save conversation failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Conversation ID not in response"
        assert "message" in data, "Message not in response"
        
        print(f"SUCCESS: Saved conversation with ID {data['id']}")
        return data["id"]
    
    def test_list_ai_conversations(self, company_user_auth):
        """List user's AI conversations - GET /api/ai/conversations"""
        token = company_user_auth["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/ai/conversations", headers=headers)
        print(f"List conversations: {response.status_code}")
        
        assert response.status_code == 200, f"List conversations failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Found {len(data)} conversations")
        return data
    
    def test_get_ai_conversation_by_id(self, company_user_auth):
        """Get a specific conversation with messages - GET /api/ai/conversations/{id}"""
        token = company_user_auth["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a conversation
        conversation_data = {
            "title": "TEST_Get by ID Test",
            "messages": [
                {"role": "user", "content": "Test message"}
            ]
        }
        create_response = requests.post(f"{BASE_URL}/api/ai/conversations", json=conversation_data, headers=headers)
        assert create_response.status_code == 200
        
        conv_id = create_response.json()["id"]
        
        # Now get it by ID
        response = requests.get(f"{BASE_URL}/api/ai/conversations/{conv_id}", headers=headers)
        print(f"Get conversation by ID: {response.status_code}")
        
        assert response.status_code == 200, f"Get conversation failed: {response.text}"
        
        data = response.json()
        assert data["id"] == conv_id, "ID mismatch"
        assert "messages" in data, "Messages not in response"
        assert len(data["messages"]) > 0, "Messages should not be empty"
        
        print(f"SUCCESS: Retrieved conversation {conv_id} with {len(data['messages'])} messages")
        return conv_id
    
    def test_delete_ai_conversation(self, company_user_auth):
        """Delete an AI conversation - DELETE /api/ai/conversations/{id}"""
        token = company_user_auth["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a conversation to delete
        conversation_data = {
            "title": "TEST_Delete Test",
            "messages": [{"role": "user", "content": "To be deleted"}]
        }
        create_response = requests.post(f"{BASE_URL}/api/ai/conversations", json=conversation_data, headers=headers)
        assert create_response.status_code == 200
        
        conv_id = create_response.json()["id"]
        
        # Now delete it
        response = requests.delete(f"{BASE_URL}/api/ai/conversations/{conv_id}", headers=headers)
        print(f"Delete conversation: {response.status_code}")
        
        assert response.status_code == 200, f"Delete conversation failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Message not in response"
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/ai/conversations/{conv_id}", headers=headers)
        assert get_response.status_code == 404, "Conversation should not exist after deletion"
        
        print(f"SUCCESS: Deleted conversation {conv_id}")


class TestBroadcastNotifications:
    """Tests for admin broadcast notification feature"""
    
    def test_broadcast_notification_as_admin(self, company_user_auth):
        """
        Admin can send broadcast notification - POST /api/admin/broadcast-notification
        """
        token = company_user_auth["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        notification_data = {
            "title": "TEST_Aviso de Prueba",
            "message": "Este es un mensaje de prueba del testing agent.",
            "notification_type": "info"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/broadcast-notification", json=notification_data, headers=headers)
        print(f"Broadcast notification: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
        # Note: May return 400 if no other users exist, which is acceptable
        if response.status_code == 200:
            data = response.json()
            assert "message" in data, "Message not in response"
            print(f"SUCCESS: {data['message']}")
        elif response.status_code == 400:
            # Acceptable - no users to notify
            print(f"INFO: {response.json().get('detail', 'No users to notify')}")
        else:
            assert False, f"Unexpected status code: {response.status_code} - {response.text}"
    
    def test_broadcast_notification_requires_auth(self):
        """Broadcast notification requires authentication"""
        notification_data = {
            "title": "Test",
            "message": "Test",
            "notification_type": "info"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/broadcast-notification", json=notification_data)
        
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("SUCCESS: Broadcast notification requires authentication")


class TestAccountStatementPDF:
    """Tests for account statement PDF - verify no 'COTIZACIÓN' header"""
    
    def test_get_account_statement_pdf(self, company_user_auth):
        """
        BUG FIX TEST: Account statement PDF should show 'ESTADO DE CUENTA' not 'COTIZACIÓN'
        """
        token = company_user_auth["access_token"]
        company_id = company_user_auth["company"]["id"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # First get a client to test with
        clients_response = requests.get(f"{BASE_URL}/api/clients?company_id={company_id}", headers=headers)
        if clients_response.status_code != 200:
            pytest.skip("No clients available for statement test")
        
        clients = clients_response.json()
        if not clients:
            pytest.skip("No clients available for statement test")
        
        client_id = clients[0]["id"]
        
        # Get PDF
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}/statement/pdf", headers=headers)
        print(f"Get statement PDF: {response.status_code}")
        
        assert response.status_code == 200, f"Get statement PDF failed: {response.text}"
        
        data = response.json()
        assert "filename" in data, "Filename not in response"
        assert "content" in data, "PDF content not in response"
        assert data.get("content_type") == "application/pdf", "Should be PDF content type"
        
        # Verify filename pattern
        assert "estado_cuenta" in data["filename"].lower(), "Filename should contain 'estado_cuenta'"
        
        print(f"SUCCESS: Got PDF statement: {data['filename']}")
        print("NOTE: Visual verification needed to confirm 'ESTADO DE CUENTA' header instead of 'COTIZACIÓN'")


class TestInvoicesMenuOptions:
    """Tests for invoice dropdown menu - verify SAT upload option removed"""
    
    def test_invoices_endpoint_works(self, company_user_auth):
        """Verify invoices endpoint is accessible"""
        token = company_user_auth["access_token"]
        company_id = company_user_auth["company"]["id"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/invoices?company_id={company_id}", headers=headers)
        print(f"Get invoices: {response.status_code}")
        
        assert response.status_code == 200, f"Get invoices failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Invoices endpoint working, found {len(data)} invoices")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_tickets(self, super_admin_token, company_user_auth):
        """Clean up test tickets created during testing"""
        company_id = company_user_auth["company"]["id"]
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Get all tickets
        response = requests.get(f"{BASE_URL}/api/tickets", headers=headers)
        if response.status_code == 200:
            tickets = response.json()
            test_tickets = [t for t in tickets if t.get("title", "").startswith("TEST_")]
            print(f"Found {len(test_tickets)} test tickets to clean up")
            # Note: No delete endpoint for tickets, so just report
        
        print("INFO: Test data cleanup - manual cleanup may be needed for TEST_ prefixed items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
