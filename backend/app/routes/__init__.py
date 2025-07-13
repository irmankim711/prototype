# Routes package
from .dashboard import dashboard_bp
from .api import api
from .users import users_bp
from .forms import forms_bp
from .files import files_bp

__all__ = ['dashboard_bp', 'api', 'users_bp', 'forms_bp', 'files_bp']
