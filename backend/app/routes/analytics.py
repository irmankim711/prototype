from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Form, FormSubmission, db
from ..services.analytics_service import DashboardAnalytics
from datetime import datetime
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_analytics_dashboard_stats():
    """Get comprehensive analytics dashboard statistics"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    real_time_stats = analytics.get_real_time_stats()
    
    return jsonify(real_time_stats)

@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_submission_trends():
    """Get submission trends over time"""
    current_user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    
    analytics = DashboardAnalytics(current_user_id)
    trends = analytics.get_submission_trends(days)
    
    return jsonify(trends)

@analytics_bp.route('/top-forms', methods=['GET'])
@jwt_required()
def get_top_performing_forms():
    """Get top performing forms"""
    current_user_id = get_jwt_identity()
    limit = request.args.get('limit', 5, type=int)
    
    analytics = DashboardAnalytics(current_user_id)
    top_forms = analytics.get_top_performing_forms(limit)
    
    return jsonify({'forms': top_forms})

@analytics_bp.route('/field-analytics/<int:form_id>', methods=['GET'])
@jwt_required()
def get_field_analytics(form_id):
    """Get field completion analytics for a specific form"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    field_data = analytics.get_field_analytics(form_id)
    
    return jsonify(field_data)

@analytics_bp.route('/geographic', methods=['GET'])
@jwt_required()
def get_geographic_distribution():
    """Get geographic distribution of submissions"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    geo_data = analytics.get_geographic_distribution()
    
    return jsonify(geo_data)

@analytics_bp.route('/time-of-day', methods=['GET'])
@jwt_required()
def get_time_of_day_analytics():
    """Get submission patterns by time of day"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    time_data = analytics.get_submission_by_time_of_day()
    
    return jsonify(time_data)

@analytics_bp.route('/performance-comparison', methods=['GET'])
@jwt_required()
def get_form_performance_comparison():
    """Get comparative performance analysis of all forms"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    performance_data = analytics.get_form_performance_comparison()
    
    return jsonify(performance_data)

@analytics_bp.route('/real-time', methods=['GET'])
@jwt_required()
def get_real_time_analytics():
    """Get real-time dashboard updates"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    real_time_data = analytics.get_real_time_stats()
    
    return jsonify(real_time_data)

@analytics_bp.route('/charts/<chart_type>', methods=['GET'])
@jwt_required()
def get_chart_data(chart_type):
    """Get chart data for specific visualization types"""
    current_user_id = get_jwt_identity()
    
    analytics = DashboardAnalytics(current_user_id)
    
    if chart_type == 'submissions-trend':
        days = request.args.get('days', 30, type=int)
        data = analytics.get_submission_trends(days)
        return jsonify({
            'type': 'line',
            'title': f'Submission Trends (Last {days} Days)',
            'data': {
                'labels': data['labels'],
                'datasets': [{
                    'label': 'Daily Submissions',
                    'data': data['data'],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'fill': True,
                    'tension': 0.4
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'top'
                    },
                    'title': {
                        'display': True,
                        'text': f'Submission Trends (Last {days} Days)'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        })
        
    elif chart_type == 'time-distribution':
        data = analytics.get_submission_by_time_of_day()
        return jsonify({
            'type': 'bar',
            'title': 'Submissions by Time of Day',
            'data': {
                'labels': data['labels'],
                'datasets': [{
                    'label': 'Submissions by Hour',
                    'data': data['hourly_data'],
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'top'
                    },
                    'title': {
                        'display': True,
                        'text': 'Submissions by Time of Day'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        })
        
    elif chart_type == 'top-forms':
        limit = request.args.get('limit', 5, type=int)
        forms = analytics.get_top_performing_forms(limit)
        return jsonify({
            'type': 'doughnut',
            'title': f'Top {limit} Performing Forms',
            'data': {
                'labels': [form['form_name'] for form in forms],
                'datasets': [{
                    'data': [form['submissions'] for form in forms],
                    'backgroundColor': [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
                    ][:limit]
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'right'
                    },
                    'title': {
                        'display': True,
                        'text': f'Top {limit} Performing Forms'
                    }
                }
            }
        })
        
    elif chart_type == 'performance-comparison':
        performance_data = analytics.get_form_performance_comparison()
        forms = performance_data['forms'][:10]  # Limit to top 10 for chart readability
        
        return jsonify({
            'type': 'bar',
            'title': 'Form Performance Comparison',
            'data': {
                'labels': [form['form_title'][:20] + '...' if len(form['form_title']) > 20 else form['form_title'] for form in forms],
                'datasets': [
                    {
                        'label': 'Total Submissions',
                        'data': [form['total_submissions'] for form in forms],
                        'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                        'yAxisID': 'y'
                    },
                    {
                        'label': 'Performance Score',
                        'data': [form['performance_score'] for form in forms],
                        'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                        'yAxisID': 'y1'
                    }
                ]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'top'
                    },
                    'title': {
                        'display': True,
                        'text': 'Form Performance Comparison'
                    }
                },
                'scales': {
                    'y': {
                        'type': 'linear',
                        'display': True,
                        'position': 'left',
                        'beginAtZero': True
                    },
                    'y1': {
                        'type': 'linear',
                        'display': True,
                        'position': 'right',
                        'beginAtZero': True,
                        'max': 100,
                        'grid': {
                            'drawOnChartArea': False
                        }
                    }
                }
            }
        })
        
    elif chart_type == 'geographic':
        geo_data = analytics.get_geographic_distribution()
        return jsonify({
            'type': 'pie',
            'title': 'Geographic Distribution',
            'data': {
                'labels': [country['name'] for country in geo_data['countries']],
                'datasets': [{
                    'data': [country['submissions'] for country in geo_data['countries']],
                    'backgroundColor': [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
                    ]
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'right'
                    },
                    'title': {
                        'display': True,
                        'text': 'Geographic Distribution of Submissions'
                    }
                }
            }
        })
    
    return jsonify({'error': 'Invalid chart type'}), 400
