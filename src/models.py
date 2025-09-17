def _analyze_with_openai(self, images: Dict, prompt: str, output_model: type) -> PartSpecification:
    # ... existing code ...
    
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