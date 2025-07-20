"""
Git Agent for handling git operations.
"""

import json
import os
import subprocess
import threading
import time
from typing import List, Dict, Optional, Any, Generator, Callable
from datetime import datetime
from urllib.parse import urlparse
import signal
import asyncio
import queue

from core.base_agent import BaseAgent
from prompts.git_prompts import GitPrompts
from core.config import Config


class GitAgent(BaseAgent):
    """
    Agent responsible for git operations and repository management.
    """
    
    def __init__(self):
        super().__init__("GitAgent")
        self.git_prompts = GitPrompts()
        self.current_operation = None
        self.output_queue = queue.Queue()
        self.operation_cancelled = False
    
    def validate_repository_url(self, url: str) -> Dict[str, Any]:
        """
        Validate and analyze a repository URL.
        
        Args:
            url: Repository URL to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            if not url or not url.strip():
                return {
                    "valid": False,
                    "message": "Repository URL cannot be empty"
                }
            
            # Parse URL
            parsed = urlparse(url)
            
            # Check for common git hosting services
            valid_hosts = {
                'github.com', 'gitlab.com', 'bitbucket.org',
                'git.sr.ht', 'codeberg.org', 'gitlab.freedesktop.org'
            }
            
            # Check if it's a valid git URL
            if parsed.scheme in ['http', 'https']:
                if parsed.hostname not in valid_hosts and not parsed.hostname.endswith('.git'):
                    return {
                        "valid": False,
                        "message": f"Unsupported hosting service: {parsed.hostname}"
                    }
            elif parsed.scheme == 'git' or '@' in url:
                # SSH format
                if not any(host in url for host in valid_hosts):
                    return {
                        "valid": False,
                        "message": "SSH URL format not recognized"
                    }
            else:
                return {
                    "valid": False,
                    "message": "Invalid URL format"
                }
            
            # Check if repository exists and is accessible
            access_check = self._check_repository_access(url)
            
            return {
                "valid": True,
                "url": url,
                "hostname": parsed.hostname,
                "scheme": parsed.scheme,
                "accessible": access_check["accessible"],
                "access_method": access_check["method"],
                "message": "Repository URL is valid"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"URL validation failed: {str(e)}"
            }
    
    def clone_to_new_repository(self, project_path: str, target_url: str, 
                              user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clone the project to a new empty repository.
        
        Args:
            project_path: Path to the project directory
            target_url: Target repository URL (should be empty)
            user_preferences: User preferences including git credentials
            
        Returns:
            Dictionary with cloning results
        """
        try:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
            # Validate target URL
            validation = self.validate_repository_url(target_url)
            if not validation["valid"]:
                return {
                    "success": False,
                    "message": f"Invalid target URL: {validation['message']}"
                }
            
            status_tracker.add_output_line(f"🔗 Cloning to target repository: {target_url}", "git")
            
            # Create a temporary directory for the new repository
            import tempfile
            import shutil
            
            temp_dir = tempfile.mkdtemp(prefix="chameleon_clone_")
            new_repo_path = os.path.join(temp_dir, "cloned_repo")
            
            try:
                # Step 1: Copy the entire project to temp directory
                status_tracker.add_output_line("📂 Copying project files...", "git")
                shutil.copytree(project_path, new_repo_path, symlinks=True)
                
                # Step 2: Initialize new git repository
                status_tracker.add_output_line("🔧 Initializing new git repository...", "git")
                subprocess.run(['git', 'init'], cwd=new_repo_path, check=True, capture_output=True)
                
                # Step 3: Remove existing git history
                git_dir = os.path.join(new_repo_path, '.git')
                if os.path.exists(git_dir):
                    shutil.rmtree(git_dir)
                    subprocess.run(['git', 'init'], cwd=new_repo_path, check=True, capture_output=True)
                
                # Step 4: Set up git config
                subprocess.run(['git', 'config', 'user.name', user_preferences.get('git_username', 'Unknown')], 
                             cwd=new_repo_path, check=True, capture_output=True)
                subprocess.run(['git', 'config', 'user.email', user_preferences.get('git_email', 'unknown@example.com')], 
                             cwd=new_repo_path, check=True, capture_output=True)
                
                # Step 5: Add remote origin
                status_tracker.add_output_line(f"🌐 Adding remote origin: {target_url}", "git")
                subprocess.run(['git', 'remote', 'add', 'origin', target_url], 
                             cwd=new_repo_path, check=True, capture_output=True)
                
                # Step 6: Add all files and create initial commit
                status_tracker.add_output_line("📝 Creating initial commit...", "git")
                subprocess.run(['git', 'add', '.'], cwd=new_repo_path, check=True, capture_output=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                             cwd=new_repo_path, check=True, capture_output=True)
                
                # Step 7: Push to remote repository
                status_tracker.add_output_line("⬆️ Pushing to remote repository...", "git")
                result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                                      cwd=new_repo_path, check=True, 
                                      capture_output=True, text=True)
                
                # Step 8: Replace original project with cloned version
                status_tracker.add_output_line("🔄 Updating local project directory...", "git")
                
                # Backup original
                backup_path = f"{project_path}_backup_{int(time.time())}"
                shutil.move(project_path, backup_path)
                
                # Move new repo to original location
                shutil.move(new_repo_path, project_path)
                
                status_tracker.add_output_line(f"✅ Successfully cloned to {target_url}", "git")
                status_tracker.add_output_line(f"📁 Original backed up to: {backup_path}", "git")
                
                return {
                    "success": True,
                    "message": f"Successfully cloned project to {target_url}",
                    "new_remote_url": target_url,
                    "backup_path": backup_path,
                    "cloned_path": project_path
                }
                
            finally:
                # Cleanup temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {e.stderr.decode() if e.stderr else str(e)}"
            status_tracker.add_output_line(f"❌ {error_msg}", "git")
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Repository cloning failed: {str(e)}"
            status_tracker.add_output_line(f"❌ {error_msg}", "git")
            return {
                "success": False,
                "message": error_msg
            }

    def setup_repository_destination(self, project_path: str, original_url: str, 
                                   target_url: str, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set up a new repository destination for a project.
        
        Args:
            project_path: Path to the project directory
            original_url: Original repository URL
            target_url: Target repository URL
            user_preferences: User preferences for setup
            
        Returns:
            Dictionary with setup results
        """
        try:
            # If target_url is provided, clone to new repository instead
            if target_url and target_url.strip():
                return self.clone_to_new_repository(project_path, target_url, user_preferences)
            
            # Validate target URL
            validation = self.validate_repository_url(target_url)
            if not validation["valid"]:
                return {
                    "success": False,
                    "message": f"Invalid target URL: {validation['message']}"
                }
            
            # Generate setup instructions using AI
            prompt = self.git_prompts.get_repository_setup_prompt(
                original_url, target_url, os.path.basename(project_path), user_preferences
            )
            
            response = self.llm.invoke(prompt)
            
            try:
                setup_instructions = json.loads(response)
            except json.JSONDecodeError:
                # Fallback to manual setup
                setup_instructions = self._generate_fallback_setup(original_url, target_url)
            
            # Execute setup commands
            if setup_instructions.get("url_valid", False):
                execution_results = self._execute_setup_commands(
                    project_path, setup_instructions.get("setup_commands", [])
                )
                
                return {
                    "success": execution_results["success"],
                    "message": "Repository destination configured successfully" if execution_results["success"] else "Setup failed",
                    "setup_instructions": setup_instructions,
                    "execution_results": execution_results,
                    "new_remote_url": target_url
                }
            else:
                return {
                    "success": False,
                    "message": "Target repository is not accessible",
                    "setup_instructions": setup_instructions
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Repository setup failed: {str(e)}"
            }
    
    def execute_git_filter_branch(self, project_path: str, filter_options: Dict[str, Any],
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute git filter-branch with real-time progress tracking.
        
        Args:
            project_path: Path to the project directory
            filter_options: Options for git filter-branch
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results
        """
        try:
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "message": "Project path does not exist"
                }
            
            # Get total commit count
            total_commits = self._get_commit_count(project_path)
            if total_commits == 0:
                return {
                    "success": False,
                    "message": "No commits found in repository"
                }
            
            # Prepare filter-branch command
            cmd = self._build_filter_branch_command(filter_options)
            
            # Execute with progress tracking
            start_time = time.time()
            result = self._execute_with_progress(
                cmd, project_path, total_commits, progress_callback
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": result["success"],
                "message": result["message"],
                "commits_processed": result.get("commits_processed", 0),
                "execution_time": execution_time,
                "output": result.get("output", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Git filter-branch failed: {str(e)}"
            }
    
    def stream_git_output(self, project_path: str, command: List[str]) -> Generator[str, None, None]:
        """
        Stream git command output in real-time.
        
        Args:
            project_path: Path to the project directory
            command: Git command to execute
            
        Yields:
            Lines of output from the git command
        """
        try:
            process = subprocess.Popen(
                command,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    yield line.rstrip()
            
            process.wait()
            
            if process.returncode != 0:
                yield f"Command failed with exit code {process.returncode}"
                
        except Exception as e:
            yield f"Error executing command: {str(e)}"
    
    def monitor_file_changes(self, project_path: str, 
                           change_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Monitor file changes in a project directory.
        
        Args:
            project_path: Path to the project directory
            change_callback: Optional callback for file changes
            
        Returns:
            Dictionary with monitoring results
        """
        try:
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "message": "Project path does not exist"
                }
            
            # Get initial file state
            initial_state = self._get_file_state(project_path)
            
            # Start monitoring thread
            monitoring_thread = threading.Thread(
                target=self._monitor_changes,
                args=(project_path, initial_state, change_callback),
                daemon=True
            )
            monitoring_thread.start()
            
            return {
                "success": True,
                "message": "File monitoring started",
                "initial_files": len(initial_state),
                "monitoring_thread": monitoring_thread
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"File monitoring failed: {str(e)}"
            }
    
    def _check_repository_access(self, url: str) -> Dict[str, Any]:
        """Check if a repository is accessible."""
        try:
            # Try to get repository info without cloning
            result = subprocess.run(
                ['git', 'ls-remote', url],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "accessible": True,
                    "method": "https" if url.startswith("https") else "ssh"
                }
            else:
                return {
                    "accessible": False,
                    "method": "unknown",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "accessible": False,
                "method": "timeout",
                "error": "Repository access check timed out"
            }
        except Exception as e:
            return {
                "accessible": False,
                "method": "error",
                "error": str(e)
            }
    
    def _generate_fallback_setup(self, original_url: str, target_url: str) -> Dict[str, Any]:
        """Generate fallback setup instructions."""
        return {
            "url_valid": True,
            "repository_exists": True,
            "access_method": "https",
            "setup_commands": [
                f"git remote remove origin",
                f"git remote add origin {target_url}",
                f"git push -u origin main"
            ],
            "authentication_required": True,
            "configuration_steps": [
                "Ensure you have write access to the target repository",
                "Configure git credentials if needed"
            ],
            "potential_issues": [
                "Target repository may not exist",
                "Authentication may be required"
            ],
            "success_probability": 7
        }
    
    def _execute_setup_commands(self, project_path: str, commands: List[str]) -> Dict[str, Any]:
        """Execute repository setup commands."""
        try:
            results = []
            
            for command in commands:
                try:
                    # Split command into parts
                    cmd_parts = command.split()
                    
                    result = subprocess.run(
                        cmd_parts,
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    results.append({
                        "command": command,
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr
                    })
                    
                    if result.returncode != 0:
                        return {
                            "success": False,
                            "message": f"Command failed: {command}",
                            "results": results
                        }
                        
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "message": f"Command timed out: {command}",
                        "results": results
                    }
            
            return {
                "success": True,
                "message": "All setup commands executed successfully",
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Setup execution failed: {str(e)}",
                "results": []
            }
    
    def _get_commit_count(self, project_path: str) -> int:
        """Get the number of commits in a repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-list', '--all', '--count'],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0
    
    def _build_filter_branch_command(self, filter_options: Dict[str, Any]) -> List[str]:
        """Build git filter-branch command from options."""
        cmd = ['git', 'filter-branch', '-f']
        
        if filter_options.get("env_filter"):
            cmd.extend(['--env-filter', filter_options["env_filter"]])
        
        if filter_options.get("msg_filter"):
            cmd.extend(['--msg-filter', filter_options["msg_filter"]])
        
        if filter_options.get("commit_filter"):
            cmd.extend(['--commit-filter', filter_options["commit_filter"]])
        
        # Add branch or commit range
        cmd.append(filter_options.get("branch", "HEAD"))
        
        return cmd
    
    def _execute_with_progress(self, command: List[str], cwd: str, total_commits: int,
                             progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Execute a command with progress tracking."""
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            output_lines = []
            commits_processed = 0
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line.rstrip())
                    
                    # Update progress if we can parse commit info
                    if "Rewrite" in line or "commit" in line.lower():
                        commits_processed += 1
                        if progress_callback:
                            progress = (commits_processed / total_commits) * 100
                            progress_callback(progress, line.rstrip())
            
            process.wait()
            
            return {
                "success": process.returncode == 0,
                "message": "Command completed successfully" if process.returncode == 0 else "Command failed",
                "commits_processed": commits_processed,
                "output": output_lines
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Command execution failed: {str(e)}",
                "commits_processed": 0,
                "output": []
            }
    
    def _get_file_state(self, project_path: str) -> Dict[str, float]:
        """Get current state of files in project."""
        file_state = {}
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        file_state[file_path] = stat.st_mtime
                    except OSError:
                        continue
        
        except Exception as e:
            print(f"⚠️ Error getting file state: {e}")
        
        return file_state
    
    def _monitor_changes(self, project_path: str, initial_state: Dict[str, float],
                        change_callback: Optional[Callable] = None):
        """Monitor file changes in a separate thread."""
        while not self.operation_cancelled:
            try:
                current_state = self._get_file_state(project_path)
                
                # Check for changes
                changed_files = []
                
                for file_path, mtime in current_state.items():
                    if file_path not in initial_state or initial_state[file_path] != mtime:
                        changed_files.append(file_path)
                
                # Check for deleted files
                for file_path in initial_state:
                    if file_path not in current_state:
                        changed_files.append(f"DELETED: {file_path}")
                
                if changed_files and change_callback:
                    change_callback(changed_files)
                
                initial_state = current_state
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"⚠️ Error monitoring changes: {e}")
                break
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute git-related tasks.
        
        Args:
            task_data: Dictionary containing task parameters
            
        Returns:
            Dictionary with execution results
        """
        task_type = task_data.get("task_type")
        
        if task_type == "validate_url":
            return self.validate_repository_url(task_data.get("url", ""))
        
        elif task_type == "setup_repository":
            return self.setup_repository_destination(
                task_data.get("project_path", ""),
                task_data.get("original_url", ""),
                task_data.get("target_url", ""),
                task_data.get("user_preferences", {})
            )
        
        elif task_type == "filter_branch":
            return self.execute_git_filter_branch(
                task_data.get("project_path", ""),
                task_data.get("filter_options", {}),
                task_data.get("progress_callback")
            )
        
        elif task_type == "monitor_changes":
            return self.monitor_file_changes(
                task_data.get("project_path", ""),
                task_data.get("change_callback")
            )
        
        else:
            return {
                "success": False,
                "message": f"Unknown task type: {task_type}"
            }
    
    def cancel_operation(self):
        """Cancel the current git operation."""
        self.operation_cancelled = True
        if self.current_operation:
            try:
                self.current_operation.terminate()
            except:
                pass 