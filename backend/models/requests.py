"""
Request models for the Chameleon Hackathon Discovery API
"""

from typing import List, Dict, Union
from pydantic import BaseModel


class TeamMember(BaseModel):
    """Team member information for multi-developer projects"""
    username: str
    email: str
    name: str = ""  # Optional display name


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
    team_members: List[TeamMember] = []  # List of team members
    target_repository_url: str = ""

    
    # Backward compatibility properties
    @property
    def git_username(self) -> str:
        """Get primary team member username for backward compatibility"""
        return self.team_members[0].username if self.team_members else ""
    
    @property
    def git_email(self) -> str:
        """Get primary team member email for backward compatibility"""
        return self.team_members[0].email if self.team_members else ""


class SettingsUpdateRequest(BaseModel):
    setting_type: str  # 'user', 'repository', 'processing', 'terminal'
    settings: Dict[str, Union[str, bool, int, float]] 