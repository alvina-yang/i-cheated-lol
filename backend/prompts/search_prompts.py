"""
Prompt templates for search-related agents.
Contains prompts for search query generation and project filtering.
"""


class SearchPrompts:
    """Centralized prompt templates for search functionality."""
    
    SEARCH_QUERY_GENERATION_PROMPT = """You are a GitHub Search Query Generator for hackathon projects.

Your task is to generate diverse, effective search queries to find hackathon winner projects that use specific technologies.

Technologies to focus on: {technologies}

Generate search queries that will find:
1. Hackathon winner projects using these technologies
2. Competition projects with these technologies  
3. Student hackathon projects with these technologies
4. Award-winning projects using these technologies

Requirements:
- Each query should include hackathon context keywords
- Include the specified technologies naturally
- Vary the query structure and keywords
- Focus on projects that would realistically be built in hackathons
- Avoid queries that would return enterprise/large-scale projects

Return a JSON array of search query strings:
["query1", "query2", "query3", ...]

Generate 8-12 diverse queries."""

    PROJECT_RELEVANCE_ANALYSIS_PROMPT = """You are a Project Relevance Analyzer for hackathon discovery.

Analyze the following project and determine if it's a relevant hackathon project using the specified technologies.

Project Information:
- Name: {project_name}
- Description: {project_description}
- Topics: {project_topics}
- Language: {project_language}
- Stars: {project_stars}
- Forks: {project_forks}

Target Technologies: {technologies}

Evaluation Criteria:
1. **Hackathon Context**: Does this appear to be from a hackathon, competition, or student project?
2. **Technology Match**: Does it use the specified technologies?
3. **Project Scope**: Is it appropriately sized for a hackathon (not too enterprise, not too simple)?
4. **Innovation**: Does it show creative use of technology suitable for hackathons?

Return a JSON object:
{{
    "is_relevant": <true/false>,
    "hackathon_score": <0-10>,
    "technology_match_score": <0-10>,
    "reasoning": "<brief explanation>",
    "confidence": <0-10>
}}"""

    @staticmethod
    def get_search_query_prompt(technologies: list) -> str:
        """
        Get the search query generation prompt with technologies.
        
        Args:
            technologies: List of technologies to search for
            
        Returns:
            Formatted prompt string
        """
        tech_list = ', '.join(technologies) if technologies else "any"
        return SearchPrompts.SEARCH_QUERY_GENERATION_PROMPT.format(technologies=tech_list)
    
    @staticmethod
    def get_relevance_analysis_prompt(project_data: dict, technologies: list) -> str:
        """
        Get the project relevance analysis prompt with project data.
        
        Args:
            project_data: Dictionary containing project information
            technologies: List of target technologies
            
        Returns:
            Formatted prompt string
        """
        return SearchPrompts.PROJECT_RELEVANCE_ANALYSIS_PROMPT.format(
            project_name=project_data.get('name', 'Unknown'),
            project_description=project_data.get('description', 'No description'),
            project_topics=', '.join(project_data.get('topics', [])),
            project_language=project_data.get('language', 'Unknown'),
            project_stars=project_data.get('stars', 0),
            project_forks=project_data.get('forks', 0),
            technologies=', '.join(technologies) if technologies else 'any'
        ) 