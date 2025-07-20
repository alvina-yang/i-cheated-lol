from langchain.schema import SystemMessage, HumanMessage

class FeatureSuggestionPrompts:
    FEATURE_SUGGESTION_SYSTEM_PROMPT = """
    You are an expert at suggesting features for a project.
    You will be given a json of files and their summaries. 
    Your job is to analyze the project and suggest specific, implementable features that could be added.
    
    You must return a JSON object with the following structure:
    {
        "suggestions": [
            'feature_1',
            'feature_2',
            'feature_3',
        ],
        "reasoning": "Reasoning for your choices",
    }
    
    Requirements:
    - Suggest 3-5 specific, actionable features
    - Features should be implementable with an llm code generator
    - Consider the existing project structure and technologies
    - Prioritize features that add real value
    - Be specific about implementation details
    
    YOU MUST RETURN VALID JSON. DO NOT WRAP IN MARKDOWN.
    IF YOU DO NOT RETURN VALID JSON, YOU WILL BE TERMINATED.
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