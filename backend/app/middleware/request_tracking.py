"""
Request tracking middleware for generating unique request IDs
and adding them to the Flask g object for error tracking
"""

from flask import g, request, current_app
import uuid
import time
from functools import wraps


class RequestTracker:
    """Middleware for tracking requests with unique IDs"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the request tracker with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """Set up request tracking before each request"""
        # Generate unique request ID
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.time()

        # Add request ID to logs
        if current_app.logger:
            current_app.logger.info(
                f"Request started: {request.method} {request.path} | "
                f"Request ID: {g.request_id} | "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )

    def after_request(self, response):
        """Log request completion after each request"""
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time

            # Add request ID to response headers for debugging
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')

            # Log request completion
            if current_app.logger:
                current_app.logger.info(
                    f"Request completed: {request.method} {request.path} | "
                    f"Status: {response.status_code} | "
                    f"Duration: {duration:.3f}s | "
                    f"Request ID: {getattr(g, 'request_id', 'unknown')}"
                )

        return response


def track_request_performance(f):
    """Decorator to track function performance within a request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        function_name = f.__name__

        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time

            current_app.logger.debug(
                f"Function {function_name} completed in {duration:.3f}s | "
                f"Request ID: {getattr(g, 'request_id', 'unknown')}"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            current_app.logger.error(
                f"Function {function_name} failed after {duration:.3f}s | "
                f"Error: {str(e)} | "
                f"Request ID: {getattr(g, 'request_id', 'unknown')}"
            )

            raise

    return decorated_function


# Global instance
request_tracker = RequestTracker()