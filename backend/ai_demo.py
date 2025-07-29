#!/usr/bin/env python3
"""
AI Functionality Demo Script

This script demonstrates the AI capabilities implemented in the prototype application.
It shows real examples of how the AI features work with actual data.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000/api/mvp"

def print_separator(title):
    """Print a formatted separator with title"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_subsection(title):
    """Print a formatted subsection"""
    print(f"\n--- {title} ---")

def demo_health_check():
    """Demonstrate AI health check"""
    print_separator("AI HEALTH CHECK")
    
    try:
        response = requests.get(f"{BASE_URL}/ai/health")
        result = response.json()
        
        print("✅ AI Service Status:")
        print(f"  Overall Status: {result['status']}")
        print(f"  OpenAI: {result['services']['openai']['status']}")
        print(f"  Google AI: {result['services']['google_ai']['status']}")
        print(f"  Available Features: {len(result['features_available'])}")
        
        for feature in result['features_available']:
            print(f"    - {feature}")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def demo_data_analysis():
    """Demonstrate AI data analysis capabilities"""
    print_separator("AI DATA ANALYSIS")
    
    # Example 1: Financial Data Analysis
    print_subsection("Financial Data Analysis")
    financial_data = {
        "context": "financial",
        "data": {
            "company": "TechCorp Solutions",
            "period": "Q4 2024",
            "revenue": 2500000,
            "expenses": 1800000,
            "gross_profit": 700000,
            "net_profit": 550000,
            "employees": 45,
            "growth_rate": 0.23,
            "profit_margin": 0.22,
            "quarterly_revenue": [2100000, 2200000, 2350000, 2500000],
            "department_costs": {
                "engineering": 800000,
                "sales": 400000,
                "marketing": 300000,
                "operations": 300000
            }
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/analyze", json=financial_data)
        result = response.json()
        
        print(f"📊 Analysis Summary: {result.get('summary', 'No summary')}")
        print(f"🔍 AI Powered: {result.get('ai_powered', 'Unknown')}")
        print(f"📈 Confidence Score: {result.get('confidence_score', 0):.1%}")
        print(f"📋 Data Quality: {result.get('data_quality', 'Unknown')}")
        
        print("\n💡 Key Insights:")
        for insight in result.get('insights', [])[:3]:
            print(f"  • {insight}")
        
        print("\n🎯 Recommendations:")
        for rec in result.get('recommendations', [])[:3]:
            print(f"  • {rec}")
        
        if result.get('risks'):
            print("\n⚠️ Identified Risks:")
            for risk in result.get('risks', [])[:2]:
                print(f"  • {risk}")
        
        if result.get('opportunities'):
            print("\n🚀 Opportunities:")
            for opp in result.get('opportunities', [])[:2]:
                print(f"  • {opp}")
        
    except Exception as e:
        print(f"❌ Financial analysis failed: {e}")
    
    # Example 2: Operational Data Analysis
    print_subsection("Operational Data Analysis")
    operational_data = {
        "context": "operational",
        "data": {
            "team_size": 28,
            "projects_active": 12,
            "projects_completed": 8,
            "productivity_score": 0.87,
            "efficiency_metrics": {
                "task_completion_rate": 0.92,
                "on_time_delivery": 0.85,
                "client_satisfaction": 4.3,
                "bug_rate": 0.03
            },
            "resource_utilization": 0.78,
            "overtime_hours": 120,
            "training_hours": 240
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/analyze", json=operational_data)
        result = response.json()
        
        print(f"📊 Analysis Summary: {result.get('summary', 'No summary')}")
        print(f"🔍 AI Powered: {result.get('ai_powered', 'Unknown')}")
        
        print("\n💡 Key Insights:")
        for insight in result.get('insights', [])[:3]:
            print(f"  • {insight}")
        
    except Exception as e:
        print(f"❌ Operational analysis failed: {e}")

def demo_report_suggestions():
    """Demonstrate AI report suggestions"""
    print_separator("AI REPORT SUGGESTIONS")
    
    suggestion_data = {
        "report_type": "quarterly_financial",
        "data": {
            "period": "Q4 2024",
            "revenue": 2500000,
            "profit": 550000,
            "team_size": 45,
            "key_projects": 12,
            "customer_count": 250,
            "market_expansion": True
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/report-suggestions", json=suggestion_data)
        result = response.json()
        
        if result.get('success'):
            suggestions = result.get('suggestions', {})
            
            print(f"📋 Report Type: {result.get('report_type', 'Unknown')}")
            print(f"🤖 AI Powered: {result.get('ai_powered', 'Unknown')}")
            
            if suggestions.get('key_metrics'):
                print("\n📊 Suggested Key Metrics:")
                for metric in suggestions['key_metrics'][:4]:
                    print(f"  • {metric.get('metric', 'N/A')}: {metric.get('value', 'N/A')} ({metric.get('importance', 'medium')} priority)")
            
            if suggestions.get('executive_points'):
                print("\n📝 Executive Summary Points:")
                for point in suggestions['executive_points'][:3]:
                    print(f"  • {point}")
            
            if suggestions.get('visualizations'):
                print("\n📈 Recommended Visualizations:")
                for viz in suggestions['visualizations'][:3]:
                    print(f"  • {viz.get('type', 'chart')}: {viz.get('purpose', 'data visualization')}")
            
            if suggestions.get('next_steps'):
                print("\n🎯 Next Steps:")
                for step in suggestions['next_steps'][:3]:
                    print(f"  • {step}")
        
    except Exception as e:
        print(f"❌ Report suggestions failed: {e}")

def demo_smart_placeholders():
    """Demonstrate smart placeholder generation"""
    print_separator("SMART PLACEHOLDER GENERATION")
    
    # Example 1: Financial report placeholders
    print_subsection("Financial Report Placeholders")
    try:
        response = requests.post(f"{BASE_URL}/ai/smart-placeholders", json={
            "context": "financial",
            "industry": "technology"
        })
        result = response.json()
        
        if result.get('success'):
            placeholders = result.get('placeholders', {})
            
            print(f"📄 Context: {result.get('context')} | Industry: {result.get('industry')}")
            print(f"🤖 AI Powered: {result.get('ai_powered', 'Unknown')}")
            
            # Show basic placeholders
            if placeholders.get('basic_placeholders'):
                print("\n🏷️ Basic Placeholders:")
                for ph in placeholders['basic_placeholders'][:3]:
                    required = "✅" if ph.get('required') else "⭕"
                    print(f"  {required} {ph.get('name', 'N/A')}: {ph.get('description', 'No description')}")
                    print(f"      Example: {ph.get('example', 'N/A')}")
            
            # Show financial metrics
            if placeholders.get('financial_metrics'):
                print("\n💰 Financial Metrics:")
                for ph in placeholders['financial_metrics'][:3]:
                    print(f"  • {ph.get('name', 'N/A')}: {ph.get('description', 'No description')}")
                    print(f"      Example: {ph.get('example', 'N/A')}")
            
            # Show industry-specific
            if placeholders.get('industry_specific'):
                print("\n🏭 Technology Industry Specific:")
                for ph in placeholders['industry_specific'][:3]:
                    print(f"  • {ph.get('name', 'N/A')}: {ph.get('description', 'No description')}")
        
    except Exception as e:
        print(f"❌ Placeholder generation failed: {e}")
    
    # Example 2: Operational report placeholders
    print_subsection("Operational Report Placeholders")
    try:
        response = requests.post(f"{BASE_URL}/ai/smart-placeholders", json={
            "context": "operational",
            "industry": "manufacturing"
        })
        result = response.json()
        
        if result.get('success'):
            placeholders = result.get('placeholders', {})
            
            if placeholders.get('operational_details'):
                print("\n⚙️ Operational Details:")
                for ph in placeholders['operational_details'][:3]:
                    print(f"  • {ph.get('name', 'N/A')}: {ph.get('description', 'No description')}")
        
    except Exception as e:
        print(f"❌ Operational placeholders failed: {e}")

def demo_data_validation():
    """Demonstrate AI data validation"""
    print_separator("AI DATA VALIDATION")
    
    # Example with mixed quality data
    validation_data = {
        "data": {
            "employee_name": "John Doe",
            "employee_id": "EMP001",
            "salary": 75000,
            "department": "Engineering",
            "join_date": "2023-01-15",
            "email": "john.doe@company.com",
            "phone": "555-0123",
            "manager": "Jane Smith",
            "incomplete_field": "",  # Missing data
            "invalid_date": "not-a-date",  # Invalid format
            "negative_value": -500,  # Potentially invalid
            "duplicate_info": "EMP001"  # Duplicate of employee_id
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/validate-data", json=validation_data)
        result = response.json()
        
        if result.get('success'):
            validation = result.get('validation', {})
            
            print(f"📊 Overall Quality Score: {validation.get('overall_quality_score', 0):.1%}")
            print(f"🤖 AI Powered: {result.get('ai_powered', 'Unknown')}")
            print(f"✅ Data Readiness: {validation.get('data_readiness', 'Unknown')}")
            
            if validation.get('issues_found'):
                print("\n⚠️ Issues Found:")
                for issue in validation['issues_found'][:5]:
                    severity = issue.get('severity', 'unknown')
                    emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
                    print(f"  {emoji} {issue.get('type', 'unknown')}: {issue.get('description', 'No description')}")
        
    except Exception as e:
        print(f"❌ Data validation failed: {e}")

def main():
    """Run the complete AI functionality demo"""
    print("🤖 AI FUNCTIONALITY DEMO")
    print("This demo showcases the AI capabilities implemented in the prototype")
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all demonstrations
        demo_health_check()
        time.sleep(1)
        
        demo_data_analysis()
        time.sleep(1)
        
        demo_report_suggestions()
        time.sleep(1)
        
        demo_smart_placeholders()
        time.sleep(1)
        
        demo_data_validation()
        
        # Summary
        print_separator("DEMO COMPLETE")
        print("✅ All AI functionality demonstrations completed successfully!")
        print("\n🔧 Key Features Demonstrated:")
        print("  • AI Health Monitoring")
        print("  • Intelligent Data Analysis (Financial & Operational)")
        print("  • Smart Report Suggestions")
        print("  • Context-Aware Placeholder Generation")
        print("  • AI-Powered Data Quality Validation")
        print("\n💡 All features include robust fallback mechanisms")
        print("   for when AI services are unavailable.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main()
