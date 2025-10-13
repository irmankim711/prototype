from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from .. import db
from ..models import Report, User, ReportTemplate
from typing import Dict, List, Any

class DashboardService:
    
    @staticmethod
    def get_user_dashboard_stats(user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics for a user"""
        
        # Basic counts
        total_reports = Report.query.filter_by(user_id=user_id).count()
        completed_reports = Report.query.filter_by(user_id=user_id, status='completed').count()
        pending_reports = Report.query.filter_by(user_id=user_id, status='processing').count()
        failed_reports = Report.query.filter_by(user_id=user_id, status='failed').count()
        
        # Time-based analytics
        now = datetime.utcnow()
        
        # This week
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        reports_this_week = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= week_start
        ).count()
        
        # This month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        reports_this_month = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= month_start
        ).count()
        
        # Last 30 days
        thirty_days_ago = now - timedelta(days=30)
        reports_last_30_days = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= thirty_days_ago
        ).count()
        
        # Success rate calculation
        if total_reports > 0:
            success_rate = round((completed_reports / total_reports) * 100, 1)
        else:
            success_rate = 0.0
            
        return {
            'totalReports': total_reports,
            'completedReports': completed_reports,
            'pendingReports': pending_reports,
            'failedReports': failed_reports,
            'reportsThisWeek': reports_this_week,
            'reportsThisMonth': reports_this_month,
            'reportsLast30Days': reports_last_30_days,
            'successRate': success_rate,
            'lastUpdated': now.isoformat()
        }
        reports_last_30_days = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= thirty_days_ago
        ).count()
        
        # Success rate
        success_rate = 0
        if total_reports > 0:
            success_rate = round((completed_reports / total_reports) * 100, 1)
        
        # Average completion time (for completed reports)
        avg_completion_time = None
        completed_reports_with_time = Report.query.filter(
            Report.user_id == user_id,
            Report.status == 'completed',
            Report.updated_at.isnot(None)
        ).all()
        
        if completed_reports_with_time:
            total_time = sum([
                (report.updated_at - report.created_at).total_seconds()
                for report in completed_reports_with_time
            ])
            avg_completion_time = total_time / len(completed_reports_with_time) / 60  # in minutes
        
        return {
            'totalReports': total_reports,
            'completedReports': completed_reports,
            'pendingReports': pending_reports,
            'failedReports': failed_reports,
            'reportsThisWeek': reports_this_week,
            'reportsThisMonth': reports_this_month,
            'reportsLast30Days': reports_last_30_days,
            'successRate': success_rate,
            'averageCompletionTime': round(avg_completion_time, 1) if avg_completion_time else None,
            # For frontend compatibility
            'totalSubmissions': total_reports,
            'averageScore': success_rate,
            'activeUsers': 1,
            'topScore': 100 if completed_reports > 0 else 0
        }
    
    @staticmethod
    def get_reports_timeline(user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get timeline data for reports over the specified number of days"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily report counts
        daily_reports = db.session.query(
            func.date(Report.created_at).label('date'),
            func.count(Report.id).label('count')
        ).filter(
            Report.user_id == user_id,
            Report.created_at >= start_date,
            Report.created_at <= end_date
        ).group_by(func.date(Report.created_at)).order_by('date').all()
        
        # Fill in missing dates with zero counts
        timeline = []
        current_date = start_date.date()
        report_dict = {date: count for date, count in daily_reports}
        
        while current_date <= end_date.date():
            timeline.append({
                'date': current_date.isoformat(),
                'count': report_dict.get(current_date, 0)
            })
            current_date += timedelta(days=1)
            
        return timeline
        """Get reports created over time for timeline charts"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily report counts
        daily_reports = db.session.query(
            func.date(Report.created_at).label('date'),
            func.count(Report.id).label('count')
        ).filter(
            Report.user_id == user_id,
            Report.created_at >= start_date
        ).group_by(func.date(Report.created_at)).order_by('date').all()
        
        # Fill in missing dates with 0 counts
        result = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        daily_counts = {date: count for date, count in daily_reports}
        
        while current_date <= end_date:
            result.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': daily_counts.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return result
    
    @staticmethod
    def get_status_distribution(user_id: int) -> Dict[str, int]:
        """Get distribution of report statuses"""
        
        status_counts = db.session.query(
            Report.status,
            func.count(Report.id).label('count')
        ).filter_by(user_id=user_id).group_by(Report.status).all()
        
        return {status: count for status, count in status_counts}
        """Get distribution of report statuses"""
        
        status_counts = db.session.query(
            Report.status,
            func.count(Report.id).label('count')
        ).filter_by(user_id=user_id).group_by(Report.status).all()
        
        return {status: count for status, count in status_counts}
    
    @staticmethod
    def get_template_usage(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used templates by the user"""
        
        template_usage = db.session.query(
            ReportTemplate.id,
            ReportTemplate.name,
            func.count(Report.id).label('usage_count')
        ).join(Report, Report.template_id == ReportTemplate.id)\
         .filter(Report.user_id == user_id)\
         .group_by(ReportTemplate.id, ReportTemplate.name)\
         .order_by(desc('usage_count'))\
         .limit(limit).all()
        
        return [{
            'templateId': template_id,
            'templateName': name,
            'usageCount': count
        } for template_id, name, count in template_usage]
        """Get most used templates"""
        
        template_usage = db.session.query(
            ReportTemplate.id,
            ReportTemplate.name,
            func.count(Report.id).label('usage_count')
        ).join(Report, Report.template_id == ReportTemplate.id)\
         .filter(Report.user_id == user_id)\
         .group_by(ReportTemplate.id, ReportTemplate.name)\
         .order_by(desc('usage_count'))\
         .limit(limit).all()
        
        return [{
            'templateId': template_id,
            'templateName': name,
            'usageCount': count
        } for template_id, name, count in template_usage]
    
    @staticmethod
    def get_performance_metrics(user_id: int) -> Dict[str, Any]:
        """Get performance metrics for the user"""
        
        # Get reports from last 7 days for trend analysis
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        weekly_reports = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= week_ago
        ).all()
        
        if not weekly_reports:
            return {
                'weeklyReports': 0,
                'weeklySuccessRate': 0.0,
                'averageProcessingTime': 0.0,
                'trend': 'stable'
            }
        
        # Calculate metrics
        total_weekly = len(weekly_reports)
        completed_weekly = len([r for r in weekly_reports if r.status == 'completed'])
        weekly_success_rate = (completed_weekly / total_weekly) * 100 if total_weekly > 0 else 0
        
        # Calculate average processing time (mock data for now)
        avg_processing_time = 2.5  # minutes
        
        # Determine trend (mock logic)
        previous_week = now - timedelta(days=14)
        previous_weekly_count = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= previous_week,
            Report.created_at < week_ago
        ).count()
        
        if total_weekly > previous_weekly_count:
            trend = 'increasing'
        elif total_weekly < previous_weekly_count:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'weeklyReports': total_weekly,
            'weeklySuccessRate': round(weekly_success_rate, 1),
            'averageProcessingTime': round(avg_processing_time, 1),
            'trend': trend
        }
        """Get performance metrics for the user"""
        
        # Get reports from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_reports = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= week_ago
        ).all()
        
        if not recent_reports:
            return {
                'weeklyReports': 0,
                'weeklySuccessRate': 0,
                'averageProcessingTime': 0,
                'trend': 'stable'
            }
        
        # Calculate metrics
        weekly_reports = len(recent_reports)
        completed_this_week = len([r for r in recent_reports if r.status == 'completed'])
        weekly_success_rate = (completed_this_week / weekly_reports * 100) if weekly_reports > 0 else 0
        
        # Calculate average processing time for completed reports
        completed_reports = [r for r in recent_reports if r.status == 'completed' and r.updated_at]
        avg_processing_time = 0
        if completed_reports:
            total_time = sum([
                (r.updated_at - r.created_at).total_seconds()
                for r in completed_reports
            ])
            avg_processing_time = total_time / len(completed_reports) / 60  # in minutes
        
        # Determine trend (compare with previous week)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        previous_week_reports = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= two_weeks_ago,
            Report.created_at < week_ago
        ).count()
        
        if weekly_reports > previous_week_reports:
            trend = 'up'
        elif weekly_reports < previous_week_reports:
            trend = 'down'
        else:
            trend = 'stable'
        
        return {
            'weeklyReports': weekly_reports,
            'weeklySuccessRate': round(weekly_success_rate, 1),
            'averageProcessingTime': round(avg_processing_time, 1),
            'trend': trend
        }

dashboard_service = DashboardService()
