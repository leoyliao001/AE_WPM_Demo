"""
API view modules, one file per frontend feature area.

Import views from submodules here when you need a single entry point.
"""

from .health import health

__all__ = ["health"]
