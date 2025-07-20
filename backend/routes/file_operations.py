"""
File operations routes for per-file code modifications
"""

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from utils.status_tracker import get_global_tracker
from models.requests import PresentationScriptRequest
from models.responses import PresentationScriptResponse

router = APIRouter(prefix="/api/file", tags=["file-operations"])


class FileOperationRequest(BaseModel):
    project_name: str
    file_path: str  # Relative path within the project


class FileSaveRequest(BaseModel):
    file_path: str
    content: str


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


@router.post("/make-better", response_model=FileOperationResponse)
async def make_file_better(request: FileOperationRequest):
    """Refactor and reorder a file to make it better without changing logic"""
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
        
        # Use the CodeModifierAgent to refactor the file
        result = agents['code_modifier'].refactor_file(full_file_path)
        
        if result.get("success", False):
            # Read modified content
            with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                modified_content = f.read()
            
            refactorings_count = result.get("refactorings_count", 0)
            
            return FileOperationResponse(
                success=True,
                message=f"Successfully refactored {request.file_path}",
                original_content=original_content,
                modified_content=modified_content,
                changes_summary=f"Applied {refactorings_count} refactoring improvements",
                lines_added=0,
                variables_changed=refactorings_count
            )
        else:
            return FileOperationResponse(
                success=False,
                message=result.get("message", "Failed to refactor file"),
                original_content=original_content,
                modified_content=original_content,
                changes_summary="No changes made",
                lines_added=0,
                variables_changed=0
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refactoring file: {str(e)}")


@router.post("/save/{project_name}")
async def save_file_content(project_name: str, request: FileSaveRequest):
    """Save content to a file"""
    try:
        from core.enhanced_config import EnhancedConfig
        
        # Build full file path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        full_file_path = os.path.join(project_path, request.file_path)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        
        # Write the content to the file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {
            "success": True,
            "message": f"File saved successfully: {request.file_path}",
            "file_path": request.file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


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


@router.post("/generate-presentation-script", response_model=PresentationScriptResponse)
async def generate_presentation_script(request: PresentationScriptRequest):
    """Generate a compelling presentation script for hackathon pitches"""
    try:
        from app import agents
        from core.enhanced_config import EnhancedConfig
        
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, request.project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {request.project_name}")
        
        # Check if script already exists
        script_path = os.path.join(project_path, ".chameleon", "presentation_script.json")
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    saved_script = json.load(f)
                    return PresentationScriptResponse(**saved_script)
            except Exception as e:
                # If there's an error reading the saved script, generate a new one
                pass
        
        # Use the PresentationAgent to generate the script
        result = agents['presentation'].generate_presentation_script(project_path, request.project_name)
        
        # Save the script if generation was successful
        if result.get("success", False):
            try:
                # Create .chameleon directory if it doesn't exist
                chameleon_dir = os.path.join(project_path, ".chameleon")
                os.makedirs(chameleon_dir, exist_ok=True)
                
                # Save the script
                with open(script_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
            except Exception as e:
                print(f"Warning: Failed to save presentation script: {e}")
        
        return PresentationScriptResponse(
            success=result.get("success", False),
            message=result.get("message", "Unknown error"),
            script=result.get("script", ""),
            project_name=result.get("project_name", request.project_name),
            technologies=result.get("technologies", []),
            structure_overview=result.get("structure_overview", "")
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presentation script: {str(e)}")


@router.get("/presentation-script/{project_name}", response_model=PresentationScriptResponse)
async def get_presentation_script(project_name: str):
    """Get the saved presentation script for a project"""
    try:
        from core.enhanced_config import EnhancedConfig
        
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Check for saved script
        script_path = os.path.join(project_path, ".chameleon", "presentation_script.json")
        if not os.path.exists(script_path):
            return PresentationScriptResponse(
                success=False,
                message="No saved presentation script found",
                project_name=project_name
            )
        
        # Read and return the saved script
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                saved_script = json.load(f)
                return PresentationScriptResponse(**saved_script)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading saved script: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving presentation script: {str(e)}")


@router.delete("/presentation-script/{project_name}")
async def delete_presentation_script(project_name: str):
    """Delete the saved presentation script for a project"""
    try:
        from core.enhanced_config import EnhancedConfig
        
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Delete the script if it exists
        script_path = os.path.join(project_path, ".chameleon", "presentation_script.json")
        if os.path.exists(script_path):
            os.remove(script_path)
            return {"success": True, "message": "Presentation script deleted"}
        else:
            return {"success": False, "message": "No presentation script found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting presentation script: {str(e)}")


@router.get("/file-metadata/{project_name}")
async def get_file_metadata(project_name: str):
    """Get file analysis metadata for a project"""
    try:
        from app import agents
        from core.enhanced_config import EnhancedConfig
        
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Get file metadata
        metadata = agents['file_analysis'].get_file_metadata(project_path)
        
        if metadata:
            return {
                "success": True,
                "project_name": project_name,
                "metadata": metadata
            }
        else:
            return {
                "success": False,
                "message": "No file analysis metadata found",
                "project_name": project_name
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file metadata: {str(e)}")
    
@router.post("/build-dependency-graph/{project_name}")
async def build_dependency_graph(project_name: str):
    """Build a dependency graph for a project"""
    try:
        from app import agents
        from core.enhanced_config import EnhancedConfig
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building dependency graph: {str(e)}")


# @router.post("/analyze-files/{project_name}")
# async def trigger_file_analysis(project_name: str):
#     """Manually trigger file analysis for a project"""
#     try:
#         from app import agents
#         from core.enhanced_config import EnhancedConfig
        
#         # Build project path
#         project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
#         # Validate project exists
#         if not os.path.exists(project_path):
#             raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
#         # Run file analysis
#         result = await agents['file_analysis'].analyze_project_files(project_path)
        
#         return {
#             "success": result.get("success", False),
#             "message": result.get("message", "Unknown error"),
#             "total_files": result.get("total_files", 0),
#             "project_name": project_name
#         }
            
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error triggering file analysis: {str(e)}") 