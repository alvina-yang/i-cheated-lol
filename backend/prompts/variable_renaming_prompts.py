"""
Prompts for the Variable Renaming Agent.
"""

from typing import Dict, Any, List


class VariableRenamingPrompts:
    """
    Collection of prompts for variable renaming operations.
    """
    
    def get_variable_rename_prompt(self, language: str, filename: str, code_content: str) -> str:
        """
        Generate a prompt for renaming variables in source code.
        
        Args:
            language: Programming language
            filename: Name of the file
            code_content: Source code content
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert {language} developer tasked with improving code readability by renaming variables to be more descriptive and meaningful.

CRITICAL RULES:
1. ONLY rename variables - do NOT change any code logic, structure, or functionality
2. Do NOT add, remove, or modify any imports, functions, classes, or methods
3. Do NOT change control flow (if/else, loops, try/catch)
4. Do NOT modify string literals, comments, or documentation
5. Do NOT change function signatures or method signatures
6. Keep all existing formatting and indentation exactly the same
7. Only rename variables to more descriptive names that clearly indicate their purpose

VARIABLE RENAMING GUIDELINES:
- Replace single letters (x, y, i, j) with descriptive names (index, count, coordinate)
- Replace abbreviations (usr, msg, cfg) with full words (user, message, config)
- Replace generic names (data, item, obj) with specific names (user_data, menu_item, configuration_object)
- Use camelCase for {language} variables where appropriate
- Ensure renamed variables are contextually meaningful
- Don't rename well-known conventions (e.g., 'self' in Python, 'this' in JavaScript)

FILE: {filename}
LANGUAGE: {language}

SOURCE CODE:
```{language}
{code_content}
```

Return ONLY the modified code with renamed variables. Do not include any explanations, comments, or additional text. The code should be functionally identical to the original, with only variable names improved.

RESPONSE FORMAT:
Return as JSON with this exact structure:
{{
    "modified_code": "... the complete modified code here ...",
    "changes": [
        {{"old_name": "x", "new_name": "user_index", "line": 5}},
        {{"old_name": "data", "new_name": "user_profile", "line": 12}}
    ]
}}

Make sure the modified_code is complete and runnable."""

    def get_variable_analysis_prompt(self, language: str, filename: str, code_content: str) -> str:
        """
        Generate a prompt for analyzing variables that could be renamed.
        
        Args:
            language: Programming language
            filename: Name of the file
            code_content: Source code content
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze the following {language} code and identify variables that could benefit from better naming.

FILE: {filename}
LANGUAGE: {language}

SOURCE CODE:
```{language}
{code_content}
```

Identify variables that are:
1. Single letters (x, y, i, j, etc.) that could be more descriptive
2. Abbreviations that could be expanded (usr, msg, cfg, etc.)
3. Generic names that could be more specific (data, item, obj, etc.)
4. Poor naming that doesn't indicate purpose

EXCLUDE:
- Well-known conventions (self, this, etc.)
- Loop counters where context is clear
- Mathematical variables where single letters are appropriate
- Variables with already good names

Return as JSON:
{{
    "variables_to_rename": [
        {{
            "current_name": "x",
            "suggested_name": "user_index",
            "reason": "Single letter variable used as user array index",
            "line_number": 5,
            "context": "for x in users:"
        }}
    ],
    "total_candidates": 3,
    "complexity_score": "low|medium|high"
}}"""

    def get_batch_rename_prompt(self, language: str, variables_info: List[Dict]) -> str:
        """
        Generate a prompt for batch renaming multiple variables.
        
        Args:
            language: Programming language
            variables_info: List of variable information
            
        Returns:
            Formatted prompt string
        """
        variables_list = "\n".join([
            f"- {var['current_name']} -> {var['suggested_name']} (Line {var.get('line_number', '?')}): {var.get('reason', '')}"
            for var in variables_info
        ])
        
        return f"""You are renaming multiple variables in {language} code to improve readability.

VARIABLES TO RENAME:
{variables_list}

RULES:
1. Only rename the specified variables
2. Ensure all instances of each variable are consistently renamed
3. Maintain all code logic and functionality
4. Keep proper scoping (don't rename variables outside their scope)
5. Use contextually appropriate names

Return the mapping of old names to new names as JSON:
{{
    "rename_mapping": {{
        "old_name1": "new_name1",
        "old_name2": "new_name2"
    }},
    "conflicts_detected": [],
    "scope_warnings": []
}}""" 