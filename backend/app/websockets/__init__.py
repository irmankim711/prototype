"""
WebSocket Infrastructure for Real-time Collaboration
"""

from .editor_namespace import EditorNamespace
from .websocket_manager import websocket_manager

__all__ = ['EditorNamespace', 'websocket_manager']