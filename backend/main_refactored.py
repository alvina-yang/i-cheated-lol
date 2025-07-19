#!/usr/bin/env python3
"""
Chameleon Hackathon Project Discovery System - Refactored FastAPI Backend

Refactored FastAPI backend with organized AI agents and enhanced features.
"""

import os
import sys
import json
import tempfile
import subprocess
from typing import List, Optional, Dict, Union, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
import time

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import enhanced components
from core.enhanced_config import EnhancedConfig
from agents.search_agent import TechnologyProjectSearchAgent
from agents.validator_agent import ValidatorAgent
from agents.commit_agent import CommitAgent
from agents.code_modifier_agent import CodeModifierAgent
from agents.git_agent import GitAgent
from utils.project_cloner import GitHubCloner
from utils.status_tracker import StatusTracker, get_global_tracker, initialize_status_tracking

# Request/Response Models
class TechnologySearchRequest(BaseModel):
    technologies: List[str] = []

class ProjectInfo(BaseModel):
    name: str
    description: str
    technologies: List[str]
    readme: str
    stars: int
    forks: int
    language: str
    url: str
    complexity_score: int
    innovation_indicators: List[str]

class ProjectSearchResponse(BaseModel):
    projects: List[ProjectInfo]
    total_found: int
    search_technologies: List[str]

class CloneRequest(BaseModel):
    project_name: str
    project_url: str
    clone_url: str

class CloneResponse(BaseModel):
    success: bool
    message: str
    location: Optional[str] = None

class EnhancedUntraceabilityRequest(BaseModel):
    hackathon_date: str  # YYYY-MM-DD format
    hackathon_start_time: str  # HH:MM format
    hackathon_duration: int = 48  # Duration in hours
    git_username: str
    git_email: str
    target_repository_url: str = ""
    add_comments: bool = True
    add_documentation: bool = False
    generate_commit_messages: bool = True
    show_terminal_output: bool = True

class EnhancedUntraceabilityResponse(BaseModel):
    success: bool
    message: str
    commits_modified: int = 0
    files_modified: int = 0
    status_tracking_id: str = ""

class SettingsUpdateRequest(BaseModel):
    setting_type: str  # 'user', 'repository', 'processing', 'terminal'
    settings: Dict[str, Union[str, bool, int, float]]

class SettingsResponse(BaseModel):
    success: bool
    message: str
    settings: Dict[str, Union[str, bool, int, float]] = {}

class StatusResponse(BaseModel):
    current_operation: Optional[str] = None
    tasks: List[Dict[str, Any]] = []
    recent_output: List[str] = []
    summary: Dict[str, Any] = {}

# Global instances
agents = {}
status_tracker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global agents, status_tracker
    
    try:
        # Initialize configuration
        EnhancedConfig.initialize()
        EnhancedConfig.validate()
        
        # Initialize status tracking
        status_tracker = initialize_status_tracking(
            enable_real_time=EnhancedConfig.ENABLE_REAL_TIME_OUTPUT,
            update_interval=1.0
        )
        
        # Initialize agents
        agents = {
            'search': TechnologyProjectSearchAgent(),
            'validator': ValidatorAgent(),
            'commit': CommitAgent(),
            'code_modifier': CodeModifierAgent(),
            'git': GitAgent(),
            'cloner': GitHubCloner()
        }
        
        print("🚀 Chameleon API Backend initialized successfully!")
        yield
        
    except Exception as e:
        print(f"❌ Failed to initialize backend: {e}")
        raise
    finally:
        # Cleanup
        if status_tracker:
            status_tracker.stop()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Chameleon Hackathon Discovery API",
    description="Enhanced API for discovering and transforming hackathon projects",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Enhanced Chameleon Hackathon Discovery API",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "AI-generated commit messages",
            "Real-time terminal output",
            "Enhanced code modification",
            "Configurable repository destinations",
            "Progress tracking"
        ]
    }


@app.post("/api/search", response_model=ProjectSearchResponse)
async def search_projects(request: TechnologySearchRequest):
    """Search for hackathon projects and return 5 for human selection"""
    try:
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


@app.post("/api/clone", response_model=CloneResponse)
async def clone_project(request: CloneRequest):
    """Clone the selected project to local filesystem"""
    try:
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


@app.post("/api/project/{project_name}/make-untraceable", response_model=EnhancedUntraceabilityResponse)
async def make_project_untraceable(project_name: str, request: EnhancedUntraceabilityRequest, background_tasks: BackgroundTasks):
    """
    Enhanced version: Make a project untraceable using AI agents with real-time progress tracking
    """
    try:
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
            add_comments=request.add_comments,
            add_documentation=request.add_documentation,
            modify_commit_messages=request.generate_commit_messages
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
            _run_untraceable_process,
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


async def _run_untraceable_process(project_name: str, project_path: str, request: EnhancedUntraceabilityRequest, main_task_id: str):
    """Run the untraceable process in the background."""
    try:
        commits_modified = 0
        files_modified = 0
        
        # Add initial terminal output
        status_tracker.add_output_line(f"🚀 Starting untraceable process for {project_name}", "system")
        status_tracker.add_output_line(f"📂 Project path: {project_path}", "system")
        status_tracker.add_output_line(f"👤 Developer: {request.git_username} <{request.git_email}>", "system")
        status_tracker.add_output_line(f"⏰ Hackathon duration: {request.hackathon_duration} hours", "system")
        status_tracker.add_output_line(f"📅 Hackathon start: {request.hackathon_date} {request.hackathon_start_time}", "system")
        
        # Step 1: Repository setup if target URL is provided
        if request.target_repository_url:
            repo_task = status_tracker.create_task(
                f"repo_setup_{project_name}",
                "Setup repository destination",
                f"Configuring repository destination: {request.target_repository_url}"
            )
            
            status_tracker.start_task(repo_task.id)
            status_tracker.update_task(main_task_id, 10, "Setting up repository destination...")
            
            # Use git agent to setup repository
            repo_result = agents['git'].execute({
                "task_type": "setup_repository",
                "project_path": project_path,
                "original_url": "",  # Will be detected
                "target_url": request.target_repository_url,
                "user_preferences": EnhancedConfig.get_user_settings().to_dict()
            })
            
            if repo_result["success"]:
                status_tracker.complete_task(repo_task.id, "Repository destination configured")
            else:
                status_tracker.fail_task(repo_task.id, repo_result["message"], "Repository setup failed")
        
        # Step 2: Code modification
        if request.add_comments or request.add_documentation:
            status_tracker.add_output_line("🔧 Starting code modification with AI enhancements...", "system")
            
            code_task = status_tracker.create_task(
                f"code_mod_{project_name}",
                "Modify code files",
                "Analyzing and modifying code files..."
            )
            
            status_tracker.start_task(code_task.id)
            status_tracker.update_task(main_task_id, 30, "Modifying code files...")
            
            # Determine modifications to apply
            modifications = []
            if request.add_comments:
                modifications.append("comments")
            if request.add_documentation:
                modifications.append("documentation")
            
            # Use code modifier agent
            code_result = agents['code_modifier'].execute({
                "task_type": "modify_project",
                "project_path": project_path,
                "modifications": modifications
            })
            
            if code_result["success"]:
                files_modified = code_result.get("files_modified", 0)
                status_tracker.complete_task(code_task.id, f"Modified {files_modified} files")
            else:
                status_tracker.fail_task(code_task.id, code_result["message"], "Code modification failed")
        
        # Step 3: Git history rewriting with AI-generated commit messages
        if request.generate_commit_messages:
            status_tracker.add_output_line("🔄 Starting git history rewriting with AI-generated commits...", "system")
            
            git_task = status_tracker.create_task(
                f"git_history_{project_name}",
                "Rewrite git history",
                "Generating AI commit messages and rewriting history..."
            )
            
            status_tracker.start_task(git_task.id)
            status_tracker.update_task(main_task_id, 60, "Rewriting git history with AI...")
            
            # Parse hackathon start time
            hackathon_start = datetime.strptime(f"{request.hackathon_date} {request.hackathon_start_time}", "%Y-%m-%d %H:%M")
            status_tracker.add_output_line(f"🕒 Hackathon timeline: {hackathon_start} to {hackathon_start + timedelta(hours=request.hackathon_duration)}", "system")
            
            # Use commit agent to create hackathon history
            commit_result = agents['commit'].execute({
                "task_type": "create_history",
                "project_path": project_path,
                "project_name": project_name,
                "project_description": f"Hackathon project: {project_name}",
                "technologies": [],  # Will be detected
                "hackathon_start": hackathon_start,
                "hackathon_duration": request.hackathon_duration,
                "developer_name": request.git_username,
                "developer_email": request.git_email
            })
            
            if commit_result["success"]:
                commits_modified = commit_result.get("commits_created", 0)
                status_tracker.complete_task(git_task.id, f"Created {commits_modified} AI-generated commits")
            else:
                status_tracker.fail_task(git_task.id, commit_result["message"], "Git history rewriting failed")
        
        # Step 4: Final commit if files were modified
        if files_modified > 0:
            final_task = status_tracker.create_task(
                f"final_commit_{project_name}",
                "Final commit",
                "Creating final commit with changes..."
            )
            
            status_tracker.start_task(final_task.id)
            status_tracker.update_task(main_task_id, 90, "Creating final commit...")
            
            # Create final commit with AI-generated message
            try:
                os.chdir(project_path)
                
                # Generate commit message using AI
                commit_messages = agents['commit'].generate_commit_messages(
                    project_name, [], f"{files_modified} files", "feature", "hackathon"
                )
                
                final_commit_message = commit_messages[0] if commit_messages else "feat: enhance project for hackathon submission"
                
                # Add and commit changes
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', final_commit_message], check=True)
                
                status_tracker.complete_task(final_task.id, "Final commit created successfully")
                
            except subprocess.CalledProcessError as e:
                status_tracker.fail_task(final_task.id, str(e), "Final commit failed")
        
        # Complete main task
        status_tracker.add_output_line("🎉 Untraceable process completed successfully!", "system")
        status_tracker.add_output_line(f"📊 Summary: Modified {commits_modified} commits and {files_modified} files", "system")
        status_tracker.add_output_line(f"✅ {project_name} is now ready for your hackathon submission!", "system")
        
        status_tracker.update_task(main_task_id, 100, "Untraceable process completed successfully")
        status_tracker.complete_task(
            main_task_id,
            f"Successfully made {project_name} untraceable! Modified {commits_modified} commits and {files_modified} files."
        )
        
        status_tracker.clear_current_operation()
        
    except Exception as e:
        print(f"❌ Error in untraceable process: {e}")
        status_tracker.fail_task(main_task_id, str(e), f"Untraceable process failed: {str(e)}")
        status_tracker.clear_current_operation()


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current status of operations and tasks"""
    try:
        summary = status_tracker.get_status_summary()
        tasks = status_tracker.get_all_tasks()
        recent_output = status_tracker.get_recent_output(20)
        
        return StatusResponse(
            current_operation=summary["current_operation"],
            tasks=tasks,
            recent_output=recent_output,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@app.get("/api/status/stream")
async def stream_status():
    """Stream real-time status updates"""
    async def generate():
        while True:
            try:
                summary = status_tracker.get_status_summary()
                tasks = status_tracker.get_active_tasks()
                recent_output = status_tracker.get_recent_output(5)
                
                data = {
                    "current_operation": summary["current_operation"],
                    "tasks": tasks,
                    "recent_output": recent_output,
                    "timestamp": datetime.now().isoformat()
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(1)
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/api/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """Update system settings"""
    try:
        success = False
        
        if request.setting_type == "user":
            success = EnhancedConfig.update_user_settings(**request.settings)
        elif request.setting_type == "repository":
            success = EnhancedConfig.update_repository_settings(**request.settings)
        elif request.setting_type == "processing":
            success = EnhancedConfig.update_processing_settings(**request.settings)
        elif request.setting_type == "terminal":
            success = EnhancedConfig.update_terminal_settings(**request.settings)
        else:
            raise HTTPException(status_code=400, detail="Invalid setting type")
        
        if success:
            return SettingsResponse(
                success=True,
                message=f"Updated {request.setting_type} settings successfully",
                settings=request.settings
            )
        else:
            return SettingsResponse(
                success=False,
                message=f"Failed to update {request.setting_type} settings"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")


@app.get("/api/settings")
async def get_settings():
    """Get all current settings"""
    try:
        return EnhancedConfig.get_all_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")


# Add these endpoints before the helper functions

@app.get("/api/project/{project_name}/terminal-output")
async def get_terminal_output(project_name: str):
    """Get terminal output for a project"""
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get recent output from status tracker
        recent_output = status_tracker.get_recent_output(100)
        
        # Filter output related to this project
        project_output = [
            line for line in recent_output 
            if project_name in line or "git" in line.lower()
        ]
        
        return {
            "project_name": project_name,
            "output": project_output,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting terminal output: {str(e)}")


@app.get("/api/project/{project_name}/stream-terminal")
async def stream_terminal_output(project_name: str):
    """Stream real-time terminal output for a project"""
    async def generate():
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            yield f"data: {json.dumps({'error': 'Project not found'})}\n\n"
            return
        
        last_output_count = 0
        
        while True:
            try:
                # Get recent output
                recent_output = status_tracker.get_recent_output(100)
                
                # Send new output lines
                if len(recent_output) > last_output_count:
                    new_lines = recent_output[last_output_count:]
                    
                    # Send all new lines (no filtering) - let frontend handle display
                    if new_lines:
                        data = {
                            "project_name": project_name,
                            "new_lines": new_lines,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        yield f"data: {json.dumps(data)}\n\n"
                    
                    last_output_count = len(recent_output)
                
                await asyncio.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/api/project/{project_name}/execute-git-command")
async def execute_git_command(project_name: str, command: dict):
    """Execute a git command and stream output"""
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate command
        git_command = command.get("command", "").strip()
        if not git_command.startswith("git "):
            raise HTTPException(status_code=400, detail="Only git commands are allowed")
        
        # Create execution task
        task_id = f"git_cmd_{project_name}_{int(time.time())}"
        exec_task = status_tracker.create_task(
            task_id,
            f"Execute git command: {git_command}",
            f"Running {git_command} in {project_name}"
        )
        
        status_tracker.start_task(task_id)
        status_tracker.set_current_operation(f"Executing git command in {project_name}")
        
        # Execute command using git agent
        cmd_parts = git_command.split()
        
        def progress_callback(progress, line):
            status_tracker.update_task(task_id, progress, f"Git: {line}")
            status_tracker.add_output_line(line, "git")
        
        try:
            # Stream command output
            output_lines = []
            for line in agents['git'].stream_git_output(project_path, cmd_parts):
                output_lines.append(line)
                status_tracker.add_output_line(line, "git")
                
                # Update progress
                progress = min(100, len(output_lines) * 10)  # Rough progress estimation
                status_tracker.update_task(task_id, progress, f"Git: {line}")
            
            status_tracker.complete_task(task_id, f"Git command completed successfully")
            status_tracker.clear_current_operation()
            
            return {
                "success": True,
                "command": git_command,
                "output": output_lines,
                "task_id": task_id
            }
            
        except Exception as e:
            status_tracker.fail_task(task_id, str(e), f"Git command failed: {str(e)}")
            status_tracker.clear_current_operation()
            
            return {
                "success": False,
                "command": git_command,
                "error": str(e),
                "task_id": task_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing git command: {str(e)}")


@app.get("/api/project/{project_name}/file-changes")
async def get_file_changes(project_name: str):
    """Get file changes for a project"""
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get git status
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    changes.append({
                        "status": status,
                        "filename": filename,
                        "type": _get_change_type(status)
                    })
            
            return {
                "project_name": project_name,
                "changes": changes,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError:
            return {
                "project_name": project_name,
                "changes": [],
                "error": "Not a git repository or git command failed"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file changes: {str(e)}")


@app.get("/api/project/{project_name}/monitor-changes")
async def monitor_file_changes(project_name: str):
    """Monitor file changes in real-time"""
    async def generate():
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            yield f"data: {json.dumps({'error': 'Project not found'})}\n\n"
            return
        
        # Start file monitoring
        def change_callback(changed_files):
            data = {
                "project_name": project_name,
                "changed_files": changed_files,
                "timestamp": datetime.now().isoformat()
            }
            # Note: This would need to be handled differently in a real async context
            # For now, we'll just log it
            status_tracker.add_output_line(f"File changes detected: {len(changed_files)} files", "filesystem")
        
        monitor_result = agents['git'].execute({
            "task_type": "monitor_changes",
            "project_path": project_path,
            "change_callback": change_callback
        })
        
        if not monitor_result["success"]:
            yield f"data: {json.dumps({'error': monitor_result['message']})}\n\n"
            return
        
        # Stream file changes
        last_check = datetime.now()
        
        while True:
            try:
                # Get recent file system output
                recent_output = status_tracker.get_recent_output(10)
                fs_output = [line for line in recent_output if "filesystem" in line]
                
                if fs_output:
                    data = {
                        "project_name": project_name,
                        "monitoring_active": True,
                        "recent_changes": fs_output,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/api/project/{project_name}/files")
async def get_project_files(project_name: str):
    """
    Get the file structure and metadata for a cloned project
    """
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Read project metadata if available
        metadata_path = os.path.join(project_path, '.chameleon_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Build file tree
        files = _build_file_tree(project_path, project_path)
        
        # Get README content if available
        readme_content = _get_project_readme(project_path)
        
        project_data = {
            "name": project_name,
            "description": metadata.get('description', 'No description available'),
            "technologies": _extract_project_technologies(project_path),
            "stars": metadata.get('stars', 0),
            "forks": metadata.get('forks', 0),
            "language": metadata.get('language', 'Unknown'),
            "files": files,
            "readme": readme_content
        }
        
        return project_data
        
    except Exception as e:
        print(f"❌ Error getting project files: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading project files: {str(e)}")


@app.get("/api/project/{project_name}/file")
async def get_project_file(project_name: str, path: str):
    """
    Get the content of a specific file in a project
    """
    try:
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Ensure the file path is within the project directory (security)
        file_path = os.path.join(project_path, path)
        if not file_path.startswith(project_path):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check file size (limit to 1MB for safety)
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # 1MB
            return Response(content="File too large to display", media_type="text/plain")
        
        # Try to read as text file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content=content, media_type="text/plain")
        except UnicodeDecodeError:
            # If it's a binary file, return a message
            return Response(content="Binary file - cannot display content", media_type="text/plain")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


def _build_file_tree(root_path: str, current_path: str, max_depth: int = 10) -> List[Dict]:
    """
    Build a file tree structure for the project
    """
    if max_depth <= 0:
        return []
    
    files = []
    relative_path = os.path.relpath(current_path, root_path)
    
    try:
        items = os.listdir(current_path)
        items.sort()  # Sort alphabetically
        
        # Separate directories and files
        directories = []
        regular_files = []
        
        for item in items:
            # Skip hidden files and common build/cache directories
            if item.startswith('.') and item not in ['.gitignore', '.env.example']:
                continue
            if item in ['node_modules', '__pycache__', '.git', 'venv', 'env', 'dist', 'build']:
                continue
                
            item_path = os.path.join(current_path, item)
            item_relative = os.path.join(relative_path, item) if relative_path != '.' else item
            
            if os.path.isdir(item_path):
                directories.append({
                    'name': item,
                    'type': 'directory',
                    'path': item_relative,
                    'children': _build_file_tree(root_path, item_path, max_depth - 1)
                })
            else:
                file_size = os.path.getsize(item_path)
                extension = os.path.splitext(item)[1][1:] if '.' in item else ''
                
                regular_files.append({
                    'name': item,
                    'type': 'file',
                    'path': item_relative,
                    'size': file_size,
                    'extension': extension
                })
        
        # Directories first, then files
        files.extend(directories)
        files.extend(regular_files)
        
    except PermissionError:
        pass  # Skip directories we can't read
    
    return files


def _get_project_readme(project_path: str) -> str:
    """
    Get README content from the project
    """
    readme_files = ['README.md', 'readme.md', 'README.txt', 'README.rst', 'README']
    
    for readme_file in readme_files:
        readme_path = os.path.join(project_path, readme_file)
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Limit README size
                    if len(content) > 50000:  # 50KB limit
                        content = content[:50000] + "\n\n... (README truncated for display)"
                    return content
            except:
                continue
    
    return "No README file found in this project."


def _extract_project_technologies(project_path: str) -> List[str]:
    """
    Extract technologies used in the project based on file extensions and package files
    """
    technologies = set()
    
    # Check for common package files and extract technologies
    package_files = {
        'package.json': ['Node.js', 'JavaScript'],
        'requirements.txt': ['Python'],
        'Pipfile': ['Python'],
        'pom.xml': ['Java', 'Maven'],
        'build.gradle': ['Java', 'Gradle'],
        'Cargo.toml': ['Rust'],
        'go.mod': ['Go'],
        'composer.json': ['PHP'],
        'Gemfile': ['Ruby'],
        'pubspec.yaml': ['Dart', 'Flutter'],
        'CMakeLists.txt': ['C++', 'CMake'],
        'Makefile': ['C/C++', 'Make']
    }
    
    for package_file, techs in package_files.items():
        if os.path.exists(os.path.join(project_path, package_file)):
            technologies.update(techs)
    
    # Check for common file extensions
    extension_map = {
        '.js': 'JavaScript',
        '.jsx': 'React',
        '.ts': 'TypeScript',
        '.tsx': 'React/TypeScript',
        '.py': 'Python',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.dart': 'Dart',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.vue': 'Vue.js',
        '.svelte': 'Svelte'
    }
    
    # Walk through files and detect technologies
    for root, dirs, files in os.walk(project_path):
        # Skip hidden and build directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env', 'dist', 'build']]
        
        for file in files[:50]:  # Limit to first 50 files for performance
            _, ext = os.path.splitext(file)
            if ext in extension_map:
                technologies.add(extension_map[ext])
    
    return list(technologies)


def _get_change_type(status: str) -> str:
    """Get human-readable change type from git status"""
    if status.startswith(' M'):
        return "modified"
    elif status.startswith(' A'):
        return "added"
    elif status.startswith(' D'):
        return "deleted"
    elif status.startswith(' R'):
        return "renamed"
    elif status.startswith(' C'):
        return "copied"
    elif status.startswith('??'):
        return "untracked"
    elif status.startswith('!!'):
        return "ignored"
    else:
        return "unknown"


# Helper functions (moved from original main.py)
def _extract_technologies(project: dict, search_technologies: List[str]) -> List[str]:
    """Extract technologies from project data"""
    detected_technologies = []
    
    # Check language
    if project.get('language'):
        detected_technologies.append(project['language'])
    
    # Check topics
    topics = project.get('topics', [])
    for topic in topics:
        if any(tech.lower() in topic.lower() for tech in search_technologies):
            detected_technologies.append(topic)
    
    # Check description
    description = project.get('description', '').lower()
    for tech in search_technologies:
        if tech.lower() in description:
            detected_technologies.append(tech)
    
    return list(set(detected_technologies))


def _get_readme_fallback(project: dict) -> str:
    """Get fallback README content"""
    return f"""# {project.get('name', 'Project')}

{project.get('description', 'No description available')}

## Language
{project.get('language', 'Unknown')}

## Repository
{project.get('html_url', 'No URL available')}

## Stats
- Stars: {project.get('stars', 0)}
- Forks: {project.get('forks', 0)}
"""


def _calculate_simple_complexity(project: dict, detailed_analysis: dict = None) -> int:
    """Calculate simple complexity score"""
    complexity = 1
    
    # Base complexity from stars and forks
    stars = project.get('stars', 0)
    forks = project.get('forks', 0)
    
    if stars > 10:
        complexity += 2
    if forks > 5:
        complexity += 2
    
    # Language complexity
    complex_languages = ['rust', 'cpp', 'c++', 'go', 'scala', 'haskell']
    if project.get('language', '').lower() in complex_languages:
        complexity += 2
    
    # Topics complexity
    topics = project.get('topics', [])
    complex_topics = ['ai', 'machine-learning', 'blockchain', 'cryptocurrency', 'deep-learning']
    if any(topic in complex_topics for topic in topics):
        complexity += 3
    
    return min(complexity, 10)


def _get_innovation_indicators(project: dict, detailed_analysis: dict = None) -> List[str]:
    """Get innovation indicators for project"""
    indicators = []
    
    # Check topics for innovation keywords
    topics = project.get('topics', [])
    innovation_topics = ['ai', 'machine-learning', 'blockchain', 'iot', 'ar', 'vr', 'quantum']
    
    for topic in topics:
        if topic in innovation_topics:
            indicators.append(f"Uses {topic.upper()} technology")
    
    # Check description for innovation keywords
    description = project.get('description', '').lower()
    innovation_keywords = ['innovative', 'novel', 'cutting-edge', 'advanced', 'revolutionary']
    
    for keyword in innovation_keywords:
        if keyword in description:
            indicators.append(f"Described as {keyword}")
    
    # Check stars for popularity
    stars = project.get('stars', 0)
    if stars > 50:
        indicators.append("High community interest")
    
    return indicators[:5]  # Limit to 5 indicators


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 