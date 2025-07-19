"""
Untraceable routes for the Chameleon Hackathon Discovery API
"""

import os
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models import EnhancedUntraceabilityRequest, EnhancedUntraceabilityResponse
from core.enhanced_config import EnhancedConfig
from utils.status_tracker import get_global_tracker
from services.background_tasks import run_untraceable_process

router = APIRouter(prefix="/api", tags=["untraceable"])


@router.post("/project/{project_name}/make-untraceable", response_model=EnhancedUntraceabilityResponse)
async def make_project_untraceable(project_name: str, request: EnhancedUntraceabilityRequest, background_tasks: BackgroundTasks):
    """
    Enhanced version: Make a project untraceable using AI agents with real-time progress tracking
    """
    try:
        status_tracker = get_global_tracker()
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update repository settings if target URL is provided
        if request.target_repository_url:
            EnhancedConfig.update_repository_settings(
                target_url=request.target_repository_url,
                original_url=""  # We'll detect this from the git repo
            )
        
        # Update user settings
        EnhancedConfig.update_user_settings(
            git_username=request.git_username,
            git_email=request.git_email
        )
        
        # Update processing settings
        EnhancedConfig.update_processing_settings(
            modify_commit_messages=True
        )
        
        # Create main untraceable task
        main_task_id = f"untraceable_{project_name}"
        status_tracker.set_current_operation(f"Making {project_name} untraceable")
        
        main_task = status_tracker.create_task(
            main_task_id,
            f"Make {project_name} untraceable",
            "Starting untraceable process..."
        )
        
        status_tracker.start_task(main_task_id)
        
        # Run the untraceable process in the background
        background_tasks.add_task(
            run_untraceable_process,
            project_name,
            project_path,
            request,
            main_task_id
        )
        
        return EnhancedUntraceabilityResponse(
            success=True,
            message=f"Started making {project_name} untraceable! Check status for progress.",
            status_tracking_id=main_task_id
        )
        
    except Exception as e:
        print(f"❌ Error making project untraceable: {e}")
        raise HTTPException(status_code=500, detail=f"Error making project untraceable: {str(e)}") 