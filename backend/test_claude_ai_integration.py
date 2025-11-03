"""
Test script for Claude AI integration
Tests the AI report service functionality
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_ai_service_initialization():
    """Test AI service initialization"""
    print("=" * 60)
    print("Testing Claude AI Service Initialization")
    print("=" * 60)

    try:
        from app.services.ai_report_service import AIReportService

        service = AIReportService()

        print(f"✓ Service initialized successfully")
        print(f"  - AI Enabled: {service.ai_enabled}")

        if service.ai_enabled:
            print(f"  - Client configured: {service.client is not None}")
        else:
            print(f"  - ANTHROPIC_API_KEY not found in environment")
            print(f"  - Service will use fallback methods")

        return service

    except Exception as e:
        print(f"✗ Failed to initialize service: {str(e)}")
        return None


def test_generate_report_content(service):
    """Test report content generation"""
    print("\n" + "=" * 60)
    print("Testing Report Content Generation")
    print("=" * 60)

    # Sample test data
    test_data = [
        {"product": "Widget A", "sales": 1500, "revenue": 45000, "region": "North"},
        {"product": "Widget B", "sales": 2000, "revenue": 60000, "region": "South"},
        {"product": "Widget C", "sales": 1200, "revenue": 36000, "region": "East"},
        {"product": "Widget D", "sales": 1800, "revenue": 54000, "region": "West"},
    ]

    try:
        result = service.generate_report_content(
            data=test_data,
            report_title="Q4 Sales Analysis",
            report_type="summary"
        )

        print(f"✓ Report generation completed")
        print(f"  - Success: {result.get('success')}")
        print(f"  - AI Generated: {result.get('ai_generated')}")
        print(f"  - Sections: {list(result.get('content', {}).keys())}")

        if result.get('ai_generated'):
            print(f"  - Model: {result.get('model')}")

        return result

    except Exception as e:
        print(f"✗ Report generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_executive_summary(service):
    """Test executive summary generation"""
    print("\n" + "=" * 60)
    print("Testing Executive Summary Generation")
    print("=" * 60)

    test_data = [
        {"quarter": "Q1", "revenue": 125000, "profit": 25000},
        {"quarter": "Q2", "revenue": 135000, "profit": 28000},
        {"quarter": "Q3", "revenue": 142000, "profit": 30000},
        {"quarter": "Q4", "revenue": 158000, "profit": 35000},
    ]

    try:
        summary = service.generate_executive_summary(data=test_data)

        print(f"✓ Executive summary generated")
        print(f"  - Length: {len(summary)} characters")
        print(f"\nSummary Preview:")
        print("-" * 60)
        print(summary[:300] + "..." if len(summary) > 300 else summary)

        return summary

    except Exception as e:
        print(f"✗ Executive summary failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_data_insights(service):
    """Test data insights analysis"""
    print("\n" + "=" * 60)
    print("Testing Data Insights Analysis")
    print("=" * 60)

    test_data = [
        {"month": "Jan", "visitors": 5000, "conversions": 250, "bounce_rate": 45},
        {"month": "Feb", "visitors": 5500, "conversions": 300, "bounce_rate": 42},
        {"month": "Mar", "visitors": 6200, "conversions": 350, "bounce_rate": 38},
        {"month": "Apr", "visitors": 7000, "conversions": 420, "bounce_rate": 35},
    ]

    try:
        insights = service.analyze_data_insights(data=test_data)

        print(f"✓ Insights analysis completed")
        print(f"  - Key Trends: {len(insights.get('key_trends', []))} found")
        print(f"  - Anomalies: {len(insights.get('anomalies', []))} found")
        print(f"  - Recommendations: {len(insights.get('recommendations', []))} provided")

        print(f"\nKey Trends:")
        for i, trend in enumerate(insights.get('key_trends', [])[:3], 1):
            print(f"  {i}. {trend}")

        return insights

    except Exception as e:
        print(f"✗ Insights analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_visualization_suggestions(service):
    """Test visualization suggestions"""
    print("\n" + "=" * 60)
    print("Testing Visualization Suggestions")
    print("=" * 60)

    test_data = [
        {"category": "Electronics", "sales": 45000, "units": 120},
        {"category": "Clothing", "sales": 32000, "units": 450},
        {"category": "Food", "sales": 28000, "units": 890},
        {"category": "Books", "sales": 15000, "units": 320},
    ]

    try:
        suggestions = service.suggest_visualizations(data=test_data)

        print(f"✓ Visualization suggestions generated")
        print(f"  - Suggestions: {len(suggestions)} provided")

        for i, viz in enumerate(suggestions[:3], 1):
            print(f"\n  {i}. {viz.get('title')}")
            print(f"     Type: {viz.get('type')}")
            print(f"     Priority: {viz.get('priority')}")

        return suggestions

    except Exception as e:
        print(f"✗ Visualization suggestions failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "CLAUDE AI INTEGRATION TEST SUITE" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    # Check environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✓ ANTHROPIC_API_KEY found in environment")
        print(f"  Key preview: {api_key[:10]}...{api_key[-4:]}")
    else:
        print(f"⚠ ANTHROPIC_API_KEY not found")
        print(f"  Tests will run in fallback mode")

    print("\n")

    # Initialize service
    service = test_ai_service_initialization()
    if not service:
        print("\n✗ Service initialization failed. Exiting.")
        return

    # Run tests
    test_generate_report_content(service)
    test_executive_summary(service)
    test_data_insights(service)
    test_visualization_suggestions(service)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Add your ANTHROPIC_API_KEY to .env.production")
    print("2. Start the Flask backend server")
    print("3. Test the new AI endpoints:")
    print("   - POST /api/nextgen-report-builder/ai/generate-report-content")
    print("   - POST /api/nextgen-report-builder/ai/executive-summary")
    print("   - POST /api/nextgen-report-builder/ai/analyze-insights")
    print("   - POST /api/nextgen-report-builder/ai/suggest-visualizations")
    print("   - GET  /api/nextgen-report-builder/ai/status")
    print("\n")


if __name__ == "__main__":
    main()
