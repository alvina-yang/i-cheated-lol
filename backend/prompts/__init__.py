"""
Prompts module for the Chameleon system.
Contains all prompt templates for AI agents.
"""

from .search_prompts import SearchPrompts
from .validator_prompts import ValidatorPrompts

from .code_modifier_prompts import CodeModifierPrompts
from .git_prompts import GitPrompts
from .presentation_prompts import PresentationPrompts
from .file_analysis_prompts import FileAnalysisPrompts

__all__ = [
    'SearchPrompts',
    'ValidatorPrompts',

    'CodeModifierPrompts',
    'GitPrompts',
    'PresentationPrompts',
    'FileAnalysisPrompts'
] 