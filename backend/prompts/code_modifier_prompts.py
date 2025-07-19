"""
Prompt templates for code modification operations.
Contains prompts for adding comments and changing variable names.
"""


class CodeModifierPrompts:
    """Centralized prompt templates for code modification functionality."""
    
    COMMENT_GENERATION_PROMPT = """You are a Code Comment Generator that adds realistic, helpful comments to code.

Your task is to analyze the following code and add appropriate comments that would be written by a developer during a hackathon.

Code Information:
- Language: {language}
- File: {filename}
- Code:
{code_content}

Add comments that:
1. Explain complex logic or algorithms
2. Describe the purpose of functions/classes
3. Clarify non-obvious code sections
4. Add TODOs for potential improvements
5. Sound natural and helpful (not over-commented)

Comment Guidelines:
- Use appropriate comment syntax for the language
- Keep comments concise but informative
- Focus on WHY rather than WHAT
- Add comments strategically, not on every line
- Use hackathon-appropriate language (mentions of time constraints, quick fixes, etc.)

Return the modified code with comments added. Maintain original formatting and structure."""

    VARIABLE_RENAME_PROMPT = """You are a Variable Renaming Assistant that improves code readability.

Your task is to rename variables in the following code to be more descriptive and follow best practices.

Code Information:
- Language: {language}
- File: {filename}
- Code:
{code_content}

Renaming Guidelines:
1. Use descriptive names that clearly indicate purpose
2. Follow language-specific naming conventions
3. Avoid abbreviations unless commonly understood
4. Keep names concise but clear
5. Maintain consistency throughout the code
6. Don't rename standard library functions or reserved keywords

Examples of good renames:
- `data` → `user_data` or `api_response`
- `i` → `index` or `item_count` (context dependent)
- `temp` → `temp_file` or `temp_value`
- `result` → `processed_data` or `calculation_result`

Return the modified code with improved variable names. Maintain original formatting and structure."""

    FUNCTION_DOCUMENTATION_PROMPT = """You are a Function Documentation Generator that adds proper docstrings.

Your task is to add comprehensive docstrings to functions in the following code.

Code Information:
- Language: {language}
- File: {filename}
- Code:
{code_content}

Documentation Guidelines:
1. Use appropriate docstring format for the language (Google/NumPy style for Python, JSDoc for JavaScript)
2. Include description of what the function does
3. Document parameters with types and descriptions
4. Document return values with types and descriptions
5. Add examples when helpful
6. Mention any exceptions that might be raised
7. Keep descriptions clear and concise

Return the modified code with proper docstrings added. Maintain original formatting and structure."""

    FILE_ANALYSIS_PROMPT = """You are a Code File Analyzer that determines the best modifications to make.

Analyze the following code file and determine what modifications would be most beneficial.

Code Information:
- Language: {language}
- File: {filename}
- File Size: {file_size} lines
- Code:
{code_content}

Analysis Criteria:
1. **Comment Opportunities**: Identify sections that need comments (complex logic, unclear purpose)
2. **Variable Quality**: Assess variable names for clarity and descriptiveness
3. **Documentation Gaps**: Find functions/classes missing docstrings
4. **Code Complexity**: Identify areas that would benefit from explanation
5. **Maintainability**: Suggest improvements for code readability

Return a JSON object with your analysis:
{{
    "needs_comments": <true/false>,
    "comment_priority_areas": ["area1", "area2", ...],
    "needs_variable_renaming": <true/false>,
    "poor_variable_names": ["var1", "var2", ...],
    "needs_documentation": <true/false>,
    "undocumented_functions": ["func1", "func2", ...],
    "complexity_score": <1-10>,
    "recommended_modifications": ["modification1", "modification2", ...],
    "estimated_improvement": <1-10>
}}"""

    @staticmethod
    def get_comment_generation_prompt(language: str, filename: str, code_content: str) -> str:
        """
        Get the comment generation prompt with code data.
        
        Args:
            language: Programming language of the code
            filename: Name of the file
            code_content: The code to add comments to
            
        Returns:
            Formatted prompt string
        """
        return CodeModifierPrompts.COMMENT_GENERATION_PROMPT.format(
            language=language,
            filename=filename,
            code_content=code_content
        )
    
    @staticmethod
    def get_variable_rename_prompt(language: str, filename: str, code_content: str) -> str:
        """
        Get the variable renaming prompt with code data.
        
        Args:
            language: Programming language of the code
            filename: Name of the file
            code_content: The code to rename variables in
            
        Returns:
            Formatted prompt string
        """
        return CodeModifierPrompts.VARIABLE_RENAME_PROMPT.format(
            language=language,
            filename=filename,
            code_content=code_content
        )
    
    @staticmethod
    def get_function_documentation_prompt(language: str, filename: str, code_content: str) -> str:
        """
        Get the function documentation prompt with code data.
        
        Args:
            language: Programming language of the code
            filename: Name of the file
            code_content: The code to add documentation to
            
        Returns:
            Formatted prompt string
        """
        return CodeModifierPrompts.FUNCTION_DOCUMENTATION_PROMPT.format(
            language=language,
            filename=filename,
            code_content=code_content
        )
    
    @staticmethod
    def get_file_analysis_prompt(language: str, filename: str, file_size: int, code_content: str) -> str:
        """
        Get the file analysis prompt with code data.
        
        Args:
            language: Programming language of the code
            filename: Name of the file
            file_size: Number of lines in the file
            code_content: The code to analyze
            
        Returns:
            Formatted prompt string
        """
        return CodeModifierPrompts.FILE_ANALYSIS_PROMPT.format(
            language=language,
            filename=filename,
            file_size=file_size,
            code_content=code_content
        ) 