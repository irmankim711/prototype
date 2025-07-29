"""
Enhanced AI Service Module for Report Analysis and Generation
Provides comprehensive AI-powered functionalities using OpenAI and Google AI APIs
"""

import openai
import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class AIService:
    """
    Enhanced AI Service class that handles various AI operations including:
    - Advanced data analysis and insights
    - Report content generation
    - Template optimization suggestions
    - Content summarization
    - Smart data validation
    - Placeholder suggestions
    """
    
    def __init__(self):
        """Initialize the AI service with API keys"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_ai_api_key = os.getenv('GOOGLE_AI_API_KEY')
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found in environment variables")
        else:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

    def analyze_data(self, data: Dict[str, Any], context: str = "general") -> Dict[str, Any]:
        """
        Enhanced data analysis with comprehensive insights
        """
        try:
            # Prepare data for analysis
            data_summary = self._prepare_data_summary(data)
            
            # Try AI analysis first
            try:
                # Create comprehensive analysis prompt
                prompt = f"""
                Analyze the following data in the context of {context} analysis and provide comprehensive insights:
                
                Data Summary:
                {data_summary}
                
                Please provide a detailed analysis including:
                1. Executive summary of key findings
                2. Important insights and patterns discovered
                3. Statistical observations and trends
                4. Any anomalies or concerning patterns
                5. Actionable recommendations
                6. Risk assessment if applicable
                7. Opportunities identified
                
                Format your response as valid JSON:
                {{
                    "summary": "Brief executive summary of findings",
                    "insights": ["insight1", "insight2", "insight3"],
                    "patterns": ["pattern1", "pattern2"],
                    "anomalies": ["anomaly1", "anomaly2"],
                    "recommendations": ["recommendation1", "recommendation2"],
                    "risks": ["risk1", "risk2"],
                    "opportunities": ["opportunity1", "opportunity2"],
                    "confidence_score": 0.85,
                    "data_quality": "high|medium|low",
                    "analysis_depth": "comprehensive"
                }}
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert data analyst. Always respond with valid JSON and provide comprehensive, actionable insights."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                # Parse the response
                analysis_result = self._parse_json_response(response.choices[0].message.content)
                
                return {
                    'success': True,
                    'summary': analysis_result.get('summary', 'AI analysis completed successfully'),
                    'insights': analysis_result.get('insights', []),
                    'patterns': analysis_result.get('patterns', []),
                    'anomalies': analysis_result.get('anomalies', []),
                    'recommendations': analysis_result.get('recommendations', []),
                    'risks': analysis_result.get('risks', []),
                    'opportunities': analysis_result.get('opportunities', []),
                    'confidence_score': analysis_result.get('confidence_score', 0.8),
                    'data_quality': analysis_result.get('data_quality', 'medium'),
                    'analysis_type': context,
                    'ai_powered': True,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as ai_error:
                # If AI fails (quota exceeded, API issues, etc.), fall back to rule-based analysis
                logger.warning(f"AI analysis failed, falling back to rule-based analysis: {str(ai_error)}")
                return self._fallback_analysis(data, context, data_summary)
            
        except Exception as e:
            logger.error(f"Error in enhanced data analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'summary': 'Analysis encountered technical difficulties',
                'insights': ['Unable to complete full analysis due to technical error'],
                'patterns': [],
                'anomalies': [],
                'recommendations': ['Please verify data format and try again'],
                'risks': ['Analysis incomplete'],
                'opportunities': [],
                'confidence_score': 0.0,
                'ai_powered': False,
                'timestamp': datetime.now().isoformat()
            }

    def _fallback_analysis(self, data: Dict[str, Any], context: str, data_summary: str) -> Dict[str, Any]:
        """
        Rule-based fallback analysis when AI is not available
        """
        try:
            insights = []
            patterns = []
            anomalies = []
            recommendations = []
            risks = []
            opportunities = []
            
            # Basic data analysis
            if isinstance(data, dict):
                # Count different data types
                numeric_fields = []
                text_fields = []
                list_fields = []
                empty_fields = []
                
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        numeric_fields.append(key)
                    elif isinstance(value, str):
                        if value.strip() == "":
                            empty_fields.append(key)
                        else:
                            text_fields.append(key)
                    elif isinstance(value, list):
                        list_fields.append(key)
                
                # Generate insights based on data structure
                if numeric_fields:
                    insights.append(f"Dataset contains {len(numeric_fields)} numeric fields for quantitative analysis")
                    
                    # Basic statistical insights
                    numeric_values = [data[field] for field in numeric_fields if isinstance(data[field], (int, float))]
                    if numeric_values:
                        avg_value = sum(numeric_values) / len(numeric_values)
                        max_value = max(numeric_values)
                        min_value = min(numeric_values)
                        
                        insights.append(f"Numeric data range: {min_value:,.0f} to {max_value:,.0f}")
                        patterns.append(f"Average numeric value: {avg_value:,.0f}")
                
                if empty_fields:
                    anomalies.append(f"Found {len(empty_fields)} empty fields that may need attention")
                    risks.append("Incomplete data may affect analysis accuracy")
                    recommendations.append("Consider filling missing data or marking as intentionally blank")
                
                if list_fields:
                    patterns.append(f"Dataset includes {len(list_fields)} array/list fields with complex data")
                    opportunities.append("List fields can be analyzed for trends and patterns")
                
                # Context-specific analysis
                if context.lower() in ['financial', 'finance']:
                    if any('revenue' in key.lower() or 'profit' in key.lower() or 'income' in key.lower() for key in data.keys()):
                        insights.append("Financial data detected - suitable for revenue and profitability analysis")
                        recommendations.append("Consider calculating key financial ratios and growth rates")
                    
                elif context.lower() in ['operational', 'operations']:
                    if any('employee' in key.lower() or 'staff' in key.lower() or 'team' in key.lower() for key in data.keys()):
                        insights.append("Operational data with human resources metrics identified")
                        recommendations.append("Analyze workforce efficiency and capacity utilization")
                
                elif context.lower() in ['performance', 'kpi']:
                    insights.append("Performance data suitable for KPI tracking and benchmarking")
                    recommendations.append("Establish baseline metrics and set improvement targets")
                
                # Data quality assessment
                total_fields = len(data)
                quality_score = max(0.5, 1.0 - (len(empty_fields) / total_fields) if total_fields > 0 else 0.5)
                
                summary = f"Analyzed {total_fields} data fields in {context} context. "
                if quality_score > 0.8:
                    summary += "Data quality is good with minimal missing values."
                elif quality_score > 0.6:
                    summary += "Data quality is acceptable but could be improved."
                else:
                    summary += "Data quality needs attention due to missing values."
                
            else:
                # Non-dictionary data
                insights.append("Simple data structure provided")
                recommendations.append("Consider providing structured data for more detailed analysis")
                summary = f"Basic {context} analysis completed on simple data structure"
                quality_score = 0.6
            
            return {
                'success': True,
                'summary': summary,
                'insights': insights,
                'patterns': patterns,
                'anomalies': anomalies,
                'recommendations': recommendations,
                'risks': risks,
                'opportunities': opportunities,
                'confidence_score': quality_score,
                'data_quality': 'high' if quality_score > 0.8 else 'medium' if quality_score > 0.6 else 'low',
                'analysis_type': context,
                'ai_powered': False,
                'fallback_reason': 'AI service unavailable - used rule-based analysis',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in fallback analysis: {str(e)}")
            return {
                'success': True,
                'summary': 'Basic analysis completed with limited functionality',
                'insights': ['Data structure analyzed successfully'],
                'patterns': ['Standard data format detected'],
                'anomalies': [],
                'recommendations': ['Consider upgrading to AI-powered analysis for deeper insights'],
                'risks': [],
                'opportunities': ['Data appears suitable for further analysis'],
                'confidence_score': 0.5,
                'data_quality': 'medium',
                'analysis_type': context,
                'ai_powered': False,
                'fallback_reason': 'Technical limitations in analysis engine',
                'timestamp': datetime.now().isoformat()
            }

    def generate_report_suggestions(self, data: Dict[str, Any], report_type: str = "general") -> Dict[str, Any]:
        """Enhanced report suggestions with specific context"""
        try:
            # Try AI-powered suggestions first
            try:
                prompt = f"""
                Based on this data for a {report_type} report, provide comprehensive suggestions:
                
                Data: {json.dumps(data, indent=2)[:1500]}
                
                Generate structured suggestions for:
                1. Key metrics to prominently display
                2. Most effective visualizations for this data
                3. Critical trends and patterns to highlight
                4. Areas requiring immediate attention
                5. Executive summary points
                6. Detailed analysis sections
                7. Recommendations and next steps
                
                Format as JSON:
                {{
                    "key_metrics": [
                        {{"metric": "metric_name", "value": "value", "importance": "high|medium|low", "description": "why important"}}
                    ],
                    "visualizations": [
                        {{"type": "chart_type", "data_fields": ["field1", "field2"], "purpose": "what it shows"}}
                    ],
                    "trends": ["trend1", "trend2"],
                    "critical_areas": ["area1", "area2"],
                    "executive_points": ["point1", "point2"],
                    "detailed_sections": ["section1", "section2"],
                    "next_steps": ["step1", "step2"],
                    "report_quality_score": 0.9
                }}
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a report generation expert. Provide actionable, specific suggestions for creating professional reports."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.6
                )
                
                suggestions = self._parse_json_response(response.choices[0].message.content or "")
                
                return {
                    'success': True,
                    'suggestions': suggestions,
                    'report_type': report_type,
                    'ai_powered': True,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as ai_error:
                logger.warning(f"AI report suggestions failed, using fallback: {str(ai_error)}")
                return self._fallback_report_suggestions(data, report_type)
            
        except Exception as e:
            logger.error(f"Error generating report suggestions: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': {},
                'timestamp': datetime.now().isoformat()
            }

    def _fallback_report_suggestions(self, data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Fallback report suggestions using rule-based logic"""
        try:
            key_metrics = []
            visualizations = []
            trends = []
            critical_areas = []
            executive_points = []
            detailed_sections = []
            next_steps = []
            
            # Analyze data structure for suggestions
            if isinstance(data, dict):
                # Identify key metrics based on data types and names
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        importance = "high" if any(keyword in key.lower() for keyword in ['revenue', 'profit', 'cost', 'sales', 'total']) else "medium"
                        key_metrics.append({
                            "metric": key.replace('_', ' ').title(),
                            "value": str(value),
                            "importance": importance,
                            "description": f"Key {report_type} metric"
                        })
                    
                    if isinstance(value, list) and len(value) > 1:
                        visualizations.append({
                            "type": "line_chart" if "time" in key.lower() or "date" in key.lower() else "bar_chart",
                            "data_fields": [key],
                            "purpose": f"Show trends in {key.replace('_', ' ')}"
                        })
                
                # Report type specific suggestions
                if report_type.lower() in ['financial', 'finance', 'quarterly_financial']:
                    executive_points.extend([
                        "Financial performance overview",
                        "Key revenue and cost drivers",
                        "Profitability analysis"
                    ])
                    detailed_sections.extend([
                        "Revenue Analysis",
                        "Cost Structure",
                        "Financial Ratios",
                        "Year-over-Year Comparison"
                    ])
                    next_steps.extend([
                        "Review budget vs actual performance",
                        "Identify cost optimization opportunities",
                        "Plan for next quarter/year"
                    ])
                
                elif report_type.lower() in ['operational', 'operations']:
                    executive_points.extend([
                        "Operational efficiency metrics",
                        "Resource utilization",
                        "Process improvements"
                    ])
                    detailed_sections.extend([
                        "Process Analysis",
                        "Resource Allocation",
                        "Efficiency Metrics",
                        "Improvement Opportunities"
                    ])
                
                else:  # General reports
                    executive_points.extend([
                        "Key findings summary",
                        "Performance highlights",
                        "Areas for improvement"
                    ])
                    detailed_sections.extend([
                        "Data Analysis",
                        "Key Insights",
                        "Recommendations"
                    ])
                
                # General next steps
                next_steps.extend([
                    "Review and validate findings",
                    "Implement recommended actions",
                    "Schedule follow-up analysis"
                ])
                
                # Basic trend analysis
                if key_metrics:
                    trends.append("Quantitative data available for trend analysis")
                
                if len(data) > 5:
                    critical_areas.append("Large dataset requires prioritized focus areas")
                
            suggestions = {
                "key_metrics": key_metrics[:5],  # Limit to top 5
                "visualizations": visualizations[:3],  # Limit to top 3
                "trends": trends,
                "critical_areas": critical_areas,
                "executive_points": executive_points,
                "detailed_sections": detailed_sections,
                "next_steps": next_steps,
                "report_quality_score": 0.7
            }
            
            return {
                'success': True,
                'suggestions': suggestions,
                'report_type': report_type,
                'ai_powered': False,
                'fallback_reason': 'Using rule-based suggestions',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in fallback report suggestions: {str(e)}")
            return {
                'success': True,
                'suggestions': {
                    "key_metrics": [],
                    "executive_points": ["Report analysis completed"],
                    "next_steps": ["Review generated report"]
                },
                'report_type': report_type,
                'ai_powered': False,
                'timestamp': datetime.now().isoformat()
            }

    def optimize_template(self, template_content: str, placeholders: List[str], template_type: str = "general") -> Dict[str, Any]:
        """
        Analyze template and provide comprehensive optimization suggestions
        """
        try:
            prompt = f"""
            Analyze this {template_type} template and provide optimization recommendations:
            
            Template Content Sample: {template_content[:1000]}...
            Current Placeholders: {placeholders}
            
            Provide suggestions for:
            1. Improved placeholder names (more descriptive and professional)
            2. Missing placeholders that would enhance the template
            3. Template structure and organization improvements
            4. Content flow and readability enhancements
            5. Professional formatting recommendations
            6. Industry-specific improvements for {template_type} reports
            
            Format as JSON:
            {{
                "placeholder_improvements": {{"current_name": "suggested_name"}},
                "missing_placeholders": [
                    {{"name": "placeholder_name", "description": "what it represents", "section": "where to place"}}
                ],
                "structure_improvements": ["improvement1", "improvement2"],
                "content_flow": ["suggestion1", "suggestion2"],
                "formatting_suggestions": ["format1", "format2"],
                "industry_specific": ["specific1", "specific2"],
                "overall_quality_score": 0.85,
                "implementation_priority": ["high_priority1", "medium_priority1", "low_priority1"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a template optimization expert. Provide specific, actionable suggestions for improving document templates."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.6
            )
            
            optimization = self._parse_json_response(response.choices[0].message.content)
            
            return {
                'success': True,
                'optimization': optimization,
                'template_type': template_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing template: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'optimization': {},
                'timestamp': datetime.now().isoformat()
            }

    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive AI-powered data quality validation
        """
        try:
            prompt = f"""
            Perform comprehensive data quality analysis on this dataset:
            
            Data: {json.dumps(data, indent=2)[:1500]}
            
            Analyze for:
            1. Completeness (missing values, empty fields)
            2. Consistency (data type mismatches, format inconsistencies)
            3. Accuracy (logical inconsistencies, impossible values)
            4. Validity (format compliance, range compliance)
            5. Uniqueness (duplicate detection)
            6. Timeliness (date consistency, temporal logic)
            
            Format as JSON:
            {{
                "overall_quality_score": 0.85,
                "completeness_score": 0.90,
                "consistency_score": 0.80,
                "accuracy_score": 0.85,
                "validity_score": 0.90,
                "issues_found": [
                    {{"type": "completeness", "field": "field_name", "severity": "high", "description": "detailed issue", "suggestion": "how to fix"}}
                ],
                "critical_issues": ["issue1", "issue2"],
                "warnings": ["warning1", "warning2"],
                "recommendations": ["rec1", "rec2"],
                "data_readiness": "ready|needs_attention|not_ready",
                "improvement_suggestions": ["suggestion1", "suggestion2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data quality expert. Provide thorough analysis and actionable recommendations for data improvement."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.5
            )
            
            validation = self._parse_json_response(response.choices[0].message.content)
            
            return {
                'success': True,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating data quality: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation': {
                    'overall_quality_score': 0.0,
                    'data_readiness': 'unknown',
                    'issues_found': [{'type': 'technical', 'description': 'Validation failed due to technical error'}]
                },
                'timestamp': datetime.now().isoformat()
            }

    def generate_smart_placeholders(self, context: str, industry: str = "general") -> Dict[str, Any]:
        """
        Generate intelligent placeholder suggestions based on context and industry
        """
        try:
            # Try AI-powered suggestions first
            try:
                prompt = f"""
                Generate comprehensive placeholder suggestions for a {context} report in the {industry} industry.
                
                Provide placeholders categorized by:
                1. Basic information (always needed)
                2. Financial/Performance metrics
                3. Operational details
                4. Analytical insights
                5. Industry-specific requirements
                6. Compliance and regulatory (if applicable)
                
                Format as JSON:
                {{
                    "basic_placeholders": [
                        {{"name": "{{report_title}}", "description": "Main title of the report", "example": "Q4 2024 Performance Report", "required": true}},
                        {{"name": "{{report_date}}", "description": "Report generation date", "example": "December 31, 2024", "required": true}}
                    ],
                    "financial_metrics": [
                        {{"name": "{{total_revenue}}", "description": "Total revenue for the period", "example": "$1,250,000", "format": "currency"}}
                    ],
                    "operational_details": [
                        {{"name": "{{team_size}}", "description": "Current team size", "example": "25 employees", "format": "number"}}
                    ],
                    "analytical_insights": [
                        {{"name": "{{key_insight_1}}", "description": "Primary analytical insight", "example": "Revenue increased by 15% YoY", "dynamic": true}}
                    ],
                    "industry_specific": [
                        {{"name": "{{industry_metric}}", "description": "Industry-specific KPI", "example": "varies by industry", "context": "{industry}"}}
                    ],
                    "compliance_regulatory": [
                        {{"name": "{{compliance_status}}", "description": "Regulatory compliance status", "example": "Fully Compliant", "optional": true}}
                    ]
                }}
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert in report templating and business documentation. Provide comprehensive, practical placeholder suggestions."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.6
                )
                
                placeholders = self._parse_json_response(response.choices[0].message.content or "")
                
                return {
                    'success': True,
                    'placeholders': placeholders,
                    'context': context,
                    'industry': industry,
                    'ai_powered': True,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as ai_error:
                logger.warning(f"AI placeholder generation failed, using fallback: {str(ai_error)}")
                return self._fallback_smart_placeholders(context, industry)
            
        except Exception as e:
            logger.error(f"Error generating smart placeholders: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'placeholders': {},
                'timestamp': datetime.now().isoformat()
            }

    def _fallback_smart_placeholders(self, context: str, industry: str) -> Dict[str, Any]:
        """Fallback placeholder generation using predefined templates"""
        try:
            # Basic placeholders that apply to all reports
            basic_placeholders = [
                {"name": "{report_title}", "description": "Main title of the report", "example": f"{context.title()} Report", "required": True},
                {"name": "{report_date}", "description": "Report generation date", "example": datetime.now().strftime("%B %d, %Y"), "required": True},
                {"name": "{author_name}", "description": "Report author", "example": "John Doe", "required": True},
                {"name": "{company_name}", "description": "Company/Organization name", "example": "ABC Corporation", "required": True},
                {"name": "{period}", "description": "Reporting period", "example": "Q4 2024", "required": True}
            ]
            
            # Context-specific placeholders
            financial_metrics = []
            operational_details = []
            analytical_insights = []
            industry_specific = []
            compliance_regulatory = []
            
            if context.lower() in ['financial', 'finance', 'quarterly_financial']:
                financial_metrics = [
                    {"name": "{total_revenue}", "description": "Total revenue for the period", "example": "$1,250,000", "format": "currency"},
                    {"name": "{total_expenses}", "description": "Total expenses", "example": "$980,000", "format": "currency"},
                    {"name": "{net_profit}", "description": "Net profit", "example": "$270,000", "format": "currency"},
                    {"name": "{profit_margin}", "description": "Profit margin percentage", "example": "21.6%", "format": "percentage"},
                    {"name": "{growth_rate}", "description": "Growth rate compared to previous period", "example": "15%", "format": "percentage"}
                ]
                analytical_insights = [
                    {"name": "{key_financial_insight}", "description": "Primary financial insight", "example": "Revenue increased by 15% YoY", "dynamic": True},
                    {"name": "{cost_analysis}", "description": "Cost analysis summary", "example": "Operating costs remained stable", "dynamic": True},
                    {"name": "{financial_recommendation}", "description": "Financial recommendation", "example": "Focus on margin improvement", "dynamic": True}
                ]
            
            elif context.lower() in ['operational', 'operations']:
                operational_details = [
                    {"name": "{team_size}", "description": "Current team size", "example": "25 employees", "format": "number"},
                    {"name": "{productivity_metric}", "description": "Key productivity measure", "example": "95% efficiency", "format": "percentage"},
                    {"name": "{project_count}", "description": "Number of active projects", "example": "12 projects", "format": "number"},
                    {"name": "{completion_rate}", "description": "Project completion rate", "example": "87%", "format": "percentage"}
                ]
                analytical_insights = [
                    {"name": "{operational_insight}", "description": "Primary operational insight", "example": "Team productivity increased", "dynamic": True},
                    {"name": "{efficiency_analysis}", "description": "Efficiency analysis", "example": "Process improvements reduced waste", "dynamic": True}
                ]
            
            elif context.lower() in ['performance', 'kpi']:
                operational_details = [
                    {"name": "{primary_kpi}", "description": "Primary KPI value", "example": "Target achieved at 105%", "format": "percentage"},
                    {"name": "{secondary_kpi}", "description": "Secondary KPI value", "example": "Customer satisfaction: 4.5/5", "format": "rating"},
                    {"name": "{benchmark_comparison}", "description": "Comparison to benchmark", "example": "15% above industry average", "format": "percentage"}
                ]
            
            # Industry-specific placeholders
            if industry.lower() == 'technology':
                industry_specific = [
                    {"name": "{user_growth}", "description": "User base growth", "example": "25% monthly growth", "context": "technology"},
                    {"name": "{system_uptime}", "description": "System uptime percentage", "example": "99.9%", "context": "technology"},
                    {"name": "{feature_releases}", "description": "Number of feature releases", "example": "8 releases", "context": "technology"}
                ]
            elif industry.lower() == 'healthcare':
                industry_specific = [
                    {"name": "{patient_satisfaction}", "description": "Patient satisfaction score", "example": "4.7/5", "context": "healthcare"},
                    {"name": "{safety_metrics}", "description": "Safety incident rate", "example": "0.02%", "context": "healthcare"}
                ]
            elif industry.lower() == 'manufacturing':
                industry_specific = [
                    {"name": "{production_volume}", "description": "Production volume", "example": "10,000 units", "context": "manufacturing"},
                    {"name": "{quality_rate}", "description": "Quality rate", "example": "99.5%", "context": "manufacturing"},
                    {"name": "{downtime}", "description": "Equipment downtime", "example": "2.3 hours", "context": "manufacturing"}
                ]
            else:
                industry_specific = [
                    {"name": "{industry_kpi}", "description": f"Key {industry} industry metric", "example": "Industry-specific value", "context": industry}
                ]
            
            # Basic compliance placeholders
            compliance_regulatory = [
                {"name": "{compliance_status}", "description": "Overall compliance status", "example": "Fully Compliant", "optional": True},
                {"name": "{audit_date}", "description": "Last audit date", "example": "December 2024", "optional": True},
                {"name": "{regulatory_notes}", "description": "Regulatory compliance notes", "example": "All requirements met", "optional": True}
            ]
            
            placeholders = {
                "basic_placeholders": basic_placeholders,
                "financial_metrics": financial_metrics,
                "operational_details": operational_details,
                "analytical_insights": analytical_insights,
                "industry_specific": industry_specific,
                "compliance_regulatory": compliance_regulatory
            }
            
            return {
                'success': True,
                'placeholders': placeholders,
                'context': context,
                'industry': industry,
                'ai_powered': False,
                'fallback_reason': 'Using predefined placeholder templates',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in fallback placeholder generation: {str(e)}")
            return {
                'success': True,
                'placeholders': {
                    "basic_placeholders": [
                        {"name": "{report_title}", "description": "Report title", "example": "Report", "required": True},
                        {"name": "{date}", "description": "Current date", "example": datetime.now().strftime("%Y-%m-%d"), "required": True}
                    ]
                },
                'context': context,
                'industry': industry,
                'ai_powered': False,
                'timestamp': datetime.now().isoformat()
            }

    def _prepare_data_summary(self, data: Dict[str, Any]) -> str:
        """Prepare a structured summary of the data for analysis"""
        try:
            summary_parts = []
            
            if isinstance(data, dict):
                summary_parts.append(f"Dataset contains {len(data)} top-level fields:")
                
                for key, value in list(data.items())[:15]:  # Limit to first 15 items
                    if isinstance(value, list):
                        summary_parts.append(f"- {key}: List with {len(value)} items")
                    elif isinstance(value, dict):
                        summary_parts.append(f"- {key}: Object with {len(value)} properties")
                    elif isinstance(value, (int, float)):
                        summary_parts.append(f"- {key}: {type(value).__name__} = {value}")
                    else:
                        value_str = str(value)[:100]
                        summary_parts.append(f"- {key}: {type(value).__name__} = {value_str}")
                
                if len(data) > 15:
                    summary_parts.append(f"... and {len(data) - 15} more fields")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error preparing data summary: {str(e)}")
            return "Data summary unavailable due to formatting issues"

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from AI with error handling"""
        try:
            # Clean the response
            response = response.strip()
            
            # Find JSON content
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != -1:
                json_str = response[start:end]
                return json.loads(json_str)
            
            # If no JSON found, try to extract key information
            logger.warning("No valid JSON found in AI response, attempting text parsing")
            return self._extract_text_content(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return self._extract_text_content(response)
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return {}

    def _extract_text_content(self, text: str) -> Dict[str, Any]:
        """Extract meaningful content from non-JSON text response"""
        try:
            # Basic extraction patterns
            summary_pattern = r'summary[:\s]*(.*?)(?=\n|\.|$)'
            insights_pattern = r'insight[s]?[:\s]*["\']?(.*?)["\']?(?=\n|,|$)'
            
            summary_match = re.search(summary_pattern, text, re.IGNORECASE)
            insights_matches = re.findall(insights_pattern, text, re.IGNORECASE)
            
            return {
                'summary': summary_match.group(1).strip() if summary_match else 'Analysis completed',
                'insights': [insight.strip() for insight in insights_matches[:3]],
                'recommendations': ['Please review the generated analysis'],
                'parsed_from_text': True
            }
            
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
            return {'error': 'Unable to parse response', 'raw_text': text[:200]}

# Global AI service instance
ai_service = AIService()
