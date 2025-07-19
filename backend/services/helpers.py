"""
Helper functions for the Chameleon Hackathon Discovery API
"""

import os
from typing import List, Dict, Any


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