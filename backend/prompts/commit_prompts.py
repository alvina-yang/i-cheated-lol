"""
Prompt templates for commit message generation.
Contains prompts for creating realistic commit messages.
"""


class CommitPrompts:
    """Centralized prompt templates for commit message generation."""
    
    COMMIT_MESSAGE_GENERATION_PROMPT = """You are a Git Commit Message Generator that creates realistic commit messages for hackathon projects.

Your task is to generate authentic commit messages that would be written by developers during a hackathon.

Project Context:
- Project Name: {project_name}
- Technologies: {technologies}
- File Changes: {file_changes}
- Change Type: {change_type}
- Hackathon Theme: {hackathon_theme}

Generate commit messages that:
1. Are concise but descriptive (50-72 characters for title)
2. Use conventional commit prefixes when appropriate (feat:, fix:, docs:, refactor:, etc.)
3. Sound like they were written during a hackathon (time pressure, iterative development)
4. Reference specific features or fixes being implemented
5. Show progression of hackathon development

Examples of good hackathon commit messages:
- "feat: add user authentication with JWT tokens"
- "fix: resolve API endpoint timeout issues"
- "docs: update README with setup instructions"
- "refactor: optimize database queries for performance"
- "feat: implement real-time chat functionality"
- "fix: handle edge cases in data validation"

Return a JSON array of 5-8 diverse commit messages:
["commit message 1", "commit message 2", ...]

Make them realistic and varied, showing typical hackathon development progression."""

    COMMIT_SEQUENCE_PROMPT = """You are a Git Commit Sequence Generator for hackathon projects.

Create a realistic sequence of commit messages that tells the story of developing a hackathon project.

Project Information:
- Name: {project_name}
- Description: {project_description}
- Technologies: {technologies}
- Number of commits needed: {commit_count}
- Hackathon duration: {hackathon_duration} hours

Generate a chronological sequence of commits that shows:
1. Initial project setup and configuration
2. Core feature development
3. Bug fixes and improvements
4. Final polishing and documentation

The sequence should:
- Start with project initialization
- Show iterative development typical of hackathons
- Include realistic mix of features, fixes, and improvements
- End with final touches and documentation
- Use appropriate commit message conventions

Return a JSON array of commit messages in chronological order:
["Initial project setup", "Add core functionality", ...]

Make it tell a realistic hackathon development story."""

    COMMIT_DESCRIPTION_PROMPT = """You are a Git Commit Description Generator for detailed commit messages.

Create a realistic commit description (body text) for the following commit.

Commit Title: {commit_title}
File Changes: {file_changes}
Project Context: {project_context}

Generate a commit description that:
1. Explains what was changed and why
2. Mentions specific files or components affected
3. Describes any technical decisions made
4. Includes any relevant implementation details
5. Sounds like it was written during a hackathon

Keep it concise but informative (2-4 lines max).

Return just the commit description text (no JSON formatting)."""

    @staticmethod
    def get_commit_message_prompt(project_name: str, technologies: list, file_changes: str, 
                                change_type: str, hackathon_theme: str = "general") -> str:
        """
        Get the commit message generation prompt with project data.
        
        Args:
            project_name: Name of the project
            technologies: List of technologies used
            file_changes: Description of files changed
            change_type: Type of change (feature, fix, docs, etc.)
            hackathon_theme: Theme or context of the hackathon
            
        Returns:
            Formatted prompt string
        """
        return CommitPrompts.COMMIT_MESSAGE_GENERATION_PROMPT.format(
            project_name=project_name,
            technologies=', '.join(technologies) if technologies else 'various',
            file_changes=file_changes,
            change_type=change_type,
            hackathon_theme=hackathon_theme
        )
    
    @staticmethod
    def get_commit_sequence_prompt(project_name: str, project_description: str, 
                                 technologies: list, commit_count: int, 
                                 hackathon_duration: int = 48) -> str:
        """
        Get the commit sequence generation prompt.
        
        Args:
            project_name: Name of the project
            project_description: Description of the project
            technologies: List of technologies used
            commit_count: Number of commits to generate
            hackathon_duration: Duration of hackathon in hours
            
        Returns:
            Formatted prompt string
        """
        return CommitPrompts.COMMIT_SEQUENCE_PROMPT.format(
            project_name=project_name,
            project_description=project_description,
            technologies=', '.join(technologies) if technologies else 'various',
            commit_count=commit_count,
            hackathon_duration=hackathon_duration
        )
    
    @staticmethod
    def get_commit_description_prompt(commit_title: str, file_changes: str, 
                                    project_context: str) -> str:
        """
        Get the commit description generation prompt.
        
        Args:
            commit_title: Title of the commit
            file_changes: Description of changed files
            project_context: Context about the project
            
        Returns:
            Formatted prompt string
        """
        return CommitPrompts.COMMIT_DESCRIPTION_PROMPT.format(
            commit_title=commit_title,
            file_changes=file_changes,
            project_context=project_context
        ) 