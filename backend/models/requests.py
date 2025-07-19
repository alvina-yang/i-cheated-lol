"""
Request models for the Chameleon Hackathon Discovery API
"""

from typing import List, Dict, Union
from pydantic import BaseModel


class TechnologySearchRequest(BaseModel):
    technologies: List[str] = []


class CloneRequest(BaseModel):
    project_name: str
    project_url: str
    clone_url: str


class EnhancedUntraceabilityRequest(BaseModel):
    hackathon_date: str = ""  # YYYY-MM-DD format - optional, only needed for git rewriting
    hackathon_start_time: str = ""  # HH:MM format - optional, only needed for git rewriting
    hackathon_duration: int = 48  # Duration in hours - optional, only needed for git rewriting
    git_username: str = ""  # Optional - only needed for git rewriting
    git_email: str = ""  # Optional - only needed for git rewriting
    target_repository_url: str = ""
    generate_commit_messages: bool = False  # Default to False so users opt-in


class SettingsUpdateRequest(BaseModel):
    setting_type: str  # 'user', 'repository', 'processing', 'terminal'
    settings: Dict[str, Union[str, bool, int, float]] 