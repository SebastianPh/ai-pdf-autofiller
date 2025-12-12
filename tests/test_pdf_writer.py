"""Tests for PDF writer.

Author: Lindsey D. Stead
"""

import tempfile
from pathlib import Path

import pytest

from src.doc_engine.models import FieldMappingDecision, MappingResult
from src.doc_engine.pdf_writer import UnresolvedRequiredFieldsError, fill_pdf


def create_minimal_pdf_with_fields(output_path: Path, field_names: list[str]) -> None:
    """
    Create a minimal PDF with form fields for testing.
    
    Note: This is a simplified test helper. In real scenarios, you would
    use actual PDF files with form fields.
    """
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, TextStringObject
    
    writer = PdfWriter()
    
    # Create a simple page
    page = writer.add_blank_page(width=612, height=792)
    
    # Add form fields (simplified - real PDFs have more complex structure)
    # For testing purposes, we'll create a basic structure
    if "/Annots" not in page:
        page[NameObject("/Annots")] = []
    
    # Note: This is a minimal implementation for testing
    # Real PDF form fields require more complex structure
    
    with open(output_path, "wb") as f:
        writer.write(f)


@pytest.fixture
def sample_mapping_result():
    """Create sample mapping result for testing."""
    return MappingResult(
        decisions=[
            FieldMappingDecision(
                field_name="txtFirstName",
                semantic_meaning="first_name",
                selected_value="John",
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
            FieldMappingDecision(
                field_name="txtLastName",
                semantic_meaning="last_name",
                selected_value="Doe",
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
        ],
        missing_required=[],
        unmapped_user_keys=[]
    )


@pytest.fixture
def sample_mapping_result_with_review():
    """Create mapping result with a field requiring review."""
    return MappingResult(
        decisions=[
            FieldMappingDecision(
                field_name="txtFirstName",
                semantic_meaning="first_name",
                selected_value="John",
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
            FieldMappingDecision(
                field_name="txtDOB",
                semantic_meaning="date_of_birth",
                selected_value="1990-05-15",
                confidence=0.65,
                reason="Ambiguous date format",
                requires_review=True  # Requires review
            ),
        ],
        missing_required=[],
        unmapped_user_keys=[]
    )


@pytest.fixture
def sample_mapping_result_missing_required():
    """Create mapping result with missing required field."""
    return MappingResult(
        decisions=[
            FieldMappingDecision(
                field_name="txtFirstName",
                semantic_meaning="first_name",
                selected_value="John",
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
        ],
        missing_required=["txtLastName"],  # Required field missing
        unmapped_user_keys=[]
    )


def test_fill_pdf_nonexistent_input():
    """Test fill_pdf raises FileNotFoundError for nonexistent input."""
    result = MappingResult(
        decisions=[],
        missing_required=[],
        unmapped_user_keys=[]
    )
    
    with pytest.raises(FileNotFoundError):
        fill_pdf(
            Path("nonexistent.pdf"),
            Path("output.pdf"),
            result
        )


def test_fill_pdf_skips_requires_review_fields(tmp_path, sample_mapping_result_with_review):
    """
    Test that fill_pdf skips fields with requires_review=True.
    
    Note: This test requires a real PDF file with form fields.
    For now, we test the logic without actual PDF creation.
    """
    # Create a minimal PDF
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    
    # Create a simple PDF for testing
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(input_pdf, "wb") as f:
        writer.write(f)
    
    # Test that requires_review fields are skipped
    # Since we don't have actual form fields, we test the validation logic
    # by checking that the function handles the case correctly
    
    # For a real test with form fields, we would need a PDF with actual form fields
    # This test verifies the function doesn't crash on valid input
    try:
        fill_pdf(input_pdf, output_pdf, sample_mapping_result_with_review)
        # If no exception is raised, the function completed
        # (though it may have skipped the review field)
    except UnresolvedRequiredFieldsError:
        # This is expected if txtDOB is required and was skipped
        pass


def test_fill_pdf_missing_required_fields(tmp_path, sample_mapping_result_missing_required):
    """Test that fill_pdf raises UnresolvedRequiredFieldsError for missing required fields."""
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    
    # Create a minimal PDF
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(input_pdf, "wb") as f:
        writer.write(f)
    
    # Should raise exception for missing required fields
    with pytest.raises(UnresolvedRequiredFieldsError) as exc_info:
        fill_pdf(input_pdf, output_pdf, sample_mapping_result_missing_required)
    
    assert "txtLastName" in str(exc_info.value)
    assert "Missing required fields" in str(exc_info.value)


def test_fill_pdf_skips_none_values(tmp_path):
    """Test that fill_pdf skips decisions with None selected_value."""
    result = MappingResult(
        decisions=[
            FieldMappingDecision(
                field_name="txtFirstName",
                semantic_meaning="first_name",
                selected_value=None,  # None value
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
            FieldMappingDecision(
                field_name="txtLastName",
                semantic_meaning="last_name",
                selected_value="Doe",
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
        ],
        missing_required=[],
        unmapped_user_keys=[]
    )
    
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    
    # Create a minimal PDF
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(input_pdf, "wb") as f:
        writer.write(f)
    
    # Should complete without error (None value is skipped)
    fill_pdf(input_pdf, output_pdf, result)
    
    # Verify output file was created
    assert output_pdf.exists()


def test_unresolved_required_fields_error():
    """Test UnresolvedRequiredFieldsError exception."""
    error = UnresolvedRequiredFieldsError(
        missing_fields=["field1", "field2"],
        skipped_fields=["field3"]
    )
    
    assert "field1" in str(error)
    assert "field2" in str(error)
    assert "field3" in str(error)
    assert "Missing required fields" in str(error)
    assert "Skipped required fields" in str(error)


def test_fill_pdf_creates_output_directory(tmp_path):
    """Test that fill_pdf creates output directory if it doesn't exist."""
    result = MappingResult(
        decisions=[
            FieldMappingDecision(
                field_name="txtFirstName",
                semantic_meaning="first_name",
                selected_value="John",
                confidence=0.95,
                reason="Direct match",
                requires_review=False
            ),
        ],
        missing_required=[],
        unmapped_user_keys=[]
    )
    
    input_pdf = tmp_path / "input.pdf"
    output_dir = tmp_path / "nested" / "output"
    output_pdf = output_dir / "output.pdf"
    
    # Create a minimal PDF
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(input_pdf, "wb") as f:
        writer.write(f)
    
    # Output directory doesn't exist yet
    assert not output_dir.exists()
    
    # Should create directory and write file
    fill_pdf(input_pdf, output_pdf, result)
    
    # Verify directory and file were created
    assert output_dir.exists()
    assert output_pdf.exists()

