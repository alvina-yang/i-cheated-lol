"""
Git-related API routes for commit history and branch information.
"""

import os
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path

router = APIRouter()

@router.get("/api/project/{project_name}/git/history")
async def get_commit_history(
    project_name: str,
    branch: str = Query(None, description="Specific branch to get history for"),
    limit: int = Query(50, description="Maximum number of commits to return")
):
    """
    Get git commit history for a project.
    
    Args:
        project_name: Name of the project
        branch: Specific branch (optional, defaults to current branch)
        limit: Maximum number of commits to return
        
    Returns:
        Dictionary with commit history and branch information
    """
    try:
        # Get project path
        project_path = Path("/Users/alvinayang/HackathonProject") / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not (project_path / ".git").exists():
            raise HTTPException(status_code=400, detail="Not a git repository")
        
        # Change to project directory
        os.chdir(project_path)
        
        # Get all branches
        branches_result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True,
            check=True
        )
        
        branches = []
        current_branch = None
        for line in branches_result.stdout.split('\n'):
            line = line.strip()
            if line:
                if line.startswith('* '):
                    current_branch = line[2:].strip()
                    branches.append({"name": current_branch, "current": True})
                elif not line.startswith('remotes/origin/HEAD'):
                    branch_name = line.replace('remotes/origin/', '').strip()
                    if branch_name not in [b["name"] for b in branches]:
                        branches.append({"name": branch_name, "current": False})
        
        # Use specified branch or current branch
        target_branch = branch if branch else current_branch
        
        # Get commit history with detailed format
        git_cmd = [
            "git", "log", 
            f"--max-count={limit}",
            "--pretty=format:%H|%an|%ae|%ad|%s|%d",
            "--date=iso",
            target_branch if target_branch else "HEAD"
        ]
        
        result = subprocess.run(
            git_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 5:
                    commit_hash = parts[0]
                    author_name = parts[1]
                    author_email = parts[2]
                    date_str = parts[3]
                    message = parts[4]
                    refs = parts[5] if len(parts) > 5 else ""
                    
                    # Parse date
                    try:
                        commit_date = datetime.fromisoformat(date_str.replace(' +', '+').replace(' -', '-'))
                        formatted_date = commit_date.strftime("%Y-%m-%d %H:%M:%S")
                        relative_date = _get_relative_time(commit_date)
                    except:
                        formatted_date = date_str
                        relative_date = date_str
                    
                    # Parse refs for branch/tag info
                    branch_info = []
                    if refs:
                        refs = refs.strip(' ()')
                        for ref in refs.split(', '):
                            if 'origin/' in ref:
                                branch_info.append(ref.strip())
                    
                    commits.append({
                        "hash": commit_hash,
                        "short_hash": commit_hash[:7],
                        "author": {
                            "name": author_name,
                            "email": author_email
                        },
                        "date": formatted_date,
                        "relative_date": relative_date,
                        "message": message,
                        "branches": branch_info,
                        "refs": refs
                    })
        
        # Get repository stats
        total_commits_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        total_commits = int(total_commits_result.stdout.strip())
        
        return {
            "commits": commits,
            "branches": branches,
            "current_branch": current_branch,
            "total_commits": total_commits,
            "repository_path": str(project_path)
        }
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting commit history: {str(e)}")

def _get_relative_time(commit_date: datetime) -> str:
    """Get relative time string for a commit date."""
    now = datetime.now(commit_date.tzinfo)
    diff = now - commit_date
    
    if diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

@router.get("/api/project/{project_name}/git/branches")
async def get_branches(project_name: str):
    """Get all branches for a project."""
    try:
        project_path = Path("/Users/alvinayang/HackathonProject") / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        os.chdir(project_path)
        
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True,
            check=True
        )
        
        branches = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('remotes/origin/HEAD'):
                is_current = line.startswith('* ')
                branch_name = line[2:] if is_current else line
                branch_name = branch_name.replace('remotes/origin/', '')
                
                if branch_name not in [b["name"] for b in branches]:
                    branches.append({
                        "name": branch_name,
                        "current": is_current,
                        "remote": line.startswith('remotes/')
                    })
        
        return {"branches": branches}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting branches: {str(e)}") 