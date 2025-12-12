"""
PDF reader for extracting form fields and text from PDF documents.

Handles low-level PDF parsing to extract form field metadata, text content,
and document properties. No AI inference happens here - this is pure extraction.

Author: Lindsey D. Stead
"""

from pathlib import Path
from typing import Optional

from pypdf import PdfReader
from pypdf.generic import IndirectObject

from .models import DocumentMetadata, DocumentStructure, FormField, TextRegion


def _get_field_type(field_obj) -> str:
    """
    Extract field type from PDF field object.
    
    PDF field types are encoded as PDF name objects like /Tx (text),
    /Btn (button), etc. This converts them to our internal string format.
    """
    ft = field_obj.get("/FT")
    if ft == "/Tx":
        return "text"
    elif ft == "/Btn":
        return "button"
    elif ft == "/Ch":
        return "choice"
    elif ft == "/Sig":
        return "signature"
    else:
        return "unknown"


def _get_field_value(field_obj) -> Optional[str]:
    """
    Extract current value from a PDF form field.
    
    PDF values can be stored as direct objects or indirect references.
    This handles both cases and converts to string representation.
    """
    v = field_obj.get("/V")
    if v is None:
        return None
    
    if isinstance(v, (str, bool, int, float)):
        return str(v)
    elif isinstance(v, IndirectObject):
        # Indirect objects need to be resolved first
        try:
            resolved = v.get_object()
            if isinstance(resolved, (str, bool, int, float)):
                return str(resolved)
        except Exception:
            pass
    
    return str(v) if v else None


def _is_field_required(field_obj) -> bool:
    """
    Check if a form field is marked as required.
    
    PDF spec uses bit flags in the /Ff field. Bit 1 (0x02) indicates
    a required field.
    """
    ff = field_obj.get("/Ff", 0)
    return bool(ff & 0x02)


def _find_field_page(reader: PdfReader, field_obj) -> int:
    """
    Determine which page a form field appears on.
    
    Fields can reference their parent page via the /P key. This tries
    to resolve that reference and match it to a page number. Falls back
    to page 1 if the reference can't be resolved.
    """
    if hasattr(field_obj, "get"):
        page_ref = field_obj.get("/P")
        if page_ref:
            try:
                if hasattr(page_ref, "get_object"):
                    page_obj = page_ref.get_object()
                else:
                    page_obj = page_ref
                
                # Match page object to page number
                for idx, page in enumerate(reader.pages, start=1):
                    if page == page_obj or (hasattr(page, "indirect_reference") and 
                                          page.indirect_reference == page_ref):
                        return idx
            except Exception:
                pass
    
    return 1


def _extract_form_fields(reader: PdfReader) -> list[FormField]:
    """
    Extract all form fields from the PDF document.
    
    Tries the standard get_fields() method first, which works for most PDFs.
    Falls back to parsing page annotations if that fails, which handles
    edge cases where fields aren't in the standard AcroForm structure.
    """
    form_fields = []
    
    try:
        root_fields = reader.get_fields()
        if root_fields:
            for field_name, field_obj in root_fields.items():
                try:
                    page_num = _find_field_page(reader, field_obj)
                    
                    form_fields.append(FormField(
                        name=str(field_name),
                        field_type=_get_field_type(field_obj),
                        value=_get_field_value(field_obj),
                        required=_is_field_required(field_obj),
                        page_number=page_num
                    ))
                except Exception:
                    continue
    except Exception:
        # Fallback: extract from page annotations
        # Some PDFs store fields as widget annotations rather than AcroForm fields
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                if "/Annots" in page:
                    annotations = page["/Annots"]
                    if annotations:
                        for annot_ref in annotations:
                            try:
                                annot = annot_ref.get_object() if hasattr(annot_ref, "get_object") else annot_ref
                                if annot.get("/Subtype") == "/Widget":
                                    field_name = annot.get("/T")
                                    if field_name:
                                        # Widget annotations may have parent field objects
                                        parent = annot.get("/Parent")
                                        if parent:
                                            field_obj = parent.get_object() if hasattr(parent, "get_object") else parent
                                        else:
                                            field_obj = annot
                                        
                                        form_fields.append(FormField(
                                            name=str(field_name),
                                            field_type=_get_field_type(field_obj),
                                            value=_get_field_value(field_obj),
                                            required=_is_field_required(field_obj),
                                            page_number=page_num
                                        ))
                            except Exception:
                                continue
            except Exception:
                continue
    
    return form_fields


def _extract_text_regions(reader: PdfReader) -> list[TextRegion]:
    """
    Extract visible text content from all PDF pages.
    
    Used primarily for context when inferring field semantics. Text extraction
    can fail on corrupted or encrypted pages, so we skip those gracefully.
    """
    text_regions = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
            if text and text.strip():
                text_regions.append(TextRegion(
                    text=text.strip(),
                    page_number=page_num
                ))
        except Exception:
            continue
    
    return text_regions


def read_pdf(pdf_path: Path) -> DocumentStructure:
    """
    Read a PDF and extract its complete structure.
    
    This is the main entry point for PDF introspection. Returns a structured
    representation of the document including form fields, text content, and
    metadata. No AI processing happens here - pure extraction only.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        DocumentStructure containing metadata, form fields, and text regions
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    reader = PdfReader(str(pdf_path))
    
    metadata_dict = reader.metadata or {}
    metadata = DocumentMetadata(
        num_pages=len(reader.pages),
        title=metadata_dict.get("/Title"),
        author=metadata_dict.get("/Author"),
        subject=metadata_dict.get("/Subject"),
        creator=metadata_dict.get("/Creator"),
        producer=metadata_dict.get("/Producer")
    )
    
    form_fields = _extract_form_fields(reader)
    text_regions = _extract_text_regions(reader)
    
    return DocumentStructure(
        metadata=metadata,
        form_fields=form_fields,
        text_regions=text_regions
    )

