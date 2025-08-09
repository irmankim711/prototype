from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc, cast, Date
from ..models import db, Form, FormSubmission, User
from typing import Dict, List, Any, Optional
import json

class DashboardAnalytics:
    """Enhanced analytics service for dashboard metrics and insights"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def get_submission_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get form submission trends over time"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate all dates in the range for complete timeline
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.date())
            current_date += timedelta(days=1)
        
        # Get actual submission counts
        submissions = db.session.query(
            cast(FormSubmission.submitted_at, Date).label('date'),
            func.count(FormSubmission.id).label('count')
        ).join(Form).filter(
            Form.creator_id == self.user_id,
            FormSubmission.submitted_at >= start_date
        ).group_by(cast(FormSubmission.submitted_at, Date)).all()
        
        # Create a map of date to count
        submission_map = {s.date: s.count for s in submissions}
        
        # Fill in missing dates with zero counts
        labels = []
        data = []
        for date in date_range:
            labels.append(date.strftime('%m/%d'))
            data.append(submission_map.get(date, 0))
        
        return {
            'labels': labels,
            'data': data,
            'total_submissions': sum(data),
            'average_daily': round(sum(data) / len(data), 1) if data else 0,
            'peak_day': labels[data.index(max(data))] if data and max(data) > 0 else None
        }
    
    def get_top_performing_forms(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get forms with highest submission rates and completion metrics"""
        forms = db.session.query(
            Form.id,
            Form.title,
            func.count(FormSubmission.id).label('submissions'),
            func.count(Form.id).label('total_forms')
        ).outerjoin(FormSubmission).filter(
            Form.creator_id == self.user_id,
            Form.is_active == True
        ).group_by(Form.id, Form.title).order_by(
            func.count(FormSubmission.id).desc()
        ).limit(limit).all()
        
        result = []
        for form in forms:
            # Calculate additional metrics
            form_submissions = FormSubmission.query.filter_by(form_id=form.id).all()
            
            # Calculate completion rate (submissions with all required fields filled)
            if form_submissions:
                # For now, assume all submissions are complete (can be enhanced with field validation)
                completion_rate = 100.0
            else:
                completion_rate = 0.0
            
            # Calculate recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_submissions = FormSubmission.query.filter(
                FormSubmission.form_id == form.id,
                FormSubmission.submitted_at >= week_ago
            ).count()
            
            result.append({
                'form_id': form.id,
                'form_name': form.title,
                'submissions': form.submissions or 0,
                'completion_rate': round(completion_rate, 2),
                'recent_activity': recent_submissions,
                'trend': 'up' if recent_submissions > 0 else 'stable'
            })
        
        return result
    
    def get_field_analytics(self, form_id: int) -> Dict[str, Any]:
        """Analyze field completion and abandonment rates for a specific form"""
        form = Form.query.filter_by(id=form_id, creator_id=self.user_id).first()
        if not form:
            return {'error': 'Form not found'}
        
        total_submissions = FormSubmission.query.filter_by(form_id=form_id).count()
        if total_submissions == 0:
            return {'error': 'No submissions found'}
        
        # Parse form schema to get fields
        try:
            schema = form.schema if isinstance(form.schema, dict) else json.loads(form.schema)
            fields = schema.get('fields', [])
        except (json.JSONDecodeError, AttributeError):
            return {'error': 'Invalid form schema'}
        
        field_stats = {}
        
        for field in fields:
            field_id = field.get('id')
            field_label = field.get('label', field_id)
            field_type = field.get('type', 'text')
            is_required = field.get('required', False)
            
            # Count submissions where this field has data
            completed_fields = 0
            submissions = FormSubmission.query.filter_by(form_id=form_id).all()
            
            for submission in submissions:
                submission_data = submission.data if isinstance(submission.data, dict) else {}
                if field_id in submission_data and submission_data[field_id] not in [None, '', []]:
                    completed_fields += 1
            
            completion_rate = (completed_fields / total_submissions * 100) if total_submissions > 0 else 0
            
            field_stats[field_label] = {
                'completion_rate': round(completion_rate, 2),
                'field_type': field_type,
                'is_required': is_required,
                'completed_count': completed_fields,
                'total_submissions': total_submissions,
                'abandonment_rate': round(100 - completion_rate, 2)
            }
        
        return {
            'field_stats': field_stats,
            'form_title': form.title,
            'total_submissions': total_submissions,
            'overall_completion': round(sum(stat['completion_rate'] for stat in field_stats.values()) / len(field_stats), 2) if field_stats else 0
        }
    
    def get_geographic_distribution(self) -> Dict[str, Any]:
        """Get geographic distribution of form submissions (mock data for now)"""
        # This would typically analyze IP addresses or location data from submissions
        # For now, returning mock data that could be replaced with real geolocation analysis
        return {
            'countries': [
                {'name': 'United States', 'submissions': 45, 'percentage': 45.0},
                {'name': 'Canada', 'submissions': 20, 'percentage': 20.0},
                {'name': 'United Kingdom', 'submissions': 15, 'percentage': 15.0},
                {'name': 'Germany', 'submissions': 10, 'percentage': 10.0},
                {'name': 'France', 'submissions': 10, 'percentage': 10.0}
            ],
            'total_countries': 5,
            'most_active_country': 'United States'
        }
    
    def get_submission_by_time_of_day(self) -> Dict[str, Any]:
        """Analyze what times of day get the most form submissions"""
        submissions = db.session.query(
            func.extract('hour', FormSubmission.submitted_at).label('hour'),
            func.count(FormSubmission.id).label('count')
        ).join(Form).filter(
            Form.creator_id == self.user_id
        ).group_by(func.extract('hour', FormSubmission.submitted_at)).all()
        
        # Initialize 24-hour array
        hourly_data = [0] * 24
        for submission in submissions:
            if submission.hour is not None:
                hour_index = int(submission.hour)
                hourly_data[hour_index] = submission[1]  # count is the second element
        
        # Find peak hours
        peak_hour = hourly_data.index(max(hourly_data)) if hourly_data else 0
        peak_submissions = max(hourly_data) if hourly_data else 0
        
        return {
            'hourly_data': hourly_data,
            'labels': [f'{hour:02d}:00' for hour in range(24)],
            'peak_hour': f'{peak_hour:02d}:00',
            'peak_submissions': peak_submissions,
            'total_submissions': sum(hourly_data)
        }
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time dashboard statistics"""
        now = datetime.utcnow()
        
        # Get submissions from last 24 hours
        yesterday = now - timedelta(hours=24)
        submissions_24h = FormSubmission.query.join(Form).filter(
            Form.creator_id == self.user_id,
            FormSubmission.submitted_at >= yesterday
        ).count()
        
        # Get submissions from last hour
        last_hour = now - timedelta(hours=1)
        submissions_1h = FormSubmission.query.join(Form).filter(
            Form.creator_id == self.user_id,
            FormSubmission.submitted_at >= last_hour
        ).count()
        
        # Get active forms count
        active_forms = Form.query.filter_by(
            creator_id=self.user_id,
            is_active=True
        ).count()
        
        # Get total forms count
        total_forms = Form.query.filter_by(creator_id=self.user_id).count()
        
        # Get most recent submissions for activity feed
        recent_submissions = db.session.query(
            FormSubmission.id,
            FormSubmission.submitted_at,
            Form.title.label('form_title')
        ).join(Form).filter(
            Form.creator_id == self.user_id
        ).order_by(desc(FormSubmission.submitted_at)).limit(5).all()
        
        activity_feed = [{
            'id': sub.id,
            'form_title': sub.form_title,
            'created_at': sub.submitted_at.isoformat(),
            'time_ago': self._get_time_ago(sub.submitted_at)
        } for sub in recent_submissions]
        
        return {
            'submissions_24h': submissions_24h,
            'submissions_1h': submissions_1h,
            'active_forms': active_forms,
            'total_forms': total_forms,
            'last_updated': now.isoformat(),
            'activity_feed': activity_feed,
            'is_active': submissions_1h > 0  # Consider "active" if submissions in last hour
        }
    
    def get_form_performance_comparison(self) -> Dict[str, Any]:
        """Compare performance across all user's forms"""
        forms = db.session.query(
            Form.id,
            Form.title,
            Form.created_at,
            func.count(FormSubmission.id).label('total_submissions')
        ).outerjoin(FormSubmission).filter(
            Form.creator_id == self.user_id
        ).group_by(Form.id, Form.title, Form.created_at).all()
        
        performance_data = []
        for form in forms:
            # Calculate days since creation
            days_active = (datetime.utcnow() - form.created_at).days + 1
            
            # Calculate average submissions per day
            avg_per_day = round(form.total_submissions / days_active, 2) if days_active > 0 else 0
            
            # Get recent performance (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_submissions = FormSubmission.query.filter(
                FormSubmission.form_id == form.id,
                FormSubmission.submitted_at >= week_ago
            ).count()
            
            performance_data.append({
                'form_id': form.id,
                'form_title': form.title,
                'total_submissions': form.total_submissions,
                'days_active': days_active,
                'avg_per_day': avg_per_day,
                'recent_submissions': recent_submissions,
                'performance_score': self._calculate_performance_score(form.total_submissions, days_active, recent_submissions)
            })
        
        # Sort by performance score
        performance_data.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return {
            'forms': performance_data,
            'best_performer': performance_data[0] if performance_data else None,
            'total_forms_analyzed': len(performance_data)
        }
    
    def _calculate_performance_score(self, total_submissions: int, days_active: int, recent_submissions: int) -> float:
        """Calculate a performance score for forms (0-100)"""
        if days_active == 0:
            return 0.0
        
        # Base score from average daily submissions
        avg_daily = total_submissions / days_active
        base_score = min(avg_daily * 10, 60)  # Cap at 60 points
        
        # Bonus for recent activity
        recent_bonus = min(recent_submissions * 5, 30)  # Cap at 30 points
        
        # Bonus for longevity with sustained performance
        longevity_bonus = min(days_active / 30 * 10, 10)  # Cap at 10 points
        
        return round(base_score + recent_bonus + longevity_bonus, 1)
    
    def _get_time_ago(self, created_at: datetime) -> str:
        """Get human-readable time difference"""
        now = datetime.utcnow()
        diff = now - created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
