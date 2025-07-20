import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
import prompts.code_generator_prompts as prompts


class FileResolver:
    """Handles all file path resolution and reading"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).expanduser()
        
    def read_file(self, file_path: str) -> Optional[str]:
        """Read a file and return its content, or None if not found"""
        try:
            full_path = self.project_path / file_path.lstrip('/')
            if full_path.exists():
                return full_path.read_text()
            return None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def resolve_dependency_path(self, main_file_path: str, dep_path: str) -> Path:
        """Resolve dependency path relative to the main file's directory"""
        main_file = self.project_path / main_file_path.lstrip('/')
        main_dir = main_file.parent
        return main_dir / dep_path.lstrip('/')


class DependencyLoader:
    """Loads file dependencies into structured format"""
    
    def __init__(self, file_resolver: FileResolver, dependency_graph: Dict):
        self.file_resolver = file_resolver
        self.dependency_graph = dependency_graph
    
    def load_file_with_dependencies(self, file_path: str, description: str) -> Dict[str, Any]:
        """Load a file and all its dependencies"""
        # Read main file
        content = self.file_resolver.read_file(file_path)
        if not content:
            return {"error": f"File not found: {file_path}"}
        
        # Load dependencies
        deps = {}
        dep_paths = self.dependency_graph.get(file_path, [])
        
        for dep_path in dep_paths:
            dep_full_path = self.file_resolver.resolve_dependency_path(file_path, dep_path)
            dep_content = self.file_resolver.read_file(str(dep_full_path.relative_to(self.file_resolver.project_path)))
            
            if dep_content:
                deps[dep_path] = {
                    "language": Path(dep_path).suffix.lstrip('.') or "unknown",
                    "description": f"Dependency: {dep_path}",
                    "code": dep_content,
                    "dependencies": self.dependency_graph.get(dep_path, [])
                }
        
        return {
            "language": Path(file_path).suffix.lstrip('.') or "unknown", 
            "description": description,
            "code": content,
            "dependencies": deps
        }


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


class CodeGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodeGenerationAgent")
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the code generation agent."""
        project_path = task_data.get("project_path")
        feature = task_data.get("feature") or task_data.get("feature_description")
        max_files = task_data.get("max_files", 5)
        
        if not project_path or not feature:
            return {
                "error": "Missing required parameters: project_path and/or feature"
            }
        
        return asyncio.run(self.generate_code(project_path, feature, max_files))
    
    async def pick_files(self, feature: str, max_files: int = 5) -> Dict[str, Any]:
        """Pick relevant files using LLM"""
        # Load file summaries
        backend_dir = Path(__file__).parent.parent
        summary_file = backend_dir / "file_summary.json"
        
        if not summary_file.exists():
            return {"error": "file_summary.json not found"}
        
        try:
            with open(summary_file) as f:
                file_summaries = json.load(f)
            
            # Extract just the file summaries dict (assuming first project)
            project_data = next(iter(file_summaries.values()))
            summaries = project_data.get("file_summaries", {})
            
            # Call LLM
            prompt = prompts.CodeModifierPrompts.get_file_picker_summary_prompt(feature, json.dumps(summaries))
            response = self.llm.invoke(prompt)
            
            result = LLMResponseHandler.extract_json(response)
            
            # Remove reasoning if present
            if "reasoning" in result:
                result.pop("reasoning")
            
            # Limit number of files if max_files is specified
            if max_files and len(result) > max_files:
                # Keep only the first max_files items
                limited_result = dict(list(result.items())[:max_files])
                return limited_result
                
            return result
            
        except Exception as e:
            return {"error": f"File picking failed: {str(e)}"}
    
    async def generate_code(self, project_path: str, feature: str, max_files: int = 5) -> Dict[str, Any]:
        """Main code generation workflow"""
        try:
            # Step 1: Pick files
            selected_files = await self.pick_files(feature, max_files)
            if "error" in selected_files:
                return selected_files
            
            # Step 2: Load dependency graph
            backend_dir = Path(__file__).parent.parent
            dep_graph_file = backend_dir / "dependancy_graph.json"
            
            if not dep_graph_file.exists():
                return {"error": "dependency_graph.json not found"}
            
            with open(dep_graph_file) as f:
                dependency_graph = json.load(f)
            
            # Step 3: Load files with dependencies
            file_resolver = FileResolver(project_path)
            dep_loader = DependencyLoader(file_resolver, dependency_graph)
            
            files_data = {}
            for file_path, description in selected_files.items():
                file_data = dep_loader.load_file_with_dependencies(file_path, description)
                if "error" not in file_data:
                    files_data[file_path] = file_data
            
            if not files_data:
                return {"error": "No valid files could be loaded"}
            
            # Step 4: Generate code
            prompt = prompts.CodeModifierPrompts.get_code_generation_prompt(json.dumps(files_data))
            response = self.llm.invoke(prompt)
            
            return LLMResponseHandler.extract_json(response)
            
        except Exception as e:
            return {"error": f"Code generation failed: {str(e)}"}


def main():
    agent = CodeGenerationAgent()
    results = asyncio.run(agent.generate_code("~/HackathonProject/pitch-please", "Modify main.py in anyway you want", 3))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()