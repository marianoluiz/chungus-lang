# Copilot Instructions for CHUNGUS Language Compiler

## Project Overview
This is a compiler for CHUNGUS - a clean, minimal, general programming language. The project is written in Python and includes:
- **Lexer**: DFA-based tokenization
- **Syntax Analyzer**: Recursive descent parser with AST generation
- **Semantic Analyzer**: Type checking and semantic validation (in development)
- **GUI**: User interface for compilation

## Project Structure

### Core Modules
- **`src/lexer/`**: DFA-based lexical analyzer
  - `dfa_lexer.py`: Main lexer implementation
  - `dfa_table.py`: DFA transition table
  - `token_builder.py`: Token construction utilities
  - `error_handler.py`: Lexical error handling
  
- **`src/syntax/`**: Recursive descent parser
  - `rd_parser.py`: Main parser implementation
  - `ast.py`: Abstract Syntax Tree node definitions
  - `rule_*.py`: Grammar rule implementations
  - `errors.py`: Syntax error handling
  
- **`src/semantic/`**: Semantic analysis (in development)

- **`src/constants/`**: Shared constants and definitions
  - `token.py`: Token class and token type constants
  - `atoms.py`: Atomic symbols/keywords
  - `delims.py`: Delimiters
  - `cfg_lark`: Grammar definition (Lark format)

### Testing
- **`test/lexer/`**: Lexer tests with CSV data files
- **`test/syntax/`**: Syntax parser tests with CSV data files
- Tests use pytest with parametrized data-driven testing

### Samples
- **`samples/`**: Sample `.chg` (CHUNGUS) programs for testing

## Coding Conventions

### Python Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Use dataclasses for simple data structures (see `Token` class)
- Keep line length reasonable (configured in `.flake8`)

### Module Organization
- Each major component (lexer, syntax, semantic) is a separate package
- Use `__init__.py` to expose public APIs
- Adapters (`*_adapter.py`) provide clean interfaces to components
- `__main__.py` enables running modules with `python -m`

### Token Handling
- Token types are defined as constants in `src/constants/token.py`
- Skip tokens include: whitespace, newline, comment
- Terminal token types: `id`, `int_literal`, `float_literal`, `str_literal`, `bool_literal`

### Error Handling
- Each component has its own error handler module
- Errors should be informative with line and column information
- Collect errors to allow multiple error reporting when possible

### Testing
- Write data-driven tests using CSV files
- Use pytest parametrization for multiple test cases
- Test files follow pattern: `test_<component>_<aspect>.py`
- Test data files: `test_<component>_<aspect>_data.csv`

## Development Workflow

### Environment Setup
1. Create virtual environment: `python3 -m venv .venv`
2. Activate: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies: `pip install -r requirements.txt` (base) or `requirements-dev.txt` (dev)

### Running Components
- **GUI**: `python -m src.main`
- **Lexer CLI**: `python -m src.lexer`
- **Syntax CLI**: `python -m src.syntax`
- **Tests**: `pytest` or `python -m pytest`

### Dependency Management
- Use pip-tools (see `docs/GUIDE-piptools.md`)
- Base dependencies in `requirements.in`
- Dev dependencies in `requirements-dev.in`
- Compile with: `pip-compile` to generate `.txt` files

### Docker Support
- Dockerfile available for containerized execution
- See `docs/GUIDE-docker.md` for details

## Important Design Patterns

### DFA Lexer
- Uses state transition table approach
- Tokens built incrementally as characters are consumed
- Error recovery to continue after lexical errors

### Recursive Descent Parser
- Grammar rules separated by complexity (single, expr, block)
- AST nodes represent program structure
- Error recovery for resilient parsing

### Adapter Pattern
- Adapters provide clean interfaces: `lexer_adapter.py`, `syntax_adapter.py`, `semantic_adapter.py`
- Isolate component internals from external usage
- Simplify integration in GUI and CLI

## Key Files to Reference

- **Grammar**: `src/constants/cfg_lark` - Formal grammar definition
- **Token Types**: `src/constants/token.py` - All token type constants
- **AST Documentation**: `src/syntax/ast.md` - AST node structure
- **Sample Programs**: `samples/*.chg` - Example CHUNGUS programs

## When Adding Features

1. **New Language Feature**:
   - Update grammar in `cfg_lark`
   - Add/modify lexer rules if new tokens needed
   - Update parser rules in appropriate `rule_*.py` files
   - Add AST node types if needed
   - Write tests with sample programs

2. **New Analysis Pass**:
   - Create module in appropriate component directory
   - Add adapter function for clean interface
   - Integrate with main pipeline in `src/main.py`
   - Add comprehensive tests

3. **Bug Fixes**:
   - Write a failing test first
   - Fix the issue
   - Verify test passes
   - Check for similar issues in related code

## Documentation
- User guides in `docs/GUIDE-*.md`
- Technical documentation in code comments and docstrings
- Update README.md for major feature additions

## Notes
- This is an educational compiler project
- Prioritize clarity and simplicity over performance
- Maintain clean separation between compilation phases
- Keep error messages helpful for language users
