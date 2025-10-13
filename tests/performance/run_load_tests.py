"""
Load Testing Execution Script
Automates load testing with different scenarios and generates comprehensive reports
"""

import subprocess
import time
import json
import os
import sys
from datetime import datetime
import psutil
import requests
from pathlib import Path

class LoadTestRunner:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results_dir = Path("load_test_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def check_system_readiness(self):
        """Check if the system is ready for load testing"""
        print("🔍 Checking system readiness...")
        
        # Check if backend is running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code != 200:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to backend: {e}")
            return False
        
        # Check system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        if memory.percent > 80:
            print(f"⚠️ High memory usage: {memory.percent}%")
        
        if disk.percent > 90:
            print(f"⚠️ High disk usage: {disk.percent}%")
        
        print("✅ System ready for load testing")
        return True
    
    def run_scenario(self, scenario_name, users, spawn_rate, duration, host=None):
        """Run a specific load testing scenario"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"{scenario_name}_{timestamp}.json"
        csv_file = self.results_dir / f"{scenario_name}_{timestamp}.csv"
        html_file = self.results_dir / f"{scenario_name}_{timestamp}.html"
        
        cmd = [
            "locust",
            "-f", "tests/performance/locustfile.py",
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", f"{duration}s",
            "--headless",
            "--csv", str(csv_file.with_suffix("")),
            "--html", str(html_file),
            "--logfile", str(self.results_dir / f"{scenario_name}_{timestamp}.log")
        ]
        
        if host:
            cmd.extend(["--host", host])
        else:
            cmd.extend(["--host", self.base_url])
        
        print(f"🚀 Running {scenario_name} with {users} users...")
        print(f"Command: {' '.join(cmd)}")
        
        start_time = time.time()
        process = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        result = {
            "scenario": scenario_name,
            "users": users,
            "spawn_rate": spawn_rate,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "execution_time": end_time - start_time,
            "return_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
        
        # Save results
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        if process.returncode == 0:
            print(f"✅ {scenario_name} completed successfully")
        else:
            print(f"❌ {scenario_name} failed with return code {process.returncode}")
            print(f"Error: {process.stderr}")
        
        return result
    
    def run_progressive_load_test(self):
        """Run progressive load testing to find breaking point"""
        print("📈 Starting progressive load testing...")
        
        scenarios = [
            {"name": "baseline", "users": 10, "duration": 300},  # 5 minutes
            {"name": "moderate", "users": 25, "duration": 600},  # 10 minutes
            {"name": "heavy", "users": 50, "duration": 900},     # 15 minutes
            {"name": "stress", "users": 75, "duration": 600},    # 10 minutes
            {"name": "breaking_point", "users": 100, "duration": 300}  # 5 minutes
        ]
        
        results = []
        for scenario in scenarios:
            result = self.run_scenario(
                scenario["name"],
                users=scenario["users"],
                spawn_rate=min(5, scenario["users"] // 2),
                duration=scenario["duration"]
            )
            results.append(result)
            
            # Wait between scenarios to let system recover
            print("⏳ Cooling down for 30 seconds...")
            time.sleep(30)
        
        return results
    
    def run_spike_test(self):
        """Run spike testing to test sudden load increases"""
        print("⚡ Starting spike testing...")
        
        # Quick ramp-up to high load
        result = self.run_scenario(
            "spike_test",
            users=80,
            spawn_rate=20,  # Spawn 20 users per second
            duration=300    # 5 minutes
        )
        
        return result
    
    def run_endurance_test(self):
        """Run endurance testing for sustained load"""
        print("🏃 Starting endurance testing...")
        
        # Moderate sustained load
        result = self.run_scenario(
            "endurance_test",
            users=30,
            spawn_rate=2,
            duration=1800   # 30 minutes
        )
        
        return result
    
    def generate_summary_report(self, results):
        """Generate comprehensive summary report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"load_test_summary_{timestamp}.md"
        
        report = f"""# Load Testing Summary Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Test Configuration
- Base URL: {self.base_url}
- Test Environment: Production-like
- Testing Tool: Locust

## Test Scenarios Executed

"""
        
        for result in results:
            status = "✅ PASSED" if result["return_code"] == 0 else "❌ FAILED"
            report += f"""### {result['scenario'].title()} Test
- **Status**: {status}
- **Users**: {result['users']}
- **Spawn Rate**: {result['spawn_rate']} users/second
- **Duration**: {result['duration']} seconds
- **Execution Time**: {result['execution_time']:.2f} seconds

"""
        
        report += """## Key Metrics Analysis

### Performance Indicators
- **Response Time**: Check p95 response times < 2 seconds
- **Throughput**: Requests per second (RPS)
- **Error Rate**: Should be < 1% under normal load
- **Resource Utilization**: CPU, Memory, Disk I/O

### Scalability Assessment
- **Breaking Point**: Maximum concurrent users before degradation
- **Linear Scaling**: Performance scales linearly with load
- **Resource Bottlenecks**: Identify CPU, memory, or I/O constraints

### Recommendations

#### Infrastructure Scaling
1. **Horizontal Scaling**: Add more API server instances
2. **Database Optimization**: Connection pooling, read replicas
3. **Caching Strategy**: Redis for session and API response caching
4. **CDN Integration**: Static asset delivery optimization

#### Application Optimization
1. **Database Queries**: Optimize slow queries, add indexes
2. **Celery Workers**: Scale background task processing
3. **API Rate Limiting**: Implement appropriate rate limits
4. **Resource Cleanup**: Ensure proper resource cleanup

#### Monitoring and Alerting
1. **Performance Monitoring**: Real-time metrics dashboard
2. **Error Tracking**: Sentry integration for error monitoring
3. **Resource Alerts**: CPU, memory, disk usage alerts
4. **SLA Monitoring**: Response time and availability tracking

## Security Considerations

### Rate Limiting
- Implement progressive rate limiting based on user patterns
- Use distributed rate limiting with Redis
- Monitor for suspicious activity patterns

### Resource Protection
- Set maximum request payload sizes
- Implement request timeout limits
- Use circuit breakers for external dependencies

### DoS Protection
- Implement proper CORS policies
- Use reverse proxy (Nginx) for DDoS protection
- Monitor for unusual traffic patterns

## Next Steps

1. **Production Deployment**: Deploy optimized configuration
2. **Continuous Monitoring**: Set up performance monitoring
3. **Regular Testing**: Schedule weekly load tests
4. **Capacity Planning**: Plan for expected growth
5. **Incident Response**: Prepare scaling procedures

"""
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📊 Summary report generated: {report_file}")
        return str(report_file)

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    runner = LoadTestRunner(base_url)
    
    # Check system readiness
    if not runner.check_system_readiness():
        print("❌ System not ready for load testing")
        sys.exit(1)
    
    all_results = []
    
    print("🎯 Starting comprehensive load testing suite...")
    
    # Run progressive load testing
    progressive_results = runner.run_progressive_load_test()
    all_results.extend(progressive_results)
    
    # Run spike testing
    spike_result = runner.run_spike_test()
    all_results.append(spike_result)
    
    # Optional: Run endurance test (comment out for quick testing)
    # endurance_result = runner.run_endurance_test()
    # all_results.append(endurance_result)
    
    # Generate summary report
    report_file = runner.generate_summary_report(all_results)
    
    print(f"""
🏁 Load testing completed!

📋 Results Summary:
- Total scenarios: {len(all_results)}
- Successful: {sum(1 for r in all_results if r['return_code'] == 0)}
- Failed: {sum(1 for r in all_results if r['return_code'] != 0)}

📊 Reports generated in: {runner.results_dir}
📄 Summary report: {report_file}

🚀 Next steps:
1. Review detailed CSV reports for performance metrics
2. Check HTML reports for visual analysis
3. Implement recommendations from summary report
4. Set up continuous performance monitoring
""")

if __name__ == "__main__":
    main()
