"""
Code Modifier Agent for adding comments and changing variable names in source code.
"""

import json
import os
import re
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from core.base_agent import BaseAgent
from prompts.code_modifier_prompts import CodeModifierPrompts
from core.config import Config


class CodeModifierAgent(BaseAgent):
    """
    Agent responsible for modifying source code by adding comments and improving variable names.
    """
    
    def __init__(self):
        super().__init__("CodeModifierAgent")
        self.code_modifier_prompts = CodeModifierPrompts()
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp'
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a source code file to determine what modifications would be beneficial.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()
            
            # Get file info
            file_extension = Path(file_path).suffix.lower()
            language = self.supported_extensions.get(file_extension, 'unknown')
            filename = os.path.basename(file_path)
            file_size = len(code_content.splitlines())
            
            if language == 'unknown':
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_extension}"
                }
            
            # Generate analysis prompt
            prompt = self.code_modifier_prompts.get_file_analysis_prompt(
                language, filename, file_size, code_content
            )
            
            response = self.llm.invoke(prompt)
            
            # Parse the JSON response
            analysis = json.loads(response.content)
            
            analysis.update({
                "success": True,
                "file_path": file_path,
                "language": language,
                "file_size": file_size
            })
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error analyzing file {file_path}: {e}")
            return {
                "success": False,
                "message": f"Analysis failed: {str(e)}",
                "file_path": file_path
            }
    
    def add_comments_to_file(self, file_path: str) -> Dict[str, Any]:
        """
        Add comments to a source code file.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Dictionary with modification results
        """
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Get file info
            file_extension = Path(file_path).suffix.lower()
            language = self.supported_extensions.get(file_extension, 'unknown')
            filename = os.path.basename(file_path)
            
            if language == 'unknown':
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_extension}"
                }
            
            # Generate comment addition prompt
            prompt = self.code_modifier_prompts.get_comment_generation_prompt(
                language, filename, original_content
            )
            
            response = self.llm.invoke(prompt)
            modified_content = response.content.strip()
            
            # Validate that the modified content is actually different
            if modified_content == original_content:
                return {
                    "success": False,
                    "message": "No comments were added to the file"
                }
            
            # Create backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # Calculate metrics
            original_lines = len(original_content.splitlines())
            modified_lines = len(modified_content.splitlines())
            lines_added = modified_lines - original_lines
            
            return {
                "success": True,
                "message": f"Added comments to {filename}",
                "file_path": file_path,
                "backup_path": backup_path,
                "original_lines": original_lines,
                "modified_lines": modified_lines,
                "lines_added": lines_added
            }
            
        except Exception as e:
            print(f"⚠️ Error adding comments to {file_path}: {e}")
            return {
                "success": False,
                "message": f"Failed to add comments: {str(e)}",
                "file_path": file_path
            }
    
    def rename_variables_in_file(self, file_path: str) -> Dict[str, Any]:
        """
        Rename variables in a source code file to be more descriptive.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Dictionary with modification results
        """
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Get file info
            file_extension = Path(file_path).suffix.lower()
            language = self.supported_extensions.get(file_extension, 'unknown')
            filename = os.path.basename(file_path)
            
            if language == 'unknown':
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_extension}"
                }
            
            # Generate variable renaming prompt
            prompt = self.code_modifier_prompts.get_variable_rename_prompt(
                language, filename, original_content
            )
            
            response = self.llm.invoke(prompt)
            modified_content = response.content.strip()
            
            # Validate that the modified content is actually different
            if modified_content == original_content:
                return {
                    "success": False,
                    "message": "No variables were renamed in the file"
                }
            
            # Create backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # Calculate changes
            changes_detected = self._analyze_variable_changes(original_content, modified_content)
            
            return {
                "success": True,
                "message": f"Renamed variables in {filename}",
                "file_path": file_path,
                "backup_path": backup_path,
                "variables_changed": changes_detected
            }
            
        except Exception as e:
            print(f"⚠️ Error renaming variables in {file_path}: {e}")
            return {
                "success": False,
                "message": f"Failed to rename variables: {str(e)}",
                "file_path": file_path
            }
    
    def add_documentation_to_file(self, file_path: str) -> Dict[str, Any]:
        """
        Add documentation/docstrings to functions in a source code file.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Dictionary with modification results
        """
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Get file info
            file_extension = Path(file_path).suffix.lower()
            language = self.supported_extensions.get(file_extension, 'unknown')
            filename = os.path.basename(file_path)
            
            if language == 'unknown':
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_extension}"
                }
            
            # Generate documentation prompt
            prompt = self.code_modifier_prompts.get_function_documentation_prompt(
                language, filename, original_content
            )
            
            response = self.llm.invoke(prompt)
            modified_content = response.content.strip()
            
            # Validate that the modified content is actually different
            if modified_content == original_content:
                return {
                    "success": False,
                    "message": "No documentation was added to the file"
                }
            
            # Create backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # Calculate metrics
            original_lines = len(original_content.splitlines())
            modified_lines = len(modified_content.splitlines())
            lines_added = modified_lines - original_lines
            
            return {
                "success": True,
                "message": f"Added documentation to {filename}",
                "file_path": file_path,
                "backup_path": backup_path,
                "original_lines": original_lines,
                "modified_lines": modified_lines,
                "lines_added": lines_added
            }
            
        except Exception as e:
            print(f"⚠️ Error adding documentation to {file_path}: {e}")
            return {
                "success": False,
                "message": f"Failed to add documentation: {str(e)}",
                "file_path": file_path
            }
    
    def modify_project_files(self, project_path: str, modifications: List[str]) -> Dict[str, Any]:
        """
        Apply modifications to all applicable files in a project.
        
        Args:
            project_path: Path to the project directory
            modifications: List of modification types ('comments', 'variables', 'documentation')
            
        Returns:
            Dictionary with overall modification results
        """
        try:
            # Import status tracker here to avoid circular imports
            from backend.app import status_tracker
            
            status_tracker.add_output_line(f"🔍 Scanning project for code files...", "code")
            
            # Find all code files in the project
            code_files = self._find_code_files(project_path)
            
            if not code_files:
                status_tracker.add_output_line("❌ No code files found in project", "code")
                return {
                    "success": False,
                    "message": "No code files found in project"
                }
            
            status_tracker.add_output_line(f"📁 Found {len(code_files)} code files to process", "code")
            
            results = {
                "success": True,
                "message": f"Modified {len(code_files)} files",
                "files_processed": len(code_files),
                "files_modified": 0,
                "files_failed": 0,
                "modifications_applied": [],
                "file_results": []
            }
            
            for i, file_path in enumerate(code_files):
                file_name = os.path.basename(file_path)
                status_tracker.add_output_line(f"🔧 Processing file {i+1}/{len(code_files)}: {file_name}", "code")
                
                file_results = {"file_path": file_path, "modifications": []}
                file_modified = False
                
                try:
                    # Apply requested modifications
                    if 'comments' in modifications:
                        status_tracker.add_output_line(f"  💬 Adding comments to {file_name}...", "code")
                        comment_result = self.add_comments_to_file(file_path)
                        file_results["modifications"].append(comment_result)
                        if comment_result["success"]:
                            results["modifications_applied"].append(f"Added comments to {file_name}")
                            file_modified = True
                            status_tracker.add_output_line(f"  ✅ Comments added to {file_name}", "code")
                        else:
                            status_tracker.add_output_line(f"  ⚠️ Failed to add comments to {file_name}: {comment_result.get('message', 'Unknown error')}", "code")
                    
                    if 'variables' in modifications:
                        status_tracker.add_output_line(f"  🔤 Renaming variables in {file_name}...", "code")
                        variable_result = self.rename_variables_in_file(file_path)
                        file_results["modifications"].append(variable_result)
                        if variable_result["success"]:
                            results["modifications_applied"].append(f"Renamed variables in {file_name}")
                            file_modified = True
                            status_tracker.add_output_line(f"  ✅ Variables renamed in {file_name}", "code")
                        else:
                            status_tracker.add_output_line(f"  ⚠️ Failed to rename variables in {file_name}: {variable_result.get('message', 'Unknown error')}", "code")
                    
                    if 'documentation' in modifications:
                        status_tracker.add_output_line(f"  📝 Adding documentation to {file_name}...", "code")
                        doc_result = self.add_documentation_to_file(file_path)
                        file_results["modifications"].append(doc_result)
                        if doc_result["success"]:
                            results["modifications_applied"].append(f"Added documentation to {file_name}")
                            file_modified = True
                            status_tracker.add_output_line(f"  ✅ Documentation added to {file_name}", "code")
                        else:
                            status_tracker.add_output_line(f"  ⚠️ Failed to add documentation to {file_name}: {doc_result.get('message', 'Unknown error')}", "code")
                    
                    if file_modified:
                        results["files_modified"] += 1
                    
                    results["file_results"].append(file_results)
                    
                except Exception as e:
                    status_tracker.add_output_line(f"  ❌ Error processing {file_name}: {str(e)}", "code")
                    results["files_failed"] += 1
                    file_results["error"] = str(e)
                    results["file_results"].append(file_results)
            
            # Summary
            status_tracker.add_output_line(f"📊 Code modification summary:", "code")
            status_tracker.add_output_line(f"  • Files processed: {results['files_processed']}", "code")
            status_tracker.add_output_line(f"  • Files modified: {results['files_modified']}", "code")
            status_tracker.add_output_line(f"  • Files failed: {results['files_failed']}", "code")
            status_tracker.add_output_line(f"  • Modifications applied: {len(results['modifications_applied'])}", "code")
            
            if results['modifications_applied']:
                status_tracker.add_output_line("✅ Code modification completed successfully!", "code")
            else:
                status_tracker.add_output_line("⚠️ No modifications were applied", "code")
            
            return results
            
        except Exception as e:
            status_tracker.add_output_line(f"❌ Error in project modification: {str(e)}", "code")
            return {
                "success": False,
                "message": f"Error modifying project: {str(e)}",
                "files_processed": 0,
                "files_modified": 0,
                "files_failed": 0
            }
    
    def _find_code_files(self, project_path: str) -> List[str]:
        """Find all code files in a project directory."""
        code_files = []
        
        # Skip certain directories
        skip_dirs = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'node_modules', '.venv', 'venv', 'env', '.env',
            'dist', 'build', '.next', '.nuxt', 'coverage',
            '.idea', '.vscode', 'target', 'bin', 'obj'
        }
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = Path(file).suffix.lower()
                
                if file_extension in self.supported_extensions:
                    code_files.append(file_path)
        
        return code_files
    
    def _analyze_variable_changes(self, original_content: str, modified_content: str) -> int:
        """Analyze how many variables were changed."""
        try:
            # Simple heuristic: count lines that changed
            original_lines = set(original_content.splitlines())
            modified_lines = set(modified_content.splitlines())
            
            changes = len(original_lines.symmetric_difference(modified_lines))
            return changes // 2  # Approximate number of variable changes
            
        except Exception:
            return 0
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code modification tasks.
        
        Args:
            task_data: Dictionary containing task parameters
            
        Returns:
            Dictionary with execution results
        """
        task_type = task_data.get("task_type")
        
        if task_type == "analyze_file":
            return self.analyze_file(task_data.get("file_path", ""))
        
        elif task_type == "add_comments":
            return self.add_comments_to_file(task_data.get("file_path", ""))
        
        elif task_type == "rename_variables":
            return self.rename_variables_in_file(task_data.get("file_path", ""))
        
        elif task_type == "add_documentation":
            return self.add_documentation_to_file(task_data.get("file_path", ""))
        
        elif task_type == "modify_project":
            return self.modify_project_files(
                task_data.get("project_path", ""),
                task_data.get("modifications", ["comments"])
            )
        
        else:
            return {
                "success": False,
                "message": f"Unknown task type: {task_type}"
            } 