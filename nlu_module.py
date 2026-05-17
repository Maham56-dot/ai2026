import os
import json
from typing import Optional
from pydantic import BaseModel, Field

# Ensure you have the google-genai library installed: pip install google-genai pydantic
# This module assumes you are using the new google.genai SDK.
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Please install google-genai and pydantic: pip install google-genai pydantic")

class IntentExtraction(BaseModel):
    service_type: str = Field(
        description="The type of service required (e.g., AC Repair, Plumbing, Electrician, Cleaning, etc.). Normalize to English."
    )
    location: Optional[str] = Field(
        description="The location or address where the service is needed. Return null if not mentioned.",
        default=None
    )
    urgency: str = Field(
        description="The urgency of the request. Must be one of: 'Low', 'Medium', 'High', 'Emergency'. Default to 'Medium' if not specified.",
        default="Medium"
    )
    preferred_time: Optional[str] = Field(
        description="The specific time or time frame preferred by the user (e.g., 'Tomorrow morning', 'Asap', '10 AM', etc.). Return null if not mentioned.",
        default=None
    )
    complexity: str = Field(
        description="The perceived complexity of the job based on the description. Must be one of: 'Basic', 'Intermediate', 'Complex'. Default to 'Basic'.",
        default="Basic"
    )

class NLUModule:
    """
    Robust NLU module to handle code-switching between English, Urdu, and Roman Urdu.
    Uses Google's Gemini model with Structured Outputs to parse intents reliably.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Initialize the GenAI client
        # Defaults to the GEMINI_API_KEY environment variable if api_key is None
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key is required. Set GEMINI_API_KEY environment variable or pass it directly.")
            
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"  # Flash is ideal for fast, structured NLP tasks
        
        self.system_instruction = (
            "You are an expert NLU assistant for an informal service economy orchestrator in Pakistan. "
            "Your task is to extract intent from user queries which may be in English, Urdu (اردو), or Roman Urdu. "
            "The user will often use code-switching (mixing languages, e.g., 'mujhe kal morning mein AC service chahiye'). "
            "Extract the service_type, location, urgency, preferred_time, and assess the job's complexity accurately according to the schema."
        )

    def extract_intent(self, text: str) -> IntentExtraction:
        """
        Parses the input text and returns a structured IntentExtraction object.
        """
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                response_mime_type="application/json",
                response_schema=IntentExtraction,
                temperature=0.1, # Low temperature for deterministic extraction
            )
        )
        
        # The response.text is guaranteed to be a JSON string matching the IntentExtraction schema
        return IntentExtraction.model_validate_json(response.text)

# Example Usage
if __name__ == "__main__":
    # Note: Ensure you have GEMINI_API_KEY set in your environment variables.
    try:
        nlu = NLUModule()
        
        test_queries = [
            "mujhe kal morning mein AC service chahiye dha phase 5 mein",
            "bhai mere ghar ki light chali gayi hai jaldi aao emergency hai",
            "I need a plumber to fix a leaking pipe tomorrow at 2 PM.",
            "yar gari dhoni hai sunday ko, F-8 markaz"
        ]
        
        for query in test_queries:
            print(f"Query: {query}")
            try:
                result = nlu.extract_intent(query)
                print(json.dumps(result.model_dump(), indent=2))
            except Exception as e:
                print(f"Extraction failed: {e}")
            print("-" * 40)
            
    except ValueError as e:
        print(f"Setup Error: {e}")
