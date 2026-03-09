import requests
import sys
from datetime import datetime
import json

class CIAServiciosAPITester:
    def __init__(self, base_url="https://cia-operacional.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.company_id = None
        self.demo_client_id = None
        self.demo_project_id = None
        self.demo_quote_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_seed_demo_data(self):
        """Create demo data first"""
        success, response = self.run_test(
            "Seed Demo Data",
            "POST", 
            "/seed-demo-data",
            200
        )
        if success:
            print(f"✅ Demo data created - Super Admin: admin@cia-servicios.com / admin123")
        return success

    def test_login_super_admin(self):
        """Test super admin login"""
        success, response = self.run_test(
            "Super Admin Login",
            "POST",
            "/auth/login", 
            200,
            data={"email": "admin@cia-servicios.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Token obtained for user: {response['user']['full_name']}")
            return True
        return False

    def test_login_company_admin(self):
        """Test company admin login"""
        success, response = self.run_test(
            "Company Admin Login",
            "POST",
            "/auth/login",
            200, 
            data={"email": "gerente@ciademo.com", "password": "gerente123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            user = response['user']
            self.company_id = user.get('company_id')
            print(f"✅ Company admin logged in: {user['full_name']}, Company ID: {self.company_id}")
            return True
        return False

    def test_get_companies(self):
        """Get companies list (super admin only)"""
        # Switch to super admin
        self.test_login_super_admin()
        success, companies = self.run_test(
            "Get Companies List",
            "GET",
            "/companies",
            200
        )
        if success and companies:
            print(f"✅ Found {len(companies)} companies")
            # Get demo company ID
            for company in companies:
                if "CIA Servicios Demo" in company.get('business_name', ''):
                    self.company_id = company['id']
                    break
        return success

    def test_super_admin_dashboard(self):
        """Test super admin subscription summary"""
        success, summary = self.run_test(
            "Super Admin Subscription Summary",
            "GET",
            "/super-admin/subscription-summary",
            200
        )
        if success:
            print(f"✅ Companies: {summary.get('total_companies')}, Active: {summary.get('active')}")
        return success

    def test_dashboard_stats(self):
        """Test company dashboard stats"""
        if not self.company_id:
            return False
        success, stats = self.run_test(
            "Dashboard Stats",
            "GET",
            "/dashboard/stats",
            200,
            params={"company_id": self.company_id}
        )
        if success:
            projects = stats.get('projects', {})
            financial = stats.get('financial', {}) 
            print(f"✅ Projects: {projects.get('total')}, Revenue: ${financial.get('total_revenue', 0)}")
        return success

    def test_create_client(self):
        """Test creating a new client"""
        if not self.company_id:
            return False
        success, client = self.run_test(
            "Create Client",
            "POST",
            "/clients",
            200,
            data={
                "company_id": self.company_id,
                "name": "Test Client Company",
                "contact_name": "Test Contact",
                "email": "test@example.com",
                "phone": "+52 55 1111 2222",
                "is_prospect": False,
                "probability": 100
            }
        )
        if success:
            self.demo_client_id = client.get('id')
            print(f"✅ Client created with ID: {self.demo_client_id}")
        return success

    def test_list_clients(self):
        """Test listing clients"""
        if not self.company_id:
            return False
        success, clients = self.run_test(
            "List Clients",
            "GET",
            "/clients",
            200,
            params={"company_id": self.company_id}
        )
        if success:
            print(f"✅ Found {len(clients)} clients")
            # Get existing client ID for other tests
            if clients and not self.demo_client_id:
                self.demo_client_id = clients[0]['id']
        return success

    def test_create_project(self):
        """Test creating a project"""
        if not self.company_id or not self.demo_client_id:
            return False
        success, project = self.run_test(
            "Create Project", 
            "POST",
            "/projects",
            200,
            data={
                "company_id": self.company_id,
                "client_id": self.demo_client_id,
                "name": "Test API Project",
                "description": "Testing project creation via API",
                "location": "Test Location",
                "contract_amount": 150000,
                "status": "active"
            }
        )
        if success:
            self.demo_project_id = project.get('id')
            print(f"✅ Project created with ID: {self.demo_project_id}")
        return success

    def test_list_projects(self):
        """Test listing projects"""
        if not self.company_id:
            return False
        success, projects = self.run_test(
            "List Projects",
            "GET",
            "/projects",
            200,
            params={"company_id": self.company_id}
        )
        if success:
            print(f"✅ Found {len(projects)} projects")
        return success

    def test_create_quote(self):
        """Test creating a quote"""
        if not self.company_id or not self.demo_client_id:
            return False
        success, quote = self.run_test(
            "Create Quote",
            "POST", 
            "/quotes",
            200,
            data={
                "company_id": self.company_id,
                "client_id": self.demo_client_id,
                "quote_number": "TEST-2024-001",
                "title": "Test Quote API",
                "description": "Testing quote creation",
                "items": [
                    {
                        "description": "Test Service",
                        "quantity": 2,
                        "unit": "hr",
                        "unit_price": 500,
                        "total": 1000
                    }
                ],
                "subtotal": 1000,
                "tax": 160,
                "total": 1160,
                "status": "prospect"
            }
        )
        if success:
            self.demo_quote_id = quote.get('id')
            print(f"✅ Quote created with ID: {self.demo_quote_id}")
        return success

    def test_list_quotes(self):
        """Test listing quotes"""
        if not self.company_id:
            return False
        success, quotes = self.run_test(
            "List Quotes",
            "GET",
            "/quotes", 
            200,
            params={"company_id": self.company_id}
        )
        if success:
            print(f"✅ Found {len(quotes)} quotes")
        return success

    def test_monthly_revenue(self):
        """Test monthly revenue endpoint"""
        if not self.company_id:
            return False
        success, revenue = self.run_test(
            "Monthly Revenue",
            "GET",
            "/dashboard/monthly-revenue",
            200,
            params={"company_id": self.company_id}
        )
        if success:
            print(f"✅ Revenue data for {len(revenue)} months")
        return success

    def test_project_progress(self):
        """Test project progress endpoint"""  
        if not self.company_id:
            return False
        success, progress = self.run_test(
            "Project Progress",
            "GET",
            "/dashboard/project-progress",
            200,
            params={"company_id": self.company_id}
        )
        if success:
            print(f"✅ Progress data for {len(progress)} active projects")
        return success

def main():
    print("🚀 CIA SERVICIOS API Testing Suite")
    print("=" * 50)
    
    tester = CIAServiciosAPITester()
    
    # Test sequence
    test_sequence = [
        ("Seed Demo Data", tester.test_seed_demo_data),
        ("Super Admin Login", tester.test_login_super_admin), 
        ("Get Companies", tester.test_get_companies),
        ("Super Admin Dashboard", tester.test_super_admin_dashboard),
        ("Company Admin Login", tester.test_login_company_admin),
        ("Dashboard Stats", tester.test_dashboard_stats),
        ("List Clients", tester.test_list_clients),
        ("Create Client", tester.test_create_client),
        ("Create Project", tester.test_create_project),
        ("List Projects", tester.test_list_projects),
        ("Create Quote", tester.test_create_quote), 
        ("List Quotes", tester.test_list_quotes),
        ("Monthly Revenue", tester.test_monthly_revenue),
        ("Project Progress", tester.test_project_progress)
    ]

    print(f"\nRunning {len(test_sequence)} API tests...\n")
    
    failed_tests = []
    for test_name, test_func in test_sequence:
        try:
            success = test_func()
            if not success:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            failed_tests.append(test_name)

    # Print results
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS")
    print(f"Total tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"  - {test}")
            
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n✅ Success rate: {success_rate:.1f}%")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())