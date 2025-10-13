from datetime import datetime
from app import db

class ReportVersion(db.Model):
    """Enhanced report versioning model for tracking changes and history"""
    __tablename__ = 'report_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.JSON, nullable=False)  # Report content as JSON
    template_id = db.Column(db.Integer, db.ForeignKey('report_templates.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    change_summary = db.Column(db.Text)
    is_current = db.Column(db.Boolean, default=False)
    file_size = db.Column(db.Integer)  # Size of content in bytes
    
    # Relationships
    report = db.relationship('Report', backref='versions')
    template = db.relationship('ReportTemplate', backref='versions')
    creator = db.relationship('User', backref='created_versions')
    
    def __repr__(self):
        return f'<ReportVersion {self.id}: v{self.version_number} of Report {self.report_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'version_number': self.version_number,
            'content': self.content,
            'template_id': self.template_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'change_summary': self.change_summary,
            'is_current': self.is_current,
            'file_size': self.file_size,
            'creator_name': self.creator.username if self.creator else None
        }

class ReportTemplate(db.Model):
    """Reusable report templates with layout and styling configurations"""
    __tablename__ = 'report_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    layout_config = db.Column(db.JSON, nullable=False)  # Template structure
    style_config = db.Column(db.JSON)  # Colors, fonts, spacing
    preview_image = db.Column(db.String(255))  # Template preview URL
    category = db.Column(db.String(50), default='general')  # business, academic, etc.
    is_public = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    tags = db.Column(db.JSON)  # Array of tags for categorization
    
    # Relationships
    creator = db.relationship('User', backref='created_templates')
    
    def __repr__(self):
        return f'<ReportTemplate {self.id}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'layout_config': self.layout_config,
            'style_config': self.style_config,
            'preview_image': self.preview_image,
            'category': self.category,
            'is_public': self.is_public,
            'is_premium': self.is_premium,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usage_count': self.usage_count,
            'rating': self.rating,
            'tags': self.tags,
            'creator_name': self.creator.username if self.creator else None
        }

class ReportEdit(db.Model):
    """Detailed edit history tracking for reports"""
    __tablename__ = 'report_edits'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    edit_type = db.Column(db.String(50), nullable=False)  # 'content', 'template', 'format', 'structure'
    section = db.Column(db.String(100))  # Which section was edited
    old_value = db.Column(db.JSON)
    new_value = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # For audit trail
    user_agent = db.Column(db.String(500))  # Browser/device info
    
    # Relationships
    report = db.relationship('Report', backref='edit_history')
    editor = db.relationship('User', backref='edits_made')
    
    def __repr__(self):
        return f'<ReportEdit {self.id}: {self.edit_type} on Report {self.report_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'user_id': self.user_id,
            'edit_type': self.edit_type,
            'section': self.section,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'editor_name': self.editor.username if self.editor else None
        }

class ReportCollaboration(db.Model):
    """Collaboration settings for shared report editing"""
    __tablename__ = 'report_collaborations'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_level = db.Column(db.String(20), nullable=False)  # 'view', 'edit', 'admin'
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    report = db.relationship('Report', backref='collaborations')
    user = db.relationship('User', foreign_keys=[user_id], backref='report_collaborations')
    inviter = db.relationship('User', foreign_keys=[invited_by], backref='collaboration_invitations')
    
    def __repr__(self):
        return f'<ReportCollaboration {self.id}: User {self.user_id} on Report {self.report_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'user_id': self.user_id,
            'permission_level': self.permission_level,
            'invited_by': self.invited_by,
            'invited_at': self.invited_at.isoformat() if self.invited_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'is_active': self.is_active,
            'user_name': self.user.username if self.user else None,
            'inviter_name': self.inviter.username if self.inviter else None
        }

class TemplateRating(db.Model):
    """User ratings for report templates"""
    __tablename__ = 'template_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('report_templates.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    template = db.relationship('ReportTemplate', backref='ratings')
    user = db.relationship('User', backref='template_ratings')
    
    # Ensure unique rating per user per template
    __table_args__ = (db.UniqueConstraint('template_id', 'user_id', name='unique_template_user_rating'),)
    
    def __repr__(self):
        return f'<TemplateRating {self.id}: {self.rating} stars for Template {self.template_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'review': self.review,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_name': self.user.username if self.user else None
        }
