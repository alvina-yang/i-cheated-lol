"""
Prompt templates for git operations and repository management.
Contains prompts for git history rewriting and repository operations.
"""


class GitPrompts:
    """Centralized prompt templates for git operations."""
    
    HISTORY_REWRITE_ANALYSIS_PROMPT = """You are a Git History Rewriter that creates realistic commit histories for hackathon projects.

Your task is to analyze the existing git history and create a new timeline that appears to be from a hackathon.

Project Information:
- Project Name: {project_name}
- Technologies: {technologies}
- Original commit count: {original_commits}
- Hackathon start: {hackathon_start}
- Hackathon duration: {hackathon_duration} hours
- Developer: {developer_name}
- Current commits: {current_commits}

Create a rewrite plan that:
1. Distributes commits realistically across the hackathon timeline
2. Shows typical hackathon development patterns (bursts of activity, late-night commits)
3. Includes realistic commit message progression
4. Maintains logical development flow
5. Shows time pressure and iterative development

Return a JSON object with the rewrite plan:
{{
    "timeline_strategy": "<description of timing strategy>",
    "commit_distribution": [
        {{
            "original_commit": "<original commit hash>",
            "new_timestamp": "<new timestamp>",
            "time_offset_hours": <hours from hackathon start>,
            "reasoning": "<why this timing makes sense>"
        }}
    ],
    "development_phases": [
        {{
            "phase": "<setup/core/polish>",
            "time_range": "<start-end hours>",
            "expected_commits": <number>,
            "typical_activities": ["activity1", "activity2"]
        }}
    ],
    "realism_factors": ["factor1", "factor2", ...],
    "estimated_success": <1-10>
}}"""

    TERMINAL_OUTPUT_PROMPT = """You are a Terminal Output Generator that creates realistic git command outputs.

Your task is to generate authentic terminal output that would be seen during git operations.

Operation Context:
- Command: {command}
- Project: {project_name}
- Current directory: {current_dir}
- Operation type: {operation_type}
- Progress: {progress_percentage}%

Generate terminal output that:
1. Shows realistic git command responses
2. Includes appropriate progress indicators
3. Displays file changes and operations
4. Shows any warnings or informational messages
5. Maintains consistent formatting and style

Output should look like real terminal output with proper formatting and timing."""

    GIT_FILTER_BRANCH_PROMPT = """You are a Git Filter Branch Output Generator.

Create realistic output for git filter-branch operations during history rewriting.

Operation Details:
- Total commits: {total_commits}
- Current commit: {current_commit}
- Progress: {progress}%
- Operation: {operation_description}
- Time elapsed: {elapsed_time}

Generate output that shows:
1. Rewrite progress with commit hashes
2. Processing indicators and timestamps
3. File modification counts
4. Any warnings or messages
5. Realistic processing timing

Format as authentic git filter-branch terminal output."""

    REPOSITORY_SETUP_PROMPT = """You are a Repository Setup Assistant that helps configure new repository destinations.

Your task is to analyze the repository URL and provide setup instructions.

Repository Information:
- Original URL: {original_url}
- Target URL: {target_url}
- Project name: {project_name}
- User preferences: {user_preferences}

Generate setup instructions that:
1. Validate the new repository URL
2. Check if the repository exists and is accessible
3. Provide git commands to change the remote
4. Suggest branch and configuration setup
5. Handle authentication requirements

Return a JSON object with setup instructions:
{{
    "url_valid": <true/false>,
    "repository_exists": <true/false>,
    "access_method": "<https/ssh>",
    "setup_commands": ["command1", "command2", ...],
    "authentication_required": <true/false>,
    "configuration_steps": ["step1", "step2", ...],
    "potential_issues": ["issue1", "issue2", ...],
    "success_probability": <1-10>
}}"""

    @staticmethod
    def get_history_rewrite_prompt(project_name: str, technologies: list, original_commits: int,
                                 hackathon_start: str, hackathon_duration: int, developer_name: str,
                                 current_commits: str) -> str:
        """
        Get the history rewrite analysis prompt.
        
        Args:
            project_name: Name of the project
            technologies: List of technologies used
            original_commits: Number of original commits
            hackathon_start: Start date/time of hackathon
            hackathon_duration: Duration in hours
            developer_name: Name of the developer
            current_commits: Current commit information
            
        Returns:
            Formatted prompt string
        """
        return GitPrompts.HISTORY_REWRITE_ANALYSIS_PROMPT.format(
            project_name=project_name,
            technologies=', '.join(technologies) if technologies else 'various',
            original_commits=original_commits,
            hackathon_start=hackathon_start,
            hackathon_duration=hackathon_duration,
            developer_name=developer_name,
            current_commits=current_commits
        )
    
    @staticmethod
    def get_terminal_output_prompt(command: str, project_name: str, current_dir: str,
                                 operation_type: str, progress_percentage: int) -> str:
        """
        Get the terminal output generation prompt.
        
        Args:
            command: The git command being executed
            project_name: Name of the project
            current_dir: Current directory
            operation_type: Type of operation
            progress_percentage: Progress percentage
            
        Returns:
            Formatted prompt string
        """
        return GitPrompts.TERMINAL_OUTPUT_PROMPT.format(
            command=command,
            project_name=project_name,
            current_dir=current_dir,
            operation_type=operation_type,
            progress_percentage=progress_percentage
        )
    
    @staticmethod
    def get_filter_branch_prompt(total_commits: int, current_commit: int, progress: int,
                               operation_description: str, elapsed_time: str) -> str:
        """
        Get the git filter-branch output prompt.
        
        Args:
            total_commits: Total number of commits
            current_commit: Current commit number
            progress: Progress percentage
            operation_description: Description of the operation
            elapsed_time: Time elapsed
            
        Returns:
            Formatted prompt string
        """
        return GitPrompts.GIT_FILTER_BRANCH_PROMPT.format(
            total_commits=total_commits,
            current_commit=current_commit,
            progress=progress,
            operation_description=operation_description,
            elapsed_time=elapsed_time
        )
    
    @staticmethod
    def get_repository_setup_prompt(original_url: str, target_url: str, project_name: str,
                                  user_preferences: dict) -> str:
        """
        Get the repository setup prompt.
        
        Args:
            original_url: Original repository URL
            target_url: Target repository URL
            project_name: Name of the project
            user_preferences: User preferences dictionary
            
        Returns:
            Formatted prompt string
        """
        return GitPrompts.REPOSITORY_SETUP_PROMPT.format(
            original_url=original_url,
            target_url=target_url,
            project_name=project_name,
            user_preferences=str(user_preferences)
        ) 