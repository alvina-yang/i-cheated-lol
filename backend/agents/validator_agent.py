"""
Validator agent for analyzing and selecting the best hackathon projects.
Performs deep code analysis by cloning repositories and examining their structure.
"""

from typing import List, Dict, Optional
import json
import tempfile
import os
import shutil
from git import Repo

from core.base_agent import BaseAgent
from core.config import Config
from prompts.validator_prompts import ValidatorPrompts


class ValidatorAgent(BaseAgent):
    """Agent that analyzes actual project files to select the best hackathon project."""
    
    def __init__(self):
        super().__init__("ValidatorAgent", temperature=0.2)
    
    def execute(self, projects: List[Dict], technologies: List[str] = None) -> Optional[Dict]:
        """
        Main execution method for project validation and selection.
        
        Args:
            projects: List of projects to analyze
            technologies: List of technologies to focus on
            
        Returns:
            Selected best project or None if no suitable project found
        """
        return self.select_best_project(projects, technologies)
    
    def select_best_project(self, projects: List[Dict], technologies: List[str] = None) -> Optional[Dict]:
        """Analyze actual project files to select the best hackathon project."""
        
        if not projects:
            self.log("No projects to validate")
            return None
        
        self.log(f"Analyzing {len(projects)} hackathon projects by examining their code and documentation...")
        
        # Analyze each project by cloning and reading files
        project_analyses = []
        
        for i, project in enumerate(projects):
            self.log_step(f"Analyzing project {i+1}/{len(projects)}: {project.get('name', 'Unknown')}")
            
            analysis = self._analyze_project_deeply(project, technologies)
            if analysis:
                project_analyses.append({
                    "index": i,
                    "project": project,
                    "analysis": analysis
                })
        
        if not project_analyses:
            self.log("Failed to analyze any projects, using fallback selection...", "WARN")
            return self._fallback_selection(projects, technologies)
        
        # Use LLM to select best project based on deep analysis
        return self._select_with_deep_analysis(project_analyses, technologies)
    
    def _analyze_project_deeply(self, project: Dict, technologies: List[str]) -> Optional[Dict]:
        """Clone and analyze a project's files for creativity and complexity."""
        
        temp_dir = None
        try:
            # Create temporary directory for cloning
            temp_dir = tempfile.mkdtemp()
            clone_url = project.get('clone_url') or project.get('html_url')
            if not clone_url.endswith('.git'):
                clone_url += '.git'
            
            # Clone the repository
            self.log_step(f"Cloning {project.get('name')} for analysis...")
            repo = Repo.clone_from(clone_url, temp_dir, depth=1)  # Shallow clone for speed
            
            analysis = {
                "readme_content": "",
                "file_structure": [],
                "package_files": [],
                "code_complexity": 0,
                "technology_usage": [],
                "documentation_quality": 0,
                "innovation_indicators": []
            }
            
            # Read README file
            readme_files = ['README.md', 'readme.md', 'README.txt', 'README.rst', 'README']
            for readme_file in readme_files:
                readme_path = os.path.join(temp_dir, readme_file)
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                            analysis["readme_content"] = f.read()[:self.config.README_MAX_LENGTH]
                        break
                    except:
                        continue
            
            # Analyze file structure and complexity
            analysis["file_structure"] = self._analyze_file_structure(temp_dir)
            analysis["package_files"] = self._find_package_files(temp_dir)
            analysis["code_complexity"] = self._calculate_code_complexity(temp_dir)
            analysis["technology_usage"] = self._detect_technologies(temp_dir, technologies)
            analysis["documentation_quality"] = self._assess_documentation_quality(temp_dir)
            analysis["innovation_indicators"] = self._find_innovation_indicators(temp_dir, analysis["readme_content"])
            
            self.log_step(f"Analysis complete: {len(analysis['file_structure'])} files, complexity: {analysis['code_complexity']}")
            return analysis
            
        except Exception as e:
            self.log(f"Failed to analyze {project.get('name', 'Unknown')}: {e}", "ERROR")
            return None
        
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    def _analyze_file_structure(self, repo_path: str) -> List[str]:
        """Analyze the file structure of the repository."""
        files = []
        try:
            for root, dirs, filenames in os.walk(repo_path):
                # Skip hidden directories and common irrelevant dirs
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for filename in filenames:
                    if not filename.startswith('.') and len(files) < self.config.MAX_FILES_TO_ANALYZE:
                        rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                        files.append(rel_path)
        except:
            pass
        
        return files
    
    def _find_package_files(self, repo_path: str) -> List[str]:
        """Find package/dependency files."""
        package_files = []
        common_package_files = [
            'package.json', 'requirements.txt', 'Pipfile', 'poetry.lock', 'Cargo.toml',
            'go.mod', 'pom.xml', 'build.gradle', 'composer.json', 'Gemfile'
        ]
        
        for package_file in common_package_files:
            if os.path.exists(os.path.join(repo_path, package_file)):
                package_files.append(package_file)
        
        return package_files
    
    def _calculate_code_complexity(self, repo_path: str) -> int:
        """Calculate a simple complexity score based on file types and structure."""
        complexity = 0
        
        code_extensions = {
            '.py': 2, '.js': 2, '.ts': 3, '.jsx': 3, '.tsx': 3,
            '.java': 2, '.cpp': 3, '.c': 2, '.go': 2, '.rs': 3,
            '.php': 2, '.rb': 2, '.swift': 3, '.kt': 2,
            '.sql': 1, '.css': 1, '.scss': 2, '.less': 2,
            '.html': 1, '.xml': 1, '.json': 1, '.yaml': 1, '.yml': 1
        }
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                complexity += code_extensions.get(ext, 0)
        
        # Bonus for directory structure
        dir_count = len([d for d in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, d)) and not d.startswith('.')])
        complexity += dir_count * 2
        
        return complexity
    
    def _detect_technologies(self, repo_path: str, target_technologies: List[str]) -> List[str]:
        """Detect technologies used in the project."""
        detected = []
        
        # Check package.json for frontend technologies
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.loads(f.read())
                    dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                    
                    for dep in dependencies:
                        if any(tech.lower() in dep.lower() for tech in (target_technologies or [])):
                            detected.append(dep)
            except:
                pass
        
        # Check requirements.txt for Python
        requirements_path = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        package = line.strip().split('==')[0].split('>=')[0].split('~=')[0]
                        if any(tech.lower() in package.lower() for tech in (target_technologies or [])):
                            detected.append(package)
            except:
                pass
        
        return detected
    
    def _assess_documentation_quality(self, repo_path: str) -> int:
        """Assess the quality of documentation."""
        score = 0
        
        # Check for README
        readme_files = ['README.md', 'readme.md', 'README.txt']
        for readme_file in readme_files:
            if os.path.exists(os.path.join(repo_path, readme_file)):
                score += 3
                break
        
        # Check for other documentation
        docs_indicators = ['docs/', 'documentation/', 'CONTRIBUTING.md', 'LICENSE', 'CHANGELOG.md']
        for indicator in docs_indicators:
            if os.path.exists(os.path.join(repo_path, indicator)):
                score += 1
        
        # Check for inline documentation (comments in code files)
        code_files = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules']]
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')) and len(code_files) < 5:
                    code_files.append(os.path.join(root, file))
        
        comment_score = 0
        for code_file in code_files:
            try:
                with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[:50]  # Check first 50 lines
                    comment_lines = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('//') or '"""' in line or '/*' in line)
                    if comment_lines > 3:
                        comment_score += 1
            except:
                continue
        
        score += min(comment_score, 3)  # Max 3 points for comments
        
        return score
    
    def _find_innovation_indicators(self, repo_path: str, readme_content: str) -> List[str]:
        """Find indicators of innovation and creativity."""
        indicators = []
        
        innovation_keywords = [
            'AI', 'machine learning', 'neural network', 'blockchain', 'AR', 'VR',
            'computer vision', 'natural language', 'IoT', 'real-time', 'API integration',
            'microservices', 'containerization', 'cloud', 'serverless', 'websocket',
            'mobile app', 'cross-platform', 'progressive web app', 'PWA'
        ]
        
        readme_lower = readme_content.lower()
        for keyword in innovation_keywords:
            if keyword.lower() in readme_lower:
                indicators.append(keyword)
        
        # Check for modern frameworks/tools
        modern_indicators = ['docker', 'kubernetes', 'redis', 'graphql', 'websocket', 'tensorflow', 'pytorch']
        for indicator in modern_indicators:
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if indicator in file.lower():
                        indicators.append(f"uses {indicator}")
                        break
        
        return list(set(indicators))  # Remove duplicates
    
    def _select_with_deep_analysis(self, project_analyses: List[Dict], technologies: List[str]) -> Optional[Dict]:
        """Use LLM to select the best project based on deep analysis."""
        
        # Prepare analysis summaries for LLM
        analysis_summaries = []
        for item in project_analyses:
            project = item["project"]
            analysis = item["analysis"]
            
            summary = {
                "index": item["index"],
                "name": project.get('name', 'Unknown'),
                "description": project.get('description', 'No description'),
                "stars": project.get('stars', 0),
                "forks": project.get('forks', 0),
                "url": project.get('html_url', ''),
                "readme_preview": analysis["readme_content"][:500] + "..." if len(analysis["readme_content"]) > 500 else analysis["readme_content"],
                "file_count": len(analysis["file_structure"]),
                "code_complexity_score": analysis["code_complexity"],
                "technologies_detected": analysis["technology_usage"],
                "documentation_quality": analysis["documentation_quality"],
                "innovation_indicators": analysis["innovation_indicators"],
                "package_files": analysis["package_files"]
            }
            analysis_summaries.append(summary)
        
        # Use prompts from the ValidatorPrompts class
        prompt = ValidatorPrompts.get_deep_analysis_prompt(
            project_analyses=json.dumps(analysis_summaries, indent=2),
            technologies=technologies
        )
        
        try:
            result = self.invoke_llm(prompt, parse_json=True)
            
            if result and isinstance(result, dict):
                selected_index = result.get('selected_index')
                reasoning = result.get('reasoning', 'No reasoning provided')
                creativity = result.get('creativity_score', 5)
                complexity = result.get('complexity_score', 5)
                confidence = result.get('overall_confidence', 5)
                
                if selected_index is not None and 0 <= selected_index < len(project_analyses):
                    selected_project = project_analyses[selected_index]["project"]
                    
                    self.log(f"Selected hackathon project: {selected_project.get('name', 'Unknown')}")
                    self.log(f"Reasoning: {reasoning}")
                    self.log(f"Creativity Score: {creativity}/10")
                    self.log(f"Complexity Score: {complexity}/10")
                    self.log(f"Confidence: {confidence}/10")
                    
                    return selected_project
            
            # Fallback: select based on complexity and documentation
            self.log("LLM analysis failed, using complexity-based selection...", "WARN")
            return self._select_by_complexity(project_analyses)
            
        except Exception as e:
            self.log(f"Error in deep analysis selection: {e}", "ERROR")
            return self._select_by_complexity(project_analyses)
    
    def _select_by_complexity(self, project_analyses: List[Dict]) -> Optional[Dict]:
        """Fallback selection based on complexity analysis."""
        
        if not project_analyses:
            return None
        
        best_score = -1
        best_project = None
        
        for item in project_analyses:
            analysis = item["analysis"]
            project = item["project"]
            
            score = 0
            
            # Code complexity score
            score += analysis["code_complexity"] * 2
            
            # Documentation quality
            score += analysis["documentation_quality"] * 3
            
            # Innovation indicators
            score += len(analysis["innovation_indicators"]) * 5
            
            # Technology usage
            score += len(analysis["technology_usage"]) * 3
            
            # README quality (length as proxy for detail)
            if len(analysis["readme_content"]) > 200:
                score += 5
            elif len(analysis["readme_content"]) > 100:
                score += 3
            
            if score > best_score:
                best_score = score
                best_project = project
        
        self.log(f"Complexity-based selection: {best_project.get('name', 'Unknown')} (score: {best_score})")
        return best_project
    
    def _fallback_selection(self, projects: List[Dict], technologies: List[str] = None) -> Optional[Dict]:
        """Simple fallback when deep analysis fails."""
        
        if not projects:
            return None
        
        # Use prompts from the ValidatorPrompts class  
        project_summaries = []
        for i, project in enumerate(projects):
            summary = {
                "index": i,
                "name": project.get('name', 'Unknown'),
                "description": project.get('description', 'No description'),
                "stars": project.get('stars', 0),
                "forks": project.get('forks', 0),
                "language": project.get('language', 'Unknown'),
                "topics": project.get('topics', []),
                "url": project.get('html_url', ''),
                "size_kb": project.get('size', 0)
            }
            project_summaries.append(summary)
        
        prompt = ValidatorPrompts.get_fallback_selection_prompt(
            project_summaries=json.dumps(project_summaries, indent=2),
            technologies=technologies
        )
        
        try:
            result = self.invoke_llm(prompt, parse_json=True)
            
            if result and isinstance(result, dict):
                selected_index = result.get('selected_index')
                reasoning = result.get('reasoning', 'No reasoning provided')
                confidence = result.get('confidence', 5)
                
                if selected_index is not None and 0 <= selected_index < len(projects):
                    selected_project = projects[selected_index]
                    
                    self.log(f"Fallback selection: {selected_project.get('name', 'Unknown')}")
                    self.log(f"Reasoning: {reasoning}")
                    self.log(f"Confidence: {confidence}/10")
                    
                    return selected_project
            
            # Final fallback: just take the first project
            return projects[0]
            
        except Exception as e:
            self.log(f"Error in fallback selection: {e}", "ERROR")
            return projects[0] if projects else None 