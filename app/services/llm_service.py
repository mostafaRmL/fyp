"""
LLM Service Module

This module handles all interactions with the Groq AI API.
Provides symptom analysis and medical condition identification.
"""

import json
from typing import List, Dict, Optional, Tuple
from groq import Groq
from app.config import settings
from app.utils.logger import get_logger
from app.utils.validators import validate_symptoms, sanitize_text

logger = get_logger(__name__)


class LLMService:
    """
    Service for AI-powered symptom analysis using Groq
    
    Analyzes user symptoms and identifies potential medical conditions.
    """
    
    def __init__(self):
        """Initialize LLM service with Groq client"""
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
            self.temperature = settings.GROQ_TEMPERATURE
            self.max_tokens = settings.GROQ_MAX_TOKENS
            logger.info(f"LLM Service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            raise
    
    def analyze_symptoms(self, symptoms: str) -> Optional[Dict[str, any]]:
        """
        Analyze symptoms and identify medical conditions
        
        Args:
            symptoms: User's description of symptoms
            
        Returns:
            Dictionary containing:
                - identified_conditions: List of condition names
                - confidence: Confidence level (low/medium/high)
                - reasoning: AI's reasoning process
            Returns None on error
            
        Example:
            >>> service = LLMService()
            >>> result = service.analyze_symptoms("headache and fever")
            >>> print(result['identified_conditions'])
            ['Pain', 'Fever']
        """
        # Validate input
        is_valid, error_msg = validate_symptoms(symptoms)
        if not is_valid:
            logger.warning(f"Invalid symptoms input: {error_msg}")
            return None
        
        # Sanitize input
        symptoms = sanitize_text(symptoms)
        logger.info(f"Analyzing symptoms: {symptoms[:100]}...")
        
        try:
            # Construct the prompt
            prompt = self._build_analysis_prompt(symptoms)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = self._parse_ai_response(response)
            
            if result:
                logger.info(f"Analysis complete. Identified {len(result.get('identified_conditions', []))} conditions")
                logger.debug(f"Conditions: {result.get('identified_conditions')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during symptom analysis: {str(e)}")
            return None
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines AI behavior
        
        Returns:
            System prompt string
        """
        return """You are a medical symptom analyzer AI assistant. Your role is to:

1. Analyze user-described symptoms carefully
2. Identify potential medical conditions (use general, common condition names)
3. Provide confidence level based on symptom clarity
4. Explain your reasoning

IMPORTANT GUIDELINES:
- Use simple, general condition names (e.g., "Pain", "Fever", "Inflammation", "Headache", "Nausea")
- Focus on SYMPTOMS as conditions (what the person is experiencing)
- Do NOT diagnose specific diseases
- Be conservative with confidence levels
- Always remind: "Consult healthcare professional for proper diagnosis"
- Return response in JSON format

CONFIDENCE LEVELS:
- high: Symptoms are clear and specific
- medium: Symptoms are somewhat vague
- low: Symptoms are very general or unclear

Return JSON with this exact structure:
{
  "identified_conditions": ["condition1", "condition2"],
  "confidence": "high|medium|low",
  "reasoning": "Explain your analysis in 1-2 sentences"
}"""
    
    def _build_analysis_prompt(self, symptoms: str) -> str:
        """
        Build the user prompt for symptom analysis
        
        Args:
            symptoms: User symptoms
            
        Returns:
            Formatted prompt
        """
        return f"""Analyze these symptoms and identify medical conditions:

Symptoms: "{symptoms}"

Provide your analysis in JSON format with:
- identified_conditions: List of general symptom/condition names
- confidence: Your confidence level (low/medium/high)
- reasoning: Brief explanation

Remember: Use simple symptom names that would be found in a medical database (e.g., Pain, Fever, Cough, etc.)"""
    
    def _parse_ai_response(self, response) -> Optional[Dict[str, any]]:
        """
        Parse and validate AI response
        
        Args:
            response: Groq API response object
            
        Returns:
            Parsed response dictionary or None
        """
        try:
            # Extract content
            content = response.choices[0].message.content
            logger.debug(f"Raw AI response: {content}")
            
            # Parse JSON
            result = json.loads(content)
            
            # Validate structure
            if not isinstance(result.get('identified_conditions'), list):
                logger.error("Invalid response structure: identified_conditions not a list")
                return None
            
            if not result.get('confidence') in ['low', 'medium', 'high']:
                logger.warning("Invalid confidence level, defaulting to 'medium'")
                result['confidence'] = 'medium'
            
            if not result.get('reasoning'):
                result['reasoning'] = "Analysis completed based on symptom description."
            
            # Clean up conditions list
            result['identified_conditions'] = [
                condition.strip().title() 
                for condition in result['identified_conditions']
                if condition and condition.strip()
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            cleaned_conditions = []
            for condition in result['identified_conditions']:
                if condition.lower() not in seen:
                    seen.add(condition.lower())
                    cleaned_conditions.append(condition)
            
            result['identified_conditions'] = cleaned_conditions
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return None
    
    def validate_condition_name(self, condition: str) -> bool:
        """
        Validate that a condition name is reasonable
        
        Args:
            condition: Condition name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not condition or len(condition.strip()) < 2:
            return False
        
        # Should not contain special characters
        if any(char in condition for char in ['<', '>', '{', '}', '[', ']']):
            return False
        
        return True


# Singleton instance
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get singleton instance of LLM service
    
    Returns:
        LLMService instance
    """
    global _llm_service_instance
    
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    
    return _llm_service_instance