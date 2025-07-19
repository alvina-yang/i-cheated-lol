"""
Clone routes for the Chameleon Hackathon Discovery API
"""

import os
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models import CloneRequest, CloneResponse
from core.enhanced_config import EnhancedConfig
from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api", tags=["clone"])


async def run_file_analysis_async(project_name: str, project_path: str):
    """Run file analysis in the background after project clone."""
    try:
        from app import agents  # Import agents from main app
        status_tracker = get_global_tracker()
        
        # Create a task for file analysis tracking
        analysis_task = status_tracker.create_task(
            "file_analysis",
            "File Analysis",
            f"Analyzing files for {project_name}"
        )
        
        status_tracker.start_task("file_analysis")
        status_tracker.add_output_line(f"🔍 Starting file analysis for {project_name}...")
        print(f"🔍 Starting file analysis for {project_name}...")
        
        # Run file analysis
        result = await agents['file_analysis'].analyze_project_files(project_path)
        
        if result.get('success', False):
            total_files = result.get('total_files', 0)
            success_msg = f"✅ File analysis complete for {project_name}! Analyzed {total_files} files."
            status_tracker.complete_task("file_analysis", success_msg)
            status_tracker.add_output_line(success_msg)
            print(success_msg)
        else:
            error_msg = f"⚠️ File analysis failed for {project_name}: {result.get('message', 'Unknown error')}"
            status_tracker.fail_task("file_analysis", "Analysis failed", error_msg)
            status_tracker.add_output_line(error_msg)
            print(error_msg)
            
    except Exception as e:
        status_tracker = get_global_tracker()
        error_msg = f"❌ File analysis error for {project_name}: {str(e)}"
        status_tracker.fail_task("file_analysis", str(e), error_msg)
        status_tracker.add_output_line(error_msg)
        print(error_msg)


@router.post("/clone", response_model=CloneResponse)
async def clone_project(request: CloneRequest, background_tasks: BackgroundTasks):
    """Clone the selected project to local filesystem"""
    try:
        from app import agents  # Import agents from main app
        status_tracker = get_global_tracker()
        
        status_tracker.set_current_operation(f"Cloning project: {request.project_name}")
        
        # Create clone task
        clone_task = status_tracker.create_task(
            "clone_project",
            "Clone project",
            f"Cloning {request.project_name} from {request.project_url}"
        )
        
        status_tracker.start_task("clone_project")
        
        print(f"📥 Cloning project: {request.project_name}")
        
        # Create a project dict for the cloner
        project_data = {
            'name': request.project_name,
            'html_url': request.project_url,
            'clone_url': request.clone_url,
            'description': f"Stolen hackathon project: {request.project_name}",
            'stars': 0,
            'forks': 0,
            'topics': [],
            'language': 'Unknown',
            'created_at': '',
            'updated_at': ''
        }
        
        status_tracker.update_task("clone_project", 30, "Initiating git clone...")
        
        # Attempt to clone
        clone_success = agents['cloner'].clone_project(project_data)
        
        if clone_success:
            status_tracker.update_task("clone_project", 80, "Saving project metadata...")
            
            # Save project metadata for the IDE
            location = os.path.join(EnhancedConfig.CLONE_DIRECTORY, request.project_name)
            metadata_path = os.path.join(location, '.chameleon_metadata.json')
            
            # Try to get enhanced metadata by searching for the project
            try:
                # Use search to find more details about this project
                search_results = agents['search'].execute([])
                matching_project = None
                
                for project in search_results[:20]:  # Check first 20 results
                    if project['name'].lower() == request.project_name.lower():
                        matching_project = project
                        break
                
                if matching_project:
                    metadata = {
                        'name': request.project_name,
                        'description': matching_project.get('description', 'No description available'),
                        'stars': matching_project.get('stars', 0),
                        'forks': matching_project.get('forks', 0),
                        'language': matching_project.get('language', 'Unknown'),
                        'url': request.project_url,
                        'topics': matching_project.get('topics', []),
                        'cloned_at': datetime.now().isoformat()
                    }
                else:
                    # Fallback metadata
                    metadata = {
                        'name': request.project_name,
                        'description': f"Hackathon project: {request.project_name}",
                        'stars': 0,
                        'forks': 0,
                        'language': 'Unknown',
                        'url': request.project_url,
                        'topics': [],
                        'cloned_at': datetime.now().isoformat()
                    }
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
            except Exception as e:
                print(f"⚠️ Failed to save metadata: {e}")
            
            # Trigger file analysis in the background
            print(f"🚀 Triggering file analysis for {request.project_name} at {location}")
            status_tracker.add_output_line(f"🚀 Scheduling file analysis for {request.project_name}...")
            
            background_tasks.add_task(
                run_file_analysis_async,
                request.project_name,
                location
            )
            
            status_tracker.complete_task("clone_project", f"Successfully cloned {request.project_name}")
            status_tracker.clear_current_operation()
            
            return CloneResponse(
                success=True,
                message=f"Successfully stole {request.project_name}! 🎉",
                location=location
            )
        else:
            status_tracker.fail_task("clone_project", "Clone failed", f"Failed to clone {request.project_name}")
            status_tracker.clear_current_operation()
            
            return CloneResponse(
                success=False,
                message=f"Failed to steal {request.project_name}. Maybe it's too well protected! 😅"
            )
            
    except Exception as e:
        print(f"❌ Error in clone endpoint: {e}")
        status_tracker.fail_task("clone_project", str(e), f"Clone failed: {str(e)}")
        status_tracker.clear_current_operation()
        return CloneResponse(
            success=False,
            message=f"Heist failed: {str(e)}"
        ) 