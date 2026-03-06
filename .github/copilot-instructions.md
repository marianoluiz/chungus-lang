# Copilot Instructions for CHUNGUS Language Compiler

## Project Overview
This is a compiler for CHUNGUS - a clean, minimal, general programming language. The project is written in Python and includes:
- **Lexer**: DFA-based tokenization (COMPLETE ✓)
- **Syntax Analyzer**: Recursive descent parser with AST generation (COMPLETE ✓)
- **Semantic Analyzer**: Type checking, symbol table management, and semantic validation (COMPLETE ✓)
- **Code Generator**: Next phase - target code generation (PENDING)
- **GUI**: User interface for compilation

## Compilation Pipeline Status

### Phase 1: Lexical Analysis ✓ COMPLETE
- DFA-based tokenizer with transition tables
- Handles all CHUNGUS tokens: keywords, identifiers, literals, operators, delimiters
- Error recovery and reporting
- Skip tokens: whitespace, newline, comments

### Phase 2: Syntax Analysis ✓ COMPLETE
- Recursive descent parser following CHUNGUS grammar
- Generates Abstract Syntax Tree (AST)
- Error recovery for resilient parsing
- Supports all language constructs: functions, control flow, arrays, expressions

### Phase 3: Semantic Analysis ✓ COMPLETE
- Two-pass analysis: declaration collection → type checking
- Symbol table with nested scopes and shadowing
- Type system with CHUNGUS coercion rules
- Comprehensive error detection and reporting
- Constant folding and propagation (optional optimization)

### Phase 4: Code Generation - NEXT PHASE
- Target: Python bytecode or intermediate representation
- Register allocation and instruction selection
- Runtime library integration
- Output executable or interpretable code

## Project Structure

### Core Modules
- **`src/lexer/`**: DFA-based lexical analyzer (COMPLETE)
  - `dfa_lexer.py`: Main lexer implementation with DFALexer class
  - `dfa_table.py`: DFA transition table and state definitions
  - `token_builder.py`: Token construction utilities
  - Processes source code character-by-character
  - Returns list of Token objects
  
- **`src/syntax/`**: Recursive descent parser (COMPLETE)
  - `rd_parser.py`: Main RDParser class and parse orchestration
  - `core.py`: Core parser utilities (match, expect, peek, advance)
  - `rule_single.py`: Single-line statement rules
  - `rule_expr.py`: Expression parsing with precedence handling
  - `rule_block.py`: Block-level structures (functions, control flow)
  - Consumes tokens, produces ASTNode tree
  
- **`src/semantic/`**: Semantic analysis (COMPLETE)
  - `semantic_analyzer.py`: SemanticAnalyzer class with:
    - **SymbolTable**: Nested scope management with enter_scope/exit_scope
    - **TypeChecker**: CHUNGUS type coercion and compatibility rules
    - **Two-pass analysis**: collect_declarations() → type_check()
    - Error classes: UndefinedVariableError, TypeMismatchError, FunctionNotDefinedError, ArgumentCountMismatchError
    - Annotates AST nodes with inferred_type attribute
    - Validates: variable definitions, function signatures, array bounds, type compatibility

- **`src/codegen/`**: Code generation (PENDING - NEXT PHASE)
  - Target architecture and instruction set to be determined
  - Will consume type-annotated AST
  - Output format to be determined (bytecode, assembly, IR, etc.)

- **`src/constants/`**: Shared constants and definitions
  - `token.py`: Token dataclass and token type constants
  - `atoms.py`: Atomic symbols/keywords (KW_IF, KW_WHILE, etc.)
  - `delims.py`: Delimiters and operators
  - `cfg_lark`: CHUNGUS grammar in Lark format (reference only)
  - `ast.py`: ASTNode and ParseResult dataclasses
  - `error_lexical.py`: LexicalError class
  - `error_syntax.py`: SyntaxError class
  - All semantic errors defined in semantic_analyzer.py

### Testing Infrastructure
- **`test/lexer/`**: Lexer tests with CSV data files
  - `test_lexer_tokens.py`: Token recognition tests
  - `test_lexer_errors.py`: Error handling tests
  - Data-driven with `test_lexer_tokens_data.csv` and `test_lexer_errors_data.csv`
  
- **`test/syntax/`**: Syntax parser tests
  - `test_syntax.py`: Parser correctness tests
  - `test_syntax_data.csv`: Test cases with expected AST structures
  
- **`test/semantic/`**: Semantic analyzer tests
  - `test_semantic.py`: Semantic validation tests
  - `test_semantic_data.csv`: Test cases covering type checking, scoping, errors
  
- All tests use pytest with parametrization
- CSV format: test_id, input_code, expected_output/errors

### Sample Programs
- **`samples/`**: Sample `.chg` (CHUNGUS) programs
  - `program1.chg` through `program10.chg`: Various language features
  - `all_stmt.chg`: Comprehensive statement coverage
  - `all_stmt_ast.chg`: AST testing reference
  - Used for manual testing and development validation

## CHUNGUS Language Specification

### Type System
CHUNGUS has 5 primitive types:
- **int**: Integer values (e.g., `42`, `-10`, `0`)
- **float**: Floating-point values (e.g., `3.14`, `-0.5`, `2.0`)
- **bool**: Boolean values (`TRUE`, `FALSE`)
- **string**: String literals (e.g., `"hello"`, `"world"`)
- **array**: One or two-dimensional arrays (e.g., `x:[10]`, `matrix:[5][5]`)

### Type Coercion Rules
CHUNGUS supports implicit type coercion:

**Numeric Coercion**: int, float, bool, string → numeric
- Used in arithmetic operations: `+`, `-`, `*`, `/`, `//`, `%`, `^`
- Result type:
  - `/` always returns float
  - If any operand is float → result is float
  - Otherwise → result is int
  - `//` (integer division) returns int unless float is involved

**Boolean Coercion**: int, float, bool, string → boolean
- Used in logical operations: `&`, `|`, `!`
- Used in control flow conditions
- Result type is always bool

**Comparison Operations**: Require numeric coercion
- Operators: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Both operands coerced to numeric
- Result type is always bool

### Type Constants (Semantic Analyzer)
```python
TY_INT = "int"
TY_FLOAT = "float"
TY_BOOL = "bool"
TY_STRING = "string"
TY_ARRAY = "array"
TY_UNKNOWN = "unknown"  # When type cannot be determined

NUMERIC_COERCIBLE = {TY_INT, TY_FLOAT, TY_BOOL, TY_STRING}
BOOL_COERCIBLE = {TY_INT, TY_FLOAT, TY_BOOL, TY_STRING}
```

### Keywords and Operators
**Keywords**: `fn`, `ret`, `if`, `elif`, `else`, `close`, `while`, `for`, `try`, `except`, `finally`, `read`, `show`, `todo`, `TRUE`, `FALSE`

**Arithmetic**: `+`, `-`, `*`, `/`, `//`, `%`, `^` (power)
**Comparison**: `<`, `>`, `<=`, `>=`, `==`, `!=`
**Logical**: `&` (and), `|` (or), `!` (not)
**Assignment**: `=`
**Array/Function**: `[`, `]`, `(`, `)`, `,`
**Delimiters**: `;`, `:`, `{`, `}`

### Statement Types
1. **Variable Declaration/Assignment**: `x = 5;`, `name = read;`
2. **Array Declaration**: `arr:[10];`, `matrix:[5][5];`
3. **Array Assignment**: `arr[0] = 42;`, `matrix[i][j] = 99;`
4. **Function Definition**: `fn name(param1, param2): ... ret value; close`
5. **Function Call**: `result = foo(1, 2);`, `bar();`
6. **Output**: `show expr;`
7. **Control Flow**: `if`, `elif`, `else`, `while`, `for`
8. **Error Handling**: `try`, `except`, `finally`
9. **Todo**: `todo "implement feature";`

### Grammar Highlights (from cfg_lark)
- Program starts with optional function definitions, followed by main statements
- Functions must end with `close`
- Return statements: `ret expr;`
- Arrays: 1D `x:[size]` or 2D `x:[rows][cols]`
- Expressions support precedence and associativity
- Comments: `// single line` and `/* multi-line */`


## Coding Conventions

### Python Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Use dataclasses for simple data structures (see `Token`, `Symbol` classes)
- Keep line length reasonable (configured in `.flake8`)

### Module Organization
- Each major component (lexer, syntax, semantic) is a separate package
- Use `__init__.py` to expose public APIs
- `__main__.py` enables running modules with `python -m`

### AST Structure
- **ASTNode dataclass** (in `src/constants/ast.py`):
  - `kind`: str - Grammar construct identifier (e.g., 'program', 'function', 'if', 'id')
  - `value`: Optional[str] - Payload for leaf nodes (identifier names, literal values)
  - `children`: List[ASTNode] - Ordered child nodes
  - `line`, `col`: Optional[int] - Source location for error reporting
  - `inferred_type`: Optional[str] - Added by semantic analyzer (e.g., 'int', 'float', 'bool')
- **ParseResult dataclass**:
  - `tree`: Optional[ASTNode] - Root AST node or None if parsing failed
  - `errors`: List[str] - Human-readable error messages

### Token Handling
- Token types are defined as constants in `src/constants/token.py`
- **Skip tokens** (not in AST): whitespace, newline, comment
- **Terminal token types**: `id`, `int_literal`, `float_literal`, `str_literal`, `bool_literal`
- **Token dataclass**:
  - `type`: str - Token type constant
  - `value`: str - Lexeme text
  - `line`, `col`: int - Source position

### Symbol Table Design
- **Symbol dataclass** (in `semantic_analyzer.py`):
  - `name`: str - Symbol identifier
  - `kind`: str - "variable", "function", "parameter"
  - `type_`: str - Type tag (int, float, bool, string, array)
  - `line`, `col`: int - Declaration location
  - `scope_level`: int - 0=global, 1+=nested
  - `params`: Optional[List[Tuple[str, str]]] - For functions: [(type, name), ...]
  - `return_type`: Optional[str] - For functions
  - `array_dims`: Optional[List[int]] - For arrays: [size] or [rows, cols]
  - `constant_value`: Optional[Any] - Compile-time constant (for optimization)

- **SymbolTable class**:
  - `scopes`: List[Dict[str, Symbol]] - Stack of scope dictionaries
  - `scope_level`: int - Current nesting level
  - `enter_scope()`, `exit_scope()` - Manage nested scopes
  - `define(symbol)` - Add symbol to current scope
  - `lookup(name)` - Search from innermost to outermost scope
  - `lookup_current_scope(name)` - Check only current scope (for shadowing)

### Error Handling
- **Semantic error classes** (all in `semantic_analyzer.py`):
  - `SemanticError`: Base class with message, line, col, source_line
  - `UndefinedVariableError`: Variable used before declaration
  - `TypeMismatchError`: Operation on incompatible types
  - `FunctionNotDefinedError`: Call to non-existent function
  - `ArgumentCountMismatchError`: Wrong number of function arguments
- **Error reporting**:
  - Include line, column, and source context for helpful messages
  - Collect errors to allow multiple error reporting (don't stop at first)
  - Never raise exceptions for language errors - collect in error lists
  - Format with caret pointing to error location

### Testing
- Write data-driven tests using CSV files
- Use pytest parametrization for multiple test cases
- Test files follow pattern: `test_<component>_<aspect>.py`
- Test data files: `test_<component>_<aspect>_data.csv`
- CSV columns: test_id, input_code, expected_output/errors

## Development Workflow

### Environment Setup
1. Create virtual environment: `python3 -m venv .venv`
2. Activate: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies: `pip install -r requirements.txt` (base) or `requirements-dev.txt` (dev)

### Running Components
- **GUI**: `python -m src.main`
- **Lexer CLI**: `python -m src.lexer`
- **Syntax CLI**: `python -m src.syntax`
- **Semantic CLI**: `python -m src.semantic`
- **Tests**: `pytest` or `python -m pytest`
- **Specific test**: `pytest test/semantic/test_semantic.py`

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
- Skip tokens (whitespace, newline, comments) are filtered before parsing

### Recursive Descent Parser
- Grammar rules separated by complexity (single, expr, block)
- AST nodes represent program structure with `kind`, `value`, and `children`
- Error recovery for resilient parsing
- Each grammar rule has a corresponding parse function
- Precedence climbing for expression parsing

### Semantic Analyzer
- **Two-pass analysis**:
  1. First pass: `collect_declarations()` - Build symbol table
     - Traverse entire AST to find all function and variable declarations
     - Populate symbol table with function signatures and global variables
     - Detect redeclaration errors
  2. Second pass: `type_check()` - Validate types and expressions
     - Check variable usage against symbol table
     - Validate function calls (existence, argument count, parameter types)
     - Infer expression types using CHUNGUS coercion rules
     - Annotate AST nodes with `inferred_type` attribute
     
- **Symbol table**: Nested scopes with shadowing support
  - Stack-based scope management
  - `enter_scope()` pushes new scope, `exit_scope()` pops
  - `lookup()` searches from innermost to outermost scope
  - `lookup_current_scope()` checks only current scope (for shadowing detection)
  
- **Type checking**: CHUNGUS coercion rules
  - **Arithmetic operations** (`+`, `-`, `*`, `/`, `//`, `%`, `^`):
    - Both operands must be numeric-coercible (int, float, bool, string)
    - `/` always returns float
    - Other ops: if either is float → result is float; else int
  - **Comparison operations** (`<`, `>`, `<=`, `>=`, `==`, `!=`):
    - Both operands must be numeric-coercible
    - Result is always bool
  - **Logical operations** (`&`, `|`, `!`):
    - Operands must be bool-coercible
    - Result is always bool
  - Arrays are NOT coercible - type errors for array operands in expressions
  
- **Error recovery**: Collect all errors, don't stop at first error
  - Errors stored in `self.errors` list
  - Continue analysis even after errors to find multiple issues
  - Each error has line, column, and source context
  
- **Common patterns**:
  - Always check if symbol exists before accessing attributes
  - Type-check all child nodes (arguments, operands, etc.) recursively
  - Return `TY_UNKNOWN` when type cannot be determined
  - Never raise exceptions for language errors - collect in error list
  - Use early returns to simplify control flow

### Adapter Pattern
- Adapters provide clean interfaces: defined in `__init__.py` files
- `analyze_lexical()`, `analyze_syntax()`, `analyze_semantic()` functions
- Isolate component internals from external usage
- Simplify integration in GUI and CLI
- Return standardized result objects (tokens, ParseResult, errors)

## Key Files to Reference

- **Grammar**: `src/constants/cfg_lark` - Formal grammar definition
- **Token Types**: `src/constants/token.py` - All token type constants
- **AST Documentation**: `src/syntax/ast.md` - AST node structure
- **Sample Programs**: `samples/*.chg` - Example CHUNGUS programs
- **Semantic Analyzer**: `src/semantic/semantic_analyzer.py` - Full implementation with comments

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
