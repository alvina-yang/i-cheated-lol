import json
import asyncio
from typing import Dict, Any
from pathlib import Path

from core.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
import prompts.feature_suggestion as prompts


class LLMResponseHandler:
    """Handles different LLM response formats"""
    
    @staticmethod
    def extract_json(response) -> Dict[str, Any]:
        """Extract JSON from various response formats"""
        try:
            # Handle ChatOpenAI response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Try direct JSON parse
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If it's wrapped in markdown, extract it
                if '```json' in content:
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    if end != -1:
                        json_str = content[start:end].strip()
                        return json.loads(json_str)
                
                # Return error with raw response for debugging
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": content[:500] + "..." if len(content) > 500 else content
                }
                
        except Exception as e:
            return {"error": f"Response processing error: {str(e)}"}


class SuggestFeatureAgent(BaseAgent):
    def __init__(self):
        super().__init__("SuggestFeatureAgent")
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the suggest feature agent."""
        project_path = task_data.get("project_path")
        
        if not project_path:
            return {
                "error": "Missing required parameter: project_path"
            }
        
        return asyncio.run(self.suggest_feature(project_path))
    
    async def suggest_feature(self, project_path: str) -> Dict[str, Any]:
        """Suggest a feature for the project."""
        try:
            backend_dir = Path(__file__).parent.parent
            summary_file = backend_dir / "file_summary.json"
            
            if not summary_file.exists():
                return {"error": "file_summary.json not found"}
            
            with open(summary_file) as f:
                file_summaries = json.load(f)
            
            # Extract just the file summaries dict (assuming first project)
            project_data = next(iter(file_summaries.values()))
            summaries = project_data.get("file_summaries", {})
            
            prompt = prompts.FeatureSuggestionPrompts.get_feature_suggestion_prompt(json.dumps(summaries))
            response = self.llm.invoke(prompt)
            
            return LLMResponseHandler.extract_json(response)
            
        except Exception as e:
            return {"error": f"Feature suggestion failed: {str(e)}"}
    
        
        
        