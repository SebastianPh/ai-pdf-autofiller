"""Tests for data mapping engine.

Author: Lindsey D. Stead
"""

import pytest

from src.doc_engine.mapping import (
    coerce_value,
    find_deterministic_match,
    map_user_data_to_fields,
    normalize_key,
)
from src.doc_engine.models import (
    EnrichedFormField,
    FieldSemantics,
    FormField,
)


@pytest.fixture
def sample_enriched_fields():
    """Create sample enriched form fields for testing."""
    return [
        EnrichedFormField(
            field=FormField(
                name="txtFirstName",
                field_type="text",
                required=True,
                page_number=1
            ),
            semantics=FieldSemantics(
                semantic_meaning="first_name",
                expected_data_type="string",
                confidence_score=0.95
            )
        ),
        EnrichedFormField(
            field=FormField(
                name="txtLastName",
                field_type="text",
                required=True,
                page_number=1
            ),
            semantics=FieldSemantics(
                semantic_meaning="last_name",
                expected_data_type="string",
                confidence_score=0.95
            )
        ),
        EnrichedFormField(
            field=FormField(
                name="txtDOB",
                field_type="text",
                required=True,
                page_number=1
            ),
            semantics=FieldSemantics(
                semantic_meaning="date_of_birth",
                expected_data_type="date",
                confidence_score=0.90
            )
        ),
        EnrichedFormField(
            field=FormField(
                name="txtEmail",
                field_type="text",
                required=False,
                page_number=1
            ),
            semantics=FieldSemantics(
                semantic_meaning="email_address",
                expected_data_type="string",
                confidence_score=0.88
            )
        ),
    ]


def test_normalize_key():
    """Test key normalization."""
    assert normalize_key("First-Name!") == "first_name"
    assert normalize_key("Email Address") == "email_address"
    assert normalize_key("phone_number") == "phone_number"
    assert normalize_key("DOB") == "dob"
    assert normalize_key("first__name") == "first_name"


def test_coerce_value_string():
    """Test value coercion for string type."""
    value, requires_review = coerce_value("John", "string")
    assert value == "John"
    assert requires_review is False


def test_coerce_value_date():
    """Test value coercion for date type."""
    # Valid date format
    value, requires_review = coerce_value("2024-01-15", "date")
    assert value == "2024-01-15"
    assert requires_review is False
    
    # Invalid date format
    value, requires_review = coerce_value("01/15/2024", "date")
    assert value == "01/15/2024"
    assert requires_review is True


def test_coerce_value_number():
    """Test value coercion for number type."""
    # Integer
    value, requires_review = coerce_value("123", "number")
    assert value == "123"
    assert requires_review is False
    
    # Float
    value, requires_review = coerce_value("123.45", "number")
    assert value == "123.45"
    assert requires_review is False
    
    # Invalid number
    value, requires_review = coerce_value("abc", "number")
    assert value == "abc"
    assert requires_review is True


def test_coerce_value_boolean():
    """Test value coercion for boolean type."""
    # True values
    value, requires_review = coerce_value("true", "boolean")
    assert value == "true"
    assert requires_review is False
    
    value, requires_review = coerce_value("yes", "boolean")
    assert value == "true"
    assert requires_review is False
    
    # False values
    value, requires_review = coerce_value("false", "boolean")
    assert value == "false"
    assert requires_review is False
    
    # Ambiguous
    value, requires_review = coerce_value("maybe", "boolean")
    assert value == "maybe"
    assert requires_review is True


def test_find_deterministic_match_direct():
    """Test deterministic matching with direct match."""
    # Use a key that will match directly, not via alias
    user_data = {"first_name": "John", "lastname": "Doe"}
    
    matched_key, matched_value, confidence, reason = find_deterministic_match(
        "first_name",
        user_data,
        "string"
    )
    
    assert matched_key == "first_name"
    assert matched_value == "John"
    assert confidence >= 0.90
    assert "Direct match" in reason or "direct" in reason.lower()


def test_find_deterministic_match_alias():
    """Test deterministic matching with alias match."""
    user_data = {"surname": "Smith", "email": "test@example.com"}
    
    matched_key, matched_value, confidence, reason = find_deterministic_match(
        "last_name",
        user_data,
        "string"
    )
    
    assert matched_key == "surname"
    assert matched_value == "Smith"
    assert confidence >= 0.85
    assert "Alias match" in reason


def test_find_deterministic_match_no_match():
    """Test deterministic matching when no match found."""
    user_data = {"unrelated": "value"}
    
    matched_key, matched_value, confidence, reason = find_deterministic_match(
        "first_name",
        user_data,
        "string"
    )
    
    assert matched_key is None
    assert matched_value is None
    assert confidence == 0.0


def test_map_user_data_to_fields_success(sample_enriched_fields):
    """Test successful mapping with deterministic matching."""
    user_data = {
        "firstname": "John",
        "lastname": "Doe",
        "dob": "1990-05-15",
        "email": "john@example.com"
    }
    
    result = map_user_data_to_fields(
        sample_enriched_fields,
        user_data,
        strict=True
    )
    
    # All fields should be mapped
    assert len(result.decisions) == 4
    assert len(result.missing_required) == 0
    
    # Check specific mappings
    first_name_decision = next(d for d in result.decisions if d.field_name == "txtFirstName")
    assert first_name_decision.selected_value == "John"
    assert first_name_decision.confidence >= 0.90
    
    dob_decision = next(d for d in result.decisions if d.field_name == "txtDOB")
    assert dob_decision.selected_value == "1990-05-15"
    assert dob_decision.requires_review is False


def test_map_user_data_to_fields_missing_required(sample_enriched_fields):
    """Test mapping with missing required field."""
    user_data = {
        "firstname": "John",
        # Missing lastname and dob
        "email": "john@example.com"
    }
    
    result = map_user_data_to_fields(
        sample_enriched_fields,
        user_data,
        strict=True
    )
    
    # Should have 2 decisions (firstname and email)
    assert len(result.decisions) == 2
    
    # Should have 2 missing required fields (lastname and dob)
    assert len(result.missing_required) == 2
    assert "txtLastName" in result.missing_required
    assert "txtDOB" in result.missing_required


def test_map_user_data_to_fields_ambiguous_requires_review(sample_enriched_fields):
    """Test mapping with ambiguous value that requires review."""
    user_data = {
        "firstname": "John",
        "lastname": "Doe",
        "dob": "05/15/1990",  # Wrong date format
        "email": "john@example.com"
    }
    
    result = map_user_data_to_fields(
        sample_enriched_fields,
        user_data,
        strict=True
    )
    
    # All fields mapped
    assert len(result.decisions) == 4
    
    # DOB should require review due to date format
    dob_decision = next(d for d in result.decisions if d.field_name == "txtDOB")
    assert dob_decision.requires_review is True
    assert dob_decision.selected_value == "05/15/1990"


def test_map_user_data_to_fields_unmapped_keys(sample_enriched_fields):
    """Test mapping with unmapped user data keys."""
    user_data = {
        "firstname": "John",
        "lastname": "Doe",
        "dob": "1990-05-15",
        "unused_key": "unused_value",
        "another_unused": "value"
    }
    
    result = map_user_data_to_fields(
        sample_enriched_fields,
        user_data,
        strict=True
    )
    
    # Should identify unmapped keys
    assert len(result.unmapped_user_keys) == 2
    assert "unused_key" in result.unmapped_user_keys
    assert "another_unused" in result.unmapped_user_keys


def test_map_user_data_to_fields_normalized_matching(sample_enriched_fields):
    """Test that normalization handles various key formats."""
    user_data = {
        "First-Name": "John",  # With punctuation
        "Last Name": "Doe",    # With space
        "DOB": "1990-05-15",   # All caps
        "Email_Address": "john@example.com"  # With underscore
    }
    
    result = map_user_data_to_fields(
        sample_enriched_fields,
        user_data,
        strict=True
    )
    
    # All fields should be mapped despite different formats
    assert len(result.decisions) == 4
    assert len(result.missing_required) == 0
    
    # Verify values
    first_name_decision = next(d for d in result.decisions if d.field_name == "txtFirstName")
    assert first_name_decision.selected_value == "John"

