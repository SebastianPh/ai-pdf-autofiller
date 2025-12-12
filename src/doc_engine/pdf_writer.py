"""
PDF writer for filling form fields with mapped values.

Takes mapping decisions and writes them to PDF form fields. Handles validation
of required fields and skips fields marked for review. This is deterministic
only - no AI processing happens here.

Author: Lindsey D. Stead
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .models import FieldMappingDecision, MappingResult


class UnresolvedRequiredFieldsError(Exception):
    """
    Exception raised when required fields can't be filled.
    
    This happens when required fields are missing from user data or were
    skipped due to requires_review=True. The system won't write incomplete
    forms to avoid producing invalid documents.
    """
    
    def __init__(self, missing_fields: list[str], skipped_fields: list[str]):
        self.missing_fields = missing_fields
        self.skipped_fields = skipped_fields
        message_parts = []
        if missing_fields:
            message_parts.append(f"Missing required fields: {', '.join(missing_fields)}")
        if skipped_fields:
            message_parts.append(f"Skipped required fields (requires_review=True): {', '.join(skipped_fields)}")
        super().__init__("; ".join(message_parts))


def fill_pdf(
    input_pdf_path: Path,
    output_pdf_path: Path,
    mapping_result: MappingResult
) -> None:
    """
    Fill PDF form fields with mapped values from mapping result.
    
    Writes values from FieldMappingDecision objects into the PDF form fields.
    Skips fields where requires_review=True or selected_value is None.
    Preserves original formatting and untouched fields.
    
    Args:
        input_pdf_path: Path to the input PDF file
        output_pdf_path: Path where the filled PDF will be saved
        mapping_result: MappingResult containing decisions and validation info
        
    Raises:
        FileNotFoundError: If input PDF does not exist
        UnresolvedRequiredFieldsError: If required fields are missing or skipped
        
    Example:
        >>> from pathlib import Path
        >>> from src.doc_engine.models import MappingResult, FieldMappingDecision
        >>> result = MappingResult(
        ...     decisions=[
        ...         FieldMappingDecision(
        ...             field_name="txtFirstName",
        ...             semantic_meaning="first_name",
        ...             selected_value="John",
        ...             confidence=0.95,
        ...             reason="Direct match",
        ...             requires_review=False
        ...         )
        ...     ],
        ...     missing_required=[],
        ...     unmapped_user_keys=[]
        ... )
        >>> fill_pdf(Path("form.pdf"), Path("filled.pdf"), result)
    """
    if not input_pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf_path}")
    
    reader = PdfReader(str(input_pdf_path))
    writer = PdfWriter()
    
    # Clone document structure to preserve formatting
    writer.clone_reader_document_root(reader)
    
    # Get form fields from original PDF
    try:
        pdf_fields = reader.get_fields()
        if pdf_fields is None:
            pdf_fields = {}
    except Exception:
        pdf_fields = {}
    
    written_fields: set[str] = set()
    skipped_required_fields: list[str] = []
    field_values: dict[str, str] = {}
    
    # Process mapping decisions
    # Skip fields marked for review or with no value
    for decision in mapping_result.decisions:
        field_name = decision.field_name
        
        if decision.requires_review:
            # Track required fields that were skipped
            if pdf_fields and field_name in pdf_fields:
                field_obj = pdf_fields[field_name]
                if field_obj and _is_field_required(field_obj):
                    skipped_required_fields.append(field_name)
            continue
        
        if decision.selected_value is None:
            continue
        
        # Only write to fields that exist in the PDF
        if pdf_fields and field_name in pdf_fields:
            field_values[field_name] = decision.selected_value
            written_fields.add(field_name)
    
    # Write field values to PDF
    # Try batch update first, fall back to individual updates if needed
    if field_values:
        for page in writer.pages:
            try:
                writer.update_page_form_field_values(page, field_values)
            except Exception:
                # Fallback: update fields individually
                for field_name, value in field_values.items():
                    try:
                        writer.update_page_form_field_values(page, {field_name: value})
                    except Exception:
                        pass
    
    # Validate that all required fields were filled
    missing_required = mapping_result.missing_required.copy()
    
    # Check PDF form fields for any required fields we missed
    for field_name, field_obj in (pdf_fields or {}).items():
        if _is_field_required(field_obj):
            if field_name not in written_fields and field_name not in missing_required:
                # Check if it was skipped due to review flag
                skipped_decisions = [
                    d for d in mapping_result.decisions
                    if d.field_name == field_name and d.requires_review
                ]
                if skipped_decisions:
                    if field_name not in skipped_required_fields:
                        skipped_required_fields.append(field_name)
                else:
                    missing_required.append(field_name)
    
    # Fail if required fields unresolved
    if missing_required or skipped_required_fields:
        raise UnresolvedRequiredFieldsError(
            missing_fields=missing_required,
            skipped_fields=skipped_required_fields
        )
    
    # Write output PDF
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)


def _is_field_required(field_obj) -> bool:
    """
    Check if a PDF form field is marked as required.
    
    PDF spec uses bit flags in the /Ff field. Bit 1 (0x02) indicates
    a required field that must be filled before submission.
    """
    if not field_obj:
        return False
    
    try:
        ff = field_obj.get("/Ff", 0)
        return bool(ff & 0x02)
    except Exception:
        return False

