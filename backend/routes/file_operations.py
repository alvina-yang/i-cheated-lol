"""
File operations routes for per-file code modifications
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api/file", tags=["file-operations"])


class FileOperationRequest(BaseModel):
    project_name: str
    file_path: str  # Relative path within the project


class FileOperationResponse(BaseModel):
    success: bool
    message: str
    original_content: str = ""
    modified_content: str = ""
    changes_summary: str = ""
    lines_added: int = 0
    variables_changed: int = 0


@router.post("/add-comments", response_model=FileOperationResponse)
async def add_comments_to_file(request: FileOperationRequest):
    """Add AI-generated comments to a specific file"""
    try:
        from app import agents
        from core.enhanced_config import EnhancedConfig
        
        # Build full file path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, request.project_name)
        full_file_path = os.path.join(project_path, request.file_path)
        
        # Validate file exists
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        # Read original content
        with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        
        # Use the CodeModifierAgent to add comments
        result = agents['code_modifier'].add_comments_to_file(full_file_path)
        
        if result.get("success", False):
            # Read modified content
            with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                modified_content = f.read()
            
            lines_added = result.get("lines_added", 0)
            
            return FileOperationResponse(
                success=True,
                message=f"Successfully added {lines_added} comment lines to {request.file_path}",
                original_content=original_content,
                modified_content=modified_content,
                changes_summary=f"Added {lines_added} AI-generated comment lines",
                lines_added=lines_added,
                variables_changed=0
            )
        else:
            return FileOperationResponse(
                success=False,
                message=result.get("message", "Failed to add comments"),
                original_content=original_content,
                modified_content=original_content,
                changes_summary="No changes made",
                lines_added=0,
                variables_changed=0
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding comments: {str(e)}")


@router.post("/rename-variables", response_model=FileOperationResponse)
async def rename_variables_in_file(request: FileOperationRequest):
    """Rename variables in a specific file"""
    try:
        from app import agents
        from core.enhanced_config import EnhancedConfig
        
        # Build full file path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, request.project_name)
        full_file_path = os.path.join(project_path, request.file_path)
        
        # Validate file exists
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        # Read original content
        with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        
        # Use the VariableRenamingAgent to rename variables
        result = agents['variable_renamer'].rename_variables_in_file(full_file_path)
        
        if result.get("success", False):
            # Read modified content
            with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                modified_content = f.read()
            
            changes_count = result.get("changes_count", 0)
            
            return FileOperationResponse(
                success=True,
                message=f"Successfully renamed {changes_count} variables in {request.file_path}",
                original_content=original_content,
                modified_content=modified_content,
                changes_summary=f"Renamed {changes_count} variables with more descriptive names",
                lines_added=0,
                variables_changed=changes_count
            )
        else:
            return FileOperationResponse(
                success=False,
                message=result.get("message", "Failed to rename variables"),
                original_content=original_content,
                modified_content=original_content,
                changes_summary="No changes made",
                lines_added=0,
                variables_changed=0
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renaming variables: {str(e)}")


@router.get("/content/{project_name}")
async def get_file_content(project_name: str, file_path: str):
    """Get the current content of a file"""
    try:
        from core.enhanced_config import EnhancedConfig
        
        # Build full file path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        full_file_path = os.path.join(project_path, file_path)
        
        # Validate file exists
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Read file content
        with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_path": file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}") 