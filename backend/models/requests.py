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
    hackathon_date: str  # YYYY-MM-DD format
    hackathon_start_time: str  # HH:MM format
    hackathon_duration: int = 48  # Duration in hours
    git_username: str
    git_email: str
    target_repository_url: str = ""
    add_comments: bool = True
    add_documentation: bool = False
    generate_commit_messages: bool = True
    show_terminal_output: bool = True


class SettingsUpdateRequest(BaseModel):
    setting_type: str  # 'user', 'repository', 'processing', 'terminal'
    settings: Dict[str, Union[str, bool, int, float]] 