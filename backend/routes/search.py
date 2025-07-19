"""
Search routes for the Chameleon Hackathon Discovery API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from models import TechnologySearchRequest, ProjectSearchResponse, ProjectInfo
from core.enhanced_config import EnhancedConfig
from utils.status_tracker import get_global_tracker
from services.helpers import (
    _extract_technologies,
    _get_readme_fallback,
    _calculate_simple_complexity,
    _get_innovation_indicators
)

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=ProjectSearchResponse)
async def search_projects(request: TechnologySearchRequest):
    """Search for hackathon projects and return 5 for human selection"""
    try:
        from app import agents  # Import agents from main app
        status_tracker = get_global_tracker()
        
        status_tracker.set_current_operation("Searching for hackathon projects")
        
        # Create search task
        search_task = status_tracker.create_task(
            "search_projects",
            "Search for hackathon projects",
            f"Searching for projects with technologies: {request.technologies}"
        )
        
        status_tracker.start_task("search_projects")
        
        print(f"🔍 Searching for projects with technologies: {request.technologies}")
        
        # Search for projects using the search agent
        status_tracker.update_task("search_projects", 20, "Executing search queries...")
        raw_projects = agents['search'].execute(request.technologies)
        
        if not raw_projects:
            status_tracker.fail_task("search_projects", "No projects found", "No hackathon projects found matching the criteria")
            raise HTTPException(status_code=404, detail="No hackathon projects found matching the criteria")
        
        # Take top 5 projects for human selection
        top_projects = raw_projects[:5]
        
        # Analyze each project to get detailed information
        analyzed_projects = []
        total_projects = len(top_projects)
        
        for i, project in enumerate(top_projects):
            try:
                progress = 20 + (i + 1) / total_projects * 60
                status_tracker.update_task("search_projects", progress, f"Analyzing project: {project.get('name', 'Unknown')}")
                
                print(f"📊 Analyzing project: {project.get('name', 'Unknown')}")
                
                # Use validator agent to get detailed analysis including README
                detailed_analysis = agents['validator']._analyze_project_deeply(project, request.technologies)
                
                if detailed_analysis:
                    readme_content = detailed_analysis.get('readme_content', '')
                    if not readme_content:
                        readme_content = _get_readme_fallback(project)
                else:
                    readme_content = _get_readme_fallback(project)
                
                # Get basic project info
                project_info = ProjectInfo(
                    name=project.get('name', 'Unknown'),
                    description=project.get('description', 'No description available'),
                    technologies=_extract_technologies(project, request.technologies),
                    readme=readme_content,
                    stars=project.get('stars', 0),
                    forks=project.get('forks', 0),
                    language=project.get('language', 'Unknown'),
                    url=project.get('html_url', ''),
                    complexity_score=_calculate_simple_complexity(project, detailed_analysis),
                    innovation_indicators=_get_innovation_indicators(project, detailed_analysis)
                )
                analyzed_projects.append(project_info)
                
            except Exception as e:
                print(f"⚠️ Error analyzing project {project.get('name', 'Unknown')}: {e}")
                # Add fallback project info
                try:
                    project_info = ProjectInfo(
                        name=project.get('name', 'Unknown'),
                        description=project.get('description', 'No description available'),
                        technologies=_extract_technologies(project, request.technologies),
                        readme=_get_readme_fallback(project),
                        stars=project.get('stars', 0),
                        forks=project.get('forks', 0),
                        language=project.get('language', 'Unknown'),
                        url=project.get('html_url', ''),
                        complexity_score=_calculate_simple_complexity(project),
                        innovation_indicators=_get_innovation_indicators(project)
                    )
                    analyzed_projects.append(project_info)
                except Exception as fallback_error:
                    print(f"❌ Failed to create fallback info for {project.get('name', 'Unknown')}: {fallback_error}")
                    continue
        
        if not analyzed_projects:
            status_tracker.fail_task("search_projects", "Analysis failed", "Failed to analyze any projects")
            raise HTTPException(status_code=500, detail="Failed to analyze any projects")
        
        status_tracker.complete_task("search_projects", f"Found and analyzed {len(analyzed_projects)} projects")
        status_tracker.clear_current_operation()
        
        return ProjectSearchResponse(
            projects=analyzed_projects,
            total_found=len(raw_projects),
            search_technologies=request.technologies
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in search endpoint: {e}")
        status_tracker.fail_task("search_projects", str(e), f"Search failed: {str(e)}")
        status_tracker.clear_current_operation()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 