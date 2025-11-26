"""
DraftCraft Backend Configuration
"""
from .celery import app as celery_app

# Expose celery app for Celery CLI
celery = celery_app

__all__ = ('celery_app', 'celery')
