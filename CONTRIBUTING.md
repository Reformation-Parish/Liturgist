# Contributing

Thank you for your interest in contributing to Liturgist! This document provides guidelines for setting up a development environment and contributing to the project.

## Development Setup

### Prerequisites
- Python 3.9 or higher
- Git
- For PDF generation: `brew install pango` (macOS) or equivalent system dependency

### Getting Started

1. **Clone the repository**:
   ```bash
   git clone git@github.com:Reformation-Parish/Liturgist.git
   cd liturgist
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

   This installs the package in editable mode with all development dependencies.

### Development Workflow

#### Code Formatting
The project uses [Black](https://github.com/psf/black) for code formatting and [Ruff](https://github.com/astral-sh/ruff) for linting.

Use an editor which supports [.editorconfig](.editorconfig) for consistent file formatting.

**Format code with Black**:
```bash
black src/ tests/
```

**Lint code with Ruff**:
```bash
ruff check src/ tests/
```

**Auto-fix linting issues**:
```bash
ruff check src/ tests/ --fix
```

#### Running Tests
```bash
pytest
```

**Run tests with coverage**:
```bash
pytest --cov=src/liturgist --cov-report=html
```

#### Type Checking (Optional)
If you want to add type checking:
```bash
pip install mypy
mypy src/liturgist
```

### Project Structure

```
liturgist/
├── src/
│   └── liturgist/
│       ├── __init__.py      # Package initialization and exports
│       ├── core.py          # Core functionality
│       └── cli.py           # Command-line interface
├── tests/                   # Test files
├── samples/                 # Sample files and templates
├── pyproject.toml          # Project configuration
├── README.md               # User documentation
└── CONTRIBUTING.md         # This file
```

### Making Changes

1. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality in the `tests/` directory

4. **Run the test suite** to ensure nothing is broken:
   ```bash
   pytest
   ```

5. **Format and lint your code**:
   ```bash
   black src/ tests/
   ruff check src/ tests/ --fix
   ```

6. **Commit your changes** with a descriptive commit message:
   ```bash
   git add .
   git commit -m "Add feature: description of what you did"
   ```

7. **Push your branch** and create a pull request

### Building the Package

To build the package for distribution:

```bash
pip install build
python -m build
```

This creates both wheel and source distributions in the `dist/` directory.

### Testing Different Scenarios

#### Mass PDF Rendering for Testing
Create a file `dates.txt` with dates (one per line) and run:

```bash
for i in $(cat dates.txt); do
  liturgist --template ./samples/order-of-worship.html ./schedule.xlsx \
    -o "./output/${i////-}-order-of-worship.pdf" --date "$i"
done
```

#### Testing Different File Formats
Test with various input formats:
- CSV: `liturgist --print-json schedule.csv`
- XLSX: `liturgist --print-json schedule.xlsx`
- ODS: `liturgist --print-json schedule.ods`

### Code Style Guidelines

- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 88 characters)
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Write docstrings for all public functions and classes
- Use type hints where appropriate
- Keep functions focused and well-named
- Add comments for complex logic

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs. actual behavior
- Sample files if applicable

### Questions?

Feel free to open an issue for questions about contributing or reach out to the maintainers.
