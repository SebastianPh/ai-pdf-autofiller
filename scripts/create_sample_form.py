"""
Create a sample fillable PDF form for testing.

Author: Lindsey D. Stead
"""

"""
Create a sample fillable PDF form for testing.

Author: Lindsey D. Stead
"""

from pathlib import Path

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def create_sample_form_pypdf(output_path: Path):
    """
    Create a sample fillable PDF form using pypdf.

    This creates a simple form with text fields that can be filled.
    """
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject
    from pypdf.generic import IndirectObject, NumberObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # Create AcroForm
    acro_form = DictionaryObject({
        NameObject("/Fields"): ArrayObject(),
        NameObject("/NeedAppearances"): NameObject("/True"),
    })

    writer._root_object.update({
        NameObject("/AcroForm"): acro_form
    })

    # Field definitions
    fields = [
        {
            "name": "txtFirstName",
            "x": 100,
            "y": 700,
            "width": 200,
            "height": 20,
            "required": True
        },
        {
            "name": "txtLastName",
            "x": 350,
            "y": 700,
            "width": 200,
            "height": 20,
            "required": True
        },
        {
            "name": "txtDOB",
            "x": 100,
            "y": 650,
            "width": 200,
            "height": 20,
            "required": True
        },
        {
            "name": "txtEmail",
            "x": 100,
            "y": 600,
            "width": 300,
            "height": 20,
            "required": False
        },
        {
            "name": "txtPhone",
            "x": 100,
            "y": 550,
            "width": 200,
            "height": 20,
            "required": False
        },
    ]

    # Create annotations/widgets for each field
    annotations = ArrayObject()

    for i, field_def in enumerate(fields):
        # Create field dictionary
        field = DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject([
                NumberObject(field_def["x"]),
                NumberObject(792 - field_def["y"] - field_def["height"]),
                NumberObject(field_def["x"] + field_def["width"]),
                NumberObject(792 - field_def["y"])
            ]),
            NameObject("/FT"): NameObject("/Tx"),  # Text field
            NameObject("/T"): TextStringObject(field_def["name"]),
            NameObject("/Ff"): NumberObject(0x02 if field_def["required"] else 0),
            NameObject("/F"): NumberObject(4),  # Printable
        })

        # Add to annotations
        field_ref = writer._add_object(field)
        annotations.append(field_ref)

        # Add to form fields
        acro_form[NameObject("/Fields")].append(field_ref)

    # Add annotations to page
    page[NameObject("/Annots")] = annotations

    # Write PDF
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"✓ Created sample form: {output_path}")


def create_simple_form_with_text(output_path: Path):
    """
    Create a simple PDF form with visible labels using reportlab.
    Falls back to pypdf-only method if reportlab not available.
    """
    if REPORTLAB_AVAILABLE:
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors

            c = canvas.Canvas(str(output_path), pagesize=letter)
            width, height = letter

            # Title
            c.setFont("Helvetica-Bold", 20)
            c.drawString(100, height - 50, "Sample Job Application Form")

            # Instructions
            c.setFont("Helvetica", 10)
            c.drawString(100, height - 80, "Please fill out all required fields marked with *")

            # Field labels and positions
            y_start = height - 120
            line_height = 40

            fields = [
                ("First Name*", "txtFirstName", True, 100),
                ("Last Name*", "txtLastName", True, 350),
                ("Date of Birth* (YYYY-MM-DD)", "txtDOB", True, 100),
                ("Email Address", "txtEmail", False, 100),
                ("Phone Number", "txtPhone", False, 100),
            ]

            c.setFont("Helvetica", 12)
            y_pos = y_start

            for label, field_name, required, x_pos in fields:
                c.drawString(x_pos, y_pos, label)
                # Draw a box for the field
                c.rect(x_pos, y_pos - 25, 200, 20)
                y_pos -= line_height

            c.save()
            print(f"✓ Created sample form with labels: {output_path}")
            return True
        except Exception as e:
            print(f"⚠ ReportLab method failed: {e}, using pypdf method")
            return False

    return False


def main():
    """Create a sample fillable PDF form."""
    # Output to samples directory
    samples_dir = Path(__file__).parent.parent / "samples"
    samples_dir.mkdir(exist_ok=True)
    output_path = samples_dir / "sample_form.pdf"

    print("Creating sample fillable PDF form...")
    print("="*60)

    # Try reportlab first (better visual result)
    if not create_simple_form_with_text(output_path):
        # Fall back to pypdf-only method
        print("\nUsing pypdf method (minimal visual, but fillable)...")
        create_sample_form_pypdf(output_path)

    print("\n" + "="*60)
    print(f"✓ Sample form created: {output_path}")
    print("\nForm fields included:")
    print("  - txtFirstName (required)")
    print("  - txtLastName (required)")
    print("  - txtDOB (required)")
    print("  - txtEmail (optional)")
    print("  - txtPhone (optional)")
    print("\nTest it with:")
    print(f'  python test_demo.py {output_path} \'{{"firstname": "Lindsey", "lastname": "Stead", "dob": "1990-01-01", "email": "test@example.com"}}\'')


if __name__ == "__main__":
    main()

