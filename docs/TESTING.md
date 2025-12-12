# Testing Guide

**Author:** Lindsey D. Stead

This guide explains how to test the PDF Autofiller application.

## Quick Start

### 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

If you don't have a virtual environment yet:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run All Tests

```bash
# Run pytest test suite
pytest tests/ -v

# Or run the comprehensive test runner
python run_tests.py
```

## Testing Options

### Option 1: Unit Tests (Recommended)

Run the full pytest test suite:

```bash
source venv/bin/activate
pytest tests/ -v
```

This runs:
- **13 mapping tests** - Tests data mapping logic
- **6 PDF writer tests** - Tests PDF filling functionality

Expected output: `19 passed`

### Option 2: Integration Tests

Run the comprehensive test runner:

```bash
source venv/bin/activate
python run_tests.py
```

This tests:
- Module imports
- Pydantic models
- Mapping functions
- Complete workflow
- LLM client availability

### Option 3: Test with Real PDF

Test the full workflow with an actual PDF form:

```bash
source venv/bin/activate
python test_demo.py path/to/your/form.pdf
```

Or with custom user data:

```bash
python test_demo.py form.pdf '{"firstname": "John", "lastname": "Doe", "dob": "1990-05-15"}'
```

## Test Files Explained

### `tests/test_mapping.py`
Tests the data mapping engine:
- Key normalization
- Value coercion (date, number, boolean)
- Deterministic matching
- Complete mapping workflow
- Edge cases (missing fields, ambiguous values)

### `tests/test_pdf_writer.py`
Tests PDF writing functionality:
- File existence checks
- Required field validation
- Review flag handling
- Output directory creation
- Error handling

### `run_tests.py`
Comprehensive integration test runner that tests:
- All module imports
- Model validation
- Core functions
- End-to-end workflows

### `test_demo.py`
Interactive demo script that:
- Reads a PDF
- Infers field semantics (if API key set)
- Maps user data
- Fills the PDF
- Shows progress and results

## Testing Without OpenAI API Key

The system works without an OpenAI API key for deterministic matching:

```bash
# This will work - uses deterministic matching only
python test_demo.py form.pdf '{"firstname": "John", "lastname": "Doe"}'
```

AI features (semantic inference) require `OPENAI_API_KEY`:
```bash
export OPENAI_API_KEY=your_key_here
```

## Example Test Scenarios

### Test 1: Basic Mapping
```python
from src.doc_engine.mapping import map_user_data_to_fields
from src.doc_engine.models import EnrichedFormField, FormField, FieldSemantics

# Create test fields
fields = [
    EnrichedFormField(
        field=FormField(name="txtFirstName", field_type="text", required=True, page_number=1),
        semantics=FieldSemantics(semantic_meaning="first_name", expected_data_type="string", confidence_score=0.95)
    )
]

# Test mapping
user_data = {"firstname": "John"}
result = map_user_data_to_fields(fields, user_data, strict=True)
print(result.decisions[0].selected_value)  # Should print "John"
```

### Test 2: Missing Required Field
```python
# Same setup as above, but missing required field
user_data = {}  # Empty
result = map_user_data_to_fields(fields, user_data, strict=True)
print(result.missing_required)  # Should contain "txtFirstName"
```

### Test 3: Full Workflow
```python
from pathlib import Path
from src.doc_engine.pdf_reader import read_pdf
from src.doc_engine.mapping import map_user_data_to_fields
from src.doc_engine.pdf_writer import fill_pdf

# Read PDF
structure = read_pdf(Path("form.pdf"))

# Create enriched fields (or use AI inference)
# ... create enriched_fields ...

# Map data
user_data = {"firstname": "John", "lastname": "Doe"}
mapping_result = map_user_data_to_fields(enriched_fields, user_data)

# Fill PDF
fill_pdf(Path("form.pdf"), Path("filled.pdf"), mapping_result)
```

## Troubleshooting

### "No module named 'pypdf'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "LLM client not available"
This is expected if `OPENAI_API_KEY` is not set. The system will use deterministic matching only.

### "PDF file not found"
Make sure the PDF path is correct and the file exists.

### Tests fail with import errors
Make sure you're in the virtual environment:
```bash
source venv/bin/activate
```

## Continuous Testing

To run tests automatically on file changes:

```bash
# Install pytest-watch
pip install pytest-watch

# Watch for changes and run tests
ptw tests/
```

## Test Coverage

To see test coverage:

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

Open `htmlcov/index.html` in your browser to see coverage report.

