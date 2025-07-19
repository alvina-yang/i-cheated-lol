"""
Main discovery workflow chain for finding and cloning hackathon projects.
Orchestrates the search, validation, and cloning process.
"""

from typing import List, Optional, Dict
import json
from datetime import datetime

from core.config import Config
from agents.search_agent import TechnologyProjectSearchAgent
from agents.validator_agent import ValidatorAgent
from utils.project_cloner import GitHubCloner


class TechnologyProjectDiscoveryChain:
    """
    Main workflow chain for discovering and cloning hackathon projects.
    
    This chain orchestrates the entire process:
    1. Search for hackathon projects using specified technologies
    2. Analyze and validate projects to select the best one
    3. Clone the selected project to the local filesystem
    """
    
    def __init__(self):
        self.config = Config
        self.search_agent = TechnologyProjectSearchAgent()
        self.validator_agent = ValidatorAgent()
        self.cloner = GitHubCloner()
        
        # Initialize workflow state
        self.workflow_state = {
            'start_time': None,
            'end_time': None,
            'technologies': [],
            'projects_found': 0,
            'project_selected': False,
            'clone_successful': False,
            'errors': [],
            'selected_project': None
        }
    
    def execute(self, technologies: List[str] = None) -> Dict:
        """
        Execute the complete technology project discovery workflow.
        
        Args:
            technologies: List of technologies to search for (optional)
            
        Returns:
            Dictionary containing workflow results and metadata
        """
        self.workflow_state['start_time'] = datetime.now().isoformat()
        self.workflow_state['technologies'] = technologies or []
        
        try:
            self._print_workflow_header(technologies)
            
            # Step 1: Search for projects
            projects = self._search_projects(technologies)
            
            if not projects:
                self._handle_no_projects_found()
                return self._finalize_workflow()
            
            # Step 2: Select best project
            selected_project = self._validate_and_select_project(projects, technologies)
            
            if not selected_project:
                self._handle_no_project_selected()
                return self._finalize_workflow()
            
            # Step 3: Clone the selected project
            clone_success = self._clone_selected_project(selected_project)
            
            # Finalize and return results
            return self._finalize_workflow()
            
        except Exception as e:
            self._handle_workflow_error(e)
            return self._finalize_workflow()
    
    def _print_workflow_header(self, technologies: List[str]):
        """Print the workflow header with configuration information."""
        print("=== Technology Project Discovery Chain ===")
        print(f"Technologies: {', '.join(technologies) if technologies else 'None (general search)'}")
        print(f"Target: Find and clone 1 project using specified technologies")
        print(f"Criteria: {self.config.MIN_STARS}-{self.config.MAX_STARS} stars, max {self.config.MAX_FORKS} forks")
        print("=" * 50)
        print()
    
    def _search_projects(self, technologies: List[str]) -> List[Dict]:
        """Step 1: Search for hackathon projects."""
        print("Step 1: Searching for projects with specified technologies...")
        
        try:
            projects = self.search_agent.execute(technologies)
            self.workflow_state['projects_found'] = len(projects)
            
            print(f"Found {len(projects)} projects")
            
            return projects
            
        except Exception as e:
            error_msg = f"Error in project search: {e}"
            self.workflow_state['errors'].append(error_msg)
            print(f"ERROR: {error_msg}")
            return []
    
    def _validate_and_select_project(self, projects: List[Dict], technologies: List[str]) -> Optional[Dict]:
        """Step 2: Validate and select the best project."""
        print("\nStep 2: Analyzing projects to select the best one...")
        
        try:
            selected_project = self.validator_agent.execute(projects, technologies)
            
            if selected_project:
                self.workflow_state['project_selected'] = True
                self.workflow_state['selected_project'] = {
                    'name': selected_project.get('name', 'Unknown'),
                    'description': selected_project.get('description', 'No description'),
                    'stars': selected_project.get('stars', 0),
                    'forks': selected_project.get('forks', 0),
                    'url': selected_project.get('html_url', ''),
                    'language': selected_project.get('language', 'Unknown')
                }
                
                print(f"Selected: {selected_project.get('name', 'Unknown')}")
                print(f"Description: {selected_project.get('description', 'No description')}")
                print(f"Stars: {selected_project.get('stars', 0)}, Forks: {selected_project.get('forks', 0)}")
                print(f"URL: {selected_project.get('html_url', '')}")
            else:
                print("No suitable project selected")
            
            return selected_project
            
        except Exception as e:
            error_msg = f"Error in project validation: {e}"
            self.workflow_state['errors'].append(error_msg)
            print(f"ERROR: {error_msg}")
            return None
    
    def _clone_selected_project(self, selected_project: Dict) -> bool:
        """Step 3: Clone the selected project."""
        print("\nStep 3: Cloning selected project...")
        
        try:
            project_name = selected_project.get('name', 'unknown-project')
            print(f"Cloning {project_name} to {self.config.CLONE_DIRECTORY}/{project_name}...")
            
            clone_success = self.cloner.clone_project(selected_project)
            self.workflow_state['clone_successful'] = clone_success
            
            if clone_success:
                print("Project cloned successfully:")
                print(f"  Name: {selected_project.get('name', 'Unknown')}")
                print(f"  Location: {self.config.CLONE_DIRECTORY}/{project_name}")
                print(f"  Stars: {selected_project.get('stars', 0)}")
                print(f"  URL: {selected_project.get('html_url', '')}")
                
                # Save discovery results
                self._save_discovery_results(selected_project)
            else:
                print("Failed to clone the selected project")
            
            return clone_success
            
        except Exception as e:
            error_msg = f"Error in project cloning: {e}"
            self.workflow_state['errors'].append(error_msg)
            print(f"ERROR: {error_msg}")
            return False
    
    def _save_discovery_results(self, selected_project: Dict):
        """Save the discovery results to a JSON file."""
        try:
            results = {
                'discovery_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'technologies_searched': self.workflow_state['technologies'],
                    'projects_found': self.workflow_state['projects_found'],
                    'search_criteria': self.config.get_search_criteria()
                },
                'selected_project': self.workflow_state['selected_project'],
                'workflow_state': self.workflow_state
            }
            
            self.cloner.save_discovery_results(results)
            
        except Exception as e:
            print(f"Warning: Could not save discovery results: {e}")
    
    def _handle_no_projects_found(self):
        """Handle the case where no projects are found."""
        error_msg = "No hackathon projects found matching the criteria"
        self.workflow_state['errors'].append(error_msg)
        print(f"ERROR: {error_msg}")
        print("Try:")
        print("- Using different technologies")
        print("- Relaxing search criteria in configuration")
        print("- Checking your internet connection")
    
    def _handle_no_project_selected(self):
        """Handle the case where no project is selected for cloning."""
        error_msg = "No suitable project selected for cloning"
        self.workflow_state['errors'].append(error_msg)
        print(f"ERROR: {error_msg}")
        print("The found projects may not meet the quality criteria for hackathon projects")
    
    def _handle_workflow_error(self, error: Exception):
        """Handle unexpected workflow errors."""
        error_msg = f"Unexpected workflow error: {error}"
        self.workflow_state['errors'].append(error_msg)
        print(f"CRITICAL ERROR: {error_msg}")
    
    def _finalize_workflow(self) -> Dict:
        """Finalize the workflow and return comprehensive results."""
        self.workflow_state['end_time'] = datetime.now().isoformat()
        
        # Calculate workflow duration
        if self.workflow_state['start_time'] and self.workflow_state['end_time']:
            start_time = datetime.fromisoformat(self.workflow_state['start_time'])
            end_time = datetime.fromisoformat(self.workflow_state['end_time'])
            duration = (end_time - start_time).total_seconds()
            self.workflow_state['duration_seconds'] = duration
        
        # Print summary
        self._print_workflow_summary()
        
        return {
            'success': self.workflow_state['clone_successful'],
            'workflow_state': self.workflow_state.copy(),
            'clone_directory': self.config.CLONE_DIRECTORY if self.workflow_state['clone_successful'] else None,
            'selected_project': self.workflow_state['selected_project']
        }
    
    def _print_workflow_summary(self):
        """Print a comprehensive workflow summary."""
        print("\n" + "=" * 50)
        print("Pipeline Summary:")
        print("=" * 30)
        
        tech_display = ', '.join(self.workflow_state['technologies']) if self.workflow_state['technologies'] else 'None'
        print(f"Technologies: {tech_display}")
        print(f"Projects found: {self.workflow_state['projects_found']}")
        print(f"Project selected: {'Yes' if self.workflow_state['project_selected'] else 'No'}")
        print(f"Clone successful: {'Yes' if self.workflow_state['clone_successful'] else 'No'}")
        print(f"Errors: {len(self.workflow_state['errors'])}")
        
        if self.workflow_state['selected_project']:
            print("\nSelected Project Details:")
            project = self.workflow_state['selected_project']
            print(f"   Name: {project.get('name', 'Unknown')}")
            print(f"   URL: {project.get('url', 'Unknown')}")
            print(f"   Stars: {project.get('stars', 0)}")
            print(f"   Language: {project.get('language', 'Unknown')}")
        
        if self.workflow_state['errors']:
            print(f"\nErrors encountered:")
            for i, error in enumerate(self.workflow_state['errors'], 1):
                print(f"   {i}. {error}")
        
        # Final status message
        if self.workflow_state['clone_successful']:
            print(f"\nDiscovery completed successfully!")
            print(f"Successfully cloned project to: {self.config.CLONE_DIRECTORY}")
        else:
            print(f"\nDiscovery completed with issues.")
            print("No project was successfully cloned.")
        
        print()
    
    def get_workflow_state(self) -> Dict:
        """Get the current workflow state."""
        return self.workflow_state.copy()
    
    def reset_workflow_state(self):
        """Reset the workflow state for a new execution."""
        self.workflow_state = {
            'start_time': None,
            'end_time': None,
            'technologies': [],
            'projects_found': 0,
            'project_selected': False,
            'clone_successful': False,
            'errors': [],
            'selected_project': None
        } 