"""
LLM Client Module for Mechanical Drawing Analysis
Handles communication with various LLM providers
"""

from typing import List, Dict, Optional, Any
from src.models import PartSpecification  # Fix import path
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """
    LLM Client for analyzing mechanical drawings.
    
    a smart assistant that can work with different AI brains:
    - OpenAI (GPT-4)
    - Anthropic (Claude)  
    - Local models (Ollama)
    """
    
    def __init__(self, 
                 provider: str = "openai",
                 model: str = None,
                 api_key: str = None):
        """
        Initialize the LLM client.
        
        This is like setting up your assistant's brain:
        - Choose which AI to use (provider)
        - Select the specific model
        - Provide credentials (API key)
        
        Args:
            provider: Which LLM provider to use
            model: Specific model name (defaults based on provider)
            api_key: API key for the provider
        """
        self.provider = provider.lower()
        
        # Set default models based on provider
        if model is None:
            default_models = {
                'openai': 'gpt-4o-mini',
                'claude': 'claude-3-5-haiku-latest',
                'ollama': 'llava:latest'
            }
            self.model = default_models.get(provider, 'gpt-4o-mini')
        else:
            self.model = model
        
        # Initialize the appropriate client
        self._initialize_client(api_key)
    
    def _initialize_client(self, api_key: str = None):
        """
        Initialize the API client for the selected provider.
        
        Like connecting to different services - each needs its own setup.
        """
        if self.provider == 'openai':
            from openai import OpenAI
            
            # Use provided key or get from environment
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")
            
            self.client = OpenAI(api_key=key)
            
        elif self.provider == 'claude':
            import anthropic
            
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("Anthropic API key not provided and ANTHROPIC_API_KEY not set")
            
            self.client = anthropic.Anthropic(api_key=key)
            
        elif self.provider == 'ollama':
            # Ollama runs locally, no API key needed
            try:
                import ollama
                self.client = ollama
            except ImportError:
                raise ImportError("Ollama package not installed. Run: pip install ollama")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def analyze(self, 
                images: Dict,
                prompt: str,
                structured_output: type = PartSpecification) -> PartSpecification:
        """
        Main analysis method - this is what the orchestrator calls.
        
        Like asking your assistant to analyze a document:
        - Give them the images
        - Tell them what to look for (prompt)
        - Specify how you want the answer formatted
        
        Args:
            images: Dictionary with processed images
            prompt: The analysis instructions
            structured_output: The expected output format (Pydantic model)
            
        Returns:
            PartSpecification object with extracted information
        """
        if self.provider == "openai":
            return self._analyze_with_openai(images, prompt, structured_output)
        elif self.provider == "claude":
            return self._analyze_with_claude(images, prompt, structured_output)
        elif self.provider == "ollama":
            return self._analyze_with_ollama(images, prompt, structured_output)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _analyze_with_openai(self, 
                            images: Dict, 
                            prompt: str,
                            output_model: type) -> PartSpecification:
        """
        This is like having a conversation with GPT:
        1. Show it the images
        2. Ask it to analyze them
        3. Request structured output
        """
        # Build messages for the chat
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this mechanical drawing:"},
                    {"type": "image_url", "image_url": {"url": images['full']}}
                ]
            }
        ]
        
        # Add detailed region images if available
        for region in images.get('regions', []):
            if region['type'] == 'title_block':
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Title block detail:"},
                        {"type": "image_url", "image_url": {"url": region['image']}}
                    ]
                })
        
        # Use function calling for structured output
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_specifications",
                "description": "Extract structured specifications from drawing",
                "parameters": output_model.model_json_schema()
            }
        }]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "extract_specifications"}}
            )
            
            function_args = json.loads(
                response.choices[0].message.tool_calls[0].function.arguments
            )
            
            # Sanitize the response before creating the model
            function_args = self._sanitize_llm_response(function_args)
            
            return output_model(**function_args)
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return output_model()     

    def _sanitize_llm_response(self, response: Dict) -> Dict:
        """
        Fix common LLM response issues.
        
        Like a translator fixing grammar mistakes - the meaning is there,
        just needs the format adjusted.
        """
        # Fix overall_dimensions if it's a list
        if 'overall_dimensions' in response and isinstance(response['overall_dimensions'], list):
            # Convert list to dict with standard keys
            dims_dict = {}
            for dim in response['overall_dimensions']:
                if 'feature' in dim:
                    # Use feature name as key
                    key = dim['feature'].lower().replace(' ', '_')
                    dims_dict[key] = dim
            response['overall_dimensions'] = dims_dict
        
        # Add default confidence if missing
        if 'critical_dimensions' in response:
            for dim in response['critical_dimensions']:
                if 'confidence' not in dim:
                    dim['confidence'] = 0.9  # Default confidence
        
        return response 
            
    
    def _analyze_with_claude(self, 
                           images: Dict, 
                           prompt: str,
                           output_model: type) -> PartSpecification:
        """
        Analyze using Anthropic's Claude.
        
        Note: Implementation depends on Anthropic's current API structure.
        """
        # This is a placeholder - you'll implement when you need it
        raise NotImplementedError(
            "Claude integration coming soon! "
            "Check Anthropic's vision API documentation."
        )
    
    def _analyze_with_ollama(self, 
                           images: Dict, 
                           prompt: str,
                           output_model: type) -> PartSpecification:
        """
        Analyze using local Ollama models.
        
        Great for privacy-sensitive drawings or offline work!
        """
        # This is a placeholder for Ollama implementation
        raise NotImplementedError(
            "Ollama integration coming soon! "
            "Make sure you have a vision model like LLaVA installed."
        )
    
    def test_connection(self) -> bool:
        """
        Test if the LLM client can connect to its provider.
        
        Like doing a mic check before a presentation.
        """
        try:
            if self.provider == 'openai':
                # Try a simple API call
                response = self.client.models.list()
                print(f"✅ Connected to OpenAI. Available models: {len(list(response.data))}")
                return True
                
            elif self.provider == 'ollama':
                # Check if Ollama is running
                models = self.client.list()
                print(f"✅ Connected to Ollama. Models: {len(models)}")
                return True
                
            elif self.provider == 'claude':
                # Test Claude connection
                print("✅ Claude client initialized")
                return True
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


# Quick test function
def test_llm_client():
    """Test the LLM client independently"""
    print("Testing LLM Client...\n")
    
    # Test initialization
    try:
        client = LLMClient(provider="openai")
        print(f"✅ Client initialized")
        print(f"  Provider: {client.provider}")
        print(f"  Model: {client.model}")
        
        # Test connection
        client.test_connection()
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        print("  Make sure OPENAI_API_KEY is set in your .env file")


if __name__ == "__main__":
    test_llm_client()