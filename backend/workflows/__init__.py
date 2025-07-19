"""
Workflow orchestration for the Chameleon Hackathon Project Discovery System.

This module contains the main workflow chains that coordinate the agents
to discover, analyze, and clone hackathon projects.
"""

from .discovery_chain import TechnologyProjectDiscoveryChain

__all__ = ['TechnologyProjectDiscoveryChain'] 