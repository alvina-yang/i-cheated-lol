"""
Background tasks for the Chameleon Hackathon Discovery API
"""

import os
import subprocess
from datetime import datetime, timedelta

from models import EnhancedUntraceabilityRequest
from core.enhanced_config import EnhancedConfig
from utils.status_tracker import get_global_tracker


async def run_untraceable_process(project_name: str, project_path: str, request: EnhancedUntraceabilityRequest, main_task_id: str):
    """Run the untraceable process in the background."""
    try:
        from app import agents  # Import agents from main app
        status_tracker = get_global_tracker()
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
            
            # Use git agent to setup repository (including cloning if target URL provided)
            user_prefs = {
                "git_username": request.git_username or "hackathon-user",
                "git_email": request.git_email or "user@hackathon.local"
            }
            
            repo_result = agents['git'].setup_repository_destination(
                project_path=project_path,
                original_url="",  # Will be detected
                target_url=request.target_repository_url,
                user_preferences=user_prefs
            )
            
            if repo_result["success"]:
                status_tracker.complete_task(repo_task.id, "Repository destination configured")
            else:
                status_tracker.fail_task(repo_task.id, repo_result["message"], "Repository setup failed")
        
        # Step 2: Repository destination cloning (if specified) 
        files_modified = 0  # No longer modifying files in bulk - will be done per-file
        
        # Skip code modification checks since these are now per-file operations
        
        # Step 3: Git history rewriting with commit messages (if date/time provided)
        if request.hackathon_date and request.hackathon_start_time:
            # Use provided credentials or defaults
            git_username = request.git_username or "hackathon-dev"
            git_email = request.git_email or "dev@hackathon.local"
            
            status_tracker.add_output_line("🔄 Starting git history rewriting with generic commits...", "system")
            status_tracker.add_output_line(f"👤 Using git identity: {git_username} <{git_email}>", "system")
            
            git_task = status_tracker.create_task(
                f"git_history_{project_name}",
                "Rewrite git history",
                "Generating generic commit messages and rewriting history..."
            )
            
            status_tracker.start_task(git_task.id)
            status_tracker.update_task(main_task_id, 60, "Rewriting git history...")
            
            # Parse hackathon start time
            try:
                hackathon_start = datetime.strptime(f"{request.hackathon_date} {request.hackathon_start_time}", "%Y-%m-%d %H:%M")
                status_tracker.add_output_line(f"🕒 Hackathon timeline: {hackathon_start} to {hackathon_start + timedelta(hours=request.hackathon_duration)}", "system")
            except ValueError as e:
                status_tracker.add_output_line(f"❌ Invalid date/time format: {e}", "system")
                status_tracker.fail_task(git_task.id, f"Invalid date/time format: {e}", "Git history rewriting failed")
                git_task = None
            
            # Use commit agent to create hackathon history (only if date parsing succeeded)
            if git_task:
                # Convert team members to the expected format
                team_members_list = []
                if hasattr(request, 'team_members') and request.team_members:
                    team_members_list = [
                        {
                            "username": member.username,
                            "email": member.email,
                            "name": member.name or member.username
                        }
                        for member in request.team_members
                    ]
                
                commit_result = agents['commit'].execute({
                    "task_type": "create_history",
                    "project_path": project_path,
                    "project_name": project_name,
                    "project_description": f"Hackathon project: {project_name}",
                    "technologies": [],  # Will be detected
                    "hackathon_start": hackathon_start,
                    "hackathon_duration": request.hackathon_duration,
                    "team_members": team_members_list,
                    "developer_name": git_username,
                    "developer_email": git_email
                })
                
                if commit_result["success"]:
                    commits_modified = commit_result.get("commits_created", 0)
                    status_tracker.complete_task(git_task.id, f"Created {commits_modified} generic commits")
                else:
                    status_tracker.fail_task(git_task.id, commit_result["message"], "Git history rewriting failed")
        else:
            status_tracker.add_output_line("⚠️ Skipping git history rewriting - no date/time provided", "system")
            status_tracker.add_output_line("⏭️ Skipping git history rewriting (disabled)", "system")
        
        # Step 4: Final commit if files were modified
        if files_modified > 0:
            final_task = status_tracker.create_task(
                f"final_commit_{project_name}",
                "Final commit",
                "Creating final commit with changes..."
            )
            
            status_tracker.start_task(final_task.id)
            status_tracker.update_task(main_task_id, 90, "Creating final commit...")
            
            # Create final commit with generic message
            try:
                os.chdir(project_path)
                
                # Generate commit message using generic bank
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
        status_tracker.add_output_line("🎉 Project enhancement completed successfully!", "system")
        status_tracker.add_output_line(f"📊 Summary: Modified {files_modified} files", "system")
        if 'commits_modified' in locals():
            status_tracker.add_output_line(f"📊 Summary: Modified {commits_modified} commits and {files_modified} files", "system")
        status_tracker.add_output_line(f"✅ {project_name} is now enhanced and ready!", "system")
        
        # Add a small delay to ensure all processes complete and users can see the output
        import time
        time.sleep(3)
        
        status_tracker.update_task(main_task_id, 100, "Project enhancement completed successfully")
        status_tracker.complete_task(
            main_task_id,
            f"Successfully enhanced {project_name}! Modified {files_modified} files."
        )
        
        status_tracker.clear_current_operation()
        
    except Exception as e:
        print(f"❌ Error in untraceable process: {e}")
        status_tracker = get_global_tracker()
        status_tracker.fail_task(main_task_id, str(e), f"Untraceable process failed: {str(e)}")
        status_tracker.clear_current_operation() 