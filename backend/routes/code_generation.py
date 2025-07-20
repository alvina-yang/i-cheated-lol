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
    tracker.set_current_operation(f"Generating code for feature: {request.feature_description}")
    
    # Create code generation task
    task_id = "code_generation"
    code_task = tracker.create_task(
        task_id,
        "Code Generation",
        f"Generating code for feature: {request.feature_description}"
    )
    
    tracker.start_task(task_id)
    tracker.add_output_line(f"🔧 Starting code generation for feature...")
    
    try:
        # Import agents from main app
        from app import agents
        
        # Use the shared code generation agent
        agent = agents['code_generation']
        
        # Prepare task data for the agent
        task_data = {
            "project_path": request.project_path,
            "feature_description": request.feature_description,
            "max_files": request.max_files
        }
        
        tracker.update_task(task_id, 20, "Agent initialized, processing request...")
        
        # Execute the code generation
        result = agent.execute(task_data)
        
        # Check if there was an error
        if "error" in result:
            error_msg = f"Code generation failed: {result['error']}"
            tracker.fail_task(task_id, "Code generation failed", error_msg)
            tracker.clear_current_operation()
            return CodeGenerationResponse(
                success=False,
                message=error_msg,
                error_details=result.get('raw_response', str(result))
            )
        
        # Check if we have generated files
        if not result or not isinstance(result, dict):
            error_msg = "Invalid response format from agent"
            tracker.fail_task(task_id, "Invalid response", error_msg)
            tracker.clear_current_operation()
            return CodeGenerationResponse(
                success=False,
                message=error_msg,
                error_details=str(result)
            )
        
        # Filter out non-file entries
        generated_files = {
            path: content for path, content in result.items()
            if isinstance(content, str) and not path.startswith('reasoning')
        }
        
        if not generated_files:
            warning_msg = "No files were generated"
            tracker.complete_task(task_id, warning_msg)
            tracker.clear_current_operation()
            return CodeGenerationResponse(
                success=True,
                message="Code generation completed but no files were modified",
                generated_files={}
            )
        
        success_msg = f"Successfully generated {len(generated_files)} files"
        tracker.complete_task(task_id, success_msg)
        tracker.clear_current_operation()
        
        return CodeGenerationResponse(
            success=True,
            message=success_msg,
            generated_files=generated_files
        )
        
    except Exception as e:
        error_msg = f"Unexpected error during code generation: {str(e)}"
        tracker.fail_task(task_id, str(e), error_msg)
        tracker.clear_current_operation()
        
        return CodeGenerationResponse(
            success=False,
            message=error_msg,
            error_details=str(e)
        )


@router.get("/status")
async def get_code_generation_status():
    """Get the current status of code generation operations"""
    tracker = get_global_tracker()
    
    return {
        "operation": "code_generation",
        "status": tracker.get_status_summary(),
        "timestamp": None
    } 