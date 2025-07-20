import json
import os
import asyncio
from typing import Dict, Any, List

from core.base_agent import BaseAgent
from prompts.dependancy_graph_prompts import DependancyGraphPrompts
from utils.status_tracker import get_global_tracker
from langchain_ollama import OllamaLLM
import prompts.code_generator_prompts as prompts
from langchain.chat_models import ChatOpenAI

class CodeGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodeGenerationAgent")
        self.chat_model = OllamaLLM(model="deepseek-r1:8b")

    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the code generation agent."""
        pass
    
    async def pick_files(self, task_data: str) -> Dict[str, Any]:
        """Pick the files that are most relevant to the feature to create."""
        chat_model = ChatOpenAI(model="gpt-4o-mini") #type: ignore
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "file_summary.json")
        if os.path.exists(file_path):
            prompt = prompts.CodeModifierPrompts.get_file_picker_summary_prompt(task_data, json.dumps(file_path))
            response = chat_model.invoke(prompt)
            return json.loads(response.content)
        else:
            return {"error": "File summary not found"}
    
    def get_files(self, task_data: str) -> Dict[str, Any]:
        """Get the files that are most relevant to the feature to create."""
    
    async def generate_code(self, task_data: str) -> Dict[str, Any]:
        input_json = await self.pick_files(task_data)
        if "error" in input_json:
            return {"error": "File summary not found"}
        else:
            ...