"""
Feature suggestion routes for AI-powered feature recommendations
"""

import os
import json
from fastapi import APIRouter
from typing import Dict, Any

from agents.suggest_feature_agent import SuggestFeatureAgent
from models.requests import FeatureSuggestionRequest
from models.responses import FeatureSuggestionResponse
from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api/feature-suggestion", tags=["feature-suggestion"])


def save_suggestions_to_file(suggestions_data: Dict[str, Any]) -> bool:
    """Save feature suggestions to features.json file"""
    try:
        features_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "features.json")
        
        # Load existing data or create new
        existing_data = {}
        if os.path.exists(features_file):
            try:
                with open(features_file, 'r') as f:
                    existing_data = json.load(f)
            except:
                existing_data = {}
        
        # Add timestamp to the suggestions
        from datetime import datetime
        suggestions_data['generated_at'] = datetime.now().isoformat()
        
        # Save to file
        existing_data['latest_suggestions'] = suggestions_data
        
        with open(features_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving suggestions to file: {e}")
        return False


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
    tracker.set_current_operation(f"Analyzing project: {request.project_path}")
    
    # Create feature suggestion task
    task_id = "feature_suggestion"
    feature_task = tracker.create_task(
        task_id,
        "Feature Suggestion",
        f"Analyzing project for feature suggestions: {request.project_path}"
    )
    
    tracker.start_task(task_id)
    tracker.add_output_line(f"🔍 Starting feature analysis for project...")
    
    try:
        # Import agents from main app
        from app import agents
        
        # Use the shared feature suggestion agent
        agent = agents['suggest_feature']
        
        # Prepare task data for the agent
        task_data = {
            "project_path": request.project_path
        }
        
        tracker.update_task(task_id, 20, "Agent initialized, analyzing project...")
        
        # Execute the feature suggestion
        result = agent.execute(task_data)
        
        # Check if there was an error
        if "error" in result:
            error_msg = f"Feature suggestion failed: {result['error']}"
            tracker.fail_task(task_id, "Feature suggestion failed", error_msg)
            tracker.clear_current_operation()
            return FeatureSuggestionResponse(
                success=False,
                message=error_msg,
                error_details=result.get('raw_response', str(result))
            )
        
        # Check if we have valid suggestions
        if not result or not isinstance(result, dict):
            error_msg = "Invalid response format from agent"
            tracker.fail_task(task_id, "Invalid response", error_msg)
            tracker.clear_current_operation()
            return FeatureSuggestionResponse(
                success=False,
                message=error_msg,
                error_details=str(result)
            )
        
        # Extract suggestions from result
        suggestions = result.get("suggestions", [])
        if not suggestions:
            warning_msg = "No feature suggestions generated"
            tracker.complete_task(task_id, warning_msg)
            tracker.clear_current_operation()
            return FeatureSuggestionResponse(
                success=True,
                message="Analysis completed but no feature suggestions were generated",
                suggestions=[]
            )
        
        success_msg = f"Successfully generated {len(suggestions)} feature suggestions"
        tracker.complete_task(task_id, success_msg)
        tracker.clear_current_operation()
        
        # Save suggestions to features.json file
        suggestion_data = {
            "suggestions": suggestions,
            "project_analysis": result.get("project_analysis", ""),
            "priority_recommendations": result.get("priority_recommendations", []),
            "project_path": request.project_path
        }
        save_suggestions_to_file(suggestion_data)
        
        return FeatureSuggestionResponse(
            success=True,
            message=success_msg,
            suggestions=suggestions,
            project_analysis=result.get("project_analysis", ""),
            priority_recommendations=result.get("priority_recommendations", [])
        )
        
    except Exception as e:
        error_msg = f"Unexpected error during feature suggestion: {str(e)}"
        tracker.fail_task(task_id, str(e), error_msg)
        tracker.clear_current_operation()
        
        return FeatureSuggestionResponse(
            success=False,
            message=error_msg,
            error_details=str(e)
        )


@router.get("/status")
async def get_feature_suggestion_status():
    """Get the current status of feature suggestion operations"""
    tracker = get_global_tracker()
    
    return {
        "operation": "feature_suggestion",
        "status": tracker.get_status_summary(),
        "timestamp": None
    }


@router.get("/features")
async def get_saved_features():
    """Get saved feature suggestions from features.json"""
    try:
        features_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "features.json")
        
        if not os.path.exists(features_file):
            return {"error": "No saved features found"}
        
        with open(features_file, 'r') as f:
            data = json.load(f)
        
        return data
        
    except Exception as e:
        return {"error": f"Failed to load features: {str(e)}"} 