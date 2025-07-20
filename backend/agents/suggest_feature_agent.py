import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
import prompts.code_generator_prompts as prompts


class SuggestFeatureAgent(BaseAgent):
    def __init__(self):
        super().__init__("SuggestFeatureAgent")
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the suggest feature agent."""
        project_path = task_data.get("project_path")
        feature = task_data.get("feature")
        
    