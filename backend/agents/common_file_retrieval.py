import os
import asyncio
from typing import Dict, List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

# Import necessary components for LLM-based file analysis
from core.base_agent import BaseAgent
from prompts.file_analysis_prompts import FileAnalysisPrompts

class CommonFileRetrieval(BaseAgent):
    def __init__(self):
        # Initialize as BaseAgent first
        super().__init__("CommonFileRetrieval")
        
        # Initialize file analysis prompts
        self.file_analysis_prompts = FileAnalysisPrompts()
        
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
    
    def execute(self, *args, **kwargs):
        """Required by BaseAgent interface - not used in this context."""
        pass
    
    def set_logging(self, log_func: Callable[[str], None]):
        """Set the logging function."""
        # Override the inherited log method if needed
        pass
    
    def _get_analyzable_files(self, project_path: str) -> List[str]:
        """Get list of files that should be analyzed."""
        analyzable_files = []
        
        # Directories to skip
        skip_dirs = {
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', 'env', '.env', 'dist', 'build', 'target', 'out', '.next',
            '.nuxt', 'coverage', '.coverage', 'htmlcov', '.tox', '.mypy_cache',
            'vendor', 'Pods', '.gradle', '.idea', '.vscode', 'temp', 'tmp'
        }
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Skip hidden and unwanted directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    # Skip hidden files
                    if file.startswith('.'):
                        continue
                    
                    # Check if file should be analyzed
                    if self._should_analyze_file(file, file_path):
                        analyzable_files.append(relative_path)
            
            return analyzable_files[:200]  # Limit to prevent overwhelming analysis
            
        except Exception as e:
            self.log(f"Error scanning files: {str(e)}", "ERROR")
            return []
    
    def _should_analyze_file(self, filename: str, file_path: str) -> bool:
        """Determine if a file should be analyzed."""
        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.supported_extensions:
            return True
        
        # Check specific filenames
        special_files = {
            'dockerfile', 'makefile', 'rakefile', 'gulpfile.js', 'gruntfile.js',
            'webpack.config.js', 'rollup.config.js', 'vite.config.js',
            'tsconfig.json', 'package.json', 'composer.json', 'requirements.txt',
            'cargo.toml', 'go.mod', 'gemfile', 'pipfile'
        }
        
        if filename.lower() in special_files:
            return True
        
        # Check if it's a text file (not binary)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Try to read first 100 characters
                sample = f.read(100)
                # If we can read it and it contains printable characters, analyze it
                return len(sample) > 0 and any(c.isprintable() or c.isspace() for c in sample)
        except:
            return False
    
    async def _process_file_batch(self, file_batch: List[str], project_path: str) -> Dict[str, str]:
        """Process a batch of files asynchronously."""
        loop = asyncio.get_event_loop()
        
        # Use ThreadPoolExecutor for concurrent file processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            tasks = []
            for file_path in file_batch:
                task = loop.run_in_executor(
                    executor, 
                    self._analyze_single_file, 
                    file_path, 
                    project_path
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Compile results
            batch_summaries = {}
            for file_path, result in zip(file_batch, results):
                if isinstance(result, Exception):
                    self.log(f"Error analyzing {file_path}: {result}", "ERROR")
                    batch_summaries[file_path] = f"Error analyzing file: {str(result)}"
                else:
                    batch_summaries[file_path] = result
            
            return batch_summaries
    
    def _analyze_single_file(self, relative_path: str, project_path: str) -> str:
        """Analyze a single file and generate a summary."""
        try:
            full_path = os.path.join(project_path, relative_path)
            
            # Read file content
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Limit content length for API efficiency
            max_content_length = 4000
            if len(content) > max_content_length:
                # Take first part and last part to capture both structure and conclusion
                content = content[:max_content_length//2] + "\n...\n" + content[-max_content_length//2:]
            
            # Generate summary using the provided summary generator function
            if self.summary_generator:
                summary = self.summary_generator(relative_path, content)
            else:
                # Fallback to a simple summary if no generator is provided
                summary = self._generate_simple_summary(relative_path, content)
            
            return summary
            
        except Exception as e:
            self.log(f"Error reading file {relative_path}: {str(e)}", "ERROR")
            return f"Error reading file: {str(e)}"

    def _generate_file_summary(self, relative_path: str, content: str) -> str:
        """Generate a summary of the file using LLM."""
        try:
            # Get file extension for context
            ext = os.path.splitext(relative_path)[1].lower()
            
            # Create prompt with system context
            system_prompt = self.file_analysis_prompts.get_system_prompt()
            user_prompt = self.file_analysis_prompts.get_file_summary_prompt(
                file_path=relative_path,
                file_extension=ext,
                content=content
            )
            
            # Combine system and user prompts for LangChain
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call LLM using the inherited invoke method
            response = self.invoke_llm(full_prompt)
            
            return response.strip() if response else f"Unable to generate summary for {relative_path}"
            
        except Exception as e:
            self.log(f"Error generating summary for {relative_path}: {str(e)}", "ERROR")
            return f"Unable to generate summary: {str(e)}"