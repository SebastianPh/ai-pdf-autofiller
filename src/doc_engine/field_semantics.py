"""
AI-assisted field semantics inference for PDF form fields.

This module uses LLMs to infer semantic meaning from form field names and context.
The goal is to understand what a field is actually asking for, not just what
it's technically called in the PDF structure.

Author: Lindsey D. Stead
"""

import json
import os
from typing import Optional

from pydantic import ValidationError

from .models import EnrichedFormField, FieldSemantics, FormField

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMClient:
    """
    Wrapper around OpenAI client with graceful degradation.
    
    Handles cases where the OpenAI SDK isn't installed or API keys aren't
    configured. This allows the rest of the system to work even if AI features
    aren't available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize client, falling back to stub if unavailable.
        
        Checks for API key in environment variable if not provided directly.
        Silently fails to stub mode if initialization fails.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None
    
    def is_available(self) -> bool:
        """Check if a working LLM client is available."""
        return self._client is not None
    
    def infer_semantics(self, field: FormField, context_text: Optional[str] = None) -> FieldSemantics:
        """
        Infer semantics for a form field using LLM.
        
        Args:
            field: Form field to analyze
            context_text: Optional surrounding text for context
            
        Returns:
            FieldSemantics with inferred meaning, data type, and confidence
            
        Raises:
            RuntimeError: If LLM is not available or inference fails
            ValueError: If LLM response cannot be parsed
        """
        if not self.is_available():
            raise RuntimeError(
                "LLM client not available. Set OPENAI_API_KEY environment variable "
                "or install openai package."
            )
        
        prompt = self._build_prompt(field, context_text)
        
        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a document analysis assistant. Analyze PDF form fields "
                            "and infer their semantic meaning. Return ONLY valid JSON matching "
                            "the required schema."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            raise RuntimeError(f"LLM inference failed: {e}") from e
    
    def _build_prompt(self, field: FormField, context_text: Optional[str] = None) -> str:
        """
        Construct the prompt sent to the LLM.
        
        Includes field metadata and optional surrounding text for context.
        The prompt explicitly requests JSON output matching our schema.
        """
        prompt_parts = [
            "Analyze this PDF form field and infer its semantic meaning.",
            "",
            "Field Information:",
            f"- Name: {field.name}",
            f"- Type: {field.field_type}",
            f"- Required: {field.required}",
            f"- Current Value: {field.value if field.value else '(empty)'}",
            f"- Page: {field.page_number}",
        ]
        
        if context_text:
            prompt_parts.extend([
                "",
                "Surrounding Context:",
                context_text[:500]
            ])
        
        prompt_parts.extend([
            "",
            "Return a JSON object with:",
            "- semantic_meaning: A snake_case identifier describing what this field represents",
            "  (e.g., 'first_name', 'date_of_birth', 'email_address', 'phone_number')",
            "- expected_data_type: One of 'string', 'date', 'number', 'boolean'",
            "- confidence_score: A float between 0.0 and 1.0 indicating confidence",
            "",
            "Example response:",
            json.dumps({
                "semantic_meaning": "first_name",
                "expected_data_type": "string",
                "confidence_score": 0.95
            }, indent=2)
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, content: str) -> FieldSemantics:
        """
        Parse LLM response and validate against schema.
        
        Handles cases where the LLM wraps JSON in markdown code blocks.
        Raises ValueError if parsing or validation fails.
        """
        try:
            content = content.strip()
            # Strip markdown code fences if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            return FieldSemantics(**data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e
        except ValidationError as e:
            raise ValueError(f"LLM response does not match schema: {e}") from e


def infer_field_semantics(
    field: FormField,
    context_text: Optional[str] = None,
    api_key: Optional[str] = None
) -> EnrichedFormField:
    """
    Infer semantic meaning for a PDF form field using LLM.
    
    Takes a raw form field (e.g., "txtFirstName") and determines what it
    actually represents (e.g., "first_name"). Also infers expected data
    type and provides a confidence score.
    
    Args:
        field: Form field extracted from PDF
        context_text: Optional surrounding text for additional context
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        
    Returns:
        EnrichedFormField with original field plus inferred semantics
        
    Raises:
        RuntimeError: If LLM client unavailable or API call fails
        ValueError: If LLM response invalid or doesn't match schema
    """
    client = LLMClient(api_key=api_key)
    semantics = client.infer_semantics(field, context_text)
    
    return EnrichedFormField(
        field=field,
        semantics=semantics
    )

