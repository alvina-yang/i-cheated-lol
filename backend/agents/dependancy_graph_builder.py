import json
import os
import asyncio
from typing import Dict, Any, List

from core.base_agent import BaseAgent
from prompts.dependancy_graph_prompts import DependancyGraphPrompts
from utils.status_tracker import get_global_tracker
from agents.common_file_retrieval import CommonFileRetrieval


class DependancyGraphBuilder(BaseAgent):
    def __init__(self):
        super().__init__("DependancyGraphBuilder")
        self.common_file_retrieval = CommonFileRetrieval()
        self.status_tracker = get_global_tracker()
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the dependancy graph builder agent."""
        project_path = task_data.get("project_path")
        
        if not project_path:
            return {
                "success": False,
                "message": "Missing required parameter: project_path"
            }
            
        return self.build_dependancy_graph(project_path)
    
    def build_dependancy_graph(self, project_path: str) -> Dict[str, Any]:
        """Build a dependancy graph for a project by analyzing imports in each file."""
        try:
            self.log(f"Starting dependancy graph build for project: {project_path}")
            status_tracker = get_global_tracker()
            
            # Get all analyzable files (returns relative paths)
            relative_file_paths = self.common_file_retrieval._get_analyzable_files(project_path)
            
            if not relative_file_paths:
                return {
                    "success": False,
                    "message": f"No analyzable files found in: {project_path}",
                    "dependancy_graph": {}
                }
            
            self.log(f"Found {len(relative_file_paths)} files to analyze")
            start_msg = f"📁 Starting dependency analysis of {len(relative_file_paths)} files..."
            status_tracker.add_output_line(start_msg)
            print(start_msg)
            
            # Analyze files to extract imports
            dependancy_graph = {}
            analyzed_count = 0
            
            for relative_file_path in relative_file_paths:
                try:
                    # Convert relative path to absolute path for file operations
                    absolute_file_path = os.path.join(project_path, relative_file_path)
                    
                    self.log_step(f"Analyzing imports in: {os.path.basename(absolute_file_path)}")
                    
                    # Analyze file imports
                    imports = self._analyze_file_imports(absolute_file_path, project_path)
                    
                    # Store the imports for this file with proper path format (leading slash)
                    formatted_path = "/" + relative_file_path.replace("\\", "/")
                    dependancy_graph[formatted_path] = imports
                    
                    analyzed_count += 1
                    progress_msg = f" Analyzed {analyzed_count}/{len(relative_file_paths)} files - Found {len(imports)} imports in {os.path.basename(absolute_file_path)}"
                    status_tracker.add_output_line(progress_msg)
                    print(progress_msg)
                    
                except Exception as e:
                    self.log(f"Error analyzing {absolute_file_path}: {str(e)}", "ERROR")
                    # Continue with other files even if one fails
                    continue
            
            # Generate summary statistics
            total_imports = sum(len(imports) for imports in dependancy_graph.values())
            files_with_imports = len([f for f, imports in dependancy_graph.items() if imports])
            
            summary_msg = f"Dependency analysis complete. Found {total_imports} total imports across {files_with_imports} files"
            status_tracker.add_output_line(summary_msg)
            print(summary_msg)
            
            return {
                "success": True,
                "message": f"Successfully built dependency graph for {analyzed_count} files",
                "dependancy_graph": dependancy_graph,
                "summary": {
                    "total_files_analyzed": analyzed_count,
                    "total_imports_found": total_imports,
                    "files_with_imports": files_with_imports
                }
            }
            
        except Exception as e:
            error_msg = f"Error building dependency graph: {str(e)}"
            self.log(error_msg, "ERROR")
            return {
                "success": False,
                "message": error_msg,
                "dependancy_graph": {}
            }
    
    def _analyze_file_imports(self, file_path: str, project_path: str) -> List[str]:
        """Analyze a single file to extract its imports."""
        try:
            # Read file content using the full file path
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Skip empty files
            if not content.strip():
                return []
            
            # Get file extension for context
            file_extension = os.path.splitext(file_path)[1]
            relative_path = os.path.relpath(file_path, project_path)
            
            # Prepare the prompt using dependency graph prompts
            system_prompt = DependancyGraphPrompts.get_system_prompt()
            file_prompt = DependancyGraphPrompts.get_file_summary_prompt(
                relative_path, 
                file_extension, 
                content[:4000]  # Limit content to avoid token limits
            )
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{file_prompt}"
            
            # Use LLM to analyze imports
            response = self.invoke_llm(full_prompt, parse_json=True)
            
            if response and isinstance(response, dict) and "imports" in response:
                imports = response["imports"]
                # Filter and validate imports
                validated_imports = []
                
                for imp in imports:
                    if isinstance(imp, str) and imp.strip():
                        # Clean up the import path
                        clean_import = imp.strip()
                        
                        # Ensure it starts with /
                        if not clean_import.startswith('/'):
                            clean_import = '/' + clean_import
                        
                        # Check if the file actually exists in the project
                        # Remove leading slash for file system check
                        check_path = clean_import[1:] if clean_import.startswith('/') else clean_import
                        full_file_path = os.path.join(project_path, check_path)
                        
                        # Try common extensions if no extension provided
                        possible_paths = [full_file_path]
                        if not os.path.splitext(clean_import)[1]:
                            # Add common extensions
                            for ext in ['.tsx', '.ts', '.jsx', '.js', '.css', '.scss', '.py']:
                                possible_paths.append(full_file_path + ext)
                                # Also try index files
                                if clean_import.endswith('/'):
                                    possible_paths.append(os.path.join(full_file_path, 'index' + ext))
                                else:
                                    possible_paths.append(os.path.join(full_file_path, 'index' + ext))
                        
                        # Check if any of the possible paths exist
                        for check_file_path in possible_paths:
                            if os.path.isfile(check_file_path):
                                # Convert back to relative path with leading slash
                                valid_relative = os.path.relpath(check_file_path, project_path)
                                validated_import = "/" + valid_relative.replace("\\", "/")
                                if validated_import not in validated_imports:
                                    validated_imports.append(validated_import)
                                break
                        else:
                            # If file doesn't exist, still include it but log a warning
                            self.log(f"Warning: Import {clean_import} in {relative_path} does not correspond to an existing file", "WARNING")
                            if clean_import not in validated_imports:
                                validated_imports.append(clean_import)
                
                return validated_imports
            else:
                self.log(f"Unexpected response format for {file_path}: {response}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"Error analyzing imports in {file_path}: {str(e)}", "ERROR")
            return []
    
    def get_dependency_graph_visualization(self, dependancy_graph: Dict[str, List[str]]) -> str:
        """Generate a text-based visualization of the dependency graph."""
        visualization = "=== PROJECT DEPENDENCY GRAPH ===\n\n"
        
        for file_path, imports in dependancy_graph.items():
            visualization += f"📁 {file_path}\n"
            if imports:
                for import_file in imports:
                    visualization += f"  └─ imports: {import_file}\n"
            else:
                visualization += f"  └─ (no local imports)\n"
            visualization += "\n"
        
        return visualization

    def save_dependency_graph(self, project_path: str, dependancy_graph: Dict[str, List[str]]) -> str:
        """Save the dependency graph to a JSON file."""
        try:
            # Get the backend directory (parent of agents directory)
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Save dependency graph to backend/dependancy_graph.json
            graph_file = os.path.join(backend_dir, "dependancy_graph.json")
            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(dependancy_graph, f, indent=2)
            
            self.log(f"Dependency graph saved to: {graph_file}")
            return graph_file
            
        except Exception as e:
            self.log(f"Error saving dependency graph: {str(e)}", "ERROR")
            return ""