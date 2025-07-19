"""
Prompts for generating concise file summaries for project analysis.
"""

from typing import Dict, Any


class FileAnalysisPrompts:
    """
    Prompts for the FileAnalysisAgent to generate concise file summaries.
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for file analysis."""
        return """You are an expert code analyst specializing in quickly understanding and summarizing source code files. Your task is to generate concise, descriptive summaries of files that help developers understand what each file does and its role in the project.

Your summaries should be:
- CONCISE (1-2 sentences max)
- DESCRIPTIVE of the file's main purpose
- FOCUSED on functionality, not implementation details
- USEFUL for identifying which files to edit for specific changes
- CLEAR about the file's role in the overall project

Format your response as a single, clear summary without extra formatting or headers."""

    @staticmethod
    def get_file_summary_prompt(file_path: str, file_extension: str, content: str) -> str:
        """
        Generate a prompt for summarizing a specific file.
        
        Args:
            file_path: Path to the file relative to project root
            file_extension: File extension for context
            content: File content (may be truncated)
        """
        return f"""Analyze this file and provide a concise summary of what it does:

**File Path:** {file_path}
**File Extension:** {file_extension}

**File Content:**
```
{content}
```

Provide a 1-2 sentence summary that explains:
1. What this file's main purpose/functionality is
2. What role it plays in the project (e.g., "handles user authentication", "defines database models", "manages API routes")

Keep it concise and focused on the file's core responsibility.""" 