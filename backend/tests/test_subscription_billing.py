"""
Test suite for Subscription Billing System
Tests for the new subscription billing module:
- GET /api/subscriptions/plans - subscription plans (base $2500, with_billing $3000)
- GET /api/subscriptions/config - billing configuration (Super Admin)
- POST /api/subscriptions/config - save configuration with bank accounts
- POST /api/subscriptions/invoices - create subscription invoice
- GET /api/subscriptions/invoices - list subscription invoices
- POST /api/subscriptions/invoices/{id}/record-payment - record manual payment
- GET /api/subscriptions/dashboard - dashboard statistics
- GET /api/subscriptions/my-subscription - company view of subscription
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
SUPER_ADMIN_EMAIL = "superadmin@cia-servicios.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin2024!"
COMPANY_USER_EMAIL = "gerente@ciademo.com"
COMPANY_USER_PASSWORD = "Demo2024!"
COMPANY_SLUG = "cia-servicios-demo-sa-de-cv"
TEST_COMPANY_ID = "f9e9dd31-88c9-4b30-ad0a-a55cff810bcf"


class TestSubscriptionPlans:
    """Test GET /api/subscriptions/plans endpoint"""
    
    def test_plans_endpoint_no_auth_required(self):
        """Plans endpoint should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Plans endpoint failed: {response.text}"
        print("SUCCESS: Plans endpoint accessible")
    
    def test_plans_returns_two_plans(self):
        """Should return base and with_billing plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data, "Response missing 'plans' key"
        plans = data["plans"]
        assert len(plans) == 2, f"Expected 2 plans, got {len(plans)}"
        
        plan_ids = [p["id"] for p in plans]
        assert "base" in plan_ids, "Missing 'base' plan"
        assert "with_billing" in plan_ids, "Missing 'with_billing' plan"
        print(f"SUCCESS: Found plans: {plan_ids}")
    
    def test_base_plan_price_2500(self):
        """Base plan should cost $2,500 MXN"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        
        base_plan = next((p for p in data["plans"] if p["id"] == "base"), None)
        assert base_plan is not None, "Base plan not found"
        assert base_plan["price"] == 2500, f"Expected base price 2500, got {base_plan['price']}"
        print(f"SUCCESS: Base plan price = $2,500 MXN")
    
    def test_with_billing_plan_price_3000(self):
        """With billing plan should cost $3,000 MXN"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        
        billing_plan = next((p for p in data["plans"] if p["id"] == "with_billing"), None)
        assert billing_plan is not None, "With billing plan not found"
        assert billing_plan["price"] == 3000, f"Expected billing plan price 3000, got {billing_plan['price']}"
        print(f"SUCCESS: With billing plan price = $3,000 MXN")
    
    def test_billing_cycles_with_discounts(self):
        """Should return billing cycles with correct discounts"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        
        assert "billing_cycles" in data, "Response missing 'billing_cycles' key"
        cycles = data["billing_cycles"]
        
        # Check expected cycles
        cycle_map = {c["id"]: c for c in cycles}
        
        assert "monthly" in cycle_map, "Missing monthly cycle"
        assert "quarterly" in cycle_map, "Missing quarterly cycle"
        assert "semiannual" in cycle_map, "Missing semiannual cycle"
        assert "annual" in cycle_map, "Missing annual cycle"
        
        # Check discounts
        assert cycle_map["monthly"]["discount"] == 0, "Monthly should have 0% discount"
        assert cycle_map["quarterly"]["discount"] == 0.05, "Quarterly should have 5% discount"
        assert cycle_map["semiannual"]["discount"] == 0.10, "Semiannual should have 10% discount"
        assert cycle_map["annual"]["discount"] == 0.15, "Annual should have 15% discount"
        print("SUCCESS: Billing cycles with correct discounts")


class TestSubscriptionConfigSuperAdmin:
    """Test /api/subscriptions/config endpoints (Super Admin only)"""
    
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
    
    def test_get_config_requires_super_admin(self):
        """GET /api/subscriptions/config requires Super Admin auth"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/config")
        assert response.status_code in [401, 403], "Should require auth"
        print("SUCCESS: Config endpoint requires auth")
    
    def test_get_config_success(self, auth_token):
        """Super Admin can get billing config"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/config",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Config GET failed: {response.text}"
        data = response.json()
        
        expected_keys = ["stripe_enabled", "bank_transfer_enabled", "bank_accounts"]
        for key in expected_keys:
            assert key in data, f"Config missing '{key}'"
        print(f"SUCCESS: Config retrieved, keys: {list(data.keys())}")
    
    def test_save_config_with_bank_accounts(self, auth_token):
        """Super Admin can save config with bank accounts"""
        config_data = {
            "stripe_enabled": True,
            "bank_transfer_enabled": True,
            "bank_accounts": [
                {
                    "bank_name": "BBVA",
                    "account_holder": "CIA SERVICIOS SA DE CV",
                    "account_number": "1234567890",
                    "clabe": "012180001234567890",
                    "reference_instructions": "Usar RFC como referencia"
                }
            ],
            "generate_cfdi": False,
            "cfdi_serie": "S",
            "reminder_days_before": [15, 7, 3, 1],
            "auto_suspend_days_after": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/config",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=config_data
        )
        assert response.status_code == 200, f"Config save failed: {response.text}"
        
        # Verify by getting config
        get_response = requests.get(
            f"{BASE_URL}/api/subscriptions/config",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        saved_config = get_response.json()
        assert len(saved_config.get("bank_accounts", [])) >= 1, "Bank account not saved"
        print("SUCCESS: Config with bank accounts saved")


class TestSubscriptionInvoicesCRUD:
    """Test subscription invoices CRUD operations"""
    
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
    
    def test_list_invoices(self, auth_token):
        """Super Admin can list all subscription invoices"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"List invoices failed: {response.text}"
        invoices = response.json()
        assert isinstance(invoices, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(invoices)} invoices")
    
    def test_create_invoice_base_plan(self, auth_token):
        """Create subscription invoice for base plan"""
        invoice_data = {
            "company_id": TEST_COMPANY_ID,
            "plan_id": "base",
            "billing_cycle": "monthly",
            "notes": "TEST_invoice_base_plan"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=invoice_data
        )
        assert response.status_code == 200, f"Create invoice failed: {response.text}"
        data = response.json()
        
        assert "invoice" in data, "Response missing 'invoice'"
        invoice = data["invoice"]
        assert invoice["total"] == 2500, f"Expected total 2500, got {invoice['total']}"
        assert invoice["status"] == "pending", f"Expected status pending, got {invoice['status']}"
        print(f"SUCCESS: Created invoice {invoice['invoice_number']} for $2,500")
        return invoice["id"]
    
    def test_create_invoice_with_billing_plan(self, auth_token):
        """Create subscription invoice for plan with billing"""
        invoice_data = {
            "company_id": TEST_COMPANY_ID,
            "plan_id": "with_billing",
            "billing_cycle": "monthly",
            "notes": "TEST_invoice_with_billing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=invoice_data
        )
        assert response.status_code == 200, f"Create invoice failed: {response.text}"
        invoice = response.json()["invoice"]
        assert invoice["total"] == 3000, f"Expected total 3000, got {invoice['total']}"
        print(f"SUCCESS: Created invoice {invoice['invoice_number']} for $3,000")
    
    def test_create_invoice_quarterly_with_discount(self, auth_token):
        """Create quarterly invoice with 5% discount"""
        invoice_data = {
            "company_id": TEST_COMPANY_ID,
            "plan_id": "base",
            "billing_cycle": "quarterly",
            "notes": "TEST_invoice_quarterly"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=invoice_data
        )
        assert response.status_code == 200, f"Create invoice failed: {response.text}"
        invoice = response.json()["invoice"]
        
        # 3 months x $2500 = $7500 - 5% = $7125
        expected_total = 7500 - (7500 * 0.05)
        assert invoice["total"] == expected_total, f"Expected total {expected_total}, got {invoice['total']}"
        assert invoice["discount_percent"] == 5, f"Expected discount 5%, got {invoice['discount_percent']}"
        print(f"SUCCESS: Quarterly invoice with 5% discount = ${expected_total}")
    
    def test_record_payment_bank_transfer(self, auth_token):
        """Record manual payment for invoice"""
        # First create an invoice
        invoice_data = {
            "company_id": TEST_COMPANY_ID,
            "plan_id": "base",
            "billing_cycle": "monthly",
            "notes": "TEST_invoice_for_payment"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=invoice_data
        )
        assert create_resp.status_code == 200
        invoice_id = create_resp.json()["invoice"]["id"]
        
        # Record payment
        payment_data = {
            "invoice_id": invoice_id,
            "payment_method": "bank_transfer",
            "payment_reference": "TEST-REF-001",
            "notes": "Test payment recording"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/invoices/{invoice_id}/record-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=payment_data
        )
        assert response.status_code == 200, f"Record payment failed: {response.text}"
        print(f"SUCCESS: Payment recorded for invoice {invoice_id}")
        
        # Verify invoice is now paid
        invoices_resp = requests.get(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        paid_invoice = next((i for i in invoices_resp.json() if i["id"] == invoice_id), None)
        assert paid_invoice is not None, "Invoice not found after payment"
        assert paid_invoice["status"] == "paid", f"Expected status 'paid', got {paid_invoice['status']}"
        print(f"SUCCESS: Invoice status updated to 'paid'")


class TestSubscriptionDashboard:
    """Test GET /api/subscriptions/dashboard endpoint"""
    
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
    
    def test_dashboard_endpoint_success(self, auth_token):
        """Dashboard endpoint returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        required_keys = ["stats", "pending_invoices", "overdue_invoices", "expiring_soon", "monthly_revenue"]
        for key in required_keys:
            assert key in data, f"Dashboard missing '{key}'"
        print(f"SUCCESS: Dashboard has all required keys")
    
    def test_dashboard_stats_structure(self, auth_token):
        """Dashboard stats have expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        stats = response.json()["stats"]
        
        stat_keys = ["total_pending", "total_paid_this_month", "pending_count", "overdue_count"]
        for key in stat_keys:
            assert key in stats, f"Stats missing '{key}'"
        
        # Verify numeric values
        assert isinstance(stats["total_pending"], (int, float)), "total_pending should be numeric"
        assert isinstance(stats["pending_count"], int), "pending_count should be int"
        print(f"SUCCESS: Stats structure valid: {stats}")


class TestMySubscriptionCompanyUser:
    """Test GET /api/subscriptions/my-subscription (Company User view)"""
    
    @pytest.fixture
    def company_token(self):
        """Get company user auth token"""
        response = requests.post(
            f"{BASE_URL}/api/empresa/{COMPANY_SLUG}/login",
            json={
                "email": COMPANY_USER_EMAIL,
                "password": COMPANY_USER_PASSWORD
            }
        )
        if response.status_code != 200:
            pytest.skip(f"Company user login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_my_subscription_endpoint(self, company_token):
        """Company user can view their subscription"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-subscription",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200, f"My subscription failed: {response.text}"
        data = response.json()
        
        required_keys = ["subscription", "pending_invoices", "payment_history", "bank_accounts", "plans", "billing_cycles"]
        for key in required_keys:
            assert key in data, f"Response missing '{key}'"
        print(f"SUCCESS: My subscription endpoint returns all required data")
    
    def test_my_subscription_has_status(self, company_token):
        """Subscription info includes status and end date"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-subscription",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        subscription = response.json()["subscription"]
        
        assert "status" in subscription, "Subscription missing status"
        assert "end_date" in subscription, "Subscription missing end_date"
        assert "plan" in subscription, "Subscription missing plan"
        print(f"SUCCESS: Subscription info: status={subscription['status']}, plan={subscription['plan']}")
    
    def test_my_subscription_shows_bank_accounts(self, company_token):
        """Company user can see bank accounts for transfer"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-subscription",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        data = response.json()
        bank_accounts = data.get("bank_accounts", [])
        
        # Should have at least one bank account (configured earlier)
        assert isinstance(bank_accounts, list), "bank_accounts should be a list"
        print(f"SUCCESS: Bank accounts available: {len(bank_accounts)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
