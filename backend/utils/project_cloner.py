"""
Project cloning utility for downloading and managing hackathon projects.
Handles Git operations and file system management.
"""

import os
import json
from typing import Dict, Optional
from git import Repo
from core.config import Config


class GitHubCloner:
    """Utility class for cloning GitHub repositories to the local filesystem."""
    
    def __init__(self):
        self.config = Config
        self.clone_directory = self.config.CLONE_DIRECTORY
        
        # Ensure clone directory exists
        os.makedirs(self.clone_directory, exist_ok=True)
    
    def clone_project(self, project: Dict) -> bool:
        """
        Clone a GitHub project to the local filesystem.
        
        Args:
            project: Project dictionary containing repository information
            
        Returns:
            True if cloning was successful, False otherwise
        """
        project_name = project.get('name', 'unknown-project')
        clone_url = project.get('clone_url') or project.get('html_url')
        
        if not clone_url:
            print(f"No clone URL available for project: {project_name}")
            return False
        
        # Ensure URL ends with .git
        if not clone_url.endswith('.git'):
            clone_url += '.git'
        
        destination_path = os.path.join(self.clone_directory, project_name)
        
        # Check if project already exists
        if os.path.exists(destination_path):
            print(f"Project {project_name} already exists at {destination_path}")
            return True
        
        try:
            print(f"Cloning {project_name} to {destination_path}...")
            
            # Clone the repository
            repo = Repo.clone_from(clone_url, destination_path)
            
            print("Successfully cloned using GitPython")
            
            # Save project metadata
            self._save_project_metadata(project, destination_path)
            
            return True
            
        except Exception as e:
            print(f"Failed to clone {project_name}: {e}")
            
            # Clean up failed clone attempt
            if os.path.exists(destination_path):
                try:
                    import shutil
                    shutil.rmtree(destination_path)
                except:
                    pass
            
            return False
    
    def _save_project_metadata(self, project: Dict, destination_path: str):
        """Save project metadata to a JSON file in the cloned directory."""
        metadata = {
            'name': project.get('name', ''),
            'full_name': project.get('full_name', ''),
            'description': project.get('description', ''),
            'html_url': project.get('html_url', ''),
            'clone_url': project.get('clone_url', ''),
            'language': project.get('language', ''),
            'stars': project.get('stars', 0),
            'forks': project.get('forks', 0),
            'topics': project.get('topics', []),
            'created_at': project.get('created_at', ''),
            'updated_at': project.get('updated_at', ''),
            'cloned_at': self._get_current_timestamp()
        }
        
        metadata_path = os.path.join(destination_path, '.chameleon_metadata.json')
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save metadata for {project.get('name', 'unknown')}: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_cloned_projects(self) -> list:
        """Get a list of all cloned projects in the clone directory."""
        if not os.path.exists(self.clone_directory):
            return []
        
        cloned_projects = []
        
        try:
            for item in os.listdir(self.clone_directory):
                item_path = os.path.join(self.clone_directory, item)
                
                if os.path.isdir(item_path):
                    # Check if it's a git repository
                    git_path = os.path.join(item_path, '.git')
                    metadata_path = os.path.join(item_path, '.chameleon_metadata.json')
                    
                    project_info = {'name': item, 'path': item_path}
                    
                    # Try to load metadata if available
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                project_info.update(metadata)
                        except:
                            pass
                    
                    # Check if it's a valid git repository
                    if os.path.exists(git_path):
                        project_info['is_git_repo'] = True
                    else:
                        project_info['is_git_repo'] = False
                    
                    cloned_projects.append(project_info)
        
        except Exception as e:
            print(f"Error listing cloned projects: {e}")
        
        return cloned_projects
    
    def remove_project(self, project_name: str) -> bool:
        """
        Remove a cloned project from the filesystem.
        
        Args:
            project_name: Name of the project to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        project_path = os.path.join(self.clone_directory, project_name)
        
        if not os.path.exists(project_path):
            print(f"Project {project_name} not found in {self.clone_directory}")
            return False
        
        try:
            import shutil
            shutil.rmtree(project_path)
            print(f"Successfully removed project: {project_name}")
            return True
        
        except Exception as e:
            print(f"Failed to remove project {project_name}: {e}")
            return False
    
    def get_project_size(self, project_name: str) -> int:
        """
        Get the total size of a cloned project in bytes.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Size in bytes, or 0 if project not found
        """
        project_path = os.path.join(self.clone_directory, project_name)
        
        if not os.path.exists(project_path):
            return 0
        
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(project_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            print(f"Error calculating size for {project_name}: {e}")
        
        return total_size
    
    def save_discovery_results(self, results: Dict):
        """Save discovery results to a JSON file."""
        results_path = os.path.join(self.clone_directory, 'discovery_results.json')
        
        try:
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Discovery results saved to: {results_path}")
        except Exception as e:
            print(f"Warning: Could not save discovery results: {e}") 