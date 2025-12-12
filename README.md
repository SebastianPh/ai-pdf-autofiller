# AI PDF Autofiller

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checking](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Tests](https://img.shields.io/badge/tests-19%20passed-success.svg)](tests/)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](README.md)

> **Automated PDF form filling with intelligent field mapping.**  
> Maps structured data to PDF form fields using deterministic matching and AI-assisted semantic inference.

**Author:** [Lindsey D. Stead](https://github.com/lindseystead)

## Features

- 🎯 **Intelligent Field Mapping** - Automatically matches user data to form fields, even when names don't match
- 🤖 **AI-Assisted Inference** - Uses LLM to understand field semantics and expected data types
- ⚡ **Deterministic-First** - Fast, reliable matching before falling back to AI
- ✅ **Type Validation** - Validates and coerces data types (dates, numbers, booleans)
- 🔒 **Safe & Reliable** - Flags ambiguous mappings for review, never mutates original PDFs
- 📊 **Production-Ready** - Comprehensive error handling, validation, and test coverage

## Overview

This system processes PDF forms through four stages:

1. **Document Introspection** - Extracts form fields and text from PDFs
2. **Semantic Inference** - Uses LLM to infer field meanings and data types
3. **Data Mapping** - Maps user data to fields using deterministic matching with optional LLM fallback
4. **PDF Writing** - Fills form fields and generates completed PDFs

### Workflow Diagram

```
┌─────────────┐
│  PDF Form   │
│  (Input)    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐     ┌──────────────────┐
│ 1. Read PDF     │────▶│ Extract Fields    │
│    Structure    │     │ & Text Content   │
└────────┬────────┘     └─────────┬──────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐     ┌──────────────────┐
│ 2. Infer        │────▶│ Understand Field  │
│    Semantics    │     │ Meanings (AI)     │
└────────┬────────┘     └─────────┬──────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐     ┌──────────────────┐
│ 3. Map Data     │────▶│ Match User Data  │
│    to Fields    │     │ to Form Fields   │
└────────┬────────┘     └─────────┬──────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐     ┌──────────────────┐
│ 4. Fill PDF     │────▶│ Completed PDF    │
│    Form         │     │ (Output)         │
└─────────────────┘     └──────────────────┘
```

## Architecture

The system is organized into discrete modules:

- `pdf_reader.py` - PDF parsing and field extraction
- `field_semantics.py` - AI-assisted semantic inference
- `mapping.py` - Data mapping engine (deterministic + LLM fallback)
- `pdf_writer.py` - PDF form field writing
- `models.py` - Pydantic models for type safety

## Requirements

- **Python** 3.11+
- **Poetry** (recommended) or pip for dependency management
- **OpenAI API key** (optional, for AI-assisted semantic inference)

## Installation

### Using Poetry (Recommended)

```bash
poetry install
```

### Using pip

```bash
pip install -r requirements.txt
```

### Environment Setup

Set your OpenAI API key (optional, for AI features):

```bash
export OPENAI_API_KEY=your_key_here
```

> **Note:** The system works without an API key using deterministic matching only. AI features require an OpenAI API key.

## Usage

### Basic Example

```python
from pathlib import Path
from src.doc_engine.pdf_reader import read_pdf
from src.doc_engine.field_semantics import infer_field_semantics
from src.doc_engine.mapping import map_user_data_to_fields
from src.doc_engine.pdf_writer import fill_pdf

# 1. Read PDF structure
structure = read_pdf(Path("form.pdf"))

# 2. Infer semantics for each field
enriched_fields = []
for field in structure.form_fields:
    enriched = infer_field_semantics(field)
    enriched_fields.append(enriched)

# 3. Map user data to fields
user_data = {
    "firstname": "John",
    "lastname": "Doe",
    "dob": "1990-05-15"
}
mapping_result = map_user_data_to_fields(enriched_fields, user_data)

# 4. Fill PDF
fill_pdf(
    Path("form.pdf"),
    Path("filled.pdf"),
    mapping_result
)
```

### Command Line Example

```bash
# Test with sample form
python scripts/test_demo.py samples/sample_form.pdf

# With custom data
python scripts/test_demo.py form.pdf '{"firstname": "Lindsey", "lastname": "Stead", "dob": "1990-01-15"}'
```

### Example Output

```
============================================================
Testing PDF Autofiller Workflow
============================================================

Step 1: Reading PDF structure...
✓ PDF loaded successfully
  - Pages: 1
  - Form fields found: 5
  - Text regions: 0

Step 2: Inferring field semantics...
✓ Processed 5 fields

Step 3: Mapping user data to fields...
  User data keys: ['firstname', 'lastname', 'dob']
✓ Mapping complete
  - Decisions made: 3
  - Missing required: 0
  - Unmapped keys: 0

  Mapping decisions:
    ✓ txtFirstName: 'Lindsey' (confidence: 0.95)
    ✓ txtLastName: 'Stead' (confidence: 0.95)
    ✓ txtDOB: '1990-01-15' (confidence: 0.95)

Step 4: Filling PDF...
✓ PDF filled successfully
  Output: form_filled.pdf

============================================================
✓ Workflow completed successfully!
============================================================
```

## Design Principles

- **Deterministic-first**: Prefers exact matching over AI inference
- **Type safety**: All data structures validated via Pydantic
- **Fail-safe**: Required fields must be resolved or system raises exception
- **Review flags**: Ambiguous mappings marked for human review
- **No mutation**: Original PDFs are never modified

## Testing

### Quick Test
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Or run comprehensive test suite
python run_tests.py
```

### Test with Real PDF
```bash
python scripts/test_demo.py path/to/form.pdf
```

### Quick Commands (Makefile)
```bash
make install      # Install dependencies
make test         # Run tests
make lint         # Run linters
make format       # Format code
make run-sample   # Test with sample form
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing instructions.

## Project Structure

```
ai_pdf_autofiller/
├── src/doc_engine/      # Core application code
├── tests/               # Test suite
├── scripts/             # Utility scripts
├── samples/             # Sample PDF forms
└── docs/                # Documentation
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure documentation.

## Future Work

The core document automation pipeline is complete and intentionally conservative.  
Planned and possible extensions include:

- **Persistent learning (memory layer)**  
  Store confirmed field semantics and mapping decisions to improve accuracy and reduce AI calls over time.

- **Expanded document support**  
  Extend beyond PDF AcroForms to additional document formats and OCR-backed PDFs.

- **Non-fillable PDF support (OCR-backed)**  
  Extend the pipeline to handle scanned or non-interactive PDFs using OCR and layout analysis as a separate ingestion path.

- **API and service integration**  
  Expose the core pipeline via a lightweight API for integration with intake forms, CRMs, and automation workflows.

- **Human-in-the-loop review UI**  
  Optional interface for reviewing and approving flagged mappings before final document generation.

These features are deliberately deferred to preserve clarity, safety, and correctness in the current implementation.

## Contributing

Contributions are welcome! Please ensure:

- Code follows existing style (Black formatter)
- All tests pass (`make test`)
- Type hints are included
- Documentation is updated

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Lindsey D. Stead**

- GitHub: [@lindseystead](https://github.com/lindseystead)
