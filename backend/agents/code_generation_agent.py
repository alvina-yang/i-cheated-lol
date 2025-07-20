import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.base_agent import BaseAgent
import prompts.code_generator_prompts as prompts

# Import OpenAI specifically for code generation
from langchain_openai import ChatOpenAI


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
        # Use OpenAI GPT-4o specifically for code generation
        import os
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            try:
                self.openai_llm = ChatOpenAI(
                    model="gpt-4o",
                    temperature=0.1  # Lower temperature for more consistent code generation
                )
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI: {e}")
                self.openai_llm = None
        else:
            print("Warning: OPENAI_API_KEY not found. Code generation will use fallback.")
            self.openai_llm = None
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the code generation agent."""
        project_path = task_data.get("project_path")
        feature = task_data.get("feature") or task_data.get("feature_description")
        max_files = task_data.get("max_files", 5)
        
        if not project_path or not feature:
            return {
                "error": "Missing required parameters: project_path and/or feature"
            }
        
        try:
            # Load file summaries
            backend_dir = Path(__file__).parent.parent
            summary_file = backend_dir / "file_summary.json"
            
            if not summary_file.exists():
                return {"error": "file_summary.json not found. Please run file analysis first."}

            with open(summary_file) as f:
                file_summaries = json.load(f)
            
            # Extract just the file summaries dict (assuming first project)
            project_data = next(iter(file_summaries.values()))
            summaries = project_data.get("file_summaries", {})
            
            # Load dependency graph
            dependency_file = backend_dir / "dependancy_graph.json"
            dependency_graph = {}
            if dependency_file.exists():
                with open(dependency_file) as f:
                    dependency_graph = json.load(f)
            
            # Generate code using OpenAI GPT-4o
            prompt_messages = prompts.CodeModifierPrompts.get_code_generation_prompt(
                json.dumps({
                    "feature_request": feature,
                    "file_summaries": summaries,
                    "dependency_graph": dependency_graph,
                    "project_path": project_path
                }, indent=2)
            )
            
            # Use OpenAI LLM for better code generation if available
            if self.openai_llm:
                response = self.openai_llm.invoke(prompt_messages)
                
                # Extract content from response
                if hasattr(response, 'content'):
                    content = response.content
                else:
                    content = str(response)
                
                # Parse JSON response
                result = LLMResponseHandler.extract_json(content)
            else:
                # Fallback to basic code generation
                result = {
                    "frontend/app/layout.tsx": f"// Generated code for: {feature}\n// Using fallback generation\n\n// TODO: Implement {feature}\nexport default function Layout() {{\n  return (\n    <div>\n      {{/* {feature} implementation */}}\n    </div>\n  );\n}}"
                }
            
            return result
            
        except Exception as e:
            return {"error": f"Code generation failed: {str(e)}"}


def main():
    agent = CodeGenerationAgent()
    results = agent.execute({"project_path": "~/HackathonProject/pitch-please", "feature": "Modify main.py in anyway you want", "max_files": 3})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()