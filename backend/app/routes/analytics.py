from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from .. import db
from ..models import User, Form, FormSubmission
from ..services.analytics_service import DashboardAnalytics
from datetime import datetime
import json
import logging

# Configure logging for analytics routes
logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

def log_validation_error(route_name, error_type, details, received=None, expected=None):
    """Log detailed validation errors for debugging"""
    error_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'route': route_name,
        'error_type': error_type,
        'details': details,
        'received': received,
        'expected': expected,
        'request_info': {
            'method': request.method,
            'url': request.url,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'headers': dict(request.headers)
        }
    }
    
    logger.error(f"🚨 VALIDATION ERROR in {route_name}: {json.dumps(error_log, indent=2)}")
    current_app.logger.error(f"🚨 VALIDATION ERROR in {route_name}: {json.dumps(error_log, indent=2)}")
    
    return error_log

def validate_jwt_and_user():
    """Validate JWT token and extract user identity with detailed logging"""
    try:
        # Verify JWT token
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        
        logger.info(f"✅ JWT validation successful for user ID: {current_user_id}")
        
        # Validate user ID format
        if current_user_id is None:
            log_validation_error(
                'JWT_Validation',
                'missing_user_identity',
                'JWT token is valid but contains no user identity',
                received={'user_id': current_user_id},
                expected={'user_id': 'non-null string or integer'}
            )
            return None, "Missing user identity in token"
        
        # Validate user ID type
        if not isinstance(current_user_id, (str, int)):
            log_validation_error(
                'JWT_Validation',
                'invalid_user_id_type',
                f'User ID has unexpected type: {type(current_user_id)}',
                received={'user_id': current_user_id, 'type': str(type(current_user_id))},
                expected={'user_id': 'string or integer'}
            )
            return None, f"Invalid user ID type: {type(current_user_id)}"
        
        # Convert to string for consistency
        user_id_str = str(current_user_id)
        
        # Validate user ID format (should be numeric)
        try:
            user_id_int = int(user_id_str)
            if user_id_int <= 0:
                log_validation_error(
                    'JWT_Validation',
                    'invalid_user_id_value',
                    f'User ID must be positive integer, got: {user_id_int}',
                    received={'user_id': user_id_int},
                    expected={'user_id': 'positive integer > 0'}
                )
                return None, f"Invalid user ID value: {user_id_int}"
        except ValueError:
            log_validation_error(
                'JWT_Validation',
                'invalid_user_id_format',
                f'User ID must be numeric, got: {user_id_str}',
                received={'user_id': user_id_str},
                expected={'user_id': 'numeric string or integer'}
            )
            return None, f"Invalid user ID format: {user_id_str}"
        
        logger.info(f"✅ User ID validation successful: {user_id_int}")
        return user_id_int, None
        
    except Exception as e:
        error_msg = f"JWT validation failed: {str(e)}"
        log_validation_error(
            'JWT_Validation',
            'jwt_verification_failed',
            error_msg,
            received={'error': str(e)},
            expected={'valid_jwt_token': 'Bearer <token>'}
        )
        return None, error_msg

@analytics_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_analytics_dashboard_stats():
    """Get comprehensive analytics dashboard statistics"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        logger.info(f"📊 Fetching dashboard stats for user {user_id}")
        
        analytics = DashboardAnalytics(user_id)
        real_time_stats = analytics.get_real_time_stats()
        
        logger.info(f"✅ Dashboard stats retrieved successfully for user {user_id}")
        return jsonify(real_time_stats)
        
    except Exception as e:
        error_msg = f"Failed to fetch dashboard stats: {str(e)}"
        logger.error(f"🚨 Error in get_analytics_dashboard_stats: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_submission_trends():
    """Get submission trends over time"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        # Validate query parameters
        days_param = request.args.get('days', '30')
        try:
            days = int(days_param)
            if days <= 0 or days > 365:
                log_validation_error(
                    'get_submission_trends',
                    'invalid_days_parameter',
                    f'Days parameter must be between 1 and 365, got: {days}',
                    received={'days': days},
                    expected={'days': 'integer between 1 and 365'}
                )
                return jsonify({'error': 'validation_failed', 'message': 'Days must be between 1 and 365'}), 422
        except ValueError:
            log_validation_error(
                'get_submission_trends',
                'invalid_days_format',
                f'Days parameter must be numeric, got: {days_param}',
                received={'days': days_param},
                expected={'days': 'numeric string or integer'}
            )
            return jsonify({'error': 'validation_failed', 'message': 'Days parameter must be numeric'}), 422
        
        logger.info(f"📈 Fetching submission trends for user {user_id}, days: {days}")
        
        analytics = DashboardAnalytics(user_id)
        trends = analytics.get_submission_trends(days)
        
        logger.info(f"✅ Submission trends retrieved successfully for user {user_id}")
        return jsonify(trends)
        
    except Exception as e:
        error_msg = f"Failed to fetch submission trends: {str(e)}"
        logger.error(f"🚨 Error in get_submission_trends: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/top-forms', methods=['GET'])
@jwt_required()
def get_top_performing_forms():
    """Get top performing forms"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        # Validate query parameters
        limit_param = request.args.get('limit', '5')
        try:
            limit = int(limit_param)
            if limit <= 0 or limit > 100:
                log_validation_error(
                    'get_top_performing_forms',
                    'invalid_limit_parameter',
                    f'Limit parameter must be between 1 and 100, got: {limit}',
                    received={'limit': limit},
                    expected={'limit': 'integer between 1 and 100'}
                )
                return jsonify({'error': 'validation_failed', 'message': 'Limit must be between 1 and 100'}), 422
        except ValueError:
            log_validation_error(
                'get_top_performing_forms',
                'invalid_limit_format',
                f'Limit parameter must be numeric, got: {limit_param}',
                received={'limit': limit_param},
                expected={'limit': 'numeric string or integer'}
            )
            return jsonify({'error': 'validation_failed', 'message': 'Limit parameter must be numeric'}), 422
        
        logger.info(f"🏆 Fetching top performing forms for user {user_id}, limit: {limit}")
        
        analytics = DashboardAnalytics(user_id)
        top_forms = analytics.get_top_performing_forms(limit)
        
        logger.info(f"✅ Top performing forms retrieved successfully for user {user_id}")
        return jsonify({'forms': top_forms})
        
    except Exception as e:
        error_msg = f"Failed to fetch top performing forms: {str(e)}"
        logger.error(f"🚨 Error in get_top_performing_forms: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/field-analytics/<int:form_id>', methods=['GET'])
@jwt_required()
def get_field_analytics(form_id):
    """Get field completion analytics for a specific form"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        # Validate form_id parameter
        if form_id <= 0:
            log_validation_error(
                'get_field_analytics',
                'invalid_form_id',
                f'Form ID must be positive integer, got: {form_id}',
                received={'form_id': form_id},
                expected={'form_id': 'positive integer > 0'}
            )
            return jsonify({'error': 'validation_failed', 'message': 'Form ID must be positive'}), 422
        
        logger.info(f"📋 Fetching field analytics for user {user_id}, form ID: {form_id}")
        
        analytics = DashboardAnalytics(user_id)
        field_data = analytics.get_field_analytics(form_id)
        
        logger.info(f"✅ Field analytics retrieved successfully for user {user_id}, form {form_id}")
        return jsonify(field_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch field analytics: {str(e)}"
        logger.error(f"🚨 Error in get_field_analytics: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/geographic', methods=['GET'])
@jwt_required()
def get_geographic_distribution():
    """Get geographic distribution of submissions"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        logger.info(f"🌍 Fetching geographic distribution for user {user_id}")
        
        analytics = DashboardAnalytics(user_id)
        geo_data = analytics.get_geographic_distribution()
        
        logger.info(f"✅ Geographic distribution retrieved successfully for user {user_id}")
        return jsonify(geo_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch geographic distribution: {str(e)}"
        logger.error(f"🚨 Error in get_geographic_distribution: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/time-of-day', methods=['GET'])
@jwt_required()
def get_time_of_day_analytics():
    """Get submission patterns by time of day"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        logger.info(f"⏰ Fetching time of day analytics for user {user_id}")
        
        analytics = DashboardAnalytics(user_id)
        time_data = analytics.get_submission_by_time_of_day()
        
        logger.info(f"✅ Time of day analytics retrieved successfully for user {user_id}")
        return jsonify(time_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch time of day analytics: {str(e)}"
        logger.error(f"🚨 Error in get_time_of_day_analytics: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/performance-comparison', methods=['GET'])
@jwt_required()
def get_form_performance_comparison():
    """Get comparative performance analysis of all forms"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        logger.info(f"📊 Fetching performance comparison for user {user_id}")
        
        analytics = DashboardAnalytics(user_id)
        performance_data = analytics.get_form_performance_comparison()
        
        logger.info(f"✅ Performance comparison retrieved successfully for user {user_id}")
        return jsonify(performance_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch performance comparison: {str(e)}"
        logger.error(f"🚨 Error in get_form_performance_comparison: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/real-time', methods=['GET'])
@jwt_required()
def get_real_time_analytics():
    """Get real-time dashboard updates"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        logger.info(f"⚡ Fetching real-time analytics for user {user_id}")
        
        analytics = DashboardAnalytics(user_id)
        real_time_data = analytics.get_real_time_stats()
        
        logger.info(f"✅ Real-time analytics retrieved successfully for user {user_id}")
        return jsonify(real_time_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch real-time analytics: {str(e)}"
        logger.error(f"🚨 Error in get_real_time_analytics: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500

@analytics_bp.route('/charts/<chart_type>', methods=['GET'])
@jwt_required()
def get_chart_data(chart_type):
    """Get chart data for specific visualization types"""
    try:
        # Validate JWT and get user ID
        user_id, error = validate_jwt_and_user()
        if error:
            return jsonify({'error': 'authentication_failed', 'message': error}), 422
        
        # Validate chart_type parameter
        valid_chart_types = [
            'submissions-trend', 'time-distribution', 'top-forms', 
            'performance-comparison', 'geographic'
        ]
        
        if chart_type not in valid_chart_types:
            log_validation_error(
                'get_chart_data',
                'invalid_chart_type',
                f'Invalid chart type: {chart_type}',
                received={'chart_type': chart_type},
                expected={'chart_type': f'one of: {", ".join(valid_chart_types)}'}
            )
            return jsonify({'error': 'validation_failed', 'message': f'Invalid chart type: {chart_type}'}), 422
        
        logger.info(f"📊 Fetching chart data for user {user_id}, chart type: {chart_type}")
        
        analytics = DashboardAnalytics(user_id)
        
        if chart_type == 'submissions-trend':
            # Validate days parameter
            days_param = request.args.get('days', '30')
            try:
                days = int(days_param)
                if days <= 0 or days > 365:
                    log_validation_error(
                        'get_chart_data_submissions_trend',
                        'invalid_days_parameter',
                        f'Days parameter must be between 1 and 365, got: {days}',
                        received={'days': days},
                        expected={'days': 'integer between 1 and 365'}
                    )
                    return jsonify({'error': 'validation_failed', 'message': 'Days must be between 1 and 365'}), 422
            except ValueError:
                log_validation_error(
                    'get_chart_data_submissions_trend',
                    'invalid_days_format',
                    f'Days parameter must be numeric, got: {days_param}',
                    received={'days': days_param},
                    expected={'days': 'numeric string or integer'}
                )
                return jsonify({'error': 'validation_failed', 'message': 'Days parameter must be numeric'}), 422
            
            data = analytics.get_submission_trends(days)
            chart_data = {
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
            }
            
        elif chart_type == 'time-distribution':
            data = analytics.get_submission_by_time_of_day()
            chart_data = {
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
            }
            
        elif chart_type == 'top-forms':
            # Validate limit parameter
            limit_param = request.args.get('limit', '5')
            try:
                limit = int(limit_param)
                if limit <= 0 or limit > 100:
                    log_validation_error(
                        'get_chart_data_top_forms',
                        'invalid_limit_parameter',
                        f'Limit parameter must be between 1 and 100, got: {limit}',
                        received={'limit': limit},
                        expected={'limit': 'integer between 1 and 100'}
                    )
                    return jsonify({'error': 'validation_failed', 'message': 'Limit must be between 1 and 100'}), 422
            except ValueError:
                log_validation_error(
                    'get_chart_data_top_forms',
                    'invalid_limit_format',
                    f'Limit parameter must be numeric, got: {limit_param}',
                    received={'limit': limit_param},
                    expected={'limit': 'numeric string or integer'}
                )
                return jsonify({'error': 'validation_failed', 'message': 'Limit parameter must be numeric'}), 422
            
            forms = analytics.get_top_performing_forms(limit)
            chart_data = {
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
            }
            
        elif chart_type == 'performance-comparison':
            performance_data = analytics.get_form_performance_comparison()
            forms = performance_data['forms'][:10]  # Limit to top 10 for chart readability
            
            chart_data = {
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
            }
            
        elif chart_type == 'geographic':
            geo_data = analytics.get_geographic_distribution()
            chart_data = {
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
            }
        
        logger.info(f"✅ Chart data retrieved successfully for user {user_id}, chart type: {chart_type}")
        return jsonify(chart_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch chart data for {chart_type}: {str(e)}"
        logger.error(f"🚨 Error in get_chart_data: {error_msg}")
        return jsonify({'error': 'internal_error', 'message': error_msg}), 500
