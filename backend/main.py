#!/usr/bin/env python3
"""
Chameleon Hackathon Project Discovery System - FastAPI Backend

FastAPI backend that provides human-in-the-loop project discovery.
Returns 5 projects for human selection instead of auto-selecting.
"""

import os
import sys
import json
import tempfile
import subprocess
import random
import re
from typing import List, Optional, Dict, Union
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from core.config import Config
from agents.search_agent import TechnologyProjectSearchAgent
from agents.validator_agent import ValidatorAgent
from utils.project_cloner import GitHubCloner

app = FastAPI(
    title="Chameleon Hackathon Discovery API",
    description="API for discovering and stealing hackathon projects",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class UntraceabilityRequest(BaseModel):
    hackathon_date: str  # YYYY-MM-DD format
    hackathon_start_time: str  # HH:MM format
    git_username: str
    git_email: str
    add_comments: bool = True
    change_variables: bool = True

class UntraceabilityResponse(BaseModel):
    success: bool
    message: str
    commits_modified: int = 0
    files_modified: int = 0

# Global instances
search_agent = None
validator_agent = None
cloner = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global search_agent, validator_agent, cloner
    
    try:
        Config.validate()
        search_agent = TechnologyProjectSearchAgent()
        validator_agent = ValidatorAgent()
        cloner = GitHubCloner()
        print("🚀 Chameleon API Backend initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize backend: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Chameleon Hackathon Discovery API",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/api/search", response_model=ProjectSearchResponse)
async def search_projects(request: TechnologySearchRequest):
    """
    Search for hackathon projects and return 5 for human selection
    """
    try:
        print(f"🔍 Searching for projects with technologies: {request.technologies}")
        
        # Search for projects using the search agent
        raw_projects = search_agent.execute(request.technologies)
        
        if not raw_projects:
            raise HTTPException(status_code=404, detail="No hackathon projects found matching the criteria")
        
        # Take top 5 projects for human selection
        top_projects = raw_projects[:5]
        
        # Analyze each project to get detailed information
        analyzed_projects = []
        
        for project in top_projects:
            try:
                print(f"📊 Analyzing project: {project.get('name', 'Unknown')}")
                
                # Use validator agent to get detailed analysis including README
                detailed_analysis = validator_agent._analyze_project_deeply(project, request.technologies)
                
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
                # Fallback to basic info if detailed analysis fails
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
            raise HTTPException(status_code=500, detail="Failed to analyze any projects")
        
        return ProjectSearchResponse(
            projects=analyzed_projects,
            total_found=len(raw_projects),
            search_technologies=request.technologies
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/clone", response_model=CloneResponse)
async def clone_project(request: CloneRequest):
    """
    Clone the selected project to local filesystem
    """
    try:
        print(f"📥 Cloning project: {request.project_name}")
        
        # Create a project dict for the cloner
        project_data = {
            'name': request.project_name,
            'html_url': request.project_url,
            'clone_url': request.clone_url,
            'description': f"Stolen hackathon project: {request.project_name}",
            'stars': 0,  # We don't have this info in the clone request
            'forks': 0,
            'topics': [],
            'language': 'Unknown',
            'created_at': '',
            'updated_at': ''
        }
        
        # Attempt to clone
        clone_success = cloner.clone_project(project_data)
        
        if clone_success:
            # Save project metadata for the IDE
            location = os.path.join(Config.CLONE_DIRECTORY, request.project_name)
            metadata_path = os.path.join(location, '.chameleon_metadata.json')
            
            # Try to get enhanced metadata by searching for the project
            try:
                # Use search to find more details about this project
                search_results = search_agent.execute([])
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
            
            return CloneResponse(
                success=True,
                message=f"Successfully stole {request.project_name}! 🎉",
                location=location
            )
        else:
            return CloneResponse(
                success=False,
                message=f"Failed to steal {request.project_name}. Maybe it's too well protected! 😅"
            )
            
    except Exception as e:
        print(f"❌ Error in clone endpoint: {e}")
        return CloneResponse(
            success=False,
            message=f"Heist failed: {str(e)}"
        )

@app.post("/api/project/{project_name}/make-untraceable", response_model=UntraceabilityResponse)
async def make_project_untraceable(project_name: str, request: UntraceabilityRequest):
    """
    Make a project untraceable by rewriting git history, adding comments, and changing variables
    """
    try:
        project_path = os.path.join(Config.CLONE_DIRECTORY, project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        print(f"🕵️‍♂️ Making {project_name} untraceable...")
        
        commits_modified = 0
        files_modified = 0
        
        # Step 1: Rewrite git history
        commits_modified = _rewrite_git_history(
            project_path, 
            request.hackathon_date, 
            request.hackathon_start_time,
            request.git_username,
            request.git_email
        )
        
        # Step 2: Add comments to code files (if requested)
        if request.add_comments:
            files_modified += _add_ai_comments(project_path)
        
        # Step 3: Change variable names (if requested)
        if request.change_variables:
            files_modified += _change_variable_names(project_path)
        
        # Step 4: Commit the changes if any files were modified
        if files_modified > 0:
            _commit_changes(project_path, request.git_username, request.git_email)
        
        return UntraceabilityResponse(
            success=True,
            message=f"Successfully made {project_name} untraceable! Modified {commits_modified} commits and {files_modified} files.",
            commits_modified=commits_modified,
            files_modified=files_modified
        )
        
    except Exception as e:
        print(f"❌ Error making project untraceable: {e}")
        raise HTTPException(status_code=500, detail=f"Error making project untraceable: {str(e)}")

def _rewrite_git_history(project_path: str, hackathon_date: str, start_time: str, username: str, email: str) -> int:
    """
    Rewrite git history to make commits appear as if they were made during a hackathon
    """
    try:
        os.chdir(project_path)
        
        # Get list of all commits
        result = subprocess.run(['git', 'rev-list', '--all', '--count'], 
                              capture_output=True, text=True, check=True)
        total_commits = int(result.stdout.strip())
        
        if total_commits == 0:
            return 0
        
        # Parse hackathon start datetime
        hackathon_start = datetime.strptime(f"{hackathon_date} {start_time}", "%Y-%m-%d %H:%M")
        
        # Create filter-branch script to rewrite commit dates
        filter_script = f"""
#!/bin/bash
export GIT_AUTHOR_NAME="{username}"
export GIT_AUTHOR_EMAIL="{email}"
export GIT_COMMITTER_NAME="{username}"
export GIT_COMMITTER_EMAIL="{email}"

# Calculate random but sequential timestamps within hackathon timeframe
commit_count=$(git rev-list --all --count)
current_commit=$(git rev-list --all | grep -n "$GIT_COMMIT" | cut -d: -f1)

if [ ! -z "$current_commit" ]; then
    # Distribute commits over hackathon period (assuming 48 hours)
    hackathon_duration_seconds=$((48 * 3600))
    commit_interval=$(($hackathon_duration_seconds / $commit_count))
    commit_offset=$(($current_commit * $commit_interval))
    
    # Add some randomness (±30 minutes) while maintaining order
    random_offset=$((RANDOM % 3600 - 1800))
    final_offset=$(($commit_offset + $random_offset))
    
    # Calculate new timestamp
    hackathon_start_timestamp={int(hackathon_start.timestamp())}
    new_timestamp=$(($hackathon_start_timestamp + $final_offset))
    
    export GIT_AUTHOR_DATE="$new_timestamp"
    export GIT_COMMITTER_DATE="$new_timestamp"
fi
"""
        
        # Write filter script
        script_path = os.path.join(project_path, 'filter_script.sh')
        with open(script_path, 'w') as f:
            f.write(filter_script)
        os.chmod(script_path, 0o755)
        
        # Run git filter-branch to rewrite history
        subprocess.run([
            'git', 'filter-branch', '-f', '--env-filter', f'source {script_path}', 'HEAD'
        ], check=True, capture_output=True)
        
        # Clean up
        os.remove(script_path)
        
        return total_commits
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git filter-branch failed: {e}")
        return 0
    except Exception as e:
        print(f"⚠️ Error rewriting git history: {e}")
        return 0

def _add_ai_comments(project_path: str) -> int:
    """
    Add AI-generated comments to code files
    """
    files_modified = 0
    
    try:
        # Find code files to modify
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs']
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env', 'dist', 'build']]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Add comments based on file type
                        modified_content = _inject_comments(content, file)
                        
                        if modified_content != content:
                            # Write modified content back
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(modified_content)
                            files_modified += 1
                            
                    except Exception as e:
                        print(f"⚠️ Failed to add comments to {file_path}: {e}")
                        continue
    
    except Exception as e:
        print(f"⚠️ Error adding AI comments: {e}")
    
    return files_modified

def _inject_comments(content: str, filename: str) -> str:
    """
    Inject realistic comments into code based on file type
    """
    if filename.endswith('.py'):
        return _inject_python_comments(content)
    elif filename.endswith(('.js', '.ts', '.jsx', '.tsx')):
        return _inject_javascript_comments(content)
    elif filename.endswith(('.java', '.cpp', '.c')):
        return _inject_c_style_comments(content)
    else:
        return content

def _inject_python_comments(content: str) -> str:
    """Add Python-style comments"""
    lines = content.split('\n')
    modified_lines = []
    
    comments = [
        "# Initialize the main functionality",
        "# Process the input data",
        "# Validate the parameters",
        "# Optimize performance for large datasets",
        "# Handle edge cases appropriately",
        "# Implement error handling",
        "# Configure default settings",
        "# Parse the response data"
    ]
    
    for i, line in enumerate(lines):
        modified_lines.append(line)
        
        # Add comments before function definitions
        if line.strip().startswith('def ') and random.random() < 0.3:
            indent = len(line) - len(line.lstrip())
            comment = ' ' * indent + random.choice(comments)
            modified_lines.insert(-1, comment)
        
        # Add comments before class definitions
        elif line.strip().startswith('class ') and random.random() < 0.4:
            indent = len(line) - len(line.lstrip())
            comment = ' ' * indent + "# Define the main class structure"
            modified_lines.insert(-1, comment)
    
    return '\n'.join(modified_lines)

def _inject_javascript_comments(content: str) -> str:
    """Add JavaScript-style comments"""
    lines = content.split('\n')
    modified_lines = []
    
    comments = [
        "// Initialize component state",
        "// Handle user interactions",
        "// Validate input data",
        "// Optimize rendering performance",
        "// Configure API endpoints",
        "// Process the response",
        "// Update the UI accordingly",
        "// Implement business logic"
    ]
    
    for line in lines:
        modified_lines.append(line)
        
        # Add comments before function declarations
        if ('function ' in line or '=>' in line or line.strip().startswith('const ')) and random.random() < 0.3:
            indent = len(line) - len(line.lstrip())
            comment = ' ' * indent + random.choice(comments)
            modified_lines.insert(-1, comment)
    
    return '\n'.join(modified_lines)

def _inject_c_style_comments(content: str) -> str:
    """Add C-style comments"""
    lines = content.split('\n')
    modified_lines = []
    
    comments = [
        "// Initialize variables",
        "// Process input parameters",
        "// Allocate memory resources",
        "// Implement core algorithm",
        "// Handle error conditions",
        "// Optimize performance",
        "// Clean up resources",
        "// Return result"
    ]
    
    for line in lines:
        modified_lines.append(line)
        
        # Add comments before function definitions
        if (line.strip().endswith('{') and '(' in line) and random.random() < 0.3:
            indent = len(line) - len(line.lstrip())
            comment = ' ' * indent + random.choice(comments)
            modified_lines.insert(-1, comment)
    
    return '\n'.join(modified_lines)

def _change_variable_names(project_path: str) -> int:
    """
    Change variable names to make code look different
    """
    files_modified = 0
    
    # Common variable mappings
    variable_mappings = {
        'data': 'payload',
        'result': 'output',
        'response': 'reply',
        'request': 'req',
        'config': 'settings',
        'options': 'opts',
        'parameter': 'param',
        'value': 'val',
        'index': 'idx',
        'count': 'cnt',
        'total': 'sum',
        'item': 'element',
        'list': 'array',
        'dict': 'mapping',
        'temp': 'tmp',
        'message': 'msg',
        'error': 'err',
        'success': 'ok'
    }
    
    try:
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env', 'dist', 'build']]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        modified_content = content
                        
                        # Apply variable mappings
                        for old_var, new_var in variable_mappings.items():
                            # Use regex to replace whole words only
                            pattern = r'\b' + re.escape(old_var) + r'\b'
                            modified_content = re.sub(pattern, new_var, modified_content)
                        
                        if modified_content != content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(modified_content)
                            files_modified += 1
                            
                    except Exception as e:
                        print(f"⚠️ Failed to change variables in {file_path}: {e}")
                        continue
    
    except Exception as e:
        print(f"⚠️ Error changing variable names: {e}")
    
    return files_modified

def _commit_changes(project_path: str, username: str, email: str):
    """
    Commit the changes made during untraceability process
    """
    try:
        os.chdir(project_path)
        
        # Configure git user
        subprocess.run(['git', 'config', 'user.name', username], check=True)
        subprocess.run(['git', 'config', 'user.email', email], check=True)
        
        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit with a realistic message
        commit_messages = [
            "Refactor code and add documentation",
            "Improve code readability and performance",
            "Add comments and optimize variables",
            "Enhance code structure and maintainability",
            "Update implementation with better practices"
        ]
        
        commit_message = random.choice(commit_messages)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to commit changes: {e}")
    except Exception as e:
        print(f"⚠️ Error committing changes: {e}")

def _extract_technologies(project: dict, search_technologies: List[str]) -> List[str]:
    """Extract technologies from project data"""
    technologies = []
    
    # Add the language if available
    if project.get('language'):
        technologies.append(project['language'])
    
    # Add topics that match technologies
    topics = project.get('topics', [])
    for topic in topics:
        if any(tech.lower() in topic.lower() for tech in search_technologies):
            technologies.append(topic)
    
    # Add search technologies that appear in description
    description = project.get('description', '').lower()
    for tech in search_technologies:
        if tech.lower() in description:
            technologies.append(tech)
    
    # Remove duplicates and return
    return list(set(technologies))

def _get_readme_fallback(project: dict) -> str:
    """Get a fallback README when detailed analysis fails"""
    description = project.get('description', '')
    if description:
        return f"# {project.get('name', 'Project')}\n\n{description}\n\nThis is a hackathon project that demonstrates innovative use of technology. Check out the full repository for more details!"
    else:
        return f"# {project.get('name', 'Mystery Project')}\n\nNo description available. This mysterious project awaits your discovery! 🕵️‍♂️\n\nExplore the repository to uncover its secrets."

def _calculate_simple_complexity(project: dict, detailed_analysis: dict = None) -> int:
    """Calculate a simple complexity score based on available data"""
    score = 0
    
    # Use detailed analysis if available
    if detailed_analysis:
        file_count = len(detailed_analysis.get('file_structure', []))
        score += min(file_count // 10, 5)  # Max 5 points from file count
        
        complexity = detailed_analysis.get('code_complexity', 0)
        score += min(complexity // 2, 3)  # Max 3 points from code complexity
        
        doc_quality = detailed_analysis.get('documentation_quality', 0)
        score += min(doc_quality, 2)  # Max 2 points from documentation
    else:
        # Fallback to basic scoring
        stars = project.get('stars', 0)
        if stars > 0:
            score += min(stars // 5, 5)  # Max 5 points from stars
        
        # Add points for description length
        description = project.get('description', '')
        if len(description) > 50:
            score += 2
        elif len(description) > 20:
            score += 1
        
        # Add points for topics
        topics = project.get('topics', [])
        score += min(len(topics), 3)  # Max 3 points from topics
    
    return min(score, 10)  # Cap at 10

def _get_innovation_indicators(project: dict, detailed_analysis: dict = None) -> List[str]:
    """Get innovation indicators from project data"""
    indicators = []
    
    # Use detailed analysis if available
    if detailed_analysis:
        indicators.extend(detailed_analysis.get('innovation_indicators', []))
    
    # Add basic indicators from project metadata
    description = project.get('description', '').lower()
    topics = [topic.lower() for topic in project.get('topics', [])]
    
    innovation_keywords = {
        'ai': 'AI/Machine Learning',
        'machine learning': 'Machine Learning',
        'blockchain': 'Blockchain',
        'ar': 'Augmented Reality',
        'vr': 'Virtual Reality',
        'iot': 'Internet of Things',
        'api': 'API Integration',
        'real-time': 'Real-time Processing',
        'mobile': 'Mobile Development',
        'web': 'Web Development',
        'cloud': 'Cloud Computing'
    }
    
    for keyword, indicator in innovation_keywords.items():
        if keyword in description or any(keyword in topic for topic in topics):
            if indicator not in indicators:
                indicators.append(indicator)
    
    return indicators[:5]  # Limit to 5 indicators

@app.get("/api/project/{project_name}/files")
async def get_project_files(project_name: str):
    """
    Get the file structure and metadata for a cloned project
    """
    try:
        project_path = os.path.join(Config.CLONE_DIRECTORY, project_name)
        
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
        project_path = os.path.join(Config.CLONE_DIRECTORY, project_name)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 