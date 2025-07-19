"""
Presentation Script Generator Agent for creating compelling hackathon pitch scripts.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from core.base_agent import BaseAgent
from prompts.presentation_prompts import PresentationPrompts
from core.config import Config


class PresentationAgent(BaseAgent):
    """
    Agent responsible for generating presentation scripts for hackathon pitches.
    Uses README content and project structure to create compelling narratives.
    """
    
    def __init__(self):
        super().__init__("PresentationAgent")
        self.presentation_prompts = PresentationPrompts()
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the main functionality of the agent.
        
        Args:
            task_data: Dictionary containing project_path and project_name
            
        Returns:
            Dict containing the generated presentation script and metadata
        """
        project_path = task_data.get("project_path")
        project_name = task_data.get("project_name")
        
        if not project_path or not project_name:
            return {
                "success": False,
                "message": "Missing required parameters: project_path and project_name",
                "script": "",
                "project_name": project_name or "Unknown"
            }
        
        return self.generate_presentation_script(project_path, project_name)
    
    def generate_presentation_script(self, project_path: str, project_name: str) -> Dict[str, Any]:
        """
        Generate a presentation script based on project README and structure.
        
        Args:
            project_path: Path to the project directory
            project_name: Name of the project
            
        Returns:
            Dict containing success status, script content, and metadata
        """
        try:
            # Read README content
            readme_content = self._get_readme_content(project_path)
            
            # Get project structure overview
            project_structure = self._get_project_structure(project_path)
            
            # Detect technologies and dependencies
            technologies = self._detect_technologies(project_path)
            
            # Generate the presentation script using LLM
            script_result = self._generate_script_with_llm(
                project_name=project_name,
                readme_content=readme_content,
                project_structure=project_structure,
                technologies=technologies
            )
            
            if script_result:
                return {
                    "success": True,
                    "script": script_result,
                    "project_name": project_name,
                    "technologies": technologies,
                    "structure_overview": project_structure,
                    "message": "Presentation script generated successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to generate presentation script",
                    "script": "",
                    "project_name": project_name
                }
                
        except Exception as e:
            self.log(f"Error generating presentation script: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"Error generating presentation script: {str(e)}",
                "script": "",
                "project_name": project_name
            }
    
    def _get_readme_content(self, project_path: str) -> str:
        """Extract README content from the project."""
        readme_files = ['README.md', 'readme.md', 'README.txt', 'readme.txt', 'README']
        
        for readme_file in readme_files:
            readme_path = os.path.join(project_path, readme_file)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except Exception as e:
                    self.log(f"Could not read {readme_file}: {str(e)}", "WARNING")
                    continue
        
        return ""
    
    def _get_project_structure(self, project_path: str) -> str:
        """Get a high-level overview of project structure."""
        try:
            structure_lines = []
            
            # Get top-level directories and important files
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    structure_lines.append(f"📁 {item}/")
                elif os.path.isfile(item_path):
                    # Only include important files
                    important_files = [
                        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
                        '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.cs',
                        'package.json', 'requirements.txt', 'Dockerfile', 'docker-compose.yml',
                        'Makefile', 'CMakeLists.txt', '.env', 'config'
                    ]
                    if any(item.endswith(ext) or item.lower() in ['dockerfile', 'makefile', 'license'] for ext in important_files):
                        structure_lines.append(f"📄 {item}")
            
            return "\n".join(structure_lines[:20])  # Limit to first 20 items
            
        except Exception as e:
            self.log(f"Could not analyze project structure: {str(e)}", "WARNING")
            return "Project structure analysis unavailable"
    
    def _detect_technologies(self, project_path: str) -> list:
        """Detect technologies used in the project."""
        technologies = []
        
        # Check for common dependency files
        tech_indicators = {
            'package.json': ['Node.js', 'JavaScript', 'npm'],
            'requirements.txt': ['Python', 'pip'],
            'Pipfile': ['Python', 'pipenv'],
            'pyproject.toml': ['Python'],
            'Gemfile': ['Ruby', 'Rails'],
            'Cargo.toml': ['Rust'],
            'go.mod': ['Go'],
            'pom.xml': ['Java', 'Maven'],
            'build.gradle': ['Java', 'Gradle'],
            'composer.json': ['PHP'],
            'Dockerfile': ['Docker'],
            'docker-compose.yml': ['Docker', 'Docker Compose'],
            '.env': ['Environment Configuration']
        }
        
        for file_name, techs in tech_indicators.items():
            if os.path.exists(os.path.join(project_path, file_name)):
                technologies.extend(techs)
        
        # Check for common file extensions
        file_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React/TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.cs': 'C#'
        }
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Skip hidden directories and common non-source directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in file_extensions:
                        tech = file_extensions[ext]
                        if tech not in technologies:
                            technologies.append(tech)
        except Exception as e:
            self.log(f"Error scanning files for technologies: {str(e)}", "WARNING")
        
        return list(set(technologies))  # Remove duplicates
    
    def _generate_script_with_llm(self, project_name: str, readme_content: str, 
                                  project_structure: str, technologies: list) -> Optional[str]:
        """Generate presentation script using LLM."""
        try:
            # Prepare context for LLM
            context = {
                "project_name": project_name,
                "readme_content": readme_content[:5000],  # Limit README length
                "project_structure": project_structure,
                "technologies": ", ".join(technologies) if technologies else "Not detected"
            }
            
            # Get the presentation script prompt
            prompt = self.presentation_prompts.get_presentation_script_prompt(context)
            
            # Call LLM with the prompt
            system_prompt = self.presentation_prompts.get_system_prompt()
            
            # Original LangChain method (commented out for Groq)
            # full_prompt = f"{system_prompt}\n\n{prompt}"
            # response = self.llm.invoke(full_prompt)
            # return response.content.strip()
            
            # Groq API call
            response = self.llm.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.log(f"LLM call failed: {str(e)}", "ERROR")
            return None 