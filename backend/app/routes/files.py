from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
from sqlalchemy import desc, func
from .. import db
from ..models import File, Permission
from ..decorators import require_permission, get_current_user

files_bp = Blueprint('files', __name__)

# Configuration
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'zip', 'rar'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_path():
    """Get the upload directory path."""
    upload_path = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_path, exist_ok=True)
    return upload_path

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
@require_permission(Permission.UPLOAD_FILE)
def upload_file():
    """Upload a file."""
    user = get_current_user()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    file_extension = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    
    # Save file
    upload_path = get_upload_path()
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Save file record to database
    file_record = File(
        filename=unique_filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.mimetype,
        uploader_id=user.id,
        is_public=request.form.get('is_public', 'false').lower() == 'true'
    )
    
    db.session.add(file_record)
    db.session.commit()
    
    return jsonify({
        'id': file_record.id,
        'filename': file_record.original_filename,
        'file_size': file_record.file_size,
        'mime_type': file_record.mime_type,
        'url': f'/api/files/{file_record.id}/download',
        'message': 'File uploaded successfully'
    }), 201

@files_bp.route('/', methods=['GET'])
@jwt_required()
def get_files():
    """Get files for the current user."""
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Users see their own files + public files
    query = File.query.filter(
        db.or_(File.uploader_id == user.id, File.is_public == True)
    )
    
    files = query.order_by(desc(File.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'files': [{
            'id': file.id,
            'filename': file.original_filename,
            'file_size': file.file_size,
            'mime_type': file.mime_type,
            'created_at': file.created_at.isoformat(),
            'uploader_id': file.uploader_id,
            'is_public': file.is_public,
            'url': f'/api/files/{file.id}/download'
        } for file in files.items],
        'pagination': {
            'page': page,
            'pages': files.pages,
            'per_page': per_page,
            'total': files.total
        }
    }), 200

@files_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_file_stats():
    """Get file statistics for the current user."""
    user = get_current_user()
    
    total_files = File.query.filter_by(uploader_id=user.id).count()
    total_size = db.session.query(func.sum(File.file_size)).filter_by(uploader_id=user.id).scalar() or 0
    public_files = File.query.filter_by(uploader_id=user.id, is_public=True).count()
    
    # Files uploaded this week
    week_ago = datetime.now() - timedelta(days=7)
    weekly_uploads = File.query.filter(
        File.uploader_id == user.id,
        File.created_at >= week_ago
    ).count()
    
    return jsonify({
        'total_files': total_files,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'public_files': public_files,
        'private_files': total_files - public_files,
        'weekly_uploads': weekly_uploads
    }), 200
