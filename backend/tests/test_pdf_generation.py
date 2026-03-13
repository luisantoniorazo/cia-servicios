"""
Test suite for PDF generation and automatic totals calculation.
Features tested:
- Quote PDF generation with professional format
- Purchase order PDF generation with professional format
- Automatic calculation of totals (subtotal, tax, total) when creating quotes
- Automatic calculation of totals when creating purchase orders
"""

import pytest
import requests
import os
import base64
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
COMPANY_SLUG = "cia-servicios-demo-sa-de-cv"
ADMIN_EMAIL = "gerente@ciademo.com"
ADMIN_PASSWORD = "Admin2024!"
TEST_CLIENT_ID = "44d9c2ee-759b-496c-9b7a-987ea4ee24b0"
TEST_SUPPLIER_ID = "53aa2bab-cfc7-48ba-9dbe-086afd5bc551"
COMPANY_ID = "f9e9dd31-88c9-4b30-ad0a-a55cff810bcf"


class TestAuthentication:
    """Test authentication for company admin"""
    
    def test_company_login(self):
        """Test company admin login"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✅ Login successful for {ADMIN_EMAIL}")
        return data["access_token"]


class TestQuoteTotalsCalculation:
    """Test automatic calculation of quote totals"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_create_quote_auto_calculates_totals(self, auth_token):
        """Test that creating a quote automatically calculates subtotal, tax, and total"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create quote with items that have unit_price and quantity
        quote_data = {
            "company_id": COMPANY_ID,
            "client_id": TEST_CLIENT_ID,
            "quote_number": f"TEST-Q-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": "Test Quote for Auto-Calculation",
            "description": "Testing automatic totals calculation with long description text that should wrap properly in the PDF without being cut off or overlapping other cells. This is an important test for the auto-adjusting cell feature.",
            "items": [
                {"description": "Service A - Web Development with responsive design", "quantity": 2, "unit": "hrs", "unit_price": 500.00},
                {"description": "Service B - Database optimization and performance tuning with extended support and maintenance", "quantity": 3, "unit": "hrs", "unit_price": 750.00},
                {"description": "Material C", "quantity": 1, "unit": "pza", "unit_price": 1000.00}
            ],
            "subtotal": 0,  # Should be calculated automatically
            "tax": 0,       # Should be calculated automatically
            "total": 0,     # Should be calculated automatically
            "show_tax": True,
            "status": "prospect"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=quote_data,
            headers=headers
        )
        assert response.status_code == 200, f"Create quote failed: {response.text}"
        
        data = response.json()
        
        # Verify automatic calculation
        # Expected: Item1 = 2*500 = 1000, Item2 = 3*750 = 2250, Item3 = 1*1000 = 1000
        # Subtotal = 4250, Tax (16%) = 680, Total = 4930
        expected_subtotal = 4250.0
        expected_tax = 680.0
        expected_total = 4930.0
        
        assert abs(data["subtotal"] - expected_subtotal) < 0.01, f"Subtotal mismatch: {data['subtotal']} != {expected_subtotal}"
        assert abs(data["tax"] - expected_tax) < 0.01, f"Tax mismatch: {data['tax']} != {expected_tax}"
        assert abs(data["total"] - expected_total) < 0.01, f"Total mismatch: {data['total']} != {expected_total}"
        
        # Verify item totals are calculated
        for item in data["items"]:
            expected_item_total = item["quantity"] * item["unit_price"]
            assert abs(item["total"] - expected_item_total) < 0.01, f"Item total mismatch for {item['description']}"
        
        print(f"✅ Quote created with auto-calculated totals: subtotal={data['subtotal']}, tax={data['tax']}, total={data['total']}")
        return data["id"]
    
    def test_create_quote_without_tax(self, auth_token):
        """Test quote creation with show_tax=False"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        quote_data = {
            "company_id": COMPANY_ID,
            "client_id": TEST_CLIENT_ID,
            "quote_number": f"TEST-QNT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": "Test Quote Without Tax",
            "items": [
                {"description": "Consulting services", "quantity": 5, "unit": "hrs", "unit_price": 200.00}
            ],
            "show_tax": False,
            "status": "prospect"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=quote_data,
            headers=headers
        )
        assert response.status_code == 200, f"Create quote failed: {response.text}"
        
        data = response.json()
        expected_subtotal = 1000.0
        
        assert abs(data["subtotal"] - expected_subtotal) < 0.01
        assert data["tax"] == 0, f"Tax should be 0 when show_tax=False, got {data['tax']}"
        assert abs(data["total"] - expected_subtotal) < 0.01
        
        print(f"✅ Quote without tax created: subtotal={data['subtotal']}, tax={data['tax']}, total={data['total']}")


class TestPurchaseOrderTotalsCalculation:
    """Test automatic calculation of purchase order totals"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_create_purchase_order_auto_calculates_totals(self, auth_token):
        """Test that creating a purchase order automatically calculates subtotal, tax, and total"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        po_data = {
            "company_id": COMPANY_ID,
            "supplier_id": TEST_SUPPLIER_ID,
            "order_number": f"TEST-PO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Test Purchase Order for Auto-Calculation with a very long description that tests the auto-adjusting cell feature in PDF generation. This description should wrap nicely in the PDF without being truncated.",
            "items": [
                {"description": "Material A - Construction materials including cement, sand, and gravel for foundation work", "quantity": 10, "unit": "kg", "unit_price": 50.00},
                {"description": "Equipment B", "quantity": 2, "unit": "pza", "unit_price": 1500.00},
                {"description": "Hardware C - Industrial grade bolts, nuts, and washers for structural assembly", "quantity": 100, "unit": "pza", "unit_price": 5.00}
            ],
            "status": "requested"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/purchase-orders",
            json=po_data,
            headers=headers
        )
        assert response.status_code == 200, f"Create PO failed: {response.text}"
        
        data = response.json()
        
        # Expected: Item1 = 10*50 = 500, Item2 = 2*1500 = 3000, Item3 = 100*5 = 500
        # Subtotal = 4000, Tax (16%) = 640, Total = 4640
        expected_subtotal = 4000.0
        expected_tax = 640.0
        expected_total = 4640.0
        
        assert abs(data["subtotal"] - expected_subtotal) < 0.01, f"Subtotal mismatch: {data['subtotal']} != {expected_subtotal}"
        assert abs(data["tax"] - expected_tax) < 0.01, f"Tax mismatch: {data['tax']} != {expected_tax}"
        assert abs(data["total"] - expected_total) < 0.01, f"Total mismatch: {data['total']} != {expected_total}"
        
        print(f"✅ Purchase Order created with auto-calculated totals: subtotal={data['subtotal']}, tax={data['tax']}, total={data['total']}")
        return data["id"]


class TestQuotePDFGeneration:
    """Test Quote PDF generation endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_generate_quote_pdf(self, auth_token):
        """Test PDF generation for a quote"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a quote
        quote_data = {
            "company_id": COMPANY_ID,
            "client_id": TEST_CLIENT_ID,
            "quote_number": f"TEST-PDF-Q-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": "Test Quote for PDF Generation",
            "description": "This is a comprehensive test to verify that the professional PDF format works correctly with auto-adjusting cells for long text content.",
            "items": [
                {"description": "Professional Web Development Services including frontend and backend development with responsive design implementation across multiple devices and browsers", "quantity": 40, "unit": "hrs", "unit_price": 150.00},
                {"description": "UI/UX Design - Complete design system creation including wireframes, mockups, and interactive prototypes for web and mobile applications", "quantity": 20, "unit": "hrs", "unit_price": 120.00}
            ],
            "show_tax": True,
            "status": "prospect"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=quote_data,
            headers=headers
        )
        assert create_response.status_code == 200, f"Create quote failed: {create_response.text}"
        quote_id = create_response.json()["id"]
        
        # Now generate PDF
        pdf_response = requests.get(
            f"{BASE_URL}/api/pdf/quote/{quote_id}",
            headers=headers
        )
        assert pdf_response.status_code == 200, f"PDF generation failed: {pdf_response.text}"
        
        pdf_data = pdf_response.json()
        assert "filename" in pdf_data
        assert "content" in pdf_data
        assert "content_type" in pdf_data
        assert pdf_data["content_type"] == "application/pdf"
        assert pdf_data["filename"].endswith(".pdf")
        
        # Verify it's valid base64 encoded PDF
        try:
            decoded = base64.b64decode(pdf_data["content"])
            # Check PDF header signature
            assert decoded[:4] == b'%PDF', "Invalid PDF file header"
            print(f"✅ Quote PDF generated successfully: {pdf_data['filename']} ({len(decoded)} bytes)")
        except Exception as e:
            pytest.fail(f"Failed to decode PDF content: {e}")
        
        return quote_id


class TestPurchaseOrderPDFGeneration:
    """Test Purchase Order PDF generation endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_generate_purchase_order_pdf(self, auth_token):
        """Test PDF generation for a purchase order"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a purchase order
        po_data = {
            "company_id": COMPANY_ID,
            "supplier_id": TEST_SUPPLIER_ID,
            "order_number": f"TEST-PDF-PO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Test Purchase Order for PDF Generation - Industrial materials and equipment for construction project phase 1",
            "items": [
                {"description": "Premium quality construction steel bars - Grade 60 reinforcement steel for structural foundations with corrosion-resistant coating", "quantity": 50, "unit": "ton", "unit_price": 800.00},
                {"description": "Industrial cement bags - Portland Type I/II for general construction purposes with enhanced workability", "quantity": 200, "unit": "bags", "unit_price": 15.00}
            ],
            "status": "requested"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/purchase-orders",
            json=po_data,
            headers=headers
        )
        assert create_response.status_code == 200, f"Create PO failed: {create_response.text}"
        po_id = create_response.json()["id"]
        
        # Now generate PDF
        pdf_response = requests.get(
            f"{BASE_URL}/api/pdf/purchase-order/{po_id}",
            headers=headers
        )
        assert pdf_response.status_code == 200, f"PDF generation failed: {pdf_response.text}"
        
        pdf_data = pdf_response.json()
        assert "filename" in pdf_data
        assert "content" in pdf_data
        assert "content_type" in pdf_data
        assert pdf_data["content_type"] == "application/pdf"
        assert pdf_data["filename"].endswith(".pdf")
        
        # Verify it's valid base64 encoded PDF
        try:
            decoded = base64.b64decode(pdf_data["content"])
            assert decoded[:4] == b'%PDF', "Invalid PDF file header"
            print(f"✅ Purchase Order PDF generated successfully: {pdf_data['filename']} ({len(decoded)} bytes)")
        except Exception as e:
            pytest.fail(f"Failed to decode PDF content: {e}")
        
        return po_id


class TestExistingQuotePDF:
    """Test PDF generation for existing quotes"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_existing_quotes_and_generate_pdf(self, auth_token):
        """Test PDF generation for existing quotes in the system"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get list of quotes
        response = requests.get(
            f"{BASE_URL}/api/quotes?company_id={COMPANY_ID}",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get quotes: {response.text}"
        
        quotes = response.json()
        if not quotes:
            pytest.skip("No existing quotes found")
        
        # Test PDF generation for the first quote
        quote = quotes[0]
        quote_id = quote["id"]
        
        pdf_response = requests.get(
            f"{BASE_URL}/api/pdf/quote/{quote_id}",
            headers=headers
        )
        assert pdf_response.status_code == 200, f"PDF generation failed for quote {quote_id}: {pdf_response.text}"
        
        pdf_data = pdf_response.json()
        decoded = base64.b64decode(pdf_data["content"])
        assert decoded[:4] == b'%PDF'
        print(f"✅ Existing quote PDF generated: {quote['quote_number']} - {pdf_data['filename']}")


class TestExistingPurchaseOrderPDF:
    """Test PDF generation for existing purchase orders"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_existing_pos_and_generate_pdf(self, auth_token):
        """Test PDF generation for existing purchase orders in the system"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get list of purchase orders
        response = requests.get(
            f"{BASE_URL}/api/purchase-orders?company_id={COMPANY_ID}",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get POs: {response.text}"
        
        pos = response.json()
        if not pos:
            pytest.skip("No existing purchase orders found")
        
        # Test PDF generation for the first PO
        po = pos[0]
        po_id = po["id"]
        
        pdf_response = requests.get(
            f"{BASE_URL}/api/pdf/purchase-order/{po_id}",
            headers=headers
        )
        assert pdf_response.status_code == 200, f"PDF generation failed for PO {po_id}: {pdf_response.text}"
        
        pdf_data = pdf_response.json()
        decoded = base64.b64decode(pdf_data["content"])
        assert decoded[:4] == b'%PDF'
        print(f"✅ Existing PO PDF generated: {po['order_number']} - {pdf_data['filename']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
