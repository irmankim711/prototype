from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from ..models import db, Report, User, ReportTemplate
from ..services.report_service import report_service
from ..services.dashboard_service import dashboard_service
from ..decorators import get_current_user_id

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics for the current user"""
    try:
        user_id = get_current_user_id()
        stats = dashboard_service.get_user_dashboard_stats(user_id)
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/charts', methods=['GET'])
@jwt_required()
def get_chart_data():
    """Get chart data for dashboard visualizations"""
    try:
        user_id = get_current_user_id()
        
        # Get chart type from query parameters
        chart_type = request.args.get('type', 'reports_by_status')
        
        if chart_type == 'reports_by_status':
            # Reports by status pie chart
            status_counts = db.session.query(
                Report.status,
                func.count(Report.id).label('count')
            ).filter_by(user_id=user_id).group_by(Report.status).all()
            
            chart_data = {
                'labels': [status for status, _ in status_counts],
                'data': [count for _, count in status_counts],
                'backgroundColor': ['#4a69dd', '#37cfab', '#f87979', '#f8d854']
            }
            
        elif chart_type == 'reports_over_time':
            # Reports created over time (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            daily_reports = db.session.query(
                func.date(Report.created_at).label('date'),
                func.count(Report.id).label('count')
            ).filter(
                Report.user_id == user_id,
                Report.created_at >= thirty_days_ago
            ).group_by(func.date(Report.created_at)).order_by('date').all()
            
            chart_data = {
                'labels': [date.strftime('%m/%d') for date, _ in daily_reports],
                'data': [count for _, count in daily_reports],
                'borderColor': '#4a90e2',
                'backgroundColor': 'rgba(74, 144, 226, 0.1)'
            }
            
        elif chart_type == 'templates_usage':
            # Most used templates
            template_usage = db.session.query(
                ReportTemplate.name,
                func.count(Report.id).label('usage_count')
            ).join(Report, Report.template_id == ReportTemplate.id)\
             .filter(Report.user_id == user_id)\
             .group_by(ReportTemplate.name)\
             .order_by(desc('usage_count'))\
             .limit(5).all()
            
            chart_data = {
                'labels': [name for name, _ in template_usage],
                'data': [count for _, count in template_usage],
                'backgroundColor': ['#4a69dd', '#37cfab', '#f87979', '#f8d854', '#6bdaf7']
            }
            
        else:
            # Default mock data for compatibility
            chart_data = {
                'labels': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'],
                'data': [94, 85, 78, 92, 88, 78],
                'backgroundColor': ['#4a69dd', '#37cfab', '#f87979', '#f8d854', '#6bdaf7', '#8b75d7']
            }
        
        return jsonify({
            'type': chart_type,
            'data': chart_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent activity for the dashboard"""
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 10, type=int)
        
        # Get recent reports
        recent_reports = Report.query.filter_by(user_id=user_id)\
            .order_by(desc(Report.created_at))\
            .limit(limit)\
            .all()
        
        activity_data = []
        for report in recent_reports:
            activity_data.append({
                'id': report.id,
                'title': report.title,
                'status': report.status,
                'createdAt': report.created_at.isoformat(),
                'updatedAt': report.updated_at.isoformat(),
                'type': 'report',
                'templateId': report.template_id,
                'outputUrl': report.output_url
            })
        
        return jsonify({
            'recent_activity': activity_data,
            'total': len(activity_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """Get comprehensive dashboard summary"""
    try:
        user_id = get_current_user_id()
        
        # Get user info
        user = User.query.get(user_id)
        
        # Get quick stats
        total_reports = Report.query.filter_by(user_id=user_id).count()
        completed_today = Report.query.filter(
            Report.user_id == user_id,
            Report.status == 'completed',
            func.date(Report.created_at) == datetime.now().date()
        ).count()
        
        # Get recent reports
        recent_reports = Report.query.filter_by(user_id=user_id)\
            .order_by(desc(Report.created_at))\
            .limit(5)\
            .all()
        
        # Get available templates
        templates = ReportTemplate.query.filter_by(is_active=True).limit(5).all()
        
        summary = {
            'user': {
                'email': user.email,
                'joinedAt': user.created_at.isoformat()
            },
            'quickStats': {
                'totalReports': total_reports,
                'completedToday': completed_today,
                'activeTemplates': len(templates)
            },
            'recentReports': [{
                'id': report.id,
                'title': report.title,
                'status': report.status,
                'createdAt': report.created_at.isoformat()
            } for report in recent_reports],
            'availableTemplates': [{
                'id': template.id,
                'name': template.name,
                'description': template.description
            } for template in templates]
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_dashboard():
    """Refresh dashboard data (simulate data refresh)"""
    try:
        # In a real application, this might trigger cache refresh,
        # data synchronization, or other background tasks
        
        return jsonify({
            'message': 'Dashboard data refreshed successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance_metrics():
    """Get performance metrics for the current user"""
    try:
        user_id = get_current_user_id()
        metrics = dashboard_service.get_performance_metrics(user_id)
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/timeline', methods=['GET'])
@jwt_required()
def get_timeline_data():
    """Get timeline data for reports"""
    try:
        user_id = get_current_user_id()
        days = request.args.get('days', 30, type=int)
        timeline = dashboard_service.get_reports_timeline(user_id, days)
        return jsonify({
            'timeline': timeline,
            'period': f'{days} days'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
