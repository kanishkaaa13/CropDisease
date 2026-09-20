"""
Deprecated module: Re-exports all models from app.db.models package
to maintain backwards compatibility and prevent shadow import conflicts.
"""
from app.db.models import *  # noqa: F401, F403
