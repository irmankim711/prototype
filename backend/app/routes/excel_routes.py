"""
Excel upload and parsing routes.
Handles file upload, parsing, and data conversion.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid
from io import BytesIO
import tempfile
import shutil
from datetime import datetime

from ..services.excel_parser import ExcelParserService
from ..models import db, ParsedExcelFile, ExcelTable
from ..tasks import parse_excel_file_async

excel_bp = Blueprint('excel', __name__)
excel_service = ExcelParserService()


@excel_bp.route('/excel/parse', methods=['POST'])
@jwt_required()
def upload_and_parse_excel():
    """
    Upload and parse an Excel file.
    Supports both synchronous and asynchronous processing.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get processing options
        async_processing = request.form.get('async', 'false').lower() == 'true'
        include_preview = request.form.get('include_preview', 'true').lower() == 'true'
        
        # Validate file
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        is_valid, error_message = excel_service.validate_file(file_size, file.filename)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{original_filename}"
        
        # Save file temporarily
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        user_id = get_jwt_identity()
        
        try:
            if async_processing or file_size > 5 * 1024 * 1024:  # > 5MB
                # Async processing
                task = parse_excel_file_async.delay(
                    file_path=file_path,
                    user_id=user_id,
                    original_filename=original_filename,
                    file_size=file_size
                )
                
                return jsonify({
                    'success': True,
                    'processing_mode': 'async',
                    'task_id': task.id,
                    'message': 'File uploaded successfully. Processing started.',
                    'status_url': f'/api/excel/status/{task.id}'
                }), 202
            
            else:
                # Synchronous processing
                result = excel_service.parse_excel_file(file_path, original_filename)
                
                if result['success']:
                    # Save to database
                    parsed_file = ParsedExcelFile(
                        id=file_id,
                        user_id=user_id,
                        original_filename=original_filename,
                        file_size=file_size,
                        status='completed',
                        tables_count=result['tables_count'],
                        parsed_at=datetime.utcnow(),
                        metadata=result['metadata']
                    )
                    db.session.add(parsed_file)
                    
                    # Save tables
                    for table in result['tables']:
                        excel_table = ExcelTable(
                            id=str(uuid.uuid4()),
                            parsed_file_id=file_id,
                            name=table['name'],
                            sheet_name=table['sheet_name'],
                            row_count=table['row_count'],
                            column_count=table['column_count'],
                            headers=table['headers'],
                            data_types=table['data_types'],
                            table_range=table['range'],
                            data=table['data'] if include_preview else None
                        )
                        db.session.add(excel_table)
                    
                    db.session.commit()
                    
                    # Prepare response
                    response = {
                        'success': True,
                        'processing_mode': 'sync',
                        'file_id': file_id,
                        'filename': original_filename,
                        'tables_count': result['tables_count'],
                        'metadata': result['metadata'],
                        'tables': result['tables'] if include_preview else []
                    }
                    
                    return jsonify(response), 200
                else:
                    return jsonify({
                        'error': 'Failed to parse Excel file',
                        'details': result.get('error', 'Unknown error')
                    }), 500
        
        finally:
            # Clean up temporary file for sync processing
            if not async_processing and file_size <= 5 * 1024 * 1024:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    
    except Exception as e:
        current_app.logger.error(f"Error in upload_and_parse_excel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@excel_bp.route('/excel/status/<task_id>', methods=['GET'])
@jwt_required()
def get_parsing_status(task_id):
    """Get the status of an async Excel parsing task."""
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'pending',
                'message': 'Task is waiting to be processed'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'status': 'processing',
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'message': task.info.get('status', 'Processing...')
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': 'completed',
                'result': task.info
            }
        else:  # FAILURE
            response = {
                'state': task.state,
                'status': 'failed',
                'error': str(task.info)
            }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/files', methods=['GET'])
@jwt_required()
def get_parsed_files():
    """Get list of user's parsed Excel files."""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        files = ParsedExcelFile.query.filter_by(user_id=user_id)\
            .order_by(ParsedExcelFile.parsed_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'files': [{
                'id': f.id,
                'filename': f.original_filename,
                'file_size': f.file_size,
                'status': f.status,
                'tables_count': f.tables_count,
                'parsed_at': f.parsed_at.isoformat() if f.parsed_at else None,
                'metadata': f.metadata
            } for f in files.items],
            'pagination': {
                'page': page,
                'pages': files.pages,
                'per_page': per_page,
                'total': files.total
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/files/<file_id>', methods=['GET'])
@jwt_required()
def get_parsed_file_details(file_id):
    """Get detailed information about a parsed Excel file."""
    try:
        user_id = get_jwt_identity()
        
        parsed_file = ParsedExcelFile.query.filter_by(
            id=file_id, 
            user_id=user_id
        ).first()
        
        if not parsed_file:
            return jsonify({'error': 'File not found'}), 404
        
        # Get associated tables
        tables = ExcelTable.query.filter_by(parsed_file_id=file_id).all()
        
        return jsonify({
            'file': {
                'id': parsed_file.id,
                'filename': parsed_file.original_filename,
                'file_size': parsed_file.file_size,
                'status': parsed_file.status,
                'tables_count': parsed_file.tables_count,
                'parsed_at': parsed_file.parsed_at.isoformat() if parsed_file.parsed_at else None,
                'metadata': parsed_file.metadata
            },
            'tables': [{
                'id': table.id,
                'name': table.name,
                'sheet_name': table.sheet_name,
                'row_count': table.row_count,
                'column_count': table.column_count,
                'headers': table.headers,
                'data_types': table.data_types,
                'range': table.table_range,
                'has_data': table.data is not None
            } for table in tables]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/tables/<table_id>/data', methods=['GET'])
@jwt_required()
def get_table_data(table_id):
    """Get full data for a specific table."""
    try:
        user_id = get_jwt_identity()
        
        # Find table and verify ownership
        table = db.session.query(ExcelTable).join(ParsedExcelFile).filter(
            ExcelTable.id == table_id,
            ParsedExcelFile.user_id == user_id
        ).first()
        
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        
        return jsonify({
            'table': {
                'id': table.id,
                'name': table.name,
                'sheet_name': table.sheet_name,
                'row_count': table.row_count,
                'column_count': table.column_count,
                'headers': table.headers,
                'data_types': table.data_types,
                'range': table.table_range,
                'data': table.data
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/tables/<table_id>/csv', methods=['GET'])
@jwt_required()
def export_table_csv(table_id):
    """Export table data as CSV."""
    try:
        user_id = get_jwt_identity()
        
        # Find table and verify ownership
        table = db.session.query(ExcelTable).join(ParsedExcelFile).filter(
            ExcelTable.id == table_id,
            ParsedExcelFile.user_id == user_id
        ).first()
        
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        
        if not table.data:
            return jsonify({'error': 'Table data not available'}), 404
        
        # Convert to CSV
        csv_content = excel_service.convert_to_csv_format(table.data)
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{table.name}.csv"'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/tables/<table_id>/sql', methods=['GET'])
@jwt_required()
def get_table_sql_schema(table_id):
    """Get SQL CREATE TABLE statement for a table."""
    try:
        user_id = get_jwt_identity()
        
        # Find table and verify ownership
        table = db.session.query(ExcelTable).join(ParsedExcelFile).filter(
            ExcelTable.id == table_id,
            ParsedExcelFile.user_id == user_id
        ).first()
        
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        
        # Generate SQL schema
        table_dict = {
            'name': table.name,
            'headers': table.headers,
            'data_types': table.data_types
        }
        
        sql_schema = excel_service.generate_sql_schema(table_dict)
        
        return jsonify({
            'table_name': table.name,
            'sql_schema': sql_schema
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/files/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_parsed_file(file_id):
    """Delete a parsed Excel file and all associated tables."""
    try:
        user_id = get_jwt_identity()
        
        parsed_file = ParsedExcelFile.query.filter_by(
            id=file_id, 
            user_id=user_id
        ).first()
        
        if not parsed_file:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete associated tables first
        ExcelTable.query.filter_by(parsed_file_id=file_id).delete()
        
        # Delete the parsed file record
        db.session.delete(parsed_file)
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@excel_bp.route('/excel/tables/<table_id>/rename', methods=['PUT'])
@jwt_required()
def rename_table(table_id):
    """Rename a table."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'New table name is required'}), 400
        
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({'error': 'Table name cannot be empty'}), 400
        
        # Find table and verify ownership
        table = db.session.query(ExcelTable).join(ParsedExcelFile).filter(
            ExcelTable.id == table_id,
            ParsedExcelFile.user_id == user_id
        ).first()
        
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        
        table.name = new_name
        db.session.commit()
        
        return jsonify({'message': 'Table renamed successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
