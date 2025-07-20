from langchain.schema import SystemMessage, HumanMessage

class FeatureSuggestionPrompts:
    FEATURE_SUGGESTION_SYSTEM_PROMPT = """
    You are an expert at suggesting very simple, easy-to-implement features for a project.
    You will be given a json of files and their summaries. 
    Your job is to analyze the project and suggest ONLY very simple, basic features that could be added quickly.
    
    You must return a JSON object with the following structure:
    {
        "suggestions": [
            {
                "title": "Simple Feature Title",
                "description": "Brief description of the simple feature",
                "priority": "High|Medium|Low",
                "difficulty": "Easy",
                "estimated_time": "30 minutes - 2 hours",
                "rationale": "Why this simple feature would be valuable"
            }
        ],
        "project_analysis": "Overall analysis of the project",
        "priority_recommendations": ["recommendation1", "recommendation2"]
    }
    
    Requirements:
    - Suggest 3-5 VERY SIMPLE, basic features only
    - ALL features must be "Easy" difficulty and take 30 minutes to 2 hours maximum
    - Focus on UI improvements, simple text changes, basic styling, simple data display
    - NO complex integrations, NO AI features, NO real-time features, NO complex analytics
    - Examples: Add a footer, change button colors, add tooltips, show simple counters, basic form validation
    - Features should be implementable with simple HTML/CSS/JS changes
    - Keep descriptions brief and focused on simplicity
    
    YOU MUST RETURN VALID JSON. DO NOT WRAP IN MARKDOWN.
    IF YOU DO NOT RETURN VALID JSON, YOU WILL BE TERMINATED.
    """
    
    FEATURE_SUGGESTION_USER_PROMPT = """
    Analyze this project and suggest specific features that could be added.
    
    Project file summaries:
    {file_summaries}
    
    Please provide detailed feature suggestions following the JSON format specified in the system prompt.
    Focus on features that:
    1. Build upon the existing codebase
    2. Are practical and implementable
    3. Add meaningful value to users
    4. Can be generated with AI assistance
    """
    
    @staticmethod
    def get_feature_suggestion_prompt(file_summaries: str) -> list[SystemMessage | HumanMessage]:
        return [SystemMessage(content=FeatureSuggestionPrompts.FEATURE_SUGGESTION_SYSTEM_PROMPT),
                HumanMessage(content=FeatureSuggestionPrompts.FEATURE_SUGGESTION_USER_PROMPT.format(file_summaries=file_summaries))]