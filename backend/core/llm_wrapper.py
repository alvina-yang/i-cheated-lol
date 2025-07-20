"""
Unified LLM wrapper that provides a consistent interface for different LLM providers.
Supports both OpenAI and Groq APIs with automatic fallback and error handling.
"""

import json
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod


class BaseLLMWrapper(ABC):
    """Abstract base class for LLM wrappers."""
    
    def __init__(self, model: str, api_key: str, temperature: float = 0.3):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
    
    @abstractmethod
    def invoke(self, prompt: str, parse_json: bool = False) -> Any:
        """Invoke the LLM with a prompt and return the response."""
        pass


class GroqLLMWrapper(BaseLLMWrapper):
    """Groq API wrapper that provides a consistent interface."""
    
    def __init__(self, model: str, api_key: str, temperature: float = 0.3):
        super().__init__(model, api_key, temperature)
        from groq import Groq
        self.client = Groq(api_key=api_key)
    
    def invoke(self, prompt: str, parse_json: bool = False) -> Any:
        """
        Invoke the Groq LLM with a prompt and handle response.
        
        Args:
            prompt: The prompt to send to the LLM
            parse_json: Whether to attempt JSON parsing of the response
            
        Returns:
            LLM response (string or parsed JSON if parse_json=True)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=4096
            )
            
            content = response.choices[0].message.content
            
            # Ensure content is a string
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            elif content is None:
                content = ""
            else:
                content = str(content)
            
            if parse_json and content:
                # Try to extract JSON from the response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    print(f"No JSON found in LLM response")
                    return None
            
            return content
            
        except Exception as e:
            print(f"Error invoking Groq LLM: {e}")
            raise


class OpenAILLMWrapper(BaseLLMWrapper):
    """OpenAI API wrapper that provides a consistent interface."""
    
    def __init__(self, model: str, api_key: str, temperature: float = 0.3):
        super().__init__(model, api_key, temperature)
        from langchain_openai import ChatOpenAI
        self.client = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature
        )
    
    def invoke(self, prompt: str, parse_json: bool = False) -> Any:
        """
        Invoke the OpenAI LLM with a prompt and handle response.
        
        Args:
            prompt: The prompt to send to the LLM
            parse_json: Whether to attempt JSON parsing of the response
            
        Returns:
            LLM response (string or parsed JSON if parse_json=True)
        """
        try:
            response = self.client.invoke(prompt)
            content = response.content
            
            # Ensure content is a string
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            elif content is None:
                content = ""
            else:
                content = str(content)
            
            if parse_json and content:
                # Try to extract JSON from the response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    print(f"No JSON found in LLM response")
                    return None
            
            return content
            
        except Exception as e:
            print(f"Error invoking OpenAI LLM: {e}")
            raise


def create_llm_wrapper(provider: str, model: str, api_key: str, temperature: float = 0.3) -> BaseLLMWrapper:
    """
    Factory function to create the appropriate LLM wrapper.
    
    Args:
        provider: Either 'groq' or 'openai'
        model: The model name to use
        api_key: API key for the provider
        temperature: Temperature setting for the LLM
        
    Returns:
        Appropriate LLM wrapper instance
    """
    if provider.lower() == 'groq':
        return GroqLLMWrapper(model, api_key, temperature)
    elif provider.lower() == 'openai':
        return OpenAILLMWrapper(model, api_key, temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_default_llm_wrapper(config) -> BaseLLMWrapper:
    """
    Get the default LLM wrapper based on configuration.
    
    Args:
        config: Configuration object with LLM settings
        
    Returns:
        Configured LLM wrapper instance
    """
    # Determine provider based on available API keys and model
    if hasattr(config, 'GROQ_API_KEY') and config.GROQ_API_KEY:
        return create_llm_wrapper('groq', config.LLM_MODEL, config.GROQ_API_KEY, config.LLM_TEMPERATURE)
    elif hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
        return create_llm_wrapper('openai', config.LLM_MODEL, config.OPENAI_API_KEY, config.LLM_TEMPERATURE)
    else:
        raise ValueError("No valid API key found for LLM providers (Groq or OpenAI)") 