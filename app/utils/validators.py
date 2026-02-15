"""
Validation Utilities Module

This module provides custom validators and validation utilities
for data validation beyond Pydantic's built-in capabilities.
"""

import re
from typing import Optional, List


class SymptomValidator:
    """
    Validator for user symptom inputs
    
    Ensures symptom descriptions are meaningful and safe to process.
    """
    
    # Patterns to detect potentially malicious input
    SUSPICIOUS_PATTERNS = [
        r'<script',
        r'javascript:',
        r'onclick',
        r'onerror',
        r'eval\(',
        r'alert\(',
    ]
    
    # Minimum meaningful word count
    MIN_WORDS = 2
    
    @staticmethod
    def is_valid_symptom_input(symptoms: str) -> tuple[bool, Optional[str]]:
        """
        Validate symptom input for safety and meaningfulness
        
        Args:
            symptoms: User input describing symptoms
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> validator = SymptomValidator()
            >>> valid, error = validator.is_valid_symptom_input("headache and fever")
            >>> if not valid:
            ...     print(error)
        """
        if not symptoms or not symptoms.strip():
            return False, "Symptoms cannot be empty"
        
        # Check for suspicious patterns (XSS, injection attempts)
        symptoms_lower = symptoms.lower()
        for pattern in SymptomValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, symptoms_lower, re.IGNORECASE):
                return False, "Invalid input detected"
        
        # Check minimum word count
        words = symptoms.strip().split()
        if len(words) < SymptomValidator.MIN_WORDS:
            return False, f"Please provide more detail (at least {SymptomValidator.MIN_WORDS} words)"
        
        # Check for excessive length (prevents abuse)
        if len(symptoms) > 1000:
            return False, "Symptom description is too long (max 1000 characters)"
        
        return True, None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input by removing potentially harmful characters
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text.strip()


class SPARQLValidator:
    """
    Validator for SPARQL query construction safety
    
    Ensures queries are safe and properly formatted.
    """
    
    @staticmethod
    def sanitize_condition_name(condition: str) -> str:
        """
        Sanitize medical condition name for SPARQL queries
        
        Args:
            condition: Raw condition name
            
        Returns:
            Sanitized condition name safe for SPARQL
        """
        # Remove special characters that could break SPARQL
        condition = re.sub(r'[^\w\s-]', '', condition)
        
        # Normalize whitespace
        condition = ' '.join(condition.split())
        
        # Capitalize properly
        condition = condition.strip().title()
        
        return condition
    
    @staticmethod
    def is_valid_wikidata_id(entity_id: str) -> bool:
        """
        Validate Wikidata entity ID format
        
        Args:
            entity_id: Wikidata ID to validate (e.g., Q18216)
            
        Returns:
            True if valid format, False otherwise
        """
        # Wikidata IDs follow pattern: Q followed by digits
        pattern = r'^Q\d+$'
        return bool(re.match(pattern, entity_id))


class ResponseValidator:
    """
    Validator for API responses and data integrity
    """
    
    @staticmethod
    def validate_medicine_data(medicine_dict: dict) -> tuple[bool, Optional[str]]:
        """
        Validate medicine data structure
        
        Args:
            medicine_dict: Dictionary containing medicine information
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['drug_id', 'name']
        
        for field in required_fields:
            if field not in medicine_dict or not medicine_dict[field]:
                return False, f"Missing required field: {field}"
        
        # Validate drug_id format
        if not SPARQLValidator.is_valid_wikidata_id(medicine_dict['drug_id']):
            return False, f"Invalid Wikidata ID format: {medicine_dict['drug_id']}"
        
        return True, None
    
    @staticmethod
    def filter_empty_values(data: dict) -> dict:
        """
        Remove None and empty string values from dictionary
        
        Args:
            data: Dictionary to filter
            
        Returns:
            Filtered dictionary
        """
        return {
            key: value 
            for key, value in data.items() 
            if value is not None and value != ""
        }


# Convenience functions
def validate_symptoms(symptoms: str) -> tuple[bool, Optional[str]]:
    """
    Validate symptom input
    
    Args:
        symptoms: User symptom description
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return SymptomValidator.is_valid_symptom_input(symptoms)


def sanitize_text(text: str) -> str:
    """
    Sanitize user input text
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    return SymptomValidator.sanitize_input(text)