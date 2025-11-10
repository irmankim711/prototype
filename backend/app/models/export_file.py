"""
Export File Model
Tracks ownership and metadata for exported files to prevent unauthorized access
"""

from datetime import datetime
from .. import db


class ExportFile(db.Model):
    """
    Model to track exported files and their owners
    This prevents unauthorized access to export files
    """
    __tablename__ = 'export_files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    user_id = db.Column(db.String(128), nullable=False, index=True)  # Firebase UID
    file_type = db.Column(db.String(50), nullable=False)  # 'google_forms_export', 'form_export', 'report_export'
    file_format = db.Column(db.String(10), nullable=False)  # 'xlsx', 'csv', 'pdf', 'docx'
    file_size = db.Column(db.Integer)  # Size in bytes
    file_path = db.Column(db.String(512), nullable=False)  # Full file path

    # Metadata
    related_id = db.Column(db.String(128))  # ID of related resource (form_id, report_id, etc.)
    related_type = db.Column(db.String(50))  # 'google_form', 'form', 'report'

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime)  # Optional expiration time
    last_downloaded_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)

    # Status
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ExportFile {self.filename} owner={self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'user_id': self.user_id,
            'file_type': self.file_type,
            'file_format': self.file_format,
            'file_size': self.file_size,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_downloaded_at': self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
            'download_count': self.download_count,
            'is_deleted': self.is_deleted
        }

    @classmethod
    def register_export(cls, filename: str, user_id: str, file_type: str, file_format: str,
                       file_size: int, file_path: str, related_id: str = None,
                       related_type: str = None, expires_at: datetime = None):
        """
        Register a new export file in the database

        Args:
            filename: Name of the file
            user_id: Firebase UID of the owner
            file_type: Type of export (e.g., 'google_forms_export')
            file_format: File format (e.g., 'xlsx', 'csv')
            file_size: Size of file in bytes
            file_path: Full path to file
            related_id: ID of related resource
            related_type: Type of related resource
            expires_at: Optional expiration datetime

        Returns:
            ExportFile instance
        """
        export_file = cls(
            filename=filename,
            user_id=user_id,
            file_type=file_type,
            file_format=file_format,
            file_size=file_size,
            file_path=file_path,
            related_id=related_id,
            related_type=related_type,
            expires_at=expires_at
        )
        db.session.add(export_file)
        db.session.commit()
        return export_file

    @classmethod
    def verify_access(cls, filename: str, user_id: str) -> bool:
        """
        Verify if a user has access to download a file

        Args:
            filename: Name of the file
            user_id: Firebase UID of the requesting user

        Returns:
            True if user has access, False otherwise
        """
        export_file = cls.query.filter_by(filename=filename, is_deleted=False).first()

        if not export_file:
            return False

        # Check if file belongs to user
        if export_file.user_id != user_id:
            return False

        # Check if file has expired
        if export_file.expires_at and export_file.expires_at < datetime.utcnow():
            return False

        return True

    @classmethod
    def get_file_by_filename(cls, filename: str):
        """Get export file by filename"""
        return cls.query.filter_by(filename=filename, is_deleted=False).first()

    @classmethod
    def get_user_files(cls, user_id: str, file_type: str = None, limit: int = 100):
        """Get all export files for a user"""
        query = cls.query.filter_by(user_id=user_id, is_deleted=False)

        if file_type:
            query = query.filter_by(file_type=file_type)

        return query.order_by(cls.created_at.desc()).limit(limit).all()

    def mark_downloaded(self):
        """Update download statistics"""
        self.last_downloaded_at = datetime.utcnow()
        self.download_count += 1
        db.session.commit()

    def soft_delete(self):
        """Soft delete the export file record"""
        self.is_deleted = True
        db.session.commit()
