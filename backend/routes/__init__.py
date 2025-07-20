"""
Routes package for the Chameleon Hackathon Discovery API
"""

from .search import router as search_router
from .clone import router as clone_router
from .untraceable import router as untraceable_router
from .status import router as status_router
from .settings import router as settings_router
from .project import router as project_router
from .code_generation import router as code_generation_router
from .feature_suggestion import router as feature_suggestion_router

__all__ = [
    "search_router",
    "clone_router", 
    "untraceable_router",
    "status_router",
    "settings_router",
    "project_router",
    "code_generation_router",
    "feature_suggestion_router"
] 