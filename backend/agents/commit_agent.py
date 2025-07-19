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
from core.config import Config
from utils.commit_message_bank import commit_bank


class CommitAgent(BaseAgent):
    """
    Agent responsible for generating realistic commit messages and managing commit operations.
    """
    
    def __init__(self):
        super().__init__("CommitAgent")
    
    def generate_commit_messages(self, project_name: str, technologies: List[str], 
                               file_changes: str, change_type: str, 
                               hackathon_theme: str = "general") -> List[str]:
        """
        Generate generic commit messages from predefined bank.
        
        Args:
            project_name: Name of the project (ignored)
            technologies: List of technologies used (ignored)
            file_changes: Description of files changed (ignored)
            change_type: Type of change (ignored)
            hackathon_theme: Theme of the hackathon (ignored)
            
        Returns:
            List of random generic commit messages
        """
        # Simply return random messages from the bank
        return [random.choice(commit_bank.messages) for _ in range(random.randint(3, 8))]
    
    def generate_commit_sequence(self, project_name: str, project_description: str,
                               technologies: List[str], commit_count: int,
                               hackathon_duration: int = 48) -> List[str]:
        """
        Generate a sequence of generic commit messages for a hackathon project.
        
        Args:
            project_name: Name of the project
            project_description: Description of the project (ignored - using generic messages)
            technologies: List of technologies used (ignored - using generic messages)
            commit_count: Number of commits to generate
            hackathon_duration: Duration of hackathon in hours
            
        Returns:
            List of generic commit messages in chronological order
        """
        # Use the generic commit message bank instead of AI-generated descriptive messages
        return commit_bank.get_hackathon_sequence(commit_count, hackathon_duration)
    
    def generate_commit_description(self, commit_title: str, file_changes: str,
                                  project_context: str) -> str:
        """
        Generate a simple commit description (just return the title).
        
        Args:
            commit_title: Title of the commit
            file_changes: Description of changed files (ignored)
            project_context: Context about the project (ignored)
            
        Returns:
            Simple commit description (same as title)
        """
        # Just return the commit title - no detailed descriptions needed
        return commit_title
    
    def create_hackathon_commit_history(self, project_path: str, project_name: str,
                                      project_description: str, technologies: List[str],
                                      hackathon_start: datetime, hackathon_duration: int,
                                      team_members: List[Dict[str, str]] = None,
                                      developer_name: str = "", developer_email: str = "") -> Dict[str, Any]:
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
            # Add status tracking
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
            status_tracker.add_output_line(f"🔄 Starting git history rewriting for {project_name}...", "git")
            
            # Get current commit count
            original_commits = self._get_commit_count(project_path)
            status_tracker.add_output_line(f"📊 Found {original_commits} existing commits", "git")
            
            if original_commits == 0:
                status_tracker.add_output_line("❌ No commits found in project", "git")
                return {
                    "success": False,
                    "message": "No commits found in project",
                    "commits_created": 0
                }
            
            # Generate commit sequence
            status_tracker.add_output_line(f"🤖 Generating AI commit messages for {hackathon_duration}h hackathon timeline...", "git")
            commit_messages = self.generate_commit_sequence(
                project_name, project_description, technologies, original_commits, hackathon_duration
            )
            status_tracker.add_output_line(f"✅ Generated {len(commit_messages)} commit messages", "git")
            
            # Create new commit history
            status_tracker.add_output_line(f"🔧 Rewriting git history with new timeline...", "git")
            
            # Use team members if provided, otherwise fall back to single developer
            if team_members and len(team_members) > 0:
                status_tracker.add_output_line(f"👥 Using {len(team_members)} team members for commit attribution", "git")
                result = self._rewrite_commit_history_with_team(
                    project_path, commit_messages, hackathon_start, hackathon_duration, team_members
                )
            else:
                # Fallback to single developer (backward compatibility)
                if not developer_name:
                    developer_name = "hackathon-dev"
                if not developer_email:
                    developer_email = "dev@hackathon.local"
                status_tracker.add_output_line(f"👤 Using single developer: {developer_name} <{developer_email}>", "git")
                result = self._rewrite_commit_history(
                    project_path, commit_messages, hackathon_start, hackathon_duration,
                    developer_name, developer_email
                )
            
            if result:
                status_tracker.add_output_line(f"✅ Successfully rewrote git history with {len(commit_messages)} commits", "git")
            else:
                status_tracker.add_output_line("❌ Failed to rewrite git history", "git")
            
            return {
                "success": result,
                "message": f"Created hackathon commit history with {len(commit_messages)} commits",
                "commits_created": len(commit_messages),
                "commit_messages": commit_messages,
                "timeline_start": hackathon_start.isoformat(),
                "timeline_duration": hackathon_duration
            }
            
        except Exception as e:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            status_tracker.add_output_line(f"❌ Error creating hackathon commit history: {str(e)}", "git")
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
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
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
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
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
    
    def _rewrite_commit_history_with_team(self, project_path: str, commit_messages: List[str],
                                         hackathon_start: datetime, hackathon_duration: int,
                                         team_members: List[Dict[str, str]]) -> bool:
        """
        Rewrite git history with new commit messages assigned to random team members.
        
        Args:
            project_path: Path to the project
            commit_messages: List of commit messages
            hackathon_start: Start time of hackathon
            hackathon_duration: Duration in hours
            team_members: List of team member dictionaries with username, email, name
            
        Returns:
            Success status
        """
        try:
            from utils.status_tracker import get_global_tracker
            status_tracker = get_global_tracker()
            
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
            
            # Create temporary script for rewriting commits with team members
            script_content = self._create_team_commit_rewriter_script(
                commit_hashes, commit_messages, time_distribution, team_members
            )
            
            script_path = os.path.join(project_path, 'team_commit_rewriter.sh')
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            
            status_tracker.add_output_line("📝 Created team commit rewriter script", "git")
            
            # Run the rewriter script
            status_tracker.add_output_line("🔄 Running team commit rewriter...", "git")
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
                status_tracker.add_output_line(f"❌ Team commit rewriter failed with exit code {process.returncode}", "git")
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
                status_tracker.add_output_line("📋 Recent commits after team rewriting:", "git")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        status_tracker.add_output_line(f"  {line}", "git")
            
            return True
            
        except Exception as e:
            status_tracker.add_output_line(f"❌ Error in team git rewriting: {e}", "git")
            return False
    
    def _create_team_commit_rewriter_script(self, commit_hashes: List[str], commit_messages: List[str],
                                           time_distribution: List[datetime], team_members: List[Dict[str, str]]) -> str:
        """Create a bash script to rewrite git history with team members on ALL branches."""
        script_lines = [
            '#!/bin/bash',
            'set -e',
            '',
            'echo "Starting comprehensive git history rewriting on ALL branches..."',
            '',
            '# Get all branches (local and remote)',
            'echo "Fetching all branches..."',
            'git fetch --all 2>/dev/null || echo "No remote to fetch"',
            '',
            '# Create backup of current state',
            'git branch backup-original-$(date +%s) HEAD 2>/dev/null || echo "Backup branch already exists"',
            '',
            '# Get all branch names (local and remote)',
            'ALL_BRANCHES=$(git branch -a | grep -v "backup-original" | sed "s/remotes\\/origin\\///" | sed "s/*//g" | sed "s/ //g" | sort -u | grep -v "^$")',
            '',
            'echo "Found branches to rewrite:"',
            'echo "$ALL_BRANCHES"',
            '',
            '# Process each branch',
            'for BRANCH in $ALL_BRANCHES; do',
            '    if [[ "$BRANCH" == "HEAD" ]] || [[ "$BRANCH" == *"backup-original"* ]]; then',
            '        continue',
            '    fi',
            '    ',
            '    echo "Processing branch: $BRANCH"',
            '    ',
            '    # Checkout or create the branch',
            '    git checkout -B "$BRANCH" 2>/dev/null || git checkout "$BRANCH" 2>/dev/null || continue',
            '    ',
            '    # Get commits for this branch',
            '    BRANCH_COMMITS=$(git rev-list --reverse HEAD)',
            '    COMMIT_COUNT=$(echo "$BRANCH_COMMITS" | wc -l)',
            '    ',
            '    if [ "$COMMIT_COUNT" -eq 0 ]; then',
            '        echo "No commits found in branch $BRANCH, skipping..."',
            '        continue',
            '    fi',
            '    ',
            '    echo "Rewriting $COMMIT_COUNT commits in branch $BRANCH"',
            '    ',
            '    # Reset to first commit of this branch',
            '    FIRST_COMMIT=$(echo "$BRANCH_COMMITS" | head -1)',
            '    FIRST_PARENT=$(git rev-list --parents "$FIRST_COMMIT" | head -1 | cut -d" " -f2)',
            '    ',
            '    if [ -n "$FIRST_PARENT" ]; then',
            '        git reset --hard "$FIRST_PARENT"',
            '    else',
            '        # Orphan branch, start fresh',
            '        git checkout --orphan temp-branch-$BRANCH',
            '        git rm -rf . 2>/dev/null || true',
            '    fi',
            '',
        ]
        
        # Add commit processing logic inside the branch loop
        script_lines.extend([
            '    # Process commits for this branch',
            '    COMMIT_INDEX=0',
            '    for ORIGINAL_COMMIT in $BRANCH_COMMITS; do',
            '        COMMIT_INDEX=$((COMMIT_INDEX + 1))',
            '        ',
            '        # Get a random commit message and team member',
        ])
        
        # Add logic to select random messages and team members
        script_lines.extend([
            f'        # Random selection of commit message and team member',
            f'        MESSAGE_INDEX=$(($RANDOM % {len(commit_messages)}))',
            f'        TEAM_INDEX=$(($RANDOM % {len(team_members)}))',
            f'        ',
        ])
        
        # Add all the commit messages as a bash array
        messages_list = '("' + '" "'.join([msg.replace('"', '\\"') for msg in commit_messages]) + '")'
        script_lines.append(f'        MESSAGES={messages_list}')
        script_lines.append(f'        MESSAGE="${{MESSAGES[$MESSAGE_INDEX]}}"')
        script_lines.append('')
        
        # Add all team members as bash arrays
        usernames = [member.get('username', 'dev') for member in team_members]
        emails = [member.get('email', 'dev@hackathon.local') for member in team_members]
        names = [member.get('name', member.get('username', 'dev')) for member in team_members]
        
        usernames_list = '("' + '" "'.join(usernames) + '")'
        emails_list = '("' + '" "'.join(emails) + '")'
        names_list = '("' + '" "'.join(names) + '")'
        
        script_lines.extend([
            f'        USERNAMES={usernames_list}',
            f'        EMAILS={emails_list}',
            f'        NAMES={names_list}',
            f'        ',
            f'        USERNAME="${{USERNAMES[$TEAM_INDEX]}}"',
            f'        EMAIL="${{EMAILS[$TEAM_INDEX]}}"',
            f'        NAME="${{NAMES[$TEAM_INDEX]}}"',
            f'        ',
            f'        # Generate random timestamp within hackathon period',
            f'        START_TIMESTAMP={int(time_distribution[0].timestamp())}',
            f'        END_TIMESTAMP={int(time_distribution[-1].timestamp())}',
            f'        RANDOM_TIMESTAMP=$(($START_TIMESTAMP + ($RANDOM % ($END_TIMESTAMP - $START_TIMESTAMP))))',
            f'        ',
            f'        echo "    Commit $COMMIT_INDEX: $MESSAGE (by $NAME)"',
            f'        ',
            f'        # Get the changes from the original commit',
            f'        if [ $COMMIT_INDEX -eq 1 ]; then',
            f'            # First commit - get all files',
            f'            git checkout $ORIGINAL_COMMIT -- . 2>/dev/null || true',
            f'            git add -A',
            f'        else',
            f'            # Cherry-pick changes from original commit',
            f'            git cherry-pick --no-commit $ORIGINAL_COMMIT || {{',
            f'                # If cherry-pick fails, just copy the files',
            f'                git checkout $ORIGINAL_COMMIT -- . 2>/dev/null || true',
            f'                git add -A',
            f'            }}',
            f'        fi',
            f'        ',
            f'        # Create new commit with random team member',
            f'        export GIT_AUTHOR_NAME="$NAME"',
            f'        export GIT_AUTHOR_EMAIL="$EMAIL"',
            f'        export GIT_COMMITTER_NAME="$NAME"',
            f'        export GIT_COMMITTER_EMAIL="$EMAIL"',
            f'        export GIT_AUTHOR_DATE="$RANDOM_TIMESTAMP"',
            f'        export GIT_COMMITTER_DATE="$RANDOM_TIMESTAMP"',
            f'        ',
            f'        git commit -m "$MESSAGE" --allow-empty',
            f'    done',
            f'    ',
            f'    # If we created a temp branch, replace the original',
            f'    if git show-ref --verify --quiet refs/heads/temp-branch-$BRANCH; then',
            f'        git branch -D "$BRANCH" 2>/dev/null || true',
            f'        git branch -m temp-branch-$BRANCH "$BRANCH"',
            f'    fi',
            f'    ',
            f'    echo "Completed rewriting branch: $BRANCH"',
            f'done',
            f'',
            f'echo "All branches rewritten successfully!"',
            f'echo "Verification of all branches:"',
            f'git branch --all',
            f'echo "Sample commits from main/master branch:"',
            f'git checkout main 2>/dev/null || git checkout master 2>/dev/null || git checkout $(git branch | head -1 | sed "s/*//g" | sed "s/ //g")',
            f'git log --oneline --format="%h %s %an <%ae>" -5'
        ])
        
        return '\n'.join(script_lines)
    
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
        """Get fallback commit messages using generic bank."""
        # Just return random messages from the bank - ignore change_type
        return [random.choice(commit_bank.messages) for _ in range(random.randint(3, 8))]
    
    def _get_fallback_commit_sequence(self, commit_count: int) -> List[str]:
        """Get fallback commit sequence using generic message bank."""
        # Use the generic commit message bank for fallback as well
        return [random.choice(commit_bank.messages) for _ in range(commit_count)]
    
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
                task_data.get("team_members", []),
                task_data.get("developer_name", ""),
                task_data.get("developer_email", "")
            )
        
        else:
            return {
                "success": False,
                "message": f"Unknown task type: {task_type}"
            } 