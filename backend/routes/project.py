"""
Project routes for the Chameleon Hackathon Discovery API
"""

import os
import json
import time
import subprocess
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from core.enhanced_config import EnhancedConfig
from utils.status_tracker import get_global_tracker
from services.helpers import (
    _build_file_tree,
    _get_project_readme,
    _extract_project_technologies,
    _get_change_type
)

router = APIRouter(prefix="/api", tags=["project"])


@router.get("/project/{project_name}/terminal-output")
async def get_terminal_output(project_name: str):
    """Get terminal output for a project"""
    try:
        status_tracker = get_global_tracker()
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get recent output from status tracker
        recent_output = status_tracker.get_recent_output(100)
        
        # Filter output related to this project
        project_output = [
            line for line in recent_output 
            if project_name in line or "git" in line.lower()
        ]
        
        return {
            "project_name": project_name,
            "output": project_output,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting terminal output: {str(e)}")





@router.post("/project/{project_name}/execute-git-command")
async def execute_git_command(project_name: str, command: dict):
    """Execute a git command and stream output"""
    try:
        from app import agents  # Import agents from main app
        status_tracker = get_global_tracker()
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate command
        git_command = command.get("command", "").strip()
        if not git_command.startswith("git "):
            raise HTTPException(status_code=400, detail="Only git commands are allowed")
        
        # Create execution task
        task_id = f"git_cmd_{project_name}_{int(time.time())}"
        exec_task = status_tracker.create_task(
            task_id,
            f"Execute git command: {git_command}",
            f"Running {git_command} in {project_name}"
        )
        
        status_tracker.start_task(task_id)
        status_tracker.set_current_operation(f"Executing git command in {project_name}")
        
        # Execute command using git agent
        cmd_parts = git_command.split()
        
        try:
            # Stream command output
            output_lines = []
            for line in agents['git'].stream_git_output(project_path, cmd_parts):
                output_lines.append(line)
                status_tracker.add_output_line(line, "git")
                
                # Update progress
                progress = min(100, len(output_lines) * 10)  # Rough progress estimation
                status_tracker.update_task(task_id, progress, f"Git: {line}")
            
            status_tracker.complete_task(task_id, f"Git command completed successfully")
            status_tracker.clear_current_operation()
            
            return {
                "success": True,
                "command": git_command,
                "output": output_lines,
                "task_id": task_id
            }
            
        except Exception as e:
            status_tracker.fail_task(task_id, str(e), f"Git command failed: {str(e)}")
            status_tracker.clear_current_operation()
            
            return {
                "success": False,
                "command": git_command,
                "error": str(e),
                "task_id": task_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing git command: {str(e)}")


@router.get("/project/{project_name}/file-changes")
async def get_file_changes(project_name: str):
    """Get file changes for a project"""
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get git status
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    changes.append({
                        "status": status,
                        "filename": filename,
                        "type": _get_change_type(status)
                    })
            
            return {
                "project_name": project_name,
                "changes": changes,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError:
            return {
                "project_name": project_name,
                "changes": [],
                "error": "Not a git repository or git command failed"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file changes: {str(e)}")


@router.get("/project/{project_name}/monitor-changes")
async def monitor_file_changes(project_name: str):
    """Monitor file changes in real-time"""
    async def generate():
        from app import agents  # Import agents from main app
        status_tracker = get_global_tracker()
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            yield f"data: {json.dumps({'error': 'Project not found'})}\n\n"
            return
        
        # Start file monitoring
        def change_callback(changed_files):
            data = {
                "project_name": project_name,
                "changed_files": changed_files,
                "timestamp": datetime.now().isoformat()
            }
            # Note: This would need to be handled differently in a real async context
            # For now, we'll just log it
            status_tracker.add_output_line(f"File changes detected: {len(changed_files)} files", "filesystem")
        
        monitor_result = agents['git'].execute({
            "task_type": "monitor_changes",
            "project_path": project_path,
            "change_callback": change_callback
        })
        
        if not monitor_result["success"]:
            yield f"data: {json.dumps({'error': monitor_result['message']})}\n\n"
            return
        
        # Stream file changes
        last_check = datetime.now()
        
        while True:
            try:
                # Get recent file system output
                recent_output = status_tracker.get_recent_output(10)
                fs_output = [line for line in recent_output if "filesystem" in line]
                
                if fs_output:
                    data = {
                        "project_name": project_name,
                        "monitoring_active": True,
                        "recent_changes": fs_output,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/project/{project_name}/files")
async def get_project_files(project_name: str):
    """
    Get the file structure and metadata for a cloned project
    """
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Read project metadata if available
        metadata_path = os.path.join(project_path, '.chameleon_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Build file tree
        files = _build_file_tree(project_path, project_path)
        
        # Get README content if available
        readme_content = _get_project_readme(project_path)
        
        project_data = {
            "name": project_name,
            "description": metadata.get('description', 'No description available'),
            "technologies": _extract_project_technologies(project_path),
            "stars": metadata.get('stars', 0),
            "forks": metadata.get('forks', 0),
            "language": metadata.get('language', 'Unknown'),
            "files": files,
            "readme": readme_content
        }
        
        return project_data
        
    except Exception as e:
        print(f"❌ Error getting project files: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading project files: {str(e)}")


@router.get("/project/{project_name}/file")
async def get_project_file(project_name: str, path: str):
    """
    Get the content of a specific file in a project
    """
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Ensure the file path is within the project directory (security)
        file_path = os.path.join(project_path, path)
        if not file_path.startswith(project_path):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check file size (limit to 1MB for safety)
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # 1MB
            return Response(content="File too large to display", media_type="text/plain")
        
        # Try to read as text file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content=content, media_type="text/plain")
        except UnicodeDecodeError:
            # If it's a binary file, return a message
            return Response(content="Binary file - cannot display content", media_type="text/plain")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}") 