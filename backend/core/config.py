"""
Configuration management for the Chameleon system.
Handles environment variables, API keys, and system settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration management for the Chameleon system."""
    
    # API Configuration
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
    
    # Analysis Configuration
    README_MAX_LENGTH = int(os.getenv('README_MAX_LENGTH', '3000'))
    MAX_FILES_TO_ANALYZE = int(os.getenv('MAX_FILES_TO_ANALYZE', '50'))
    ANALYSIS_TIMEOUT_SECONDS = int(os.getenv('ANALYSIS_TIMEOUT_SECONDS', '300'))
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create clone directory if it doesn't exist
        os.makedirs(cls.CLONE_DIRECTORY, exist_ok=True)
        
        print("Configuration validated successfully")
        print(f"- Using LLM model: {cls.LLM_MODEL}")
        print(f"- Max projects to find: {cls.MAX_PROJECTS_TO_FIND}")
        print(f"- Target star range: {cls.MIN_STARS}-{cls.MAX_STARS}")
        print(f"- Max forks allowed: {cls.MAX_FORKS}")
        print(f"- Clone directory: {cls.CLONE_DIRECTORY}")
    
    @classmethod
    def get_search_criteria(cls):
        """Get formatted search criteria for display."""
        return {
            'star_range': f"{cls.MIN_STARS}-{cls.MAX_STARS}",
            'max_forks': cls.MAX_FORKS,
            'max_size_kb': cls.MAX_REPO_SIZE_KB,
            'max_projects': cls.MAX_PROJECTS_TO_FIND
        } 