"""
Dependency analysis routes for building project dependency graphs
"""

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from utils.status_tracker import get_global_tracker
from core.enhanced_config import EnhancedConfig

router = APIRouter(prefix="/api/dependency", tags=["dependency-analysis"])


class DependencyAnalysisRequest(BaseModel):
    project_name: str


class DependencyAnalysisResponse(BaseModel):
    success: bool
    message: str
    dependancy_graph: Dict[str, List[str]] = {}
    summary: Dict[str, int] = {}
    visualization: str = ""


@router.post("/analyze", response_model=DependencyAnalysisResponse)
async def analyze_project_dependencies(request: DependencyAnalysisRequest):
    """Analyze a project to build a dependency graph showing imports between files"""
    try:
        from app import agents
        
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, request.project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {request.project_name}")
        
        # Use the DependencyGraphBuilder agent
        dependency_agent = agents['dependency_graph']
        
        task_data = {
            "project_path": project_path
        }
        
        # Build the dependency graph  
        result = dependency_agent.execute(task_data)
        
        if result.get("success", False):
            dependancy_graph = result.get("dependancy_graph", {})
            
            # Generate visualization
            visualization = dependency_agent.get_dependency_graph_visualization(dependancy_graph)
            
            # Save the dependency graph
            graph_file = dependency_agent.save_dependency_graph(project_path, dependancy_graph)
            
            return DependencyAnalysisResponse(
                success=True,
                message=result.get("message", "Dependency analysis completed successfully"),
                dependancy_graph=dependancy_graph,
                summary=result.get("summary", {}),
                visualization=visualization
            )
        else:
            return DependencyAnalysisResponse(
                success=False,
                message=result.get("message", "Failed to analyze dependencies"),
                dependancy_graph={},
                summary={},
                visualization=""
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing dependencies: {str(e)}")


@router.get("/graph/{project_name}", response_model=DependencyAnalysisResponse)
async def get_saved_dependency_graph(project_name: str):
    """Get a previously saved dependency graph for a project"""
    try:
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Check for saved dependency graph
        graph_file = os.path.join(project_path, ".chameleon", "dependency_graph.json")
        if not os.path.exists(graph_file):
            return DependencyAnalysisResponse(
                success=False,
                message="No saved dependency graph found. Run analysis first.",
                dependancy_graph={},
                summary={},
                visualization=""
            )
        
        # Read the saved dependency graph
        try:
            with open(graph_file, 'r', encoding='utf-8') as f:
                dependancy_graph = json.load(f)
            
            # Generate visualization
            from app import agents
            dependency_agent = agents['dependency_graph']
            visualization = dependency_agent.get_dependency_graph_visualization(dependancy_graph)
            
            # Calculate summary
            total_imports = sum(len(imports) for imports in dependancy_graph.values())
            files_with_imports = len([f for f, imports in dependancy_graph.items() if imports])
            
            summary = {
                "total_files_analyzed": len(dependancy_graph),
                "total_imports_found": total_imports,
                "files_with_imports": files_with_imports
            }
            
            return DependencyAnalysisResponse(
                success=True,
                message="Dependency graph loaded successfully",
                dependancy_graph=dependancy_graph,
                summary=summary,
                visualization=visualization
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading saved dependency graph: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dependency graph: {str(e)}")


@router.delete("/graph/{project_name}")
async def delete_dependency_graph(project_name: str):
    """Delete the saved dependency graph for a project"""
    try:
        # Build project path
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        # Validate project exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
        
        # Delete the dependency graph if it exists
        graph_file = os.path.join(project_path, ".chameleon", "dependency_graph.json")
        if os.path.exists(graph_file):
            os.remove(graph_file)
            return {"success": True, "message": "Dependency graph deleted"}
        else:
            return {"success": False, "message": "No dependency graph found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting dependency graph: {str(e)}")


@router.get("/status/{project_name}")
async def get_dependency_analysis_status(project_name: str):
    """Get the status of dependency analysis for a project"""
    try:
        status_tracker = get_global_tracker()
        
        return {
            "success": True,
            "status": status_tracker.get_status_summary(),
            "output_lines": status_tracker.get_recent_output()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}") 