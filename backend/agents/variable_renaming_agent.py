"""
Variable Renaming Agent for intelligently renaming variables in source code.
"""

import json
import os
import asyncio
import concurrent.futures
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from core.base_agent import BaseAgent
from prompts.variable_renaming_prompts import VariableRenamingPrompts
from core.config import Config


class VariableRenamingAgent(BaseAgent):
    """
    Agent responsible for intelligently renaming variables in source code using pure LLM.
    Only renames variables - does NOT modify code logic.
    """
    
    def __init__(self):
        super().__init__("VariableRenamingAgent")
        self.variable_prompts = VariableRenamingPrompts()
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
            
            # Skip very small files
            if len(original_content.strip()) < 50:
                return {
                    "success": False,
                    "message": "File too small for variable renaming"
                }
            
            # Generate variable renaming prompt
            prompt = self.variable_prompts.get_variable_rename_prompt(
                language, filename, original_content
            )
            
            response = self.llm.invoke(prompt)
            
            try:
                # Try to parse as JSON first for structured response
                rename_data = json.loads(response)
                if "modified_code" in rename_data:
                    modified_content = rename_data["modified_code"]
                    variable_changes = rename_data.get("changes", [])
                else:
                    modified_content = response.strip()
                    variable_changes = []
            except json.JSONDecodeError:
                # Fallback to plain text response
                modified_content = response.strip()
                variable_changes = []
            
            # Validate that the modified content is actually different
            if modified_content == original_content:
                return {
                    "success": False,
                    "message": "No variables were renamed in the file"
                }
            
            # Verify the code logic hasn't changed (basic validation)
            if not self._validate_code_integrity(original_content, modified_content, language):
                return {
                    "success": False,
                    "message": "Code logic validation failed - changes rejected"
                }
            
            # Create backup
            backup_path = file_path + '.var_backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # Calculate metrics
            original_lines = len(original_content.splitlines())
            modified_lines = len(modified_content.splitlines())
            
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            status_tracker.add_output_line(f"🔤 Renamed variables in {filename} ({len(variable_changes)} changes)", "code")
            
            return {
                "success": True,
                "message": f"Renamed variables in {filename}",
                "file_path": file_path,
                "backup_path": backup_path,
                "original_lines": original_lines,
                "modified_lines": modified_lines,
                "variable_changes": variable_changes,
                "changes_count": len(variable_changes)
            }
            
        except Exception as e:
            print(f"⚠️ Error renaming variables in {file_path}: {e}")
            return {
                "success": False,
                "message": f"Failed to rename variables: {str(e)}",
                "file_path": file_path
            }
    
    def _validate_code_integrity(self, original: str, modified: str, language: str) -> bool:
        """
        Basic validation to ensure code logic hasn't changed.
        
        Args:
            original: Original code content
            modified: Modified code content  
            language: Programming language
            
        Returns:
            True if code integrity is maintained
        """
        try:
            # Basic checks
            if len(modified) < len(original) * 0.8:  # Too much content removed
                return False
            
            if len(modified) > len(original) * 1.3:  # Too much content added
                return False
            
            # Language-specific validation
            if language == 'python':
                # Check import statements are preserved
                orig_imports = [line.strip() for line in original.split('\n') if line.strip().startswith(('import ', 'from '))]
                mod_imports = [line.strip() for line in modified.split('\n') if line.strip().startswith(('import ', 'from '))]
                if len(orig_imports) != len(mod_imports):
                    return False
                
                # Check function/class definitions are preserved
                orig_defs = len([line for line in original.split('\n') if line.strip().startswith(('def ', 'class '))])
                mod_defs = len([line for line in modified.split('\n') if line.strip().startswith(('def ', 'class '))])
                if orig_defs != mod_defs:
                    return False
            
            elif language in ['javascript', 'typescript']:
                # Check function declarations are preserved
                import re
                orig_funcs = len(re.findall(r'function\s+\w+\s*\(', original))
                mod_funcs = len(re.findall(r'function\s+\w+\s*\(', modified))
                if orig_funcs != mod_funcs:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _find_code_files(self, project_path: str) -> List[str]:
        """
        Find all supported code files in the project directory.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of code file paths
        """
        code_files = []
        
        # Directories to skip
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.next', 'dist', 'build', 
                    '.vscode', '.idea', 'venv', '.env', 'env', '.pytest_cache'}
        
        for root, dirs, files in os.walk(project_path):
            # Remove skipped directories from dirs to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                # Only process supported file types
                if file_ext in self.supported_extensions:
                    code_files.append(file_path)
        
        return code_files
    
    async def process_files_batch(self, files: List[str]) -> List[Dict[str, Any]]:
        """
        Process a batch of files in parallel.
        
        Args:
            files: List of file paths to process
            
        Returns:
            List of processing results
        """
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            tasks = [
                loop.run_in_executor(executor, self.rename_variables_in_file, file_path)
                for file_path in files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to error results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "message": f"Error processing file: {str(result)}",
                        "file_path": files[i]
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
    
    async def rename_variables_in_project(self, project_path: str) -> Dict[str, Any]:
        """
        Rename variables in all applicable files in a project using parallel processing.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with overall renaming results
        """
        try:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
            status_tracker.add_output_line(f"🔍 Scanning project for code files to rename variables...", "code")
            
            # Find all code files in the project
            code_files = self._find_code_files(project_path)
            
            if not code_files:
                status_tracker.add_output_line("❌ No code files found for variable renaming", "code")
                return {
                    "success": False,
                    "message": "No code files found for variable renaming"
                }
            
            status_tracker.add_output_line(f"📁 Found {len(code_files)} code files for variable renaming", "code")
            
            # Process files in batches for better performance
            batch_size = 8  # Process 8 files at a time
            all_results = []
            
            for i in range(0, len(code_files), batch_size):
                batch = code_files[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(code_files) + batch_size - 1) // batch_size
                
                status_tracker.add_output_line(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} files)...", "code")
                
                batch_results = await self.process_files_batch(batch)
                all_results.extend(batch_results)
                
                # Log progress
                successful = sum(1 for r in batch_results if r.get("success", False))
                status_tracker.add_output_line(f"✅ Batch {batch_num} completed: {successful}/{len(batch)} files processed successfully", "code")
            
            # Calculate overall results
            files_modified = sum(1 for r in all_results if r.get("success", False))
            files_failed = len(all_results) - files_modified
            total_changes = sum(r.get("changes_count", 0) for r in all_results if r.get("success", False))
            
            status_tracker.add_output_line(f"🎯 Variable renaming completed: {files_modified} files modified, {total_changes} total variable changes", "code")
            
            return {
                "success": True,
                "message": f"Renamed variables in {files_modified} files ({total_changes} total changes)",
                "files_processed": len(code_files),
                "files_modified": files_modified,
                "files_failed": files_failed,
                "total_variable_changes": total_changes,
                "file_results": all_results
            }
            
        except Exception as e:
            print(f"⚠️ Error in variable renaming project: {e}")
            return {
                "success": False,
                "message": f"Variable renaming failed: {str(e)}"
            }
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute variable renaming tasks.
        
        Args:
            task_data: Dictionary containing task parameters
            
        Returns:
            Dictionary with execution results
        """
        task_type = task_data.get("task_type")
        
        if task_type == "rename_file":
            return self.rename_variables_in_file(task_data.get("file_path", ""))
        
        elif task_type == "rename_project":
            # Use synchronous file-by-file processing
            return self.rename_variables_in_project_sync(task_data.get("project_path", ""))
        
        else:
            return {
                "success": False,
                "message": f"Unknown task type: {task_type}"
            }
    
    def rename_variables_in_project_sync(self, project_path: str) -> Dict[str, Any]:
        """
        Rename variables in all applicable files in a project using synchronous processing.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with overall renaming results
        """
        try:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
            status_tracker.add_output_line(f"🔍 Scanning project for code files to rename variables...", "code")
            
            # Find all code files in the project
            code_files = self._find_code_files(project_path)
            
            if not code_files:
                status_tracker.add_output_line("❌ No code files found for variable renaming", "code")
                return {
                    "success": False,
                    "message": "No code files found for variable renaming"
                }
            
            status_tracker.add_output_line(f"📁 Found {len(code_files)} code files for variable renaming", "code")
            
            # Process files one by one with detailed logging
            files_modified = 0
            files_failed = 0
            total_changes = 0
            
            for i, file_path in enumerate(code_files):
                file_name = os.path.basename(file_path)
                status_tracker.add_output_line(f"🔤 Processing file {i+1}/{len(code_files)}: {file_name}", "code")
                
                try:
                    result = self.rename_variables_in_file(file_path)
                    
                    if result.get("success", False):
                        files_modified += 1
                        changes_count = result.get("changes_count", 0)
                        total_changes += changes_count
                        status_tracker.add_output_line(f"  ✅ {file_name}: Renamed {changes_count} variables", "code")
                    else:
                        files_failed += 1
                        error_msg = result.get("message", "Unknown error")
                        status_tracker.add_output_line(f"  ⚠️ {file_name}: {error_msg}", "code")
                        
                except Exception as e:
                    files_failed += 1
                    status_tracker.add_output_line(f"  ❌ {file_name}: Error - {str(e)}", "code")
            
            status_tracker.add_output_line(f"🔤 Variable renaming summary: {files_modified} files modified, {files_failed} failed, {total_changes} total variable changes", "code")
            
            return {
                "success": files_modified > 0,
                "message": f"Renamed variables in {files_modified} files ({total_changes} total changes)",
                "files_processed": len(code_files),
                "files_modified": files_modified,
                "files_failed": files_failed,
                "total_variable_changes": total_changes
            }
            
        except Exception as e:
            print(f"⚠️ Error in variable renaming project: {e}")
            return {
                "success": False,
                "message": f"Variable renaming failed: {str(e)}"
            } 