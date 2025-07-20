"""
Feature suggestion routes for AI-powered feature recommendations
"""

from fastapi import APIRouter
from typing import Dict, Any

from agents.suggest_feature_agent import SuggestFeatureAgent
from models.requests import FeatureSuggestionRequest
from models.responses import FeatureSuggestionResponse
from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api/feature-suggestion", tags=["feature-suggestion"])


@router.post("/suggest", response_model=FeatureSuggestionResponse)
async def suggest_feature(request: FeatureSuggestionRequest):
    """
    Suggest new features for a project based on its current structure and files.
    
    This endpoint:
    1. Analyzes the project structure and existing files
    2. Identifies gaps or potential improvements
    3. Suggests relevant features that could be added
    4. Returns structured suggestions with descriptions and rationale
    """
    tracker = get_global_tracker()
    tracker.update("feature_suggestion", "started", f"Analyzing project: {request.project_path}")
    
    try:
        # Initialize the feature suggestion agent
        agent = SuggestFeatureAgent()
        
        # Prepare task data for the agent
        task_data = {
            "project_path": request.project_path
        }
        
        tracker.update("feature_suggestion", "processing", "Agent initialized, analyzing project...")
        
        # Execute the feature suggestion
        result = agent.execute(task_data)
        
        # Check if there was an error
        if "error" in result:
            tracker.update("feature_suggestion", "error", f"Feature suggestion failed: {result['error']}")
            return FeatureSuggestionResponse(
                success=False,
                message=f"Feature suggestion failed: {result['error']}",
                error_details=result.get('raw_response', str(result))
            )
        
        # Check if we have valid suggestions
        if not result or not isinstance(result, dict):
            tracker.update("feature_suggestion", "error", "Invalid response format from agent")
            return FeatureSuggestionResponse(
                success=False,
                message="Invalid response format from feature suggestion agent",
                error_details=str(result)
            )
        
        # Extract suggestions from result
        suggestions = result.get("suggestions", [])
        if not suggestions:
            tracker.update("feature_suggestion", "warning", "No feature suggestions generated")
            return FeatureSuggestionResponse(
                success=True,
                message="Analysis completed but no feature suggestions were generated",
                suggestions=[]
            )
        
        tracker.update("feature_suggestion", "completed", f"Successfully generated {len(suggestions)} feature suggestions")
        
        return FeatureSuggestionResponse(
            success=True,
            message=f"Successfully generated {len(suggestions)} feature suggestions",
            suggestions=suggestions,
            project_analysis=result.get("project_analysis", ""),
            priority_recommendations=result.get("priority_recommendations", [])
        )
        
    except Exception as e:
        error_msg = f"Unexpected error during feature suggestion: {str(e)}"
        tracker.update("feature_suggestion", "error", error_msg)
        
        return FeatureSuggestionResponse(
            success=False,
            message=error_msg,
            error_details=str(e)
        )


@router.get("/status")
async def get_feature_suggestion_status():
    """Get the current status of feature suggestion operations"""
    tracker = get_global_tracker()
    status = tracker.get_status("feature_suggestion")
    
    return {
        "operation": "feature_suggestion",
        "status": status.get("status", "idle"),
        "message": status.get("message", "No active feature suggestion"),
        "timestamp": status.get("timestamp")
    } 