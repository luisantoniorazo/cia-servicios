"""
CIA SERVICIOS - New Features Test Suite
Tests: AI Integration (GPT-5.2), PDF Generation (Quotes/Invoices), File Upload/Download
"""

import pytest
import requests
import os
import base64
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============== TEST CREDENTIALS ==============
COMPANY_ADMIN_CREDS = {
    "email": "gerente@ciademo.com",
    "password": "Admin2024!",
    "company_slug": "cia-servicios-demo-sa-de-cv"
}

# Test data IDs provided
TEST_QUOTE_ID = "c81d4493-e779-455b-9f3e-2592e9cfe7ef"
TEST_INVOICE_ID = "d0c88d06-f4f1-4502-9dbf-4019d2621f7e"


# ============== FIXTURES ==============
@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


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
def auth_headers(company_admin_token):
    """Authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {company_admin_token}"}


@pytest.fixture(scope="module")
def company_id(api_client, company_admin_token):
    """Get the company ID from the user's token"""
    response = api_client.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {company_admin_token}"}
    )
    if response.status_code == 200:
        return response.json().get("company_id")
    return None


# ============== AI INTEGRATION TESTS ==============
class TestAIChatIntegration:
    """AI Chat endpoint tests - POST /api/ai/chat"""

    def test_ai_chat_basic_message(self, api_client, auth_headers):
        """Test AI chat with a simple business question"""
        response = api_client.post(
            f"{BASE_URL}/api/ai/chat",
            headers=auth_headers,
            json={
                "message": "¿Cuál es el estado financiero actual de la empresa?",
                "context": "Análisis financiero"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert "model" in data, "Response should contain 'model' field"
        assert data["model"] == "gpt-5.2", f"Expected model gpt-5.2, got {data['model']}"
        assert len(data["response"]) > 0, "AI response should not be empty"
        print(f"✓ AI Chat response received (length: {len(data['response'])} chars)")

    def test_ai_chat_financial_analysis(self, api_client, auth_headers):
        """Test AI chat for financial analysis prompt"""
        response = api_client.post(
            f"{BASE_URL}/api/ai/chat",
            headers=auth_headers,
            json={
                "message": "Dame un resumen de facturación y cobranza",
                "context": ""
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 50, "Financial analysis should be substantial"
        print("✓ AI financial analysis works correctly")

    def test_ai_chat_without_auth_fails(self, api_client):
        """Test AI chat requires authentication"""
        response = api_client.post(
            f"{BASE_URL}/api/ai/chat",
            json={"message": "test", "context": ""}
        )
        assert response.status_code in [401, 403], "Unauthenticated request should fail"
        print("✓ AI chat correctly requires authentication")


class TestAIProjectAnalysis:
    """AI Project Analysis endpoint tests - POST /api/ai/analyze-project/{project_id}"""

    def test_ai_analyze_project_success(self, api_client, auth_headers, company_id):
        """Test AI project analysis with existing project"""
        # First get a project ID
        projects_response = api_client.get(
            f"{BASE_URL}/api/projects?company_id={company_id}",
            headers=auth_headers
        )
        if projects_response.status_code != 200 or len(projects_response.json()) == 0:
            pytest.skip("No projects available for analysis")
        
        project_id = projects_response.json()[0]["id"]
        
        response = api_client.post(
            f"{BASE_URL}/api/ai/analyze-project/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "project_id" in data
        assert "project_name" in data
        assert "analysis" in data
        assert "summary" in data
        assert len(data["analysis"]) > 0, "Analysis should not be empty"
        print(f"✓ AI project analysis completed for: {data['project_name']}")

    def test_ai_analyze_project_not_found(self, api_client, auth_headers):
        """Test AI analysis with non-existent project returns 404"""
        response = api_client.post(
            f"{BASE_URL}/api/ai/analyze-project/nonexistent-project-id",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent project correctly returns 404")


# ============== PDF GENERATION TESTS ==============
class TestQuotePDFGeneration:
    """Quote PDF generation tests - GET /api/pdf/quote/{quote_id}"""

    def test_generate_quote_pdf_success(self, api_client, auth_headers, company_id):
        """Test PDF generation for a quote"""
        # First get a quote ID
        quotes_response = api_client.get(
            f"{BASE_URL}/api/quotes?company_id={company_id}",
            headers=auth_headers
        )
        if quotes_response.status_code != 200 or len(quotes_response.json()) == 0:
            pytest.skip("No quotes available for PDF generation")
        
        quote_id = quotes_response.json()[0]["id"]
        
        response = api_client.get(
            f"{BASE_URL}/api/pdf/quote/{quote_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "filename" in data, "Response should contain filename"
        assert "content" in data, "Response should contain base64 content"
        assert "content_type" in data, "Response should contain content_type"
        assert data["content_type"] == "application/pdf"
        assert data["filename"].endswith(".pdf")
        
        # Validate base64 content
        try:
            pdf_bytes = base64.b64decode(data["content"])
            assert len(pdf_bytes) > 1000, "PDF should have reasonable size"
            assert pdf_bytes[:4] == b'%PDF', "Content should be valid PDF"
        except Exception as e:
            pytest.fail(f"Invalid PDF content: {e}")
        
        print(f"✓ Quote PDF generated: {data['filename']} ({len(pdf_bytes)} bytes)")

    def test_generate_quote_pdf_not_found(self, api_client, auth_headers):
        """Test PDF generation with non-existent quote returns 404"""
        response = api_client.get(
            f"{BASE_URL}/api/pdf/quote/nonexistent-quote-id",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent quote correctly returns 404")


class TestInvoicePDFGeneration:
    """Invoice PDF generation tests - GET /api/pdf/invoice/{invoice_id}"""

    def test_generate_invoice_pdf_success(self, api_client, auth_headers, company_id):
        """Test PDF generation for an invoice"""
        # First get an invoice ID
        invoices_response = api_client.get(
            f"{BASE_URL}/api/invoices?company_id={company_id}",
            headers=auth_headers
        )
        if invoices_response.status_code != 200 or len(invoices_response.json()) == 0:
            pytest.skip("No invoices available for PDF generation")
        
        invoice_id = invoices_response.json()[0]["id"]
        
        response = api_client.get(
            f"{BASE_URL}/api/pdf/invoice/{invoice_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "filename" in data
        assert "content" in data
        assert "content_type" in data
        assert data["content_type"] == "application/pdf"
        assert data["filename"].endswith(".pdf")
        
        # Validate base64 content
        pdf_bytes = base64.b64decode(data["content"])
        assert len(pdf_bytes) > 1000, "PDF should have reasonable size"
        assert pdf_bytes[:4] == b'%PDF', "Content should be valid PDF"
        
        print(f"✓ Invoice PDF generated: {data['filename']} ({len(pdf_bytes)} bytes)")

    def test_generate_invoice_pdf_not_found(self, api_client, auth_headers):
        """Test PDF generation with non-existent invoice returns 404"""
        response = api_client.get(
            f"{BASE_URL}/api/pdf/invoice/nonexistent-invoice-id",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent invoice correctly returns 404")


# ============== FILE UPLOAD/DOWNLOAD TESTS ==============
class TestFileUpload:
    """File upload tests - POST /api/files/upload"""

    def test_file_upload_success(self, api_client, auth_headers):
        """Test file upload with base64 content"""
        # Create a simple test file content
        test_content = b"Test document content for CIA SERVICIOS testing"
        base64_content = base64.b64encode(test_content).decode('utf-8')
        
        response = api_client.post(
            f"{BASE_URL}/api/files/upload",
            headers=auth_headers,
            json={
                "filename": "TEST_archivo_prueba.txt",
                "content": base64_content,
                "content_type": "text/plain",
                "category": "otros"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain document ID"
        assert "filename" in data
        assert "size" in data
        assert data["size"] == len(test_content)
        
        print(f"✓ File uploaded successfully: {data['filename']} (ID: {data['id']})")
        return data["id"]

    def test_file_upload_with_project(self, api_client, auth_headers, company_id):
        """Test file upload associated with a project"""
        # Get a project ID first
        projects_response = api_client.get(
            f"{BASE_URL}/api/projects?company_id={company_id}",
            headers=auth_headers
        )
        project_id = None
        if projects_response.status_code == 200 and len(projects_response.json()) > 0:
            project_id = projects_response.json()[0]["id"]
        
        test_content = b"Project document content"
        base64_content = base64.b64encode(test_content).decode('utf-8')
        
        response = api_client.post(
            f"{BASE_URL}/api/files/upload",
            headers=auth_headers,
            json={
                "filename": "TEST_proyecto_doc.pdf",
                "content": base64_content,
                "content_type": "application/pdf",
                "project_id": project_id,
                "category": "reportes"
            }
        )
        assert response.status_code == 200
        print(f"✓ File uploaded with project association: {project_id}")

    def test_file_upload_too_large(self, api_client, auth_headers):
        """Test file upload exceeding 5MB limit"""
        # Create content larger than 5MB
        large_content = b"X" * (6 * 1024 * 1024)  # 6MB
        base64_content = base64.b64encode(large_content).decode('utf-8')
        
        response = api_client.post(
            f"{BASE_URL}/api/files/upload",
            headers=auth_headers,
            json={
                "filename": "TEST_large_file.txt",
                "content": base64_content,
                "content_type": "text/plain",
                "category": "otros"
            }
        )
        assert response.status_code == 400, f"Expected 400 for oversized file, got {response.status_code}"
        print("✓ Oversized file correctly rejected (5MB limit)")

    def test_file_upload_invalid_base64(self, api_client, auth_headers):
        """Test file upload with invalid base64 content"""
        response = api_client.post(
            f"{BASE_URL}/api/files/upload",
            headers=auth_headers,
            json={
                "filename": "TEST_invalid.txt",
                "content": "not-valid-base64!!!",
                "content_type": "text/plain",
                "category": "otros"
            }
        )
        assert response.status_code == 400
        print("✓ Invalid base64 content correctly rejected")


class TestFileDownload:
    """File download tests - GET /api/files/{doc_id}/download"""

    def test_file_download_roundtrip(self, api_client, auth_headers):
        """Test upload and download roundtrip"""
        # Upload a file
        original_content = b"Test content for download verification - CIA SERVICIOS"
        base64_content = base64.b64encode(original_content).decode('utf-8')
        
        upload_response = api_client.post(
            f"{BASE_URL}/api/files/upload",
            headers=auth_headers,
            json={
                "filename": "TEST_download_test.txt",
                "content": base64_content,
                "content_type": "text/plain",
                "category": "otros"
            }
        )
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["id"]
        
        # Download the file
        download_response = api_client.get(
            f"{BASE_URL}/api/files/{doc_id}/download",
            headers=auth_headers
        )
        assert download_response.status_code == 200, f"Expected 200, got {download_response.status_code}"
        
        data = download_response.json()
        assert "filename" in data
        assert "content" in data
        assert "content_type" in data
        
        # Verify content matches
        downloaded_content = base64.b64decode(data["content"])
        assert downloaded_content == original_content, "Downloaded content should match uploaded content"
        
        print(f"✓ File download roundtrip successful: {data['filename']}")

    def test_file_download_not_found(self, api_client, auth_headers):
        """Test download with non-existent document returns 404"""
        response = api_client.get(
            f"{BASE_URL}/api/files/nonexistent-doc-id/download",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent document correctly returns 404")


# ============== INTEGRATION TESTS ==============
class TestEndToEndIntegration:
    """End-to-end integration tests for new features"""

    def test_full_document_workflow(self, api_client, auth_headers, company_id):
        """Test complete document upload, list, download workflow"""
        # 1. Upload document
        test_content = b"Integration test document"
        base64_content = base64.b64encode(test_content).decode('utf-8')
        
        upload_response = api_client.post(
            f"{BASE_URL}/api/files/upload",
            headers=auth_headers,
            json={
                "filename": "TEST_integration_doc.txt",
                "content": base64_content,
                "content_type": "text/plain",
                "category": "reportes"
            }
        )
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["id"]
        
        # 2. Verify document appears in list
        list_response = api_client.get(
            f"{BASE_URL}/api/documents?company_id={company_id}",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        docs = list_response.json()
        uploaded_doc = next((d for d in docs if d["id"] == doc_id), None)
        assert uploaded_doc is not None, "Uploaded document should appear in list"
        
        # 3. Download and verify
        download_response = api_client.get(
            f"{BASE_URL}/api/files/{doc_id}/download",
            headers=auth_headers
        )
        assert download_response.status_code == 200
        downloaded_content = base64.b64decode(download_response.json()["content"])
        assert downloaded_content == test_content
        
        print("✓ Full document workflow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
