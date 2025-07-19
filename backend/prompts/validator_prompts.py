"""
Prompt templates for the ValidatorAgent.
Contains all prompts used for project analysis and selection.
"""


class ValidatorPrompts:
    """Centralized prompt templates for project validation and selection."""
    
    DEEP_ANALYSIS_PROMPT = """You are an expert Hackathon Project Evaluator. Your task is to select the BEST hackathon project{tech_context} based on deep code analysis.

I have analyzed the actual codebases, README files, and project structures. Evaluate based on:

1. **CREATIVITY & INNOVATION**: Unique ideas, creative solutions, innovative use of technology
2. **TECHNOLOGICAL COMPLEXITY**: Sophisticated implementation, multiple technologies, advanced features
3. **HACKATHON CONTEXT**: Clear evidence this was built for a hackathon (time constraints, specific problem solving)
4. **CODE QUALITY**: Well-structured code, good documentation, proper implementation
5. **COMPLETENESS**: Functional project with clear purpose and working features
6. **TECHNOLOGY INTEGRATION**: Effective use of specified technologies{tech_list}

Project Analyses:
{project_analyses}

Based on the actual code analysis, README content, and project complexity, select the ONE project that demonstrates the best combination of creativity, technological sophistication, and hackathon-appropriate scope.

Return your response as a JSON object:
{{
    "selected_index": <index_of_best_project>,
    "reasoning": "<detailed explanation focusing on creativity, technical complexity, and code analysis>",
    "creativity_score": <score_1_to_10>,
    "complexity_score": <score_1_to_10>,
    "overall_confidence": <confidence_1_to_10>
}}

Focus especially on projects that show genuine innovation and technical depth suitable for a hackathon."""

    FALLBACK_SELECTION_PROMPT = """You are a Hackathon Project Evaluator. Select the BEST hackathon winner project{tech_context} from the following list.

Consider these criteria when evaluating:
1. **Hackathon Context**: Clear evidence this is from a hackathon (winner, award, competition)
2. **Technology Relevance**: How well it uses the specified technologies{tech_list}
3. **Project Scope**: Appropriate hackathon-sized project (not too big/enterprise, not too simple)
4. **Innovation**: Creative solution or unique approach for a hackathon
5. **Completeness**: Functional project that was actually built during hackathon
6. **Code Quality**: Well-documented hackathon project
7. **Technical Implementation**: Good use of specified technologies in hackathon context

Projects to evaluate:
{project_summaries}

Please analyze each project and select the ONE best hackathon project. Return your response as a JSON object with:
{{
    "selected_index": <index_of_best_project>,
    "reasoning": "<detailed explanation focusing on why this is the best hackathon project>",
    "confidence": <confidence_score_from_1_to_10>
}}

Focus especially on hackathon context, technology usage, and project quality for a hackathon setting."""

    @staticmethod
    def get_deep_analysis_prompt(project_analyses: str, technologies: list = None) -> str:
        """
        Get the deep analysis prompt with formatted data.
        
        Args:
            project_analyses: JSON string of project analysis data
            technologies: List of technologies to focus on
            
        Returns:
            Formatted prompt string
        """
        tech_context = f" using technologies: {', '.join(technologies)}" if technologies else ""
        tech_list = f": {', '.join(technologies)}" if technologies else ""
        
        return ValidatorPrompts.DEEP_ANALYSIS_PROMPT.format(
            tech_context=tech_context,
            tech_list=tech_list,
            project_analyses=project_analyses
        )
    
    @staticmethod
    def get_fallback_selection_prompt(project_summaries: str, technologies: list = None) -> str:
        """
        Get the fallback selection prompt with formatted data.
        
        Args:
            project_summaries: JSON string of project summaries
            technologies: List of technologies to focus on
            
        Returns:
            Formatted prompt string
        """
        tech_context = f" using technologies: {', '.join(technologies)}" if technologies else ""
        tech_list = f": {', '.join(technologies)}" if technologies else ""
        
        return ValidatorPrompts.FALLBACK_SELECTION_PROMPT.format(
            tech_context=tech_context,
            tech_list=tech_list,
            project_summaries=project_summaries
        ) 