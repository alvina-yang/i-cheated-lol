"""
File Analysis Agent for generating descriptive summaries of project files.
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional

from core.base_agent import BaseAgent
from prompts.file_analysis_prompts import FileAnalysisPrompts
from utils.status_tracker import get_global_tracker
from agents.common_file_retrieval import CommonFileRetrieval


class FileAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing project files and generating descriptive summaries.
    Used to help identify the most relevant files for editing suggestions.
    """
    
    def __init__(self):
        super().__init__("FileAnalysisAgent")
        self.file_analysis_prompts = FileAnalysisPrompts()
        self.common_file_retrieval = CommonFileRetrieval()
        # Set the summary generator after initialization
        self.common_file_retrieval.set_summary_generator(self._generate_file_summary)
        # Override model for faster file analysis
        self.analysis_model = "llama-3.1-8b-instant"  # Use instant model for file analysis
        self.supported_extensions = {
            # Programming languages
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.cs', '.scala', '.clj',
            '.lua', '.dart', '.elm', '.haskell', '.ocaml', '.fsharp', '.vb',
            
            # Web technologies
            '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            
            # Config and data files
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.xml', '.md', '.txt', '.rst', '.properties',
            
            # Build and package files
            '.dockerfile', '.makefile', '.gradle', '.maven', '.cmake',
            'package.json', 'requirements.txt', 'cargo.toml', 'go.mod',
            'composer.json', 'gemfile', 'pipfile', 'poetry.lock',
            
            # Database and SQL
            '.sql', '.sqlite', '.db'
        }
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the main functionality of the agent.
        
        Args:
            task_data: Dictionary containing project_path
            
        Returns:
            Dict containing analysis results
        """
        project_path = task_data.get("project_path")
        
        if not project_path:
            return {
                "success": False,
                "message": "Missing required parameter: project_path"
            }
        
        return asyncio.run(self.analyze_project_files(project_path))
    
    async def analyze_project_files(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze all relevant files in a project and generate summaries.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dict containing analysis results and metadata
        """
        try:
            self.log(f"Starting file analysis for project: {project_path}")
            status_tracker = get_global_tracker()
            
            # Get all analyzable files
            files_to_analyze = self.common_file_retrieval._get_analyzable_files(project_path)
            
            if not files_to_analyze:
                return {
                    "success": True,
                    "message": "No analyzable files found",
                    "file_summaries": {},
                    "total_files": 0
                }
            
            self.log(f"Found {len(files_to_analyze)} files to analyze")
            start_msg = f"📁 Starting analysis of {len(files_to_analyze)} files..."
            status_tracker.add_output_line(start_msg)
            print(start_msg)
            
            # Analyze files in batches to avoid overwhelming the API
            batch_size = 3  # Smaller batches for better progress visibility
            file_summaries = {}
            analyzed_count = 0
            
            for i in range(0, len(files_to_analyze), batch_size):
                batch = files_to_analyze[i:i + batch_size]
                
                # Log batch start
                batch_msg = f"🔄 Processing batch {i//batch_size + 1}/{(len(files_to_analyze) + batch_size - 1)//batch_size} ({len(batch)} files)..."
                status_tracker.add_output_line(batch_msg)
                print(batch_msg)
                
                # Process batch asynchronously
                batch_results = await self.common_file_retrieval._process_file_batch(batch, project_path)
                
                # Update results
                file_summaries.update(batch_results)
                analyzed_count += len(batch)
                
                # Update progress
                progress_msg = f"📄 Analyzed {analyzed_count}/{len(files_to_analyze)} files ({(analyzed_count/len(files_to_analyze)*100):.1f}%)"
                status_tracker.add_output_line(progress_msg)
                print(progress_msg)
                self.log(progress_msg)
            
            # Save metadata to project
            metadata_path = self._save_file_metadata(project_path, file_summaries)
            
            completion_msg = f"✅ File analysis complete! Metadata saved to {metadata_path}"
            status_tracker.add_output_line(completion_msg)
            print(completion_msg)
            
            summary_msg = f"📊 Summary: {len(file_summaries)} files analyzed and saved to backend/file_summary.json"
            status_tracker.add_output_line(summary_msg)
            print(summary_msg)
            self.log(f"File analysis completed. {len(file_summaries)} files analyzed")
            
            return {
                "success": True,
                "message": f"Successfully analyzed {len(file_summaries)} files",
                "file_summaries": file_summaries,
                "total_files": len(file_summaries),
                "metadata_path": metadata_path
            }
            
        except Exception as e:
            self.log(f"Error analyzing project files: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"Error analyzing project files: {str(e)}",
                "file_summaries": {},
                "total_files": 0
            }
    
    
    def _generate_file_summary(self, file_path: str, content: str) -> str:
        """Generate a summary of the file using LLM."""
        try:
            # Get file extension for context
            ext = os.path.splitext(file_path)[1].lower()
            
            # Create prompt
            prompt = self.file_analysis_prompts.get_file_summary_prompt(
                file_path=file_path,
                file_extension=ext,
                content=content
            )
            
            # Call LLM with instant model for faster analysis
            response = self.llm.chat.completions.create(
                model=self.analysis_model,  # Use instant model
                messages=[
                    {"role": "system", "content": self.file_analysis_prompts.get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent summaries
                max_tokens=150    # Keep summaries concise
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.log(f"Error generating summary for {file_path}: {str(e)}", "ERROR")
            return f"Unable to generate summary: {str(e)}"
    
    def _save_file_metadata(self, project_path: str, file_summaries: Dict[str, str]) -> str:
        """Save file metadata to backend/file_summary.json."""
        try:
            # Get project name from path
            project_name = os.path.basename(project_path)
            
            # Create backend directory path
            backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Prepare metadata for this specific project
            project_metadata = {
                "project_name": project_name,
                "project_path": project_path,
                "generated_at": self._get_current_timestamp(),
                "total_files": len(file_summaries),
                "file_summaries": file_summaries
            }
            
            # Load existing file summary data or create new
            summary_file_path = os.path.join(backend_dir, "file_summary.json")
            existing_data = {}
            
            if os.path.exists(summary_file_path):
                try:
                    with open(summary_file_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as e:
                    self.log(f"Error reading existing file summary: {str(e)}", "WARNING")
            
            # Update with new project data
            existing_data[project_name] = project_metadata
            
            # Save updated data
            with open(summary_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            return summary_file_path
            
        except Exception as e:
            self.log(f"Error saving metadata: {str(e)}", "ERROR")
            return ""
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_file_metadata(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Retrieve saved file metadata for a project from backend/file_summary.json."""
        try:
            # Get project name from path
            project_name = os.path.basename(project_path)
            
            # Create backend directory path
            backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            summary_file_path = os.path.join(backend_dir, "file_summary.json")
            
            if not os.path.exists(summary_file_path):
                return None
            
            with open(summary_file_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                return all_data.get(project_name)
                
        except Exception as e:
            self.log(f"Error loading file metadata: {str(e)}", "ERROR")
            return None 