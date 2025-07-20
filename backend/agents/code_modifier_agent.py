"""
Code Modifier Agent for adding intelligent comments to source code.
"""

import json
import os
import asyncio
import concurrent.futures
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from core.base_agent import BaseAgent
from prompts.code_modifier_prompts import CodeModifierPrompts
from core.config import Config


class CodeModifierAgent(BaseAgent):
    """
    Agent responsible for adding intelligent comments to source code.
    ONLY adds comments - does NOT modify code logic or rename variables.
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
            analysis = json.loads(response)
            
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
            
            # Skip very small files
            if len(original_content.strip()) < 30:
                return {
                    "success": False,
                    "message": "File too small for comment addition"
                }
            
            # Generate comment addition prompt
            prompt = self.code_modifier_prompts.get_comment_generation_prompt(
                language, filename, original_content
            )
            
            response = self.llm.invoke(prompt)
            modified_content = response.strip()
            
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
            
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            status_tracker.add_output_line(f"💬 Added {lines_added} comment lines to {filename}", "code")
            
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
    
    async def process_files_batch(self, files: List[str]) -> List[Dict[str, Any]]:
        """
        Process a batch of files in parallel for comment addition.
        
        Args:
            files: List of file paths to process
            
        Returns:
            List of processing results
        """
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            tasks = [
                loop.run_in_executor(executor, self.add_comments_to_file, file_path)
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
    
    async def add_comments_to_project(self, project_path: str) -> Dict[str, Any]:
        """
        Add comments to all applicable files in a project using parallel processing.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with overall commenting results
        """
        try:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
            status_tracker.add_output_line(f"🔍 Scanning project for code files to add comments...", "code")
            
            # Find all code files in the project
            code_files = self._find_code_files(project_path)
            
            if not code_files:
                status_tracker.add_output_line("❌ No code files found for commenting", "code")
                return {
                    "success": False,
                    "message": "No code files found for commenting"
                }
            
            status_tracker.add_output_line(f"📁 Found {len(code_files)} code files for commenting", "code")
            
            # Process files in batches for better performance
            batch_size = 6  # Process 6 files at a time for comments (slower than variable renaming)
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
            total_lines_added = sum(r.get("lines_added", 0) for r in all_results if r.get("success", False))
            
            status_tracker.add_output_line(f"💬 Comment addition completed: {files_modified} files modified, {total_lines_added} total comment lines added", "code")
            
            return {
                "success": True,
                "message": f"Added comments to {files_modified} files ({total_lines_added} lines added)",
                "files_processed": len(code_files),
                "files_modified": files_modified,
                "files_failed": files_failed,
                "total_lines_added": total_lines_added,
                "file_results": all_results
            }
            
        except Exception as e:
            print(f"⚠️ Error in comment addition project: {e}")
            return {
                "success": False,
                "message": f"Comment addition failed: {str(e)}"
            }
    
    def add_comments_to_project_sync(self, project_path: str) -> Dict[str, Any]:
        """
        Add comments to all applicable files in a project using synchronous processing.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with overall commenting results
        """
        try:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
            status_tracker.add_output_line(f"🔍 Scanning project for code files to add comments...", "code")
            
            # Find all code files in the project
            code_files = self._find_code_files(project_path)
            
            if not code_files:
                status_tracker.add_output_line("❌ No code files found for commenting", "code")
                return {
                    "success": False,
                    "message": "No code files found for commenting"
                }
            
            status_tracker.add_output_line(f"📁 Found {len(code_files)} code files for commenting", "code")
            
            # Process files one by one with detailed logging
            files_modified = 0
            files_failed = 0
            total_lines_added = 0
            
            for i, file_path in enumerate(code_files):
                file_name = os.path.basename(file_path)
                status_tracker.add_output_line(f"💬 Processing file {i+1}/{len(code_files)}: {file_name}", "code")
                
                try:
                    result = self.add_comments_to_file(file_path)
                    
                    if result.get("success", False):
                        files_modified += 1
                        lines_added = result.get("lines_added", 0)
                        total_lines_added += lines_added
                        status_tracker.add_output_line(f"  ✅ {file_name}: Added {lines_added} comment lines", "code")
                    else:
                        files_failed += 1
                        error_msg = result.get("message", "Unknown error")
                        status_tracker.add_output_line(f"  ⚠️ {file_name}: {error_msg}", "code")
                        
                except Exception as e:
                    files_failed += 1
                    status_tracker.add_output_line(f"  ❌ {file_name}: Error - {str(e)}", "code")
            
            status_tracker.add_output_line(f"💬 Comment addition summary: {files_modified} files modified, {files_failed} failed, {total_lines_added} total lines added", "code")
            
            return {
                "success": files_modified > 0,
                "message": f"Added comments to {files_modified} files ({total_lines_added} lines added)",
                "files_processed": len(code_files),
                "files_modified": files_modified,
                "files_failed": files_failed,
                "total_lines_added": total_lines_added
            }
            
        except Exception as e:
            print(f"⚠️ Error in comment addition project: {e}")
            return {
                "success": False,
                "message": f"Comment addition failed: {str(e)}"
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
            modified_content = response.strip()
            
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
    
    def refactor_file(self, file_path: str) -> Dict[str, Any]:
        """
        Refactor and reorder a source code file to make it better without changing logic.
        
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
            if len(original_content.strip()) < 30:
                return {
                    "success": False,
                    "message": "File too small for refactoring"
                }
            
            # Generate refactoring prompt
            prompt = self.code_modifier_prompts.get_refactor_prompt(
                language, filename, original_content
            )
            
            response = self.llm.invoke(prompt)
            modified_content = response.strip()
            
            # Validate that the modified content is actually different
            if modified_content == original_content:
                return {
                    "success": False,
                    "message": "No refactoring improvements were made to the file"
                }
            
            # Create backup
            backup_path = file_path + '.refactor_backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # Calculate metrics
            original_lines = len(original_content.splitlines())
            modified_lines = len(modified_content.splitlines())
            refactorings_count = 1  # Simple count - could be enhanced to detect specific improvements
            
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            status_tracker.add_output_line(f"🔧 Refactored {filename} with code improvements", "code")
            
            return {
                "success": True,
                "message": f"Refactored {filename}",
                "file_path": file_path,
                "backup_path": backup_path,
                "original_lines": original_lines,
                "modified_lines": modified_lines,
                "refactorings_count": refactorings_count
            }
            
        except Exception as e:
            print(f"⚠️ Error refactoring {file_path}: {e}")
            return {
                "success": False,
                "message": f"Failed to refactor file: {str(e)}",
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
        
        elif task_type == "add_comments_project":
            # Use synchronous file-by-file processing
            return self.add_comments_to_project_sync(task_data.get("project_path", ""))
        
        elif task_type == "add_documentation":
            return self.add_documentation_to_file(task_data.get("file_path", ""))
        
        elif task_type == "refactor_file":
            return self.refactor_file(task_data.get("file_path", ""))
        
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