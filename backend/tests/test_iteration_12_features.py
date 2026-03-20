"""
Test Iteration 12 Features:
1. Company logo with base64 prefix in company login page
2. Invoice custom fields (custom_field, custom_field_label) in backend model
3. PDF generation with custom field
4. App compilation without ProfitabilityReports.js errors
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestIteration12Features:
    """Test iteration 12 bug fixes and new features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for all tests"""
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Get auth token for company user
        self.token = None
        self.company_id = None
        
    def get_auth_token(self):
        """Get authentication token for demo company"""
        try:
            response = self.session.post(f"{self.base_url}/api/empresa/demo-test-sa-de-cv/login", json={
                "email": "admin@demo-test.com",
                "password": "Demo2024!"
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.company_id = data.get("company", {}).get("id")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
        except Exception as e:
            print(f"Auth failed: {e}")
        return False
    
    # Test 1: Company info endpoint returns logo_file field
    def test_company_info_returns_logo_file(self):
        """GET /api/empresa/{slug}/info should return logo_file with base64 data"""
        response = self.session.get(f"{self.base_url}/api/empresa/marisela-vazquez-garcia/info")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "id" in data, "Response should include company id"
        assert "business_name" in data, "Response should include business_name"
        assert "logo_file" in data or "logo_url" in data, "Response should include logo_file or logo_url"
        
        # If logo_file exists, it should be a base64 string (without the prefix)
        if data.get("logo_file"):
            logo = data["logo_file"]
            assert isinstance(logo, str), "logo_file should be a string"
            # The prefix is added in frontend, not backend
            assert len(logo) > 100, "logo_file should contain base64 data"
            print(f"SUCCESS: Company has logo_file with {len(logo)} chars of base64 data")
    
    # Test 2: Invoice model accepts custom_field and custom_field_label
    def test_invoice_model_has_custom_fields(self):
        """Invoice creation should accept custom_field and custom_field_label"""
        if not self.get_auth_token():
            pytest.skip("Could not authenticate")
        
        # Get existing clients
        clients_response = self.session.get(f"{self.base_url}/api/clients?company_id={self.company_id}")
        if clients_response.status_code != 200 or not clients_response.json():
            pytest.skip("No clients available for testing")
        
        clients = clients_response.json()
        client_id = clients[0]["id"]
        
        # Create invoice with custom fields
        invoice_data = {
            "company_id": self.company_id,
            "client_id": client_id,
            "invoice_number": f"FAC-TEST-{os.urandom(4).hex()}",
            "items": [
                {
                    "description": "Test item with custom field",
                    "quantity": 1,
                    "unit": "pza",
                    "unit_price": 100.00,
                    "total": 100.00
                }
            ],
            "subtotal": 100.00,
            "tax": 16.00,
            "total": 116.00,
            "custom_field_label": "Orden de Trabajo",
            "custom_field": "OT-2024-001"
        }
        
        response = self.session.post(f"{self.base_url}/api/invoices", json=invoice_data)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should include invoice id"
        
        # Verify custom fields were saved
        invoice_id = data["id"]
        get_response = self.session.get(f"{self.base_url}/api/invoices?company_id={self.company_id}")
        assert get_response.status_code == 200
        
        invoices = get_response.json()
        created_invoice = next((inv for inv in invoices if inv["id"] == invoice_id), None)
        
        if created_invoice:
            assert created_invoice.get("custom_field") == "OT-2024-001", "custom_field should be saved"
            assert created_invoice.get("custom_field_label") == "Orden de Trabajo", "custom_field_label should be saved"
            print("SUCCESS: Invoice custom fields saved correctly")
        
        # Cleanup - delete the test invoice
        self.session.delete(f"{self.base_url}/api/invoices/{invoice_id}")
    
    # Test 3: PDF generation endpoint works
    def test_pdf_invoice_generation(self):
        """GET /api/pdf/invoice/{id} should generate PDF"""
        if not self.get_auth_token():
            pytest.skip("Could not authenticate")
        
        # Get existing invoices
        invoices_response = self.session.get(f"{self.base_url}/api/invoices?company_id={self.company_id}")
        if invoices_response.status_code != 200 or not invoices_response.json():
            pytest.skip("No invoices available for testing PDF generation")
        
        invoices = invoices_response.json()
        invoice_id = invoices[0]["id"]
        
        # Request PDF
        response = self.session.get(f"{self.base_url}/api/pdf/invoice/{invoice_id}")
        assert response.status_code == 200, f"PDF generation failed: {response.status_code}"
        
        data = response.json()
        assert "filename" in data, "Response should include filename"
        assert "content" in data, "Response should include content (base64)"
        assert data["filename"].endswith(".pdf"), "Filename should have .pdf extension"
        assert len(data["content"]) > 1000, "PDF content should have substantial base64 data"
        
        print(f"SUCCESS: PDF generated with filename {data['filename']}")
    
    # Test 4: Health check - app compiles correctly
    def test_app_health(self):
        """Basic health check to ensure app is running without compilation errors"""
        # Test frontend is serving content
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            assert response.status_code == 200, "Frontend should return 200"
            assert "<!DOCTYPE html>" in response.text or "<!doctype html>" in response.text.lower(), "Should return HTML"
            print("SUCCESS: Frontend is running and serving content")
        except Exception as e:
            pytest.fail(f"Frontend health check failed: {e}")
    
    # Test 5: Company login page for marisela-vazquez-garcia works
    def test_company_login_page_exists(self):
        """Company login page should load for existing company"""
        response = self.session.get(f"{self.base_url}/api/empresa/marisela-vazquez-garcia/info")
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("business_name"), "Company should have business_name"
            assert data.get("slug") == "marisela-vazquez-garcia", "Slug should match"
            print(f"SUCCESS: Company '{data.get('business_name')}' exists and is accessible")
        elif response.status_code == 404:
            # Company doesn't exist in this DB (forked environment)
            print("INFO: Company 'marisela-vazquez-garcia' not found (expected in forked environment)")
            pytest.skip("Company not found in forked environment database")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
