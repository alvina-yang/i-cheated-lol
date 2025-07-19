"""
Enhanced configuration management for the Chameleon system.
Handles user settings, repository configurations, and dynamic preferences.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class UserSettings:
    """User-specific settings for the Chameleon system."""
    git_username: str = ""
    git_email: str = ""
    preferred_branch: str = "main"
    hackathon_duration_hours: int = 48
    auto_backup: bool = True
    verbose_output: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        return cls(**data)


@dataclass
class RepositorySettings:
    """Repository-specific settings."""
    original_url: str = ""
    target_url: str = ""
    target_branch: str = "main"
    preserve_history: bool = False
    auto_push: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RepositorySettings':
        return cls(**data)


@dataclass
class ProcessingSettings:
    """Settings for code processing and modification."""
    add_comments: bool = True
    rename_variables: bool = True
    add_documentation: bool = False
    modify_commit_messages: bool = True
    obfuscate_author_info: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingSettings':
        return cls(**data)


@dataclass
class TerminalSettings:
    """Settings for terminal output and progress tracking."""
    show_progress: bool = True
    show_file_changes: bool = True
    show_git_output: bool = True
    update_interval_seconds: float = 1.0
    max_output_lines: int = 1000
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerminalSettings':
        return cls(**data)


class EnhancedConfig:
    """Enhanced configuration management for the Chameleon system."""
    
    # Base Configuration (from original config)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # LLM Configuration
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))
    
    # Search Configuration
    MAX_PROJECTS_TO_FIND = int(os.getenv('MAX_PROJECTS_TO_FIND', '10'))
    MIN_STARS = int(os.getenv('MIN_STARS', '1'))
    MAX_STARS = int(os.getenv('MAX_STARS', '100'))
    MAX_FORKS = int(os.getenv('MAX_FORKS', '30'))
    MAX_REPO_SIZE_KB = int(os.getenv('MAX_REPO_SIZE_KB', '10000'))
    
    # GitHub API Configuration
    GITHUB_API_BASE_URL = "https://api.github.com"
    GITHUB_SEARCH_DELAY = float(os.getenv('GITHUB_SEARCH_DELAY', '2.0'))
    GITHUB_REQUESTS_PER_MINUTE = int(os.getenv('GITHUB_REQUESTS_PER_MINUTE', '30'))
    
    # File System Configuration
    CLONE_DIRECTORY = os.path.expanduser(os.getenv('CLONE_DIRECTORY', '~/HackathonProject'))
    CONFIG_DIRECTORY = os.path.expanduser(os.getenv('CONFIG_DIRECTORY', '~/.chameleon'))
    
    # Analysis Configuration
    README_MAX_LENGTH = int(os.getenv('README_MAX_LENGTH', '3000'))
    MAX_FILES_TO_ANALYZE = int(os.getenv('MAX_FILES_TO_ANALYZE', '50'))
    ANALYSIS_TIMEOUT_SECONDS = int(os.getenv('ANALYSIS_TIMEOUT_SECONDS', '300'))
    
    # New Enhanced Configuration
    ENABLE_REAL_TIME_OUTPUT = bool(os.getenv('ENABLE_REAL_TIME_OUTPUT', 'True').lower() == 'true')
    ENABLE_FILE_MONITORING = bool(os.getenv('ENABLE_FILE_MONITORING', 'True').lower() == 'true')
    BACKUP_ORIGINAL_FILES = bool(os.getenv('BACKUP_ORIGINAL_FILES', 'True').lower() == 'true')
    
    # Configuration files
    USER_SETTINGS_FILE = "user_settings.json"
    REPOSITORY_SETTINGS_FILE = "repository_settings.json"
    PROCESSING_SETTINGS_FILE = "processing_settings.json"
    TERMINAL_SETTINGS_FILE = "terminal_settings.json"
    
    # Default settings instances
    _user_settings: Optional[UserSettings] = None
    _repository_settings: Optional[RepositorySettings] = None
    _processing_settings: Optional[ProcessingSettings] = None
    _terminal_settings: Optional[TerminalSettings] = None
    
    @classmethod
    def initialize(cls):
        """Initialize the enhanced configuration system."""
        # Create config directory if it doesn't exist
        os.makedirs(cls.CONFIG_DIRECTORY, exist_ok=True)
        os.makedirs(cls.CLONE_DIRECTORY, exist_ok=True)
        
        # Load all settings
        cls._load_all_settings()
        
        print("Enhanced configuration initialized successfully")
        print(f"- Config directory: {cls.CONFIG_DIRECTORY}")
        print(f"- Clone directory: {cls.CLONE_DIRECTORY}")
        print(f"- Real-time output: {cls.ENABLE_REAL_TIME_OUTPUT}")
        print(f"- File monitoring: {cls.ENABLE_FILE_MONITORING}")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize if not already done
        if cls._user_settings is None:
            cls.initialize()
        
        print("Configuration validated successfully")
        print(f"- Using LLM model: {cls.LLM_MODEL}")
        print(f"- Max projects to find: {cls.MAX_PROJECTS_TO_FIND}")
        print(f"- Target star range: {cls.MIN_STARS}-{cls.MAX_STARS}")
        print(f"- Max forks allowed: {cls.MAX_FORKS}")
        print(f"- Clone directory: {cls.CLONE_DIRECTORY}")
    
    @classmethod
    def get_user_settings(cls) -> UserSettings:
        """Get user settings, loading from file if necessary."""
        if cls._user_settings is None:
            cls._user_settings = cls._load_settings(cls.USER_SETTINGS_FILE, UserSettings)
        return cls._user_settings
    
    @classmethod
    def get_repository_settings(cls) -> RepositorySettings:
        """Get repository settings, loading from file if necessary."""
        if cls._repository_settings is None:
            cls._repository_settings = cls._load_settings(cls.REPOSITORY_SETTINGS_FILE, RepositorySettings)
        return cls._repository_settings
    
    @classmethod
    def get_processing_settings(cls) -> ProcessingSettings:
        """Get processing settings, loading from file if necessary."""
        if cls._processing_settings is None:
            cls._processing_settings = cls._load_settings(cls.PROCESSING_SETTINGS_FILE, ProcessingSettings)
        return cls._processing_settings
    
    @classmethod
    def get_terminal_settings(cls) -> TerminalSettings:
        """Get terminal settings, loading from file if necessary."""
        if cls._terminal_settings is None:
            cls._terminal_settings = cls._load_settings(cls.TERMINAL_SETTINGS_FILE, TerminalSettings)
        return cls._terminal_settings
    
    @classmethod
    def update_user_settings(cls, **kwargs) -> bool:
        """Update user settings and save to file."""
        try:
            current_settings = cls.get_user_settings()
            
            # Update settings
            for key, value in kwargs.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
            
            # Save to file
            cls._save_settings(cls.USER_SETTINGS_FILE, current_settings)
            cls._user_settings = current_settings
            
            return True
        except Exception as e:
            print(f"⚠️ Error updating user settings: {e}")
            return False
    
    @classmethod
    def update_repository_settings(cls, **kwargs) -> bool:
        """Update repository settings and save to file."""
        try:
            current_settings = cls.get_repository_settings()
            
            # Update settings
            for key, value in kwargs.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
            
            # Save to file
            cls._save_settings(cls.REPOSITORY_SETTINGS_FILE, current_settings)
            cls._repository_settings = current_settings
            
            return True
        except Exception as e:
            print(f"⚠️ Error updating repository settings: {e}")
            return False
    
    @classmethod
    def update_processing_settings(cls, **kwargs) -> bool:
        """Update processing settings and save to file."""
        try:
            current_settings = cls.get_processing_settings()
            
            # Update settings
            for key, value in kwargs.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
            
            # Save to file
            cls._save_settings(cls.PROCESSING_SETTINGS_FILE, current_settings)
            cls._processing_settings = current_settings
            
            return True
        except Exception as e:
            print(f"⚠️ Error updating processing settings: {e}")
            return False
    
    @classmethod
    def update_terminal_settings(cls, **kwargs) -> bool:
        """Update terminal settings and save to file."""
        try:
            current_settings = cls.get_terminal_settings()
            
            # Update settings
            for key, value in kwargs.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
            
            # Save to file
            cls._save_settings(cls.TERMINAL_SETTINGS_FILE, current_settings)
            cls._terminal_settings = current_settings
            
            return True
        except Exception as e:
            print(f"⚠️ Error updating terminal settings: {e}")
            return False
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        return {
            "user": cls.get_user_settings().to_dict(),
            "repository": cls.get_repository_settings().to_dict(),
            "processing": cls.get_processing_settings().to_dict(),
            "terminal": cls.get_terminal_settings().to_dict()
        }
    
    @classmethod
    def reset_settings(cls, setting_type: str = "all") -> bool:
        """Reset settings to defaults."""
        try:
            if setting_type == "all" or setting_type == "user":
                cls._user_settings = UserSettings()
                cls._save_settings(cls.USER_SETTINGS_FILE, cls._user_settings)
            
            if setting_type == "all" or setting_type == "repository":
                cls._repository_settings = RepositorySettings()
                cls._save_settings(cls.REPOSITORY_SETTINGS_FILE, cls._repository_settings)
            
            if setting_type == "all" or setting_type == "processing":
                cls._processing_settings = ProcessingSettings()
                cls._save_settings(cls.PROCESSING_SETTINGS_FILE, cls._processing_settings)
            
            if setting_type == "all" or setting_type == "terminal":
                cls._terminal_settings = TerminalSettings()
                cls._save_settings(cls.TERMINAL_SETTINGS_FILE, cls._terminal_settings)
            
            return True
        except Exception as e:
            print(f"⚠️ Error resetting settings: {e}")
            return False
    
    @classmethod
    def _load_all_settings(cls):
        """Load all settings from files."""
        cls._user_settings = cls._load_settings(cls.USER_SETTINGS_FILE, UserSettings)
        cls._repository_settings = cls._load_settings(cls.REPOSITORY_SETTINGS_FILE, RepositorySettings)
        cls._processing_settings = cls._load_settings(cls.PROCESSING_SETTINGS_FILE, ProcessingSettings)
        cls._terminal_settings = cls._load_settings(cls.TERMINAL_SETTINGS_FILE, TerminalSettings)
    
    @classmethod
    def _load_settings(cls, filename: str, settings_class) -> Any:
        """Load settings from a JSON file."""
        file_path = Path(cls.CONFIG_DIRECTORY) / filename
        
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return settings_class.from_dict(data)
            else:
                # Create default settings and save
                default_settings = settings_class()
                cls._save_settings(filename, default_settings)
                return default_settings
        except Exception as e:
            print(f"⚠️ Error loading settings from {filename}: {e}")
            return settings_class()
    
    @classmethod
    def _save_settings(cls, filename: str, settings: Any):
        """Save settings to a JSON file."""
        file_path = Path(cls.CONFIG_DIRECTORY) / filename
        
        try:
            with open(file_path, 'w') as f:
                json.dump(settings.to_dict(), f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving settings to {filename}: {e}")
    
    @classmethod
    def get_search_criteria(cls):
        """Get formatted search criteria for display."""
        return {
            'star_range': f"{cls.MIN_STARS}-{cls.MAX_STARS}",
            'max_forks': cls.MAX_FORKS,
            'max_size_kb': cls.MAX_REPO_SIZE_KB,
            'max_projects': cls.MAX_PROJECTS_TO_FIND
        }
    
    @classmethod
    def get_project_settings(cls, project_name: str) -> Dict[str, Any]:
        """Get settings for a specific project."""
        return {
            "project_name": project_name,
            "clone_path": os.path.join(cls.CLONE_DIRECTORY, project_name),
            "user_settings": cls.get_user_settings().to_dict(),
            "repository_settings": cls.get_repository_settings().to_dict(),
            "processing_settings": cls.get_processing_settings().to_dict(),
            "terminal_settings": cls.get_terminal_settings().to_dict()
        }
    
    @classmethod
    def validate_repository_url(cls, url: str) -> bool:
        """Validate a repository URL format."""
        if not url or not url.strip():
            return False
        
        # Basic URL validation
        valid_patterns = [
            'https://github.com/',
            'https://gitlab.com/',
            'https://bitbucket.org/',
            'git@github.com:',
            'git@gitlab.com:',
            'git@bitbucket.org:'
        ]
        
        return any(url.startswith(pattern) for pattern in valid_patterns)
    
    @classmethod
    def get_status_config(cls) -> Dict[str, Any]:
        """Get configuration for status tracking."""
        terminal_settings = cls.get_terminal_settings()
        
        return {
            "show_progress": terminal_settings.show_progress,
            "show_file_changes": terminal_settings.show_file_changes,
            "show_git_output": terminal_settings.show_git_output,
            "update_interval": terminal_settings.update_interval_seconds,
            "max_output_lines": terminal_settings.max_output_lines,
            "enable_real_time": cls.ENABLE_REAL_TIME_OUTPUT,
            "enable_monitoring": cls.ENABLE_FILE_MONITORING
        } 