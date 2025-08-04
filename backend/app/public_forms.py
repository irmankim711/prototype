"""
Public forms blueprint - wrapper for routes/public_forms.py
"""
from .routes.public_forms import public_forms_bp

# Re-export the blueprint
__all__ = ['public_forms_bp']
