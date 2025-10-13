"""
Query Optimization Utilities
Provides optimized query patterns and utilities for better database performance.
"""

from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, or_
from .. import db
from ..models import Form, FormSubmission, Report, User, ReportTemplate
import logging

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Utility class for optimized database queries."""
    
    @staticmethod
    def get_form_with_submissions(form_id, user_id=None):
        """
        Get form with optimized loading of submissions.
        Uses joinedload to avoid N+1 queries.
        """
        query = Form.query.options(
            joinedload(Form.submissions)
        ).filter(Form.id == form_id)
        
        if user_id:
            query = query.filter(
                or_(
                    Form.creator_id == user_id,
                    Form.is_public == True
                )
            )
        
        return query.first()
    
    @staticmethod
    def get_user_forms_optimized(user_id, include_submissions=False):
        """
        Get user's forms with optimized loading.
        Optionally includes submission count.
        """
        query = Form.query.filter(Form.creator_id == user_id)
        
        if include_submissions:
            query = query.options(selectinload(Form.submissions))
        
        return query.order_by(Form.created_at.desc()).all()
    
    @staticmethod
    def get_form_submissions_batch(form_id, page=1, per_page=50):
        """
        Get form submissions with pagination and optimized loading.
        """
        return FormSubmission.query.filter(
            FormSubmission.form_id == form_id
        ).order_by(
            FormSubmission.submitted_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def get_user_reports_optimized(user_id, status=None, limit=None):
        """
        Get user reports with optimized filtering and optional status filter.
        """
        # Handle both string and integer user_id comparisons for compatibility
        query = Report.query.filter(
            or_(
                Report.created_by == str(user_id),
                Report.created_by == user_id
            )
        )
        
        if status:
            query = query.filter(Report.generation_status == status)
        
        query = query.order_by(Report.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_active_templates_cached():
        """
        Get active report templates with caching consideration.
        """
        return ReportTemplate.query.filter(
            ReportTemplate.is_active == True
        ).order_by(ReportTemplate.name).all()
    
    @staticmethod
    def get_public_forms_optimized(limit=None):
        """
        Get public forms with optimized loading.
        """
        query = Form.query.filter(
            and_(
                Form.is_public == True,
                Form.is_active == True
            )
        ).order_by(Form.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def bulk_update_form_view_counts(form_ids):
        """
        Bulk update view counts for multiple forms.
        More efficient than individual updates.
        """
        if not form_ids:
            return
        
        try:
            # Use bulk update for better performance
            db.session.query(Form).filter(
                Form.id.in_(form_ids)
            ).update(
                {Form.view_count: Form.view_count + 1},
                synchronize_session=False
            )
            db.session.commit()
        except Exception as e:
            logger.error(f"Error bulk updating form view counts: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def get_form_submission_stats(form_id):
        """
        Get form submission statistics with optimized aggregation.
        """
        from sqlalchemy import func
        
        stats = db.session.query(
            func.count(FormSubmission.id).label('total_submissions'),
            func.count(
                FormSubmission.id.filter(FormSubmission.status == 'submitted')
            ).label('pending_submissions'),
            func.count(
                FormSubmission.id.filter(FormSubmission.status == 'reviewed')
            ).label('reviewed_submissions')
        ).filter(
            FormSubmission.form_id == form_id
        ).first()
        
        return {
            'total_submissions': stats.total_submissions or 0,
            'pending_submissions': stats.pending_submissions or 0,
            'reviewed_submissions': stats.reviewed_submissions or 0
        }
    
    @staticmethod
    def search_forms_optimized(search_term, user_id=None, is_public_only=False):
        """
        Search forms with optimized text search.
        """
        query = Form.query.filter(
            or_(
                Form.title.ilike(f'%{search_term}%'),
                Form.description.ilike(f'%{search_term}%')
            )
        )
        
        if is_public_only:
            query = query.filter(Form.is_public == True)
        elif user_id:
            query = query.filter(
                or_(
                    Form.creator_id == user_id,
                    Form.is_public == True
                )
            )
        
        return query.filter(Form.is_active == True).order_by(
            Form.created_at.desc()
        ).all()

class CachedQueryManager:
    """
    Manager for cached query results to reduce database load.
    """
    
    _cache = {}
    _cache_ttl = {}
    
    @classmethod
    def get_cached_result(cls, cache_key, query_func, ttl_seconds=300):
        """
        Get cached query result or execute query if cache miss.
        """
        import time
        
        current_time = time.time()
        
        # Check if cache exists and is still valid
        if (cache_key in cls._cache and 
            cache_key in cls._cache_ttl and 
            current_time < cls._cache_ttl[cache_key]):
            return cls._cache[cache_key]
        
        # Execute query and cache result
        result = query_func()
        cls._cache[cache_key] = result
        cls._cache_ttl[cache_key] = current_time + ttl_seconds
        
        return result
    
    @classmethod
    def invalidate_cache(cls, pattern=None):
        """
        Invalidate cache entries matching pattern or all if no pattern.
        """
        if pattern:
            keys_to_remove = [key for key in cls._cache.keys() if pattern in key]
            for key in keys_to_remove:
                cls._cache.pop(key, None)
                cls._cache_ttl.pop(key, None)
        else:
            cls._cache.clear()
            cls._cache_ttl.clear()

# Query timing decorator for performance monitoring
def time_query(func):
    """Decorator to time database queries for performance monitoring."""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 1.0:  # Log slow queries (>1 second)
            logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f}s")
        elif execution_time > 0.5:  # Log moderately slow queries
            logger.info(f"Query timing: {func.__name__} took {execution_time:.2f}s")
        
        return result
    
    return wrapper