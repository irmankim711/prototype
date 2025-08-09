"""
Load Testing Configuration for Form Automation and Report Generation Platform
Simulates 50-100 concurrent users performing realistic workflows
"""

from locust import HttpUser, task, between
import random
import json
import uuid
from datetime import datetime, timedelta

class FormAutomationUser(HttpUser):
    """Simulates user interactions with the form automation platform"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    host = "http://localhost:5000"  # Override with production URL
    
    def on_start(self):
        """Setup performed when each user starts"""
        self.auth_token = None
        self.user_id = None
        self.form_ids = []
        self.report_ids = []
        
        # Authenticate user
        self.authenticate()
    
    def authenticate(self):
        """Authenticate user and get JWT token"""
        user_data = {
            "email": f"loadtest_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!"
        }
        
        # Register user
        response = self.client.post("/api/auth/register", json=user_data)
        if response.status_code == 201:
            # Login to get token
            login_response = self.client.post("/api/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            if login_response.status_code == 200:
                data = login_response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
    
    @property
    def headers(self):
        """Return headers with auth token"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    @task(3)
    def submit_form_data(self):
        """Submit form data - most common operation"""
        form_data = {
            "form_id": f"survey-{random.randint(1, 10)}",
            "form_title": f"Load Test Survey {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "data": {
                "customer_name": f"Test User {random.randint(1, 1000)}",
                "rating": random.randint(1, 5),
                "feedback": f"This is test feedback #{random.randint(1, 1000)}",
                "department": random.choice(["HR", "IT", "Sales", "Support"]),
                "date_submitted": datetime.now().isoformat(),
                "satisfaction_level": random.choice(["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"]),
                "recommend": random.choice([True, False]),
                "contact_method": random.choice(["email", "phone", "chat"])
            },
            "source": "load_test"
        }
        
        with self.client.post("/api/public-forms/submit", 
                             json=form_data, 
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                # Store form ID for report generation
                self.form_ids.append(form_data["form_id"])
            else:
                response.failure(f"Form submission failed: {response.status_code}")
    
    @task(2)
    def batch_submit_forms(self):
        """Submit multiple forms in batch - moderate load"""
        batch_size = random.randint(5, 15)
        submissions = []
        
        for i in range(batch_size):
            submissions.append({
                "form_id": f"batch-survey-{random.randint(1, 5)}",
                "data": {
                    "participant_id": f"batch_{i}_{uuid.uuid4().hex[:6]}",
                    "score": random.randint(1, 100),
                    "category": random.choice(["A", "B", "C", "D"]),
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat()
                }
            })
        
        with self.client.post("/api/public-forms/batch-submit",
                             json={"submissions": submissions},
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Batch submission failed: {response.status_code}")
    
    @task(1)
    def generate_report(self):
        """Generate report - heavy computational task"""
        if not self.form_ids:
            return
            
        form_id = random.choice(self.form_ids)
        report_data = {
            "form_id": form_id,
            "title": f"Load Test Report {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "include_charts": True,
            "analysis_type": random.choice(["summary", "detailed", "trends", "comprehensive"]),
            "date_range": random.choice(["last_7_days", "last_30_days", "last_90_days"]),
            "export_format": random.choice(["pdf", "docx", "xlsx"])
        }
        
        with self.client.post("/api/public-forms/generate-report",
                             json=report_data,
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code in [200, 202]:  # 202 for async processing
                response.success()
                if response.status_code == 200:
                    data = response.json()
                    self.report_ids.append(data.get("report_id"))
            else:
                response.failure(f"Report generation failed: {response.status_code}")
    
    @task(2)
    def get_reports_list(self):
        """Fetch reports list - common read operation"""
        with self.client.get("/api/reports",
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get reports failed: {response.status_code}")
    
    @task(1)
    def download_report(self):
        """Download report - I/O intensive operation"""
        if not self.report_ids:
            return
            
        report_id = random.choice(self.report_ids)
        with self.client.get(f"/api/reports/{report_id}/download",
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Report download failed: {response.status_code}")
    
    @task(4)
    def health_check(self):
        """Health check endpoint - frequent monitoring"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def analytics_dashboard(self):
        """Access analytics dashboard"""
        with self.client.get("/api/analytics/dashboard",
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Analytics dashboard failed: {response.status_code}")

class AdminUser(HttpUser):
    """Simulates admin user performing management tasks"""
    
    wait_time = between(5, 15)  # Admins work slower but do more complex tasks
    host = "http://localhost:5000"
    weight = 1  # Lower weight = fewer admin users
    
    def on_start(self):
        """Setup admin user"""
        self.auth_token = None
        self.authenticate_admin()
    
    def authenticate_admin(self):
        """Authenticate as admin user"""
        admin_data = {
            "email": f"admin_{uuid.uuid4().hex[:6]}@company.com",
            "password": "AdminPassword123!",
            "role": "admin"
        }
        
        # Register admin (in real scenario, this would be pre-created)
        response = self.client.post("/api/auth/register", json=admin_data)
        if response.status_code == 201:
            login_response = self.client.post("/api/auth/login", json={
                "email": admin_data["email"],
                "password": admin_data["password"]
            })
            
            if login_response.status_code == 200:
                data = login_response.json()
                self.auth_token = data.get("access_token")
    
    @property
    def headers(self):
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    @task(3)
    def view_system_metrics(self):
        """View system performance metrics"""
        with self.client.get("/api/admin/metrics",
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"System metrics failed: {response.status_code}")
    
    @task(2)
    def manage_forms(self):
        """Manage form configurations"""
        with self.client.get("/api/admin/forms",
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Form management failed: {response.status_code}")
    
    @task(1)
    def bulk_export_data(self):
        """Export large datasets - heavy operation"""
        export_config = {
            "date_range": "last_30_days",
            "format": "csv",
            "include_analytics": True
        }
        
        with self.client.post("/api/admin/export",
                             json=export_config,
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Bulk export failed: {response.status_code}")

# Load Testing Scenarios
class QuickScenario(FormAutomationUser):
    """Quick load test for CI/CD pipeline"""
    weight = 10
    tasks = [FormAutomationUser.submit_form_data, FormAutomationUser.health_check]

class HeavyScenario(FormAutomationUser):
    """Heavy load scenario for stress testing"""
    weight = 3
    tasks = [FormAutomationUser.generate_report, FormAutomationUser.batch_submit_forms]
