"""
Commit Agent for generating realistic commit messages and handling commit operations.
"""

import json
import os
import subprocess
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random

from core.base_agent import BaseAgent
from prompts.commit_prompts import CommitPrompts
from core.config import Config


class CommitAgent(BaseAgent):
    """
    Agent responsible for generating realistic commit messages and managing commit operations.
    """
    
    def __init__(self):
        super().__init__("CommitAgent")
        self.commit_prompts = CommitPrompts()
    
    def generate_commit_messages(self, project_name: str, technologies: List[str], 
                               file_changes: str, change_type: str, 
                               hackathon_theme: str = "general") -> List[str]:
        """
        Generate realistic commit messages for a project.
        
        Args:
            project_name: Name of the project
            technologies: List of technologies used
            file_changes: Description of files changed
            change_type: Type of change (feature, fix, docs, etc.)
            hackathon_theme: Theme of the hackathon
            
        Returns:
            List of generated commit messages
        """
        try:
            prompt = self.commit_prompts.get_commit_message_prompt(
                project_name, technologies, file_changes, change_type, hackathon_theme
            )
            
            response = self.llm.invoke(prompt)
            
            # Parse the JSON response
            commit_messages = json.loads(response.content)
            
            if isinstance(commit_messages, list):
                return commit_messages
            else:
                return [response.content]
                
        except Exception as e:
            print(f"⚠️ Error generating commit messages: {e}")
            # Fallback to hardcoded messages
            return self._get_fallback_commit_messages(change_type)
    
    def generate_commit_sequence(self, project_name: str, project_description: str,
                               technologies: List[str], commit_count: int,
                               hackathon_duration: int = 48) -> List[str]:
        """
        Generate a sequence of commit messages for a complete hackathon project.
        
        Args:
            project_name: Name of the project
            project_description: Description of the project
            technologies: List of technologies used
            commit_count: Number of commits to generate
            hackathon_duration: Duration of hackathon in hours
            
        Returns:
            List of commit messages in chronological order
        """
        try:
            prompt = self.commit_prompts.get_commit_sequence_prompt(
                project_name, project_description, technologies, commit_count, hackathon_duration
            )
            
            response = self.llm.invoke(prompt)
            
            # Parse the JSON response
            commit_sequence = json.loads(response.content)
            
            if isinstance(commit_sequence, list):
                return commit_sequence[:commit_count]  # Ensure we don't exceed requested count
            else:
                return [response.content]
                
        except Exception as e:
            print(f"⚠️ Error generating commit sequence: {e}")
            # Fallback to a basic sequence
            return self._get_fallback_commit_sequence(commit_count)
    
    def generate_commit_description(self, commit_title: str, file_changes: str,
                                  project_context: str) -> str:
        """
        Generate a detailed commit description.
        
        Args:
            commit_title: Title of the commit
            file_changes: Description of changed files
            project_context: Context about the project
            
        Returns:
            Detailed commit description
        """
        try:
            prompt = self.commit_prompts.get_commit_description_prompt(
                commit_title, file_changes, project_context
            )
            
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            print(f"⚠️ Error generating commit description: {e}")
            return f"Updated {file_changes} to improve functionality"
    
    def create_hackathon_commit_history(self, project_path: str, project_name: str,
                                      project_description: str, technologies: List[str],
                                      hackathon_start: datetime, hackathon_duration: int,
                                      developer_name: str, developer_email: str) -> Dict[str, Any]:
        """
        Create a complete hackathon commit history for a project.
        
        Args:
            project_path: Path to the project directory
            project_name: Name of the project
            project_description: Description of the project
            technologies: List of technologies used
            hackathon_start: Start time of the hackathon
            hackathon_duration: Duration in hours
            developer_name: Name of the developer
            developer_email: Email of the developer
            
        Returns:
            Dictionary with commit history results
        """
        try:
            # Get current commit count
            original_commits = self._get_commit_count(project_path)
            
            if original_commits == 0:
                return {
                    "success": False,
                    "message": "No commits found in project",
                    "commits_created": 0
                }
            
            # Generate commit sequence
            commit_messages = self.generate_commit_sequence(
                project_name, project_description, technologies, original_commits, hackathon_duration
            )
            
            # Create new commit history
            result = self._rewrite_commit_history(
                project_path, commit_messages, hackathon_start, hackathon_duration,
                developer_name, developer_email
            )
            
            return {
                "success": True,
                "message": f"Created hackathon commit history with {len(commit_messages)} commits",
                "commits_created": len(commit_messages),
                "commit_messages": commit_messages,
                "timeline_start": hackathon_start.isoformat(),
                "timeline_duration": hackathon_duration
            }
            
        except Exception as e:
            print(f"❌ Error creating hackathon commit history: {e}")
            return {
                "success": False,
                "message": f"Failed to create commit history: {str(e)}",
                "commits_created": 0
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
    
    def _rewrite_commit_history(self, project_path: str, commit_messages: List[str],
                               hackathon_start: datetime, hackathon_duration: int,
                               developer_name: str, developer_email: str) -> bool:
        """
        Rewrite the git history with new commit messages and timestamps.
        
        Args:
            project_path: Path to the project
            commit_messages: List of commit messages
            hackathon_start: Start time of hackathon
            hackathon_duration: Duration in hours
            developer_name: Developer name
            developer_email: Developer email
            
        Returns:
            Success status
        """
        try:
            # Import status tracker here to avoid circular imports
            from backend.app import status_tracker
            
            status_tracker.add_output_line("🔄 Getting commit history...", "git")
            
            # Get list of all commits
            result = subprocess.run(
                ['git', 'log', '--format=%H', '--reverse'],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hashes = result.stdout.strip().split('\n')
            status_tracker.add_output_line(f"📊 Found {len(commit_hashes)} commits to rewrite", "git")
            
            # Create time distribution
            time_distribution = self._create_time_distribution(
                len(commit_hashes), hackathon_start, hackathon_duration
            )
            
            status_tracker.add_output_line("⏰ Generated hackathon timeline for commits", "git")
            
            # Use git filter-repo approach (more reliable than filter-branch)
            success = self._rewrite_with_git_commands(
                project_path, commit_hashes, commit_messages, time_distribution,
                developer_name, developer_email
            )
            
            if success:
                status_tracker.add_output_line("✅ Git history rewritten successfully!", "git")
                return True
            else:
                status_tracker.add_output_line("❌ Git history rewriting failed", "git")
                return False
            
        except subprocess.CalledProcessError as e:
            status_tracker.add_output_line(f"❌ Git command failed: {e}", "git")
            return False
        except Exception as e:
            status_tracker.add_output_line(f"❌ Error rewriting commit history: {e}", "git")
            return False
    
    def _rewrite_with_git_commands(self, project_path: str, commit_hashes: List[str],
                                 commit_messages: List[str], time_distribution: List[datetime],
                                 developer_name: str, developer_email: str) -> bool:
        """Rewrite git history using direct git commands."""
        try:
            # Import status tracker here to avoid circular imports
            from backend.app import status_tracker
            
            # Create a backup branch first
            status_tracker.add_output_line("🔄 Creating backup branch...", "git")
            subprocess.run(['git', 'branch', 'backup-original'], cwd=project_path, check=True)
            
            # Configure git user for this repository
            status_tracker.add_output_line(f"👤 Setting git user: {developer_name} <{developer_email}>", "git")
            subprocess.run(['git', 'config', 'user.name', developer_name], cwd=project_path, check=True)
            subprocess.run(['git', 'config', 'user.email', developer_email], cwd=project_path, check=True)
            
            # Use a more reliable approach: reset to first commit and replay with new info
            status_tracker.add_output_line("🔄 Rewriting git history with new author and timestamps...", "git")
            
            # Get first commit
            result = subprocess.run(
                ['git', 'rev-list', '--reverse', 'HEAD'],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            all_commits = result.stdout.strip().split('\n')
            
            if len(all_commits) != len(commit_hashes):
                status_tracker.add_output_line(f"⚠️ Commit count mismatch: {len(all_commits)} vs {len(commit_hashes)}", "git")
                # Adjust arrays to match
                min_len = min(len(all_commits), len(commit_hashes), len(commit_messages), len(time_distribution))
                all_commits = all_commits[:min_len]
                commit_messages = commit_messages[:min_len]
                time_distribution = time_distribution[:min_len]
            
            # Create temporary script for rewriting commits
            script_content = self._create_commit_rewriter_script(
                all_commits, commit_messages, time_distribution, developer_name, developer_email
            )
            
            script_path = os.path.join(project_path, 'commit_rewriter.sh')
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            
            status_tracker.add_output_line("📝 Created commit rewriter script", "git")
            
            # Run the rewriter script
            status_tracker.add_output_line("🔄 Running commit rewriter...", "git")
            process = subprocess.Popen(
                ['bash', script_path],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    status_tracker.add_output_line(line, "git")
            
            process.wait()
            
            if process.returncode != 0:
                status_tracker.add_output_line(f"❌ Commit rewriter failed with exit code {process.returncode}", "git")
                return False
            
            # Clean up
            try:
                os.remove(script_path)
                status_tracker.add_output_line("🧹 Cleaned up temporary files", "git")
            except:
                pass
            
            # Verify the changes
            result = subprocess.run(
                ['git', 'log', '--oneline', '--format=%H %s %an <%ae> %ad', '--date=iso', '-10'],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                status_tracker.add_output_line("📋 Recent commits after rewriting:", "git")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        status_tracker.add_output_line(f"  {line}", "git")
            
            return True
            
        except Exception as e:
            status_tracker.add_output_line(f"❌ Error in git rewriting: {e}", "git")
            return False
    
    def _create_time_distribution(self, commit_count: int, hackathon_start: datetime,
                                hackathon_duration: int) -> List[datetime]:
        """Create realistic time distribution for commits during hackathon."""
        times = []
        hackathon_end = hackathon_start + timedelta(hours=hackathon_duration)
        
        # Start coding around 5 hours after hackathon begins (planning, team formation, etc.)
        coding_start_offset = 5  # hours
        actual_coding_time = hackathon_duration - coding_start_offset
        coding_start = hackathon_start + timedelta(hours=coding_start_offset)
        
        # Create realistic phases of development
        initial_setup = actual_coding_time * 0.20   # First 20% - initial setup and first features
        core_development = actual_coding_time * 0.60   # Next 60% - core development
        final_push = actual_coding_time * 0.20   # Last 20% - final features and polish
        
        phase_commits = [
            max(1, int(commit_count * 0.25)),  # 25% initial setup
            max(1, int(commit_count * 0.60)),  # 60% core development  
            max(1, commit_count - int(commit_count * 0.85))  # 15% final push
        ]
        
        # Generate timestamps for each phase
        
        # Initial setup phase (starts 5 hours after hackathon start)
        for i in range(phase_commits[0]):
            time_offset = random.uniform(0, initial_setup)
            times.append(coding_start + timedelta(hours=time_offset))
        
        # Core development phase
        for i in range(phase_commits[1]):
            time_offset = initial_setup + random.uniform(0, core_development)
            times.append(coding_start + timedelta(hours=time_offset))
        
        # Final push phase
        for i in range(phase_commits[2]):
            time_offset = initial_setup + core_development + random.uniform(0, final_push)
            times.append(coding_start + timedelta(hours=time_offset))
        
        return sorted(times)
    
    def _create_commit_rewriter_script(self, commit_hashes: List[str], commit_messages: List[str],
                                     time_distribution: List[datetime], developer_name: str,
                                     developer_email: str) -> str:
        """Create a script to rewrite commits using git reset and recommit."""
        script_lines = ['#!/bin/bash', 'set -e', '']
        
        script_lines.append('echo "Starting commit rewriting process..."')
        script_lines.append('')
        
        # Create environment variables for git
        script_lines.extend([
            f'export GIT_AUTHOR_NAME="{developer_name}"',
            f'export GIT_AUTHOR_EMAIL="{developer_email}"',
            f'export GIT_COMMITTER_NAME="{developer_name}"',
            f'export GIT_COMMITTER_EMAIL="{developer_email}"',
            ''
        ])
        
        # Get root commit
        script_lines.append('ROOT_COMMIT=$(git rev-list --reverse HEAD | head -1)')
        script_lines.append('echo "Root commit: $ROOT_COMMIT"')
        script_lines.append('')
        
        # Reset to root
        script_lines.append('git reset --hard $ROOT_COMMIT')
        script_lines.append('echo "Reset to root commit"')
        script_lines.append('')
        
        # Process each commit
        for i, (commit_hash, message, timestamp) in enumerate(zip(commit_hashes, commit_messages, time_distribution)):
            timestamp_str = str(int(timestamp.timestamp()))
            escaped_message = message.replace('"', '\\"').replace('`', '\\`')
            
            script_lines.extend([
                f'echo "Processing commit {i+1}/{len(commit_hashes)}: {escaped_message[:50]}..."',
                f'',
                f'# Get the changes from the original commit',
                f'if [ {i} -eq 0 ]; then',
                f'    # First commit - use the files as they are',
                f'    git add -A',
                f'else',
                f'    # Cherry-pick the changes from the next commit',
                f'    NEXT_COMMIT=$(git rev-list --reverse HEAD^..backup-original | sed -n "{i+1}p")',
                f'    if [ -n "$NEXT_COMMIT" ]; then',
                f'        git cherry-pick --no-commit $NEXT_COMMIT || true',
                f'        git add -A',
                f'    fi',
                f'fi',
                f'',
                f'# Create new commit with rewritten info',
                f'export GIT_AUTHOR_DATE="{timestamp_str}"',
                f'export GIT_COMMITTER_DATE="{timestamp_str}"',
                f'',
                f'git commit -m "{escaped_message}" --allow-empty',
                f'echo "Created commit: {escaped_message}"',
                f''
            ])
        
        script_lines.extend([
            'echo "Commit rewriting completed!"',
            'echo "Final commit count: $(git rev-list --count HEAD)"',
            'echo "Author verification:"',
            'git log --oneline --format="%h %s %an <%ae>" -5'
        ])
        
        return '\n'.join(script_lines)
    
    def _get_fallback_commit_messages(self, change_type: str) -> List[str]:
        """Get fallback commit messages when AI generation fails."""
        fallback_messages = {
            "feature": [
                "feat: add new feature implementation",
                "feat: implement core functionality",
                "feat: add user interface components",
                "feat: integrate API endpoints",
                "feat: add data processing logic"
            ],
            "fix": [
                "fix: resolve critical bug",
                "fix: handle edge case scenario",
                "fix: improve error handling",
                "fix: optimize performance",
                "fix: update dependencies"
            ],
            "docs": [
                "docs: update README file",
                "docs: add code documentation",
                "docs: improve API documentation",
                "docs: add usage examples",
                "docs: update installation guide"
            ]
        }
        
        return fallback_messages.get(change_type, fallback_messages["feature"])
    
    def _get_fallback_commit_sequence(self, commit_count: int) -> List[str]:
        """Get fallback commit sequence when AI generation fails."""
        base_sequence = [
            "Initial project setup and configuration",
            "Add basic project structure",
            "Implement core functionality",
            "Add user interface components",
            "Integrate API endpoints",
            "Add data processing logic",
            "Implement error handling",
            "Add validation and security",
            "Optimize performance",
            "Update documentation",
            "Final testing and bug fixes",
            "Polish and cleanup"
        ]
        
        if commit_count <= len(base_sequence):
            return base_sequence[:commit_count]
        else:
            # Extend with generic messages
            extended = base_sequence[:]
            for i in range(commit_count - len(base_sequence)):
                extended.append(f"Additional improvements and fixes #{i + 1}")
            return extended
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute commit-related tasks.
        
        Args:
            task_data: Dictionary containing task parameters
            
        Returns:
            Dictionary with execution results
        """
        task_type = task_data.get("task_type")
        
        if task_type == "generate_messages":
            return {
                "messages": self.generate_commit_messages(
                    task_data.get("project_name", ""),
                    task_data.get("technologies", []),
                    task_data.get("file_changes", ""),
                    task_data.get("change_type", "feature"),
                    task_data.get("hackathon_theme", "general")
                )
            }
        
        elif task_type == "generate_sequence":
            return {
                "sequence": self.generate_commit_sequence(
                    task_data.get("project_name", ""),
                    task_data.get("project_description", ""),
                    task_data.get("technologies", []),
                    task_data.get("commit_count", 10),
                    task_data.get("hackathon_duration", 48)
                )
            }
        
        elif task_type == "create_history":
            return self.create_hackathon_commit_history(
                task_data.get("project_path", ""),
                task_data.get("project_name", ""),
                task_data.get("project_description", ""),
                task_data.get("technologies", []),
                task_data.get("hackathon_start"),
                task_data.get("hackathon_duration", 48),
                task_data.get("developer_name", ""),
                task_data.get("developer_email", "")
            )
        
        else:
            return {
                "success": False,
                "message": f"Unknown task type: {task_type}"
            } 