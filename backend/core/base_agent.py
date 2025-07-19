"""
Base agent class for all Chameleon agents.
Provides common functionality and interface for agent implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI 
# from groq import Groq  # Commented out for OpenAI
from .config import Config


class BaseAgent(ABC):
    """
    Abstract base class for all Chameleon agents.
    
    Provides common functionality like LLM initialization, configuration validation,
    and standardized logging.
    """
    
    def __init__(self, agent_name: str, temperature: Optional[float] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name of the agent for logging purposes
            temperature: LLM temperature override (uses config default if None)
        """
        self.agent_name = agent_name
        self.config = Config
        
        # Validate configuration
        self.config.validate()
        
        # Initialize LLM
        self.llm = ChatOpenAI(  # Uncommented for OpenAI
            model=self.config.LLM_MODEL,
            api_key=self.config.OPENAI_API_KEY,
            temperature=temperature or self.config.LLM_TEMPERATURE
        )
        # self.llm = Groq(  # Commented out for OpenAI
        #     api_key=self.config.GROQ_API_KEY
        # )
        self.temperature = temperature or self.config.LLM_TEMPERATURE
        
        self.log(f"Initialized {self.agent_name}")
    
    def log(self, message: str, level: str = "INFO"):
        """
        Log a message with agent context.
        
        Args:
            message: Message to log
            level: Log level (INFO, DEBUG, ERROR, etc.)
        """
        print(f"[{level}] {self.agent_name}: {message}")
    
    def log_step(self, step: str, details: str = ""):
        """
        Log a major step in the agent's process.
        
        Args:
            step: The step being performed
            details: Additional details about the step
        """
        separator = f"  {details}" if details else ""
        print(f"  {step}{separator}")
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the main functionality of the agent.
        
        This method must be implemented by all concrete agent classes.
        """
        pass
    
    def format_prompt_with_data(self, prompt_template: str, **kwargs) -> str:
        """
        Format a prompt template with provided data.
        
        Args:
            prompt_template: The prompt template string
            **kwargs: Data to substitute in the template
            
        Returns:
            Formatted prompt string
        """
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            self.log(f"Missing required prompt parameter: {e}", "ERROR")
            raise
    
    def invoke_llm(self, prompt: str, parse_json: bool = False) -> Any:
        """
        Invoke the LLM with a prompt and handle response.
        
        Args:
            prompt: The prompt to send to the LLM
            parse_json: Whether to attempt JSON parsing of the response
            
        Returns:
            LLM response (string or parsed JSON if parse_json=True)
        """
        try:
            # Original LangChain method (uncommented for OpenAI)
            response = self.llm.invoke(prompt)
            content = response.content
            
            # Groq API call (commented out for OpenAI)
            # response = self.llm.chat.completions.create(
            #     model=self.config.LLM_MODEL,
            #     messages=[
            #         {"role": "user", "content": prompt}
            #     ],
            #     temperature=self.temperature,
            #     max_tokens=2048
            # )
            # content = response.choices[0].message.content
            
            # Ensure content is a string
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            elif content is None:
                content = ""
            else:
                content = str(content)
            
            if parse_json and content:
                import json
                # Try to extract JSON from the response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    self.log(f"No JSON found in LLM response", "ERROR")
                    return None
            
            return content
            
        except Exception as e:
            self.log(f"Error invoking LLM: {e}", "ERROR")
            raise 