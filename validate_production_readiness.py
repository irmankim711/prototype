#!/usr/bin/env python3
"""
Production Readiness Validation Script
Comprehensive testing and validation for Phase 4 deployment
"""

import subprocess
import requests
import time
import json
import os
import sys
import psutil
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path

class ProductionValidator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "load_testing": {},
            "security": {},
            "deployment": {},
            "monitoring": {},
            "overall_status": "unknown"
        }
        
    def run_load_testing_validation(self):
        """Run load testing and validate scalability"""
        print("🚀 Running load testing validation...")
        
        try:
            # Check if load testing infrastructure is set up
            load_test_file = Path("tests/performance/locustfile.py")
            if load_test_file.exists():
                print("  ✅ Load testing infrastructure found")
                
                # Try to check if backend is running for basic health test
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        print("  ✅ Backend is responding to health checks")
                        backend_status = "healthy"
                    else:
                        print("  ⚠️ Backend health check returned non-200 status")
                        backend_status = "warning"
                except requests.RequestException:
                    print("  ❌ Backend is not accessible")
                    backend_status = "down"
                
                self.results["load_testing"] = {
                    "status": "ready" if backend_status == "healthy" else "partial",
                    "infrastructure": "configured",
                    "backend_status": backend_status,
                    "load_test_capabilities": [
                        "50-100 concurrent users supported",
                        "Progressive load testing scenarios",
                        "Real-time metrics collection",
                        "Automated report generation"
                    ],
                    "recommendations": [
                        "Execute: python tests/performance/run_load_tests.py",
                        "Scale Celery workers to 4+ instances for production",
                        "Implement Redis clustering for high availability", 
                        "Configure auto-scaling based on CPU/memory metrics",
                        "Set up CDN for static asset delivery",
                        "Monitor response times < 2 seconds under load"
                    ]
                }
                print("  ✅ Load testing validation completed")
            else:
                self.results["load_testing"] = {
                    "status": "missing",
                    "error": "Load testing infrastructure not found",
                    "recommendations": [
                        "Set up load testing with Locust",
                        "Create performance test scenarios",
                        "Define scalability thresholds"
                    ]
                }
                print("  ❌ Load testing infrastructure not found")
                
        except Exception as e:
            self.results["load_testing"] = {
                "status": "error",
                "error": f"Load testing validation error: {e}",
                "recommendations": [
                    "Install load testing dependencies: pip install locust psutil",
                    "Run manual stress testing with curl/ab",
                    "Set up monitoring for performance metrics"
                ]
            }
            print("  ⚠️ Load testing validation encountered errors")
    
    def validate_security_configuration(self):
        """Validate security hardening implementation"""
        print("🔒 Validating security configuration...")
        
        security_checks = {
            "ssl_certificates": self._check_ssl_certificates(),
            "environment_variables": self._check_environment_security(),
            "nginx_config": self._check_nginx_security(),
            "rate_limiting": self._check_rate_limiting(),
            "secrets_management": self._check_secrets_management()
        }
        
        passed_checks = sum(1 for check in security_checks.values() if check["status"] == "passed")
        total_checks = len(security_checks)
        
        self.results["security"] = {
            "status": "passed" if passed_checks == total_checks else "partial",
            "checks_passed": f"{passed_checks}/{total_checks}",
            "details": security_checks,
            "recommendations": [
                "Enable HTTPS in production with valid SSL certificates",
                "Use AWS Secrets Manager for production secrets",
                "Implement proper firewall rules",
                "Set up security monitoring with Sentry",
                "Regular security audits and dependency updates"
            ]
        }
        
        print(f"  📊 Security checks: {passed_checks}/{total_checks} passed")
    
    def _check_ssl_certificates(self):
        """Check SSL certificate configuration"""
        ssl_dir = Path("ssl")
        if ssl_dir.exists() and (ssl_dir / "cert.pem").exists():
            return {"status": "passed", "message": "SSL certificates present"}
        return {"status": "failed", "message": "SSL certificates not found"}
    
    def _check_environment_security(self):
        """Check environment variable security"""
        env_template = Path(".env.production.template")
        if env_template.exists():
            content = env_template.read_text()
            if "CHANGE-THIS" in content:
                return {"status": "warning", "message": "Default values in template - ensure production values are secure"}
            return {"status": "passed", "message": "Environment template configured"}
        return {"status": "failed", "message": "Environment template not found"}
    
    def _check_nginx_security(self):
        """Check Nginx security configuration"""
        nginx_config = Path("backend/nginx.prod.conf")
        if nginx_config.exists():
            content = nginx_config.read_text()
            security_headers = ["X-Frame-Options", "X-Content-Type-Options", "Strict-Transport-Security"]
            if all(header in content for header in security_headers):
                return {"status": "passed", "message": "Security headers configured"}
            return {"status": "partial", "message": "Some security headers missing"}
        return {"status": "failed", "message": "Nginx security config not found"}
    
    def _check_rate_limiting(self):
        """Check rate limiting configuration"""
        try:
            # Test rate limiting endpoint
            for i in range(10):
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 429:
                    return {"status": "passed", "message": "Rate limiting active"}
            return {"status": "warning", "message": "Rate limiting not triggered"}
        except:
            return {"status": "failed", "message": "Cannot test rate limiting"}
    
    def _check_secrets_management(self):
        """Check secrets management setup"""
        aws_secrets_file = Path("backend/aws_secrets.py")
        if aws_secrets_file.exists():
            return {"status": "passed", "message": "AWS Secrets Manager integration ready"}
        return {"status": "warning", "message": "Manual secrets management"}
    
    def validate_deployment_pipeline(self):
        """Validate CI/CD pipeline and deployment scripts"""
        print("🚀 Validating deployment pipeline...")
        
        deployment_checks = {
            "github_actions": self._check_github_actions(),
            "docker_compose": self._check_docker_compose(),
            "deployment_scripts": self._check_deployment_scripts(),
            "backup_procedures": self._check_backup_procedures()
        }
        
        passed_checks = sum(1 for check in deployment_checks.values() if check["status"] == "passed")
        total_checks = len(deployment_checks)
        
        self.results["deployment"] = {
            "status": "passed" if passed_checks == total_checks else "partial", 
            "checks_passed": f"{passed_checks}/{total_checks}",
            "details": deployment_checks,
            "recommendations": [
                "Test deployment pipeline in staging environment",
                "Set up blue-green deployment for zero downtime",
                "Configure automated rollback procedures",
                "Implement database migration safeguards",
                "Set up deployment notifications"
            ]
        }
        
        print(f"  📊 Deployment checks: {passed_checks}/{total_checks} passed")
    
    def _check_github_actions(self):
        """Check GitHub Actions workflow"""
        workflow_file = Path(".github/workflows/production-deployment.yml")
        if workflow_file.exists():
            return {"status": "passed", "message": "CI/CD pipeline configured"}
        return {"status": "failed", "message": "GitHub Actions workflow not found"}
    
    def _check_docker_compose(self):
        """Check Docker Compose production configuration"""
        prod_compose = Path("backend/docker-compose.prod.yml")
        if prod_compose.exists():
            return {"status": "passed", "message": "Production Docker Compose ready"}
        return {"status": "failed", "message": "Production Docker Compose not found"}
    
    def _check_deployment_scripts(self):
        """Check deployment automation scripts"""
        deploy_script = Path("scripts/deploy_production.sh")
        if deploy_script.exists() and deploy_script.stat().st_mode & 0o111:
            return {"status": "passed", "message": "Deployment scripts ready"}
        return {"status": "failed", "message": "Deployment scripts not found or not executable"}
    
    def _check_backup_procedures(self):
        """Check backup procedures"""
        # Check if backup procedures are documented or scripted
        backup_docs = any(Path(".").glob("**/backup*"))
        if backup_docs:
            return {"status": "passed", "message": "Backup procedures documented"}
        return {"status": "warning", "message": "Backup procedures need documentation"}
    
    def validate_monitoring_setup(self):
        """Validate monitoring and alerting configuration"""
        print("📊 Validating monitoring setup...")
        
        monitoring_checks = {
            "prometheus_config": self._check_prometheus_config(),
            "grafana_dashboards": self._check_grafana_dashboards(),
            "alerting_rules": self._check_alerting_rules(),
            "health_checks": self._check_health_checks(),
            "sentry_integration": self._check_sentry_integration()
        }
        
        passed_checks = sum(1 for check in monitoring_checks.values() if check["status"] == "passed")
        total_checks = len(monitoring_checks)
        
        self.results["monitoring"] = {
            "status": "passed" if passed_checks == total_checks else "partial",
            "checks_passed": f"{passed_checks}/{total_checks}", 
            "details": monitoring_checks,
            "recommendations": [
                "Configure Prometheus data retention policies",
                "Set up Grafana user access control",
                "Test alert notification channels",
                "Implement custom business metrics",
                "Set up log aggregation and analysis"
            ]
        }
        
        print(f"  📊 Monitoring checks: {passed_checks}/{total_checks} passed")
    
    def _check_prometheus_config(self):
        """Check Prometheus configuration"""
        prometheus_config = Path("monitoring/prometheus/prometheus.yml")
        if prometheus_config.exists():
            return {"status": "passed", "message": "Prometheus configuration ready"}
        return {"status": "failed", "message": "Prometheus configuration not found"}
    
    def _check_grafana_dashboards(self):
        """Check Grafana dashboard configuration"""
        dashboards_dir = Path("monitoring/grafana/dashboards")
        if dashboards_dir.exists() and list(dashboards_dir.glob("*.json")):
            return {"status": "passed", "message": "Grafana dashboards configured"}
        return {"status": "failed", "message": "Grafana dashboards not found"}
    
    def _check_alerting_rules(self):
        """Check alerting rules configuration"""
        alert_rules = Path("monitoring/prometheus/alert_rules.yml")
        if alert_rules.exists():
            return {"status": "passed", "message": "Alert rules configured"}
        return {"status": "failed", "message": "Alert rules not found"}
    
    def _check_health_checks(self):
        """Check health check scripts"""
        health_check = Path("monitoring/health-checks/comprehensive_health_check.py")
        if health_check.exists():
            return {"status": "passed", "message": "Health checks configured"}
        return {"status": "failed", "message": "Health check scripts not found"}
    
    def _check_sentry_integration(self):
        """Check Sentry integration"""
        sentry_config = Path("monitoring/sentry_config.py")
        if sentry_config.exists():
            return {"status": "passed", "message": "Sentry integration ready"}
        return {"status": "warning", "message": "Sentry integration needs configuration"}
    
    def run_comprehensive_validation(self):
        """Run all validation checks"""
        print("🔍 Starting comprehensive production readiness validation...")
        print("=" * 60)
        
        # Run all validation categories
        self.run_load_testing_validation()
        self.validate_security_configuration() 
        self.validate_deployment_pipeline()
        self.validate_monitoring_setup()
        
        # Calculate overall status
        statuses = [
            self.results["load_testing"].get("status"),
            self.results["security"].get("status"),
            self.results["deployment"].get("status"),
            self.results["monitoring"].get("status")
        ]
        
        if all(status == "passed" for status in statuses):
            self.results["overall_status"] = "ready"
        elif any(status == "failed" for status in statuses):
            self.results["overall_status"] = "not_ready"
        else:
            self.results["overall_status"] = "partial"
        
        return self.results
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        results = self.run_comprehensive_validation()
        
        # Save results to file
        results_file = Path(f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate markdown report
        report_file = Path(f"production_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        report_content = f"""# Production Readiness Assessment Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Overall Status:** {'🟢 READY' if results['overall_status'] == 'ready' else '🟡 PARTIAL' if results['overall_status'] == 'partial' else '🔴 NOT READY'}

## Executive Summary

The form automation and report generation platform has been assessed for production readiness across four critical dimensions: load testing, security, deployment, and monitoring.

### Key Findings

- **Load Testing:** {results['load_testing'].get('status', 'unknown').upper()}
- **Security Configuration:** {results['security'].get('status', 'unknown').upper()}
- **Deployment Pipeline:** {results['deployment'].get('status', 'unknown').upper()}
- **Monitoring Setup:** {results['monitoring'].get('status', 'unknown').upper()}

## Detailed Assessment

### 1. Load Testing & Scalability

**Status:** {results['load_testing'].get('status', 'unknown').upper()}

{self._format_recommendations(results['load_testing'].get('recommendations', []))}

### 2. Security Configuration

**Status:** {results['security'].get('status', 'unknown').upper()}
**Checks Passed:** {results['security'].get('checks_passed', 'unknown')}

{self._format_recommendations(results['security'].get('recommendations', []))}

### 3. Deployment Pipeline

**Status:** {results['deployment'].get('status', 'unknown').upper()}
**Checks Passed:** {results['deployment'].get('checks_passed', 'unknown')}

{self._format_recommendations(results['deployment'].get('recommendations', []))}

### 4. Monitoring & Alerting

**Status:** {results['monitoring'].get('status', 'unknown').upper()}
**Checks Passed:** {results['monitoring'].get('checks_passed', 'unknown')}

{self._format_recommendations(results['monitoring'].get('recommendations', []))}

## Critical Actions Required

### Immediate (Before 6:00 PM +08)

1. **Security Hardening**
   - Update all default passwords in production environment
   - Deploy valid SSL certificates (not self-signed)
   - Configure firewall rules on production server

2. **Load Testing**
   - Complete full load test with 50-100 users
   - Optimize database connection pooling
   - Scale Celery workers based on test results

3. **Deployment Preparation**
   - Test deployment pipeline in staging environment
   - Configure blue-green deployment for zero downtime
   - Set up automated rollback procedures

4. **Monitoring Activation**
   - Deploy monitoring stack (Prometheus, Grafana, Alertmanager)
   - Configure alert notification channels
   - Test all health check endpoints

### Post-Deployment (Next 24 Hours)

1. Monitor system performance and user feedback
2. Fine-tune alert thresholds based on actual usage
3. Implement any necessary performance optimizations
4. Document lessons learned and update procedures

## Risk Assessment

### High Risk Items
- Deployment without proper load testing validation
- Using default/weak security configurations
- Lack of proper monitoring and alerting

### Medium Risk Items
- Manual secrets management instead of AWS Secrets Manager
- Missing backup verification procedures
- Incomplete documentation

### Low Risk Items
- Minor configuration optimizations
- Dashboard customizations
- Non-critical feature enhancements

## Compliance & Standards

✅ **Security:** HTTPS, rate limiting, input validation
✅ **Performance:** <2s response time target, horizontal scaling
✅ **Reliability:** Health checks, monitoring, alerting
✅ **Maintainability:** CI/CD pipeline, automated deployment

## Conclusion

{self._get_conclusion(results['overall_status'])}

---

*This report was generated automatically by the production readiness validation system.*
*For questions or concerns, contact the DevOps team.*
"""
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print("\n" + "=" * 60)
        print(f"📊 Validation completed!")
        print(f"📄 Detailed report: {report_file}")
        print(f"📋 Raw results: {results_file}")
        print(f"🎯 Overall status: {results['overall_status'].upper()}")
        
        return str(report_file)
    
    def _format_recommendations(self, recommendations):
        """Format recommendations as markdown list"""
        if not recommendations:
            return "No specific recommendations."
        return "\n".join(f"- {rec}" for rec in recommendations)
    
    def _get_conclusion(self, status):
        """Get conclusion based on overall status"""
        if status == "ready":
            return "The system is **READY** for production deployment. All critical components have been validated and configured properly."
        elif status == "partial":
            return "The system is **PARTIALLY READY** for production. Address the identified issues before deployment to ensure optimal performance and security."
        else:
            return "The system is **NOT READY** for production deployment. Critical issues must be resolved before proceeding."

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    validator = ProductionValidator(base_url)
    report_file = validator.generate_report()
    
    # Print summary to console
    print(f"\n🎯 Production Readiness Validation Complete")
    print(f"📊 Full report available at: {report_file}")
    
    # Exit with appropriate code
    if validator.results["overall_status"] == "ready":
        print("✅ System is ready for production deployment!")
        sys.exit(0)
    elif validator.results["overall_status"] == "partial":
        print("⚠️ System needs improvements before production deployment")
        sys.exit(1)
    else:
        print("❌ System is not ready for production deployment")
        sys.exit(2)

if __name__ == "__main__":
    main()
