#!/usr/bin/env python3
"""
Test script to verify AI suggestions rate limiting fixes
Tests the frontend's new rate limiting implementation to prevent HTTP 429 errors
"""

import requests
import time
import json
import threading
from typing import List, Dict, Any
from datetime import datetime


class RateLimitTester:
    """Test rate limiting implementation for AI suggestions endpoint"""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1/nextgen/ai/suggestions"
        self.results: List[Dict[str, Any]] = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RateLimitTester/1.0'
        })

    def test_sequential_requests(self, count: int = 10, delay: float = 0.5) -> Dict[str, Any]:
        """Test sequential requests to check rate limiting"""
        print(f"🔄 Testing {count} sequential requests with {delay}s delay...")

        results = {
            'test_type': 'sequential',
            'total_requests': count,
            'delay_between_requests': delay,
            'successful_requests': 0,
            'rate_limited_requests': 0,
            'error_requests': 0,
            'response_times': [],
            'status_codes': [],
            'timestamps': []
        }

        for i in range(count):
            start_time = time.time()
            timestamp = datetime.now().isoformat()

            try:
                response = self.session.post(
                    self.api_url,
                    json={
                        'dataSourceId': 'test-data-source',
                        'context': {'test': True, 'iteration': i}
                    },
                    timeout=10
                )

                response_time = time.time() - start_time
                status_code = response.status_code

                results['response_times'].append(response_time)
                results['status_codes'].append(status_code)
                results['timestamps'].append(timestamp)

                if status_code == 200:
                    results['successful_requests'] += 1
                    print(f"  ✅ Request {i+1}: Success ({response_time:.2f}s)")
                elif status_code == 429:
                    results['rate_limited_requests'] += 1
                    retry_after = response.headers.get('Retry-After', 'N/A')
                    print(f"  🚫 Request {i+1}: Rate limited (Retry-After: {retry_after})")
                else:
                    results['error_requests'] += 1
                    print(f"  ❌ Request {i+1}: Error {status_code}")

            except requests.exceptions.RequestException as e:
                results['error_requests'] += 1
                results['response_times'].append(None)
                results['status_codes'].append(None)
                results['timestamps'].append(timestamp)
                print(f"  💥 Request {i+1}: Exception - {str(e)}")

            if i < count - 1:  # Don't delay after the last request
                time.sleep(delay)

        return results

    def test_concurrent_requests(self, count: int = 5) -> Dict[str, Any]:
        """Test concurrent requests to check deduplication"""
        print(f"🔄 Testing {count} concurrent requests...")

        results = {
            'test_type': 'concurrent',
            'total_requests': count,
            'successful_requests': 0,
            'rate_limited_requests': 0,
            'error_requests': 0,
            'response_times': [],
            'status_codes': [],
            'thread_results': []
        }

        threads = []
        thread_results = []

        def make_request(thread_id: int):
            start_time = time.time()
            thread_result = {
                'thread_id': thread_id,
                'status_code': None,
                'response_time': None,
                'error': None,
                'timestamp': datetime.now().isoformat()
            }

            try:
                response = self.session.post(
                    self.api_url,
                    json={
                        'dataSourceId': 'concurrent-test',
                        'context': {'test': True, 'thread_id': thread_id}
                    },
                    timeout=15
                )

                thread_result['response_time'] = time.time() - start_time
                thread_result['status_code'] = response.status_code

                if response.status_code == 200:
                    print(f"  ✅ Thread {thread_id}: Success ({thread_result['response_time']:.2f}s)")
                elif response.status_code == 429:
                    print(f"  🚫 Thread {thread_id}: Rate limited")
                else:
                    print(f"  ❌ Thread {thread_id}: Error {response.status_code}")

            except requests.exceptions.RequestException as e:
                thread_result['error'] = str(e)
                thread_result['response_time'] = time.time() - start_time
                print(f"  💥 Thread {thread_id}: Exception - {str(e)}")

            thread_results.append(thread_result)

        # Start all threads
        start_time = time.time()
        for i in range(count):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Process results
        for result in thread_results:
            if result['status_code'] == 200:
                results['successful_requests'] += 1
            elif result['status_code'] == 429:
                results['rate_limited_requests'] += 1
            else:
                results['error_requests'] += 1

            results['response_times'].append(result['response_time'])
            results['status_codes'].append(result['status_code'])

        results['thread_results'] = thread_results
        results['total_test_time'] = time.time() - start_time

        return results

    def test_burst_then_wait(self, burst_size: int = 8, wait_time: int = 15) -> Dict[str, Any]:
        """Test burst requests followed by wait to verify backoff"""
        print(f"🔄 Testing burst of {burst_size} requests, then waiting {wait_time}s...")

        results = {
            'test_type': 'burst_then_wait',
            'burst_size': burst_size,
            'wait_time': wait_time,
            'burst_results': [],
            'recovery_results': []
        }

        # Burst phase
        print("  📈 Burst phase:")
        for i in range(burst_size):
            start_time = time.time()
            try:
                response = self.session.post(
                    self.api_url,
                    json={
                        'dataSourceId': 'burst-test',
                        'context': {'test': True, 'burst_iteration': i}
                    },
                    timeout=10
                )

                result = {
                    'iteration': i,
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat()
                }

                results['burst_results'].append(result)

                if response.status_code == 200:
                    print(f"    ✅ Burst {i+1}: Success")
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', 'N/A')
                    print(f"    🚫 Burst {i+1}: Rate limited (Retry-After: {retry_after})")
                else:
                    print(f"    ❌ Burst {i+1}: Error {response.status_code}")

            except requests.exceptions.RequestException as e:
                result = {
                    'iteration': i,
                    'status_code': None,
                    'response_time': time.time() - start_time,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['burst_results'].append(result)
                print(f"    💥 Burst {i+1}: Exception - {str(e)}")

            # Small delay between burst requests
            time.sleep(0.1)

        # Wait phase
        print(f"  ⏰ Waiting {wait_time} seconds for rate limit recovery...")
        time.sleep(wait_time)

        # Recovery phase
        print("  🔄 Recovery phase:")
        for i in range(3):  # Test 3 requests after waiting
            start_time = time.time()
            try:
                response = self.session.post(
                    self.api_url,
                    json={
                        'dataSourceId': 'recovery-test',
                        'context': {'test': True, 'recovery_iteration': i}
                    },
                    timeout=10
                )

                result = {
                    'iteration': i,
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat()
                }

                results['recovery_results'].append(result)

                if response.status_code == 200:
                    print(f"    ✅ Recovery {i+1}: Success")
                elif response.status_code == 429:
                    print(f"    🚫 Recovery {i+1}: Still rate limited")
                else:
                    print(f"    ❌ Recovery {i+1}: Error {response.status_code}")

            except requests.exceptions.RequestException as e:
                result = {
                    'iteration': i,
                    'status_code': None,
                    'response_time': time.time() - start_time,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['recovery_results'].append(result)
                print(f"    💥 Recovery {i+1}: Exception - {str(e)}")

            time.sleep(2)  # 2 second delay between recovery requests

        return results

    def generate_report(self, all_results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive report of all tests"""
        report = []
        report.append("=" * 80)
        report.append("AI SUGGESTIONS RATE LIMITING TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"API Endpoint: {self.api_url}")
        report.append("")

        for i, result in enumerate(all_results, 1):
            report.append(f"TEST {i}: {result['test_type'].upper()}")
            report.append("-" * 40)

            if result['test_type'] == 'sequential':
                success_rate = (result['successful_requests'] / result['total_requests']) * 100
                rate_limit_rate = (result['rate_limited_requests'] / result['total_requests']) * 100

                report.append(f"Total Requests: {result['total_requests']}")
                report.append(f"Successful: {result['successful_requests']} ({success_rate:.1f}%)")
                report.append(f"Rate Limited: {result['rate_limited_requests']} ({rate_limit_rate:.1f}%)")
                report.append(f"Errors: {result['error_requests']}")

                valid_times = [t for t in result['response_times'] if t is not None]
                if valid_times:
                    report.append(f"Avg Response Time: {sum(valid_times)/len(valid_times):.3f}s")
                    report.append(f"Max Response Time: {max(valid_times):.3f}s")

            elif result['test_type'] == 'concurrent':
                success_rate = (result['successful_requests'] / result['total_requests']) * 100
                rate_limit_rate = (result['rate_limited_requests'] / result['total_requests']) * 100

                report.append(f"Concurrent Requests: {result['total_requests']}")
                report.append(f"Successful: {result['successful_requests']} ({success_rate:.1f}%)")
                report.append(f"Rate Limited: {result['rate_limited_requests']} ({rate_limit_rate:.1f}%)")
                report.append(f"Total Test Time: {result['total_test_time']:.2f}s")

            elif result['test_type'] == 'burst_then_wait':
                burst_success = len([r for r in result['burst_results'] if r.get('status_code') == 200])
                burst_rate_limited = len([r for r in result['burst_results'] if r.get('status_code') == 429])

                recovery_success = len([r for r in result['recovery_results'] if r.get('status_code') == 200])
                recovery_rate_limited = len([r for r in result['recovery_results'] if r.get('status_code') == 429])

                report.append(f"Burst Phase ({result['burst_size']} requests):")
                report.append(f"  Successful: {burst_success}")
                report.append(f"  Rate Limited: {burst_rate_limited}")

                report.append(f"Recovery Phase (after {result['wait_time']}s wait):")
                report.append(f"  Successful: {recovery_success}")
                report.append(f"  Rate Limited: {recovery_rate_limited}")

            report.append("")

        # Overall assessment
        report.append("ASSESSMENT")
        report.append("-" * 40)

        total_requests = sum(r.get('total_requests', 0) for r in all_results)
        total_rate_limited = sum(r.get('rate_limited_requests', 0) for r in all_results)

        if total_requests > 0:
            overall_rate_limit_rate = (total_rate_limited / total_requests) * 100

            if overall_rate_limit_rate < 30:
                report.append("✅ GOOD: Rate limiting is working effectively")
                report.append("   - Most requests are being processed successfully")
                report.append("   - Rate limiting is preventing server overload")
            elif overall_rate_limit_rate < 60:
                report.append("⚠️ MODERATE: Rate limiting is active but aggressive")
                report.append("   - Consider adjusting rate limits or improving caching")
            else:
                report.append("❌ POOR: Rate limiting is too aggressive")
                report.append("   - Most requests are being rejected")
                report.append("   - User experience will be significantly impacted")

            report.append(f"   - Overall rate limit rate: {overall_rate_limit_rate:.1f}%")

        report.append("")
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        report.append("1. Monitor rate limit rates in production")
        report.append("2. Implement proper user feedback for rate limited requests")
        report.append("3. Consider implementing request queuing for better UX")
        report.append("4. Use caching to reduce API calls")
        report.append("5. Implement exponential backoff in client-side retry logic")

        return "\n".join(report)

    def run_all_tests(self) -> str:
        """Run all rate limiting tests and generate report"""
        print("🚀 Starting AI Suggestions Rate Limiting Tests")
        print("=" * 60)

        all_results = []

        try:
            # Test 1: Sequential requests with normal delay
            result1 = self.test_sequential_requests(count=8, delay=1.0)
            all_results.append(result1)

            print("\n" + "=" * 60)

            # Test 2: Concurrent requests
            result2 = self.test_concurrent_requests(count=5)
            all_results.append(result2)

            print("\n" + "=" * 60)

            # Test 3: Burst then wait
            result3 = self.test_burst_then_wait(burst_size=6, wait_time=10)
            all_results.append(result3)

        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            return f"Test execution failed: {str(e)}"

        print("\n" + "=" * 60)
        print("📊 Generating comprehensive report...")

        report = self.generate_report(all_results)

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_suggestions_rate_limit_test_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(report)

        print(f"📁 Report saved to: {filename}")

        return report


def main():
    """Main test execution"""
    print("AI Suggestions Rate Limiting Fix - Verification Test")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        print("✅ Frontend server is accessible")
    except requests.exceptions.RequestException:
        print("❌ Frontend server is not accessible at http://localhost:3000")
        print("   Please start the frontend server and try again")
        return

    # Initialize tester
    tester = RateLimitTester()

    # Run all tests
    report = tester.run_all_tests()

    print("\n" + "=" * 80)
    print(report)


if __name__ == "__main__":
    main()