"""
Database Health Check API Routes
Provides endpoints for monitoring database health and connection status
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..core.database import (
    check_database_health, 
    get_database_info, 
    get_db_manager,
    DatabaseConnectionError
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
db_health_bp = Blueprint('database_health', __name__, url_prefix='/api/database')

@db_health_bp.route('/health', methods=['GET'])
@jwt_required()
def health_check():
    """
    Check database health status
    
    Query Parameters:
        force (bool): Force health check regardless of interval (default: false)
    
    Returns:
        JSON response with health status
    """
    try:
        # Get query parameters
        force = request.args.get('force', 'false').lower() == 'true'
        
        # Perform health check
        health_status = check_database_health(force=force)
        
        # Log health check result
        if health_status.get('status') == 'healthy':
            logger.info("Database health check requested - Status: Healthy")
        else:
            logger.warning(f"Database health check requested - Status: {health_status.get('status')}")
        
        return jsonify({
            'success': True,
            'data': health_status,
            'message': 'Database health check completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to perform database health check'
        }), 500

@db_health_bp.route('/info', methods=['GET'])
@jwt_required()
def connection_info():
    """
    Get database connection information
    
    Returns:
        JSON response with connection details
    """
    try:
        # Get connection information
        conn_info = get_database_info()
        
        # Log connection info request
        logger.info("Database connection info requested")
        
        return jsonify({
            'success': True,
            'data': conn_info,
            'message': 'Database connection information retrieved'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get database connection info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve database connection information'
        }), 500

@db_health_bp.route('/status', methods=['GET'])
@jwt_required()
def detailed_status():
    """
    Get detailed database status including health, connection info, and pool status
    
    Returns:
        JSON response with comprehensive database status
    """
    try:
        # Get database manager
        db_manager = get_db_manager()
        
        # Perform health check
        health_status = db_manager.health_check(force=True)
        
        # Get connection info
        conn_info = db_manager.get_connection_info()
        
        # Get pool status if available
        pool_status = {}
        if db_manager.engine and hasattr(db_manager.engine, 'pool'):
            try:
                pool = db_manager.engine.pool
                pool_status = {
                    'pool_size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid() if hasattr(pool, 'invalid') else 0
                }
            except Exception as e:
                logger.warning(f"Failed to get pool status: {str(e)}")
                pool_status = {'error': str(e)}
        
        # Compile comprehensive status
        status = {
            'health': health_status,
            'connection': conn_info,
            'pool': pool_status,
            'manager_status': {
                'initialized': db_manager.is_initialized,
                'last_health_check': db_manager.last_health_check
            }
        }
        
        # Log status request
        logger.info("Database detailed status requested")
        
        return jsonify({
            'success': True,
            'data': status,
            'message': 'Database status retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get database status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve database status'
        }), 500

@db_health_bp.route('/test', methods=['POST'])
@jwt_required()
def test_connection():
    """
    Test database connection with custom query
    
    Request Body:
        query (str): SQL query to test (optional, defaults to SELECT 1)
        timeout (int): Connection timeout in seconds (optional, defaults to 10)
    
    Returns:
        JSON response with test results
    """
    try:
        # Get request data
        data = request.get_json() or {}
        test_query = data.get('query', 'SELECT 1 as test')
        timeout = data.get('timeout', 10)
        
        # Get database manager
        db_manager = get_db_manager()
        
        # Test connection with custom query
        try:
            with db_manager.get_session() as session:
                from sqlalchemy import text
                result = session.execute(text(test_query))
                
                # Fetch results (limit to first 10 rows for safety)
                rows = []
                for i, row in enumerate(result):
                    if i >= 10:  # Limit results
                        break
                    if hasattr(row, '_asdict'):
                        rows.append(row._asdict())
                    else:
                        rows.append([str(col) for col in row])
                
                # Get row count
                row_count = len(rows)
                
                test_result = {
                    'query': test_query,
                    'execution_time': 'N/A',  # Could be enhanced with timing
                    'row_count': row_count,
                    'results': rows,
                    'status': 'success'
                }
                
                logger.info(f"Database connection test successful - Query: {test_query}, Rows: {row_count}")
                
                return jsonify({
                    'success': True,
                    'data': test_result,
                    'message': 'Database connection test successful'
                }), 200
                
        except Exception as query_error:
            logger.warning(f"Database query test failed: {str(query_error)}")
            return jsonify({
                'success': False,
                'error': str(query_error),
                'message': 'Database query test failed',
                'data': {
                    'query': test_query,
                    'status': 'failed'
                }
            }), 400
            
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to perform database connection test'
        }), 500

@db_health_bp.route('/reconnect', methods=['POST'])
@jwt_required()
def reconnect():
    """
    Force database reconnection (useful for troubleshooting connection issues)
    
    Returns:
        JSON response with reconnection status
    """
    try:
        # Get database manager
        db_manager = get_db_manager()
        
        # Close existing connections
        db_manager.close()
        
        # Reinitialize
        db_manager.initialize()
        
        # Test connection
        health_status = db_manager.health_check(force=True)
        
        logger.info("Database reconnection completed successfully")
        
        return jsonify({
            'success': True,
            'data': {
                'reconnection_status': 'completed',
                'health_after_reconnect': health_status
            },
            'message': 'Database reconnection completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Database reconnection failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to reconnect to database'
        }), 500

# Error handlers
@db_health_bp.errorhandler(DatabaseConnectionError)
def handle_database_error(error):
    """Handle database connection errors"""
    logger.error(f"Database connection error: {str(error)}")
    return jsonify({
        'success': False,
        'error': str(error),
        'message': 'Database connection error occurred'
    }), 503

@db_health_bp.errorhandler(Exception)
def handle_generic_error(error):
    """Handle generic errors"""
    logger.error(f"Unexpected error in database health API: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
