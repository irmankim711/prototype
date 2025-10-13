"""
Cache Warming Utilities

Provides utilities for warming frequently accessed data in cache:
- Form definitions and schemas
- User permissions and roles
- Report templates
- Dashboard statistics
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from flask import current_app
from sqlalchemy import text

logger = logging.getLogger(__name__)


class CacheWarmingService:
    """Service for warming frequently accessed data in cache"""
    
    def __init__(self):
        self.cache_manager = None
        self.form_cache = None
        self.user_cache = None
        self.template_cache = None
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.cache_manager = getattr(app, 'cache_manager', None)
        self.form_cache = getattr(app, 'form_cache', None)
        self.user_cache = getattr(app, 'user_cache', None)
        self.template_cache = getattr(app, 'template_cache', None)
    
    def warm_all_caches(self) -> Dict[str, Any]:
        """Warm all frequently accessed caches"""
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'forms': {},
            'users': {},
            'templates': {},
            'dashboard': {},
            'errors': []
        }
        
        try:
            # Warm form caches
            results['forms'] = self.warm_form_caches()
        except Exception as e:
            logger.error(f"Error warming form caches: {e}")
            results['errors'].append(f"Form cache warming failed: {e}")
        
        try:
            # Warm user caches
            results['users'] = self.warm_user_caches()
        except Exception as e:
            logger.error(f"Error warming user caches: {e}")
            results['errors'].append(f"User cache warming failed: {e}")
        
        try:
            # Warm template caches
            results['templates'] = self.warm_template_caches()
        except Exception as e:
            logger.error(f"Error warming template caches: {e}")
            results['errors'].append(f"Template cache warming failed: {e}")
        
        try:
            # Warm dashboard caches
            results['dashboard'] = self.warm_dashboard_caches()
        except Exception as e:
            logger.error(f"Error warming dashboard caches: {e}")
            results['errors'].append(f"Dashboard cache warming failed: {e}")
        
        results['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Cache warming completed with {len(results['errors'])} errors")
        return results
    
    def warm_form_caches(self) -> Dict[str, Any]:
        """Warm form-related caches"""
        if not self.form_cache:
            return {'error': 'Form cache not available'}
        
        results = {
            'definitions_warmed': 0,
            'schemas_warmed': 0,
            'submission_counts_warmed': 0,
            'errors': []
        }
        
        try:
            from app.models import Form
            
            # Get most frequently accessed forms (active forms with recent activity)
            forms = Form.query.filter_by(is_active=True).limit(50).all()
            
            for form in forms:
                try:
                    # Warm form definition
                    form_data = {
                        'id': form.id,
                        'title': form.title,
                        'description': form.description,
                        'schema': form.schema,
                        'is_active': form.is_active,
                        'is_public': form.is_public,
                        'created_at': form.created_at.isoformat() if form.created_at else None,
                        'updated_at': form.updated_at.isoformat() if form.updated_at else None
                    }
                    
                    if self.form_cache.set_form_definition(form.id, form_data):
                        results['definitions_warmed'] += 1
                    
                    # Warm form schema separately
                    if form.schema and self.form_cache.set_form_schema(form.id, form.schema):
                        results['schemas_warmed'] += 1
                    
                    # Warm submission count
                    submission_count = len(form.submissions) if hasattr(form, 'submissions') else 0
                    if self.form_cache.set_form_submissions_count(form.id, submission_count):
                        results['submission_counts_warmed'] += 1
                        
                except Exception as e:
                    logger.warning(f"Error warming cache for form {form.id}: {e}")
                    results['errors'].append(f"Form {form.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in warm_form_caches: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def warm_user_caches(self) -> Dict[str, Any]:
        """Warm user-related caches"""
        if not self.user_cache:
            return {'error': 'User cache not available'}
        
        results = {
            'permissions_warmed': 0,
            'roles_warmed': 0,
            'profiles_warmed': 0,
            'errors': []
        }
        
        try:
            from app.models import User
            
            # Get active users (limit to most recent/active users)
            users = User.query.filter_by(is_active=True).limit(100).all()
            
            for user in users:
                try:
                    # Warm user permissions
                    permissions = [perm.value for perm in user.get_permissions()]
                    if self.user_cache.set_user_permissions(user.id, permissions):
                        results['permissions_warmed'] += 1
                    
                    # Warm user role
                    role = user.role.value if user.role else 'user'
                    if self.user_cache.set_user_role(user.id, role):
                        results['roles_warmed'] += 1
                    
                    # Warm user profile
                    profile_data = {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.full_name,
                        'role': role,
                        'is_active': user.is_active,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    }
                    
                    if self.user_cache.set_user_profile(user.id, profile_data):
                        results['profiles_warmed'] += 1
                        
                except Exception as e:
                    logger.warning(f"Error warming cache for user {user.id}: {e}")
                    results['errors'].append(f"User {user.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in warm_user_caches: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def warm_template_caches(self) -> Dict[str, Any]:
        """Warm template-related caches"""
        if not self.template_cache:
            return {'error': 'Template cache not available'}
        
        results = {
            'templates_warmed': 0,
            'template_lists_warmed': 0,
            'errors': []
        }
        
        try:
            from app.models import ReportTemplate
            
            # Get active templates
            templates = ReportTemplate.query.limit(50).all()
            
            for template in templates:
                try:
                    template_data = {
                        'id': template.id,
                        'name': template.name,
                        'description': template.description,
                        'template_type': template.template_type,
                        'content_template': template.content_template,
                        'data_sources': template.data_sources,
                        'parameters': template.parameters,
                        'styling': template.styling,
                        'chart_configs': template.chart_configs,
                        'is_public': template.is_public,
                        'usage_count': template.usage_count,
                        'created_at': template.created_at.isoformat() if template.created_at else None,
                        'updated_at': template.updated_at.isoformat() if template.updated_at else None
                    }
                    
                    if self.template_cache.set_template(template.id, template_data):
                        results['templates_warmed'] += 1
                        
                except Exception as e:
                    logger.warning(f"Error warming cache for template {template.id}: {e}")
                    results['errors'].append(f"Template {template.id}: {e}")
            
            # Warm template lists
            try:
                template_list = [
                    {
                        'id': t.id,
                        'name': t.name,
                        'description': t.description,
                        'template_type': t.template_type,
                        'is_public': t.is_public,
                        'usage_count': t.usage_count
                    }
                    for t in templates
                ]
                
                if self.template_cache.set_template_list(template_list):
                    results['template_lists_warmed'] += 1
                    
            except Exception as e:
                logger.warning(f"Error warming template lists: {e}")
                results['errors'].append(f"Template lists: {e}")
            
        except Exception as e:
            logger.error(f"Error in warm_template_caches: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def warm_dashboard_caches(self) -> Dict[str, Any]:
        """Warm dashboard statistics and frequently accessed data"""
        results = {
            'stats_warmed': 0,
            'errors': []
        }
        
        if not self.cache_manager:
            return {'error': 'Cache manager not available'}
        
        try:
            from app.models import Form, Report, User
            from app import db
            
            # Cache dashboard statistics
            stats = {}
            
            try:
                stats['total_forms'] = Form.query.filter_by(is_active=True).count()
                stats['total_reports'] = Report.query.count()
                stats['total_users'] = User.query.filter_by(is_active=True).count()
                stats['recent_reports'] = Report.query.filter(
                    Report.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()
                
                # Cache for 5 minutes (dashboard stats change frequently)
                cache_key = self.cache_manager._generate_cache_key('dashboard', 'stats')
                if self.cache_manager.set(cache_key, stats, 300):
                    results['stats_warmed'] += 1
                    
            except Exception as e:
                logger.warning(f"Error warming dashboard stats: {e}")
                results['errors'].append(f"Dashboard stats: {e}")
            
        except Exception as e:
            logger.error(f"Error in warm_dashboard_caches: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def warm_cache_for_user(self, user_id: int) -> Dict[str, Any]:
        """Warm cache for a specific user"""
        results = {
            'user_id': user_id,
            'permissions_warmed': False,
            'role_warmed': False,
            'profile_warmed': False,
            'user_forms_warmed': 0,
            'errors': []
        }
        
        try:
            from app.models import User, Form
            
            user = User.query.get(user_id)
            if not user:
                results['errors'].append('User not found')
                return results
            
            # Warm user-specific caches
            if self.user_cache:
                try:
                    # Permissions
                    permissions = [perm.value for perm in user.get_permissions()]
                    results['permissions_warmed'] = self.user_cache.set_user_permissions(user.id, permissions)
                    
                    # Role
                    role = user.role.value if user.role else 'user'
                    results['role_warmed'] = self.user_cache.set_user_role(user.id, role)
                    
                    # Profile
                    profile_data = {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.full_name,
                        'role': role,
                        'is_active': user.is_active
                    }
                    results['profile_warmed'] = self.user_cache.set_user_profile(user.id, profile_data)
                    
                except Exception as e:
                    results['errors'].append(f"User cache warming: {e}")
            
            # Warm user's forms
            if self.form_cache:
                try:
                    user_forms = Form.query.filter_by(creator_id=user.id, is_active=True).all()
                    for form in user_forms:
                        form_data = {
                            'id': form.id,
                            'title': form.title,
                            'description': form.description,
                            'schema': form.schema,
                            'is_active': form.is_active,
                            'is_public': form.is_public
                        }
                        if self.form_cache.set_form_definition(form.id, form_data):
                            results['user_forms_warmed'] += 1
                            
                except Exception as e:
                    results['errors'].append(f"User forms warming: {e}")
            
        except Exception as e:
            logger.error(f"Error warming cache for user {user_id}: {e}")
            results['errors'].append(str(e))
        
        return results


# Global cache warming service
cache_warming_service = CacheWarmingService()

def init_cache_warming_service(app):
    """Initialize cache warming service"""
    cache_warming_service.init_app(app)
    app.cache_warming_service = cache_warming_service
    logger.info("Cache warming service initialized")