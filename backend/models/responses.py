"""
Response models for the Chameleon Hackathon Discovery API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ProjectInfo(BaseModel):
    name: str
    description: str
    technologies: List[str]
    readme: str
    stars: int
    forks: int
    language: str
    url: str
    complexity_score: int
    innovation_indicators: List[str]


class ProjectSearchResponse(BaseModel):
    projects: List[ProjectInfo]
    total_found: int
    search_technologies: List[str]


class CloneResponse(BaseModel):
    success: bool
    message: str
    location: Optional[str] = None


class EnhancedUntraceabilityResponse(BaseModel):
    success: bool
    message: str
    commits_modified: int = 0
    files_modified: int = 0
    status_tracking_id: str = ""


class SettingsResponse(BaseModel):
    success: bool
    message: str
    settings: Dict[str, Any] = {}


class StatusResponse(BaseModel):
    current_operation: Optional[str] = None
    tasks: List[Dict[str, Any]] = []
    recent_output: List[str] = []
    summary: Dict[str, Any] = {} 