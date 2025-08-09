"""
Advanced Report Editing Service with Version Control and Template Management
Handles report versioning, diff calculations, template applications, and collaborative editing
"""

import json
import difflib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from flask import current_app
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import joinedload

from app import db
# from app.models.report_models import ReportVersion, ReportTemplate, ReportEdit, ReportCollaboration, TemplateRating
# from app.models.form import Report  # Will be imported when models are integrated


class ReportEditingService:
    """Comprehensive service for advanced report editing capabilities"""
    
    @staticmethod
    def create_version(report_id: int, content: Dict[str, Any], user_id: int, 
                      change_summary: Optional[str] = None, template_id: Optional[int] = None):
        """
        Create a new version of a report with comprehensive tracking
        
        Args:
            report_id: ID of the report to version
            content: New content for the report
            user_id: ID of user making the change
            change_summary: Optional description of changes
            template_id: Optional template applied to this version
            
        Returns:
            New ReportVersion instance (to be implemented with actual model)
        """
        try:
            # Get current version to increment version number
            current_version = ReportVersion.query.filter_by(
                report_id=report_id, 
                is_current=True
            ).first()
            
            new_version_number = (current_version.version_number + 1) if current_version else 1
            
            # Mark current version as not current
            if current_version:
                current_version.is_current = False
            
            # Calculate content size
            content_size = len(json.dumps(content, separators=(',', ':')))
            
            # Create new version
            new_version = ReportVersion(
                report_id=report_id,
                version_number=new_version_number,
                content=content,
                created_by=user_id,
                change_summary=change_summary or f"Version {new_version_number} update",
                is_current=True,
                template_id=template_id,
                file_size=content_size
            )
            
            db.session.add(new_version)
            db.session.commit()
            
            current_app.logger.info(f"Created version {new_version_number} for report {report_id} by user {user_id}")
            return new_version
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create version for report {report_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_version_diff(version1_id: int, version2_id: int) -> Dict[str, Any]:
        """
        Compare two versions and return detailed differences
        
        Args:
            version1_id: ID of first version (older)
            version2_id: ID of second version (newer)
            
        Returns:
            Dictionary containing diff information
        """
        v1 = ReportVersion.query.get_or_404(version1_id)
        v2 = ReportVersion.query.get_or_404(version2_id)
        
        changes = []
        stats = {
            'added': 0,
            'removed': 0,
            'modified': 0,
            'total_changes': 0
        }
        
        def compare_objects(obj1: Any, obj2: Any, path: str = "") -> None:
            """Recursively compare objects and track changes"""
            if isinstance(obj1, dict) and isinstance(obj2, dict):
                all_keys = set(list(obj1.keys()) + list(obj2.keys()))
                
                for key in all_keys:
                    new_path = f"{path}.{key}" if path else key
                    
                    if key not in obj1:
                        changes.append({
                            'type': 'added',
                            'path': new_path,
                            'value': obj2[key],
                            'timestamp': v2.created_at.isoformat()
                        })
                        stats['added'] += 1
                    elif key not in obj2:
                        changes.append({
                            'type': 'removed',
                            'path': new_path,
                            'value': obj1[key],
                            'timestamp': v1.created_at.isoformat()
                        })
                        stats['removed'] += 1
                    else:
                        compare_objects(obj1[key], obj2[key], new_path)
                        
            elif isinstance(obj1, list) and isinstance(obj2, list):
                # Compare lists using difflib for better sequence comparison
                if obj1 != obj2:
                    changes.append({
                        'type': 'modified',
                        'path': path,
                        'old_value': obj1,
                        'new_value': obj2,
                        'list_diff': list(difflib.unified_diff(
                            [str(item) for item in obj1],
                            [str(item) for item in obj2],
                            lineterm='',
                            n=3
                        ))
                    })
                    stats['modified'] += 1
                    
            elif obj1 != obj2:
                change_entry = {
                    'type': 'modified',
                    'path': path,
                    'old_value': obj1,
                    'new_value': obj2
                }
                
                # For text content, provide word-level diff
                if isinstance(obj1, str) and isinstance(obj2, str):
                    change_entry['text_diff'] = list(difflib.unified_diff(
                        obj1.splitlines(),
                        obj2.splitlines(),
                        lineterm='',
                        n=3
                    ))
                
                changes.append(change_entry)
                stats['modified'] += 1
        
        compare_objects(v1.content, v2.content)
        stats['total_changes'] = stats['added'] + stats['removed'] + stats['modified']
        
        return {
            'version1': v1.to_dict(),
            'version2': v2.to_dict(),
            'changes': changes,
            'statistics': stats,
            'summary': f"{stats['total_changes']} changes: {stats['added']} added, {stats['modified']} modified, {stats['removed']} removed"
        }
    
    @staticmethod
    def rollback_to_version(report_id: int, version_id: int, user_id: int) -> ReportVersion:
        """
        Rollback report to a specific version by creating new version with old content
        
        Args:
            report_id: ID of the report
            version_id: ID of version to rollback to
            user_id: ID of user performing rollback
            
        Returns:
            New ReportVersion instance with rollback content
        """
        target_version = ReportVersion.query.get_or_404(version_id)
        
        if target_version.report_id != report_id:
            raise ValueError("Version does not belong to specified report")
        
        # Create new version with content from target version
        new_version = ReportEditingService.create_version(
            report_id=report_id,
            content=target_version.content.copy(),
            user_id=user_id,
            change_summary=f"Rollback to version {target_version.version_number}",
            template_id=target_version.template_id
        )
        
        # Log the rollback action
        ReportEditingService.log_edit(
            report_id=report_id,
            user_id=user_id,
            edit_type='rollback',
            section='full_report',
            new_value={'target_version': target_version.version_number}
        )
        
        return new_version
    
    @staticmethod
    def log_edit(report_id: int, user_id: int, edit_type: str, 
                 section: str = None, old_value: Any = None, new_value: Any = None,
                 ip_address: str = None, user_agent: str = None) -> ReportEdit:
        """
        Log detailed edit information for audit trail
        
        Args:
            report_id: ID of the report
            user_id: ID of user making edit
            edit_type: Type of edit (content, template, format, etc.)
            section: Specific section edited
            old_value: Previous value
            new_value: New value
            ip_address: User's IP address
            user_agent: User's browser/device info
            
        Returns:
            ReportEdit instance
        """
        edit_log = ReportEdit(
            report_id=report_id,
            user_id=user_id,
            edit_type=edit_type,
            section=section,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(edit_log)
        db.session.commit()
        
        return edit_log
    
    @staticmethod
    def get_edit_history(report_id: int, limit: int = 50, user_id: int = None) -> List[ReportEdit]:
        """
        Get edit history for a report with optional filtering
        
        Args:
            report_id: ID of the report
            limit: Maximum number of edits to return
            user_id: Optional filter by specific user
            
        Returns:
            List of ReportEdit instances
        """
        query = ReportEdit.query.filter_by(report_id=report_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(desc(ReportEdit.timestamp)).limit(limit).all()
    
    @staticmethod
    def auto_save_content(report_id: int, content: Dict[str, Any], user_id: int,
                         section: str = None) -> bool:
        """
        Auto-save functionality with smart versioning
        Only creates new version if significant changes detected
        
        Args:
            report_id: ID of the report
            content: New content to save
            user_id: ID of user making changes
            section: Specific section being auto-saved
            
        Returns:
            Boolean indicating if new version was created
        """
        current_version = ReportVersion.query.filter_by(
            report_id=report_id,
            is_current=True
        ).first()
        
        if not current_version:
            # No current version, create first one
            ReportEditingService.create_version(
                report_id=report_id,
                content=content,
                user_id=user_id,
                change_summary="Initial auto-save"
            )
            return True
        
        # Check if changes are significant enough for new version
        # Simple heuristic: create version if content differs significantly
        old_content_str = json.dumps(current_version.content, sort_keys=True)
        new_content_str = json.dumps(content, sort_keys=True)
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, old_content_str, new_content_str).ratio()
        
        # Create new version if less than 95% similar (significant change)
        if similarity < 0.95:
            ReportEditingService.create_version(
                report_id=report_id,
                content=content,
                user_id=user_id,
                change_summary="Auto-save with significant changes"
            )
            return True
        
        # Update current version timestamp to indicate recent activity
        current_version.created_at = datetime.utcnow()
        db.session.commit()
        
        return False


class TemplateService:
    """Service for managing report templates and applications"""
    
    @staticmethod
    def create_template(name: str, layout_config: Dict[str, Any], 
                       style_config: Dict[str, Any], user_id: int,
                       description: str = None, category: str = 'general',
                       tags: List[str] = None, is_public: bool = False) -> ReportTemplate:
        """
        Create a new report template
        
        Args:
            name: Template name
            layout_config: Layout configuration dictionary
            style_config: Style configuration dictionary
            user_id: ID of template creator
            description: Optional template description
            category: Template category
            tags: Optional list of tags
            is_public: Whether template is publicly available
            
        Returns:
            ReportTemplate instance
        """
        template = ReportTemplate(
            name=name,
            description=description,
            layout_config=layout_config,
            style_config=style_config,
            category=category,
            tags=tags or [],
            is_public=is_public,
            created_by=user_id
        )
        
        db.session.add(template)
        db.session.commit()
        
        current_app.logger.info(f"Created template '{name}' by user {user_id}")
        return template
    
    @staticmethod
    def apply_template(report_id: int, template_id: int, user_id: int, 
                      preserve_content: bool = True) -> ReportVersion:
        """
        Apply a template to a report, creating a new version
        
        Args:
            report_id: ID of the report
            template_id: ID of template to apply
            user_id: ID of user applying template
            preserve_content: Whether to preserve existing content when applying template
            
        Returns:
            New ReportVersion with template applied
        """
        template = ReportTemplate.query.get_or_404(template_id)
        current_version = ReportVersion.query.filter_by(
            report_id=report_id, 
            is_current=True
        ).first_or_404()
        
        # Start with template configuration
        new_content = {
            'layout': template.layout_config,
            'style': template.style_config,
            'template_info': {
                'id': template.id,
                'name': template.name,
                'applied_at': datetime.utcnow().isoformat()
            }
        }
        
        # Preserve existing content if requested
        if preserve_content and current_version.content:
            # Merge existing content with template, preserving data
            existing_content = current_version.content.copy()
            
            # Keep existing text content, form data, etc.
            for key in ['content', 'data', 'text', 'sections']:
                if key in existing_content:
                    new_content[key] = existing_content[key]
            
            # Merge any custom configurations
            if 'custom' in existing_content:
                new_content['custom'] = existing_content['custom']
        
        # Create new version with template applied
        new_version = ReportEditingService.create_version(
            report_id=report_id,
            content=new_content,
            user_id=user_id,
            change_summary=f"Applied template: {template.name}",
            template_id=template.id
        )
        
        # Update template usage count
        template.usage_count += 1
        
        # Log the template application
        ReportEditingService.log_edit(
            report_id=report_id,
            user_id=user_id,
            edit_type='template',
            section='layout_style',
            new_value={
                'template_id': template.id,
                'template_name': template.name,
                'preserve_content': preserve_content
            }
        )
        
        db.session.commit()
        
        return new_version
    
    @staticmethod
    def get_templates(user_id: int = None, category: str = None, 
                     search_term: str = None, is_public: bool = None,
                     limit: int = 50, offset: int = 0) -> Tuple[List[ReportTemplate], int]:
        """
        Get templates with filtering and pagination
        
        Args:
            user_id: Optional filter by creator
            category: Optional filter by category
            search_term: Optional search in name/description
            is_public: Optional filter by public status
            limit: Maximum number of templates to return
            offset: Number of templates to skip
            
        Returns:
            Tuple of (templates list, total count)
        """
        query = ReportTemplate.query
        
        # Apply filters
        if user_id is not None:
            query = query.filter_by(created_by=user_id)
        
        if category:
            query = query.filter_by(category=category)
        
        if is_public is not None:
            query = query.filter_by(is_public=is_public)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    ReportTemplate.name.ilike(search_pattern),
                    ReportTemplate.description.ilike(search_pattern)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        templates = query.order_by(desc(ReportTemplate.usage_count), desc(ReportTemplate.rating))\
                        .offset(offset).limit(limit).all()
        
        return templates, total_count
    
    @staticmethod
    def rate_template(template_id: int, user_id: int, rating: int, 
                     review: str = None) -> TemplateRating:
        """
        Rate a template (1-5 stars)
        
        Args:
            template_id: ID of template to rate
            user_id: ID of user giving rating
            rating: Rating value (1-5)
            review: Optional review text
            
        Returns:
            TemplateRating instance
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        # Check if user already rated this template
        existing_rating = TemplateRating.query.filter_by(
            template_id=template_id,
            user_id=user_id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.review = review
            rating_obj = existing_rating
        else:
            # Create new rating
            rating_obj = TemplateRating(
                template_id=template_id,
                user_id=user_id,
                rating=rating,
                review=review
            )
            db.session.add(rating_obj)
        
        # Update template's average rating
        template = ReportTemplate.query.get(template_id)
        if template:
            avg_rating = db.session.query(func.avg(TemplateRating.rating))\
                                  .filter_by(template_id=template_id).scalar()
            template.rating = round(avg_rating, 2) if avg_rating else 0.0
        
        db.session.commit()
        
        return rating_obj
    
    @staticmethod
    def duplicate_template(template_id: int, user_id: int, new_name: str = None) -> ReportTemplate:
        """
        Create a copy of an existing template
        
        Args:
            template_id: ID of template to duplicate
            user_id: ID of user creating the copy
            new_name: Optional new name for the copy
            
        Returns:
            New ReportTemplate instance
        """
        original = ReportTemplate.query.get_or_404(template_id)
        
        copy_name = new_name or f"Copy of {original.name}"
        
        new_template = ReportTemplate(
            name=copy_name,
            description=f"Copy of: {original.description}" if original.description else None,
            layout_config=original.layout_config.copy(),
            style_config=original.style_config.copy() if original.style_config else None,
            category=original.category,
            tags=original.tags.copy() if original.tags else [],
            is_public=False,  # Copies are private by default
            created_by=user_id
        )
        
        db.session.add(new_template)
        db.session.commit()
        
        return new_template


class CollaborationService:
    """Service for managing collaborative report editing"""
    
    @staticmethod
    def invite_collaborator(report_id: int, user_id: int, permission_level: str,
                           inviter_id: int) -> ReportCollaboration:
        """
        Invite a user to collaborate on a report
        
        Args:
            report_id: ID of the report
            user_id: ID of user to invite
            permission_level: 'view', 'edit', or 'admin'
            inviter_id: ID of user sending invitation
            
        Returns:
            ReportCollaboration instance
        """
        if permission_level not in ['view', 'edit', 'admin']:
            raise ValueError("Permission level must be 'view', 'edit', or 'admin'")
        
        # Check if collaboration already exists
        existing = ReportCollaboration.query.filter_by(
            report_id=report_id,
            user_id=user_id
        ).first()
        
        if existing:
            # Update existing collaboration
            existing.permission_level = permission_level
            existing.invited_by = inviter_id
            existing.invited_at = datetime.utcnow()
            existing.is_active = True
            return existing
        
        collaboration = ReportCollaboration(
            report_id=report_id,
            user_id=user_id,
            permission_level=permission_level,
            invited_by=inviter_id
        )
        
        db.session.add(collaboration)
        db.session.commit()
        
        return collaboration
    
    @staticmethod
    def accept_collaboration(collaboration_id: int) -> ReportCollaboration:
        """Accept a collaboration invitation"""
        collaboration = ReportCollaboration.query.get_or_404(collaboration_id)
        collaboration.accepted_at = datetime.utcnow()
        collaboration.last_accessed = datetime.utcnow()
        
        db.session.commit()
        return collaboration
    
    @staticmethod
    def check_permission(report_id: int, user_id: int, required_permission: str) -> bool:
        """
        Check if user has required permission for a report
        
        Args:
            report_id: ID of the report
            user_id: ID of the user
            required_permission: Required permission level
            
        Returns:
            Boolean indicating if user has permission
        """
        # Check if user owns the report
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        if report:
            return True  # Owner has all permissions
        
        # Check collaboration permissions
        collaboration = ReportCollaboration.query.filter_by(
            report_id=report_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not collaboration or not collaboration.accepted_at:
            return False
        
        # Permission hierarchy: admin > edit > view
        permission_levels = {'view': 1, 'edit': 2, 'admin': 3}
        
        user_level = permission_levels.get(collaboration.permission_level, 0)
        required_level = permission_levels.get(required_permission, 0)
        
        return user_level >= required_level
