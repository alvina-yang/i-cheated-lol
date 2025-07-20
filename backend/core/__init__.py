"""
Core module for the Chameleon Hackathon Project Discovery System.

This module contains the foundational classes and utilities used throughout the system.
"""

from .config import Config
from .base_agent import BaseAgent
from .llm_wrapper import get_default_llm_wrapper, create_llm_wrapper, BaseLLMWrapper

__all__ = ['Config', 'BaseAgent', 'get_default_llm_wrapper', 'create_llm_wrapper', 'BaseLLMWrapper'] 