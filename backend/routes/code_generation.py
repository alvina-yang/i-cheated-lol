"""
Code generation routes for AI-powered code modifications
"""

import asyncio
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from agents.code_generation_agent import CodeGenerationAgent
from models.requests import CodeGenerationRequest
from models.responses import CodeGenerationResponse
from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api/code-generation", tags=["code-generation"])


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """
    Generate code modifications for a project based on feature description.
    
    This endpoint:
    1. Analyzes the project structure and files
    2. Selects relevant files to modify based on the feature description
    3. Generates code modifications using AI
    4. Returns the modified code for each file
    """
    tracker = get_global_tracker()
    tracker.update("code_generation", "started", f"Generating code for feature: {request.feature_description}")
    
    try:
        # Initialize the code generation agent
        agent = CodeGenerationAgent()
        
        # Prepare task data for the agent
        task_data = {
            "project_path": request.project_path,
            "feature": request.feature_description,
            "max_files": request.max_files
        }
        
        tracker.update("code_generation", "processing", "Agent initialized, processing request...")
        
        # Execute the code generation
        result = agent.execute(task_data)
        
        # Check if there was an error
        if "error" in result:
            tracker.update("code_generation", "error", f"Code generation failed: {result['error']}")
            return CodeGenerationResponse(
                success=False,
                message=f"Code generation failed: {result['error']}",
                error_details=result.get('raw_response', str(result))
            )
        
        # Check if we have generated files
        if not result or not isinstance(result, dict):
            tracker.update("code_generation", "error", "Invalid response format from agent")
            return CodeGenerationResponse(
                success=False,
                message="Invalid response format from code generation agent",
                error_details=str(result)
            )
        
        # Filter out non-file entries
        generated_files = {
            path: content for path, content in result.items()
            if isinstance(content, str) and path.startswith('/')
        }
        
        if not generated_files:
            tracker.update("code_generation", "warning", "No files were generated")
            return CodeGenerationResponse(
                success=True,
                message="Code generation completed but no files were modified",
                generated_files={}
            )
        
        tracker.update("code_generation", "completed", f"Successfully generated {len(generated_files)} files")
        
        return CodeGenerationResponse(
            success=True,
            message=f"Successfully generated code modifications for {len(generated_files)} files",
            generated_files=generated_files
        )
        
    except Exception as e:
        error_msg = f"Unexpected error during code generation: {str(e)}"
        tracker.update("code_generation", "error", error_msg)
        
        return CodeGenerationResponse(
            success=False,
            message=error_msg,
            error_details=str(e)
        )


@router.get("/status")
async def get_code_generation_status():
    """Get the current status of code generation operations"""
    tracker = get_global_tracker()
    status = tracker.get_status("code_generation")
    
    return {
        "operation": "code_generation",
        "status": status.get("status", "idle"),
        "message": status.get("message", "No active code generation"),
        "timestamp": status.get("timestamp")
    } 