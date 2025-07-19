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
                "git_username": request.git_username,
                "git_email": request.git_email
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
        status_tracker = get_global_tracker()
        status_tracker.fail_task(main_task_id, str(e), f"Untraceable process failed: {str(e)}")
        status_tracker.clear_current_operation() 