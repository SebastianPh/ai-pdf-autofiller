# Project Structure

**Author:** Lindsey D. Stead

## Directory Layout

```
ai_pdf_autofiller/
├── src/                      # Source code
│   └── doc_engine/           # Main package
│       ├── __init__.py
│       ├── models.py         # Pydantic models
│       ├── pdf_reader.py     # PDF reading/extraction
│       ├── field_semantics.py # AI semantic inference
│       ├── mapping.py        # Data mapping engine
│       └── pdf_writer.py     # PDF form filling
│
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_mapping.py       # Mapping tests
│   └── test_pdf_writer.py    # PDF writer tests
│
├── scripts/                   # Utility scripts
│   ├── __init__.py
│   ├── create_sample_form.py # Generate test PDFs
│   ├── test_demo.py          # Demo workflow
│   └── run_tests.py          # Integration tests
│
├── samples/                  # Sample PDFs
│   ├── README.md
│   └── sample_form.pdf       # Test form
│
├── docs/                     # Documentation
│   ├── README.md
│   ├── TESTING.md            # Testing guide
│   ├── PURPOSE.md            # Purpose & use cases
│   └── test_results.html     # Test reports
│
├── .test-output/             # Test output (gitignored)
│
├── .gitignore               # Git ignore rules
├── .editorconfig            # Editor configuration
├── Makefile                 # Build commands
├── pyproject.toml           # Poetry config
├── requirements.txt         # Pip requirements
└── README.md                # Main documentation
```

## Module Organization

### Core Modules (`src/doc_engine/`)

- **models.py** - Data structures (Pydantic models)
- **pdf_reader.py** - PDF parsing and field extraction
- **field_semantics.py** - AI-assisted semantic inference
- **mapping.py** - Data mapping engine (deterministic + LLM)
- **pdf_writer.py** - PDF form field writing

### Test Organization (`tests/`)

- Tests mirror source structure
- One test file per major module
- Integration tests in `scripts/run_tests.py`

### Scripts (`scripts/`)

- Utility scripts for development/testing
- Can be run standalone or imported
- All scripts handle path resolution correctly

## Design Principles

1. **Separation of Concerns** - Each module has a single responsibility
2. **Type Safety** - All data structures use Pydantic
3. **Testability** - Clear interfaces, easy to mock
4. **Documentation** - Docstrings and type hints throughout
5. **Error Handling** - Clear exceptions, graceful degradation

## Adding New Features

1. Add models to `src/doc_engine/models.py`
2. Implement logic in appropriate module
3. Add tests to `tests/`
4. Update documentation in `docs/`
5. Add script if needed in `scripts/`

