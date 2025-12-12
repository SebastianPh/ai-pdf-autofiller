"""
Demo script to test the full PDF autofiller workflow.

Author: Lindsey D. Stead
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.doc_engine.pdf_reader import read_pdf
from src.doc_engine.field_semantics import infer_field_semantics
from src.doc_engine.mapping import map_user_data_to_fields
from src.doc_engine.pdf_writer import fill_pdf


def test_workflow(pdf_path: Path, user_data: dict):
    """
    Test the complete workflow from PDF reading to filling.

    Args:
        pdf_path: Path to input PDF
        user_data: Dictionary of user data to map
    """
    print(f"\n{'='*60}")
    print(f"Testing PDF Autofiller Workflow")
    print(f"{'='*60}\n")

    # Step 1: Read PDF
    print("Step 1: Reading PDF structure...")
    try:
        structure = read_pdf(pdf_path)
        print(f"✓ PDF loaded successfully")
        print(f"  - Pages: {structure.metadata.num_pages}")
        print(f"  - Form fields found: {len(structure.form_fields)}")
        print(f"  - Text regions: {len(structure.text_regions)}")

        if structure.form_fields:
            print(f"\n  Form fields:")
            for field in structure.form_fields[:5]:  # Show first 5
                print(f"    - {field.name} ({field.field_type}, required={field.required})")
            if len(structure.form_fields) > 5:
                print(f"    ... and {len(structure.form_fields) - 5} more")
    except FileNotFoundError:
        print(f"✗ PDF file not found: {pdf_path}")
        return False
    except Exception as e:
        print(f"✗ Error reading PDF: {e}")
        return False

    # Step 2: Infer semantics (if OpenAI API key available)
    print(f"\nStep 2: Inferring field semantics...")
    enriched_fields = []
    semantics_available = False

    for field in structure.form_fields:
        try:
            enriched = infer_field_semantics(field)
            enriched_fields.append(enriched)
            semantics_available = True
        except RuntimeError:
            # LLM not available, skip semantic inference
            print("  ⚠ OpenAI API key not configured, skipping semantic inference")
            print("  (Set OPENAI_API_KEY environment variable to enable)")
            break
        except Exception as e:
            print(f"  ⚠ Error inferring semantics for {field.name}: {e}")
            break

    if not semantics_available:
        print("  ⚠ Semantic inference skipped - using field names directly")
        # Create mock enriched fields for testing
        from src.doc_engine.models import EnrichedFormField, FieldSemantics
        for field in structure.form_fields:
            enriched_fields.append(EnrichedFormField(
                field=field,
                semantics=FieldSemantics(
                    semantic_meaning=normalize_field_name(field.name),
                    expected_data_type="string",
                    confidence_score=0.5
                )
            ))

    print(f"✓ Processed {len(enriched_fields)} fields")

    # Step 3: Map user data
    print(f"\nStep 3: Mapping user data to fields...")
    print(f"  User data keys: {list(user_data.keys())}")

    try:
        mapping_result = map_user_data_to_fields(
            enriched_fields,
            user_data,
            strict=True  # Use deterministic matching only for demo
        )

        print(f"✓ Mapping complete")
        print(f"  - Decisions made: {len(mapping_result.decisions)}")
        print(f"  - Missing required: {len(mapping_result.missing_required)}")
        print(f"  - Unmapped keys: {len(mapping_result.unmapped_user_keys)}")

        if mapping_result.decisions:
            print(f"\n  Mapping decisions:")
            for decision in mapping_result.decisions[:5]:
                status = "⚠ REVIEW" if decision.requires_review else "✓"
                print(f"    {status} {decision.field_name}: '{decision.selected_value}' "
                      f"(confidence: {decision.confidence:.2f})")
            if len(mapping_result.decisions) > 5:
                print(f"    ... and {len(mapping_result.decisions) - 5} more")

        if mapping_result.missing_required:
            print(f"\n  ⚠ Missing required fields: {mapping_result.missing_required}")

        if mapping_result.unmapped_user_keys:
            print(f"\n  ⚠ Unmapped user keys: {mapping_result.unmapped_user_keys}")

    except Exception as e:
        print(f"✗ Error mapping data: {e}")
        return False

    # Step 4: Fill PDF
    print(f"\nStep 4: Filling PDF...")
    output_path = pdf_path.parent / f"{pdf_path.stem}_filled.pdf"

    try:
        fill_pdf(pdf_path, output_path, mapping_result)
        print(f"✓ PDF filled successfully")
        print(f"  Output: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error filling PDF: {e}")
        if "UnresolvedRequiredFieldsError" in str(type(e)):
            print(f"  This is expected if required fields are missing")
        return False


def normalize_field_name(name: str) -> str:
    """Simple normalization for demo purposes."""
    return name.lower().replace("txt", "").replace("_", "").strip()


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_demo.py <path_to_pdf> [user_data_json]")
        print("\nExample:")
        print('  python test_demo.py form.pdf \'{"firstname": "John", "lastname": "Doe"}\'')
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if len(sys.argv) >= 3:
        user_data = json.loads(sys.argv[2])
    else:
        # Default test data
        user_data = {
            "firstname": "John",
            "lastname": "Doe",
            "dob": "1990-05-15",
            "email": "john.doe@example.com"
        }

    success = test_workflow(pdf_path, user_data)

    if success:
        print(f"\n{'='*60}")
        print("✓ Workflow completed successfully!")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("✗ Workflow completed with errors")
        print(f"{'='*60}\n")
        sys.exit(1)

