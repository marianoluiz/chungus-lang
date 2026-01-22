# Semantic Analyzer Guide for CHUNGUS Compiler

## Overview: The Compilation Pipeline

Your compiler currently has **3 phases**:

```
SOURCE CODE → LEXER → TOKENS → PARSER → AST → [SEMANTIC ANALYZER] → CODE GENERATION
```

- **Lexer** (✅ Done): Converts source text into tokens
- **Syntax Analyzer** (✅ Done): Converts tokens into an Abstract Syntax Tree (AST)
- **Semantic Analyzer** (🔨 To Build): Validates the AST against language rules
- **Code Generation** (Future): Converts validated AST to executable code

## Why Do You Need a Semantic Analyzer?

The **parser** only checks if code follows the **grammar rules**. It answers:
- "Is this valid Python/Java/CHUNGUS syntax?" ✅ YES/NO

The **semantic analyzer** checks if code makes **logical sense**. It answers:
- "Is variable `x` declared before use?" 
- "Does the type of `y` match where it's used?"
- "Do function calls have the right number of arguments?"
- "Is this operation valid for this type?"

### Example: Why You Need Semantic Analysis

```chungus
fn add(int x, int y)
    ret x + y
END

// Syntactically valid: ✅ PARSER ACCEPTS
// But semantically problematic:
let z = add(5, "hello")    // Type mismatch!
let w = undefined_var + 3  // Variable not declared!
```

**The parser accepts both lines.** The semantic analyzer must reject them.

---

## Key Responsibilities of a Semantic Analyzer

### 1. **Symbol Table Management**
Track all declared variables, functions, and parameters.

```python
# What you track:
{
  "x": {"type": "int", "scope": "local", "line": 5},
  "result": {"type": "float", "scope": "local", "line": 7},
  "add": {"type": "function", "params": [("int", "x"), ("int", "y")], "return_type": "int"}
}
```

### 2. **Type Checking**
Ensure operations are type-safe.

```
int x = 5;
float y = x;      // ✅ Implicit conversion (int → float) - OK
string s = y;     // ❌ float → string not allowed
z = x + "hello";  // ❌ int + string not allowed
```

### 3. **Scope Management**
Track where variables are visible (global vs local vs function-scoped).

```chungus
fn foo()
    let x = 5        // x is local to foo
END

print x              // ❌ ERROR: x not visible here
```

### 4. **Function Call Validation**
Check arguments match parameters.

```chungus
fn greet(str name, int age)
    ret name
END

greet("Alice", 30)   // ✅ 2 args, correct types
greet("Bob")         // ❌ Missing argument
greet(100, 200)      // ❌ First arg wrong type
```

### 5. **Forward Declaration Checking**
In CHUNGUS, functions must be declared before use (unless you support forward declarations).

---

## Architectural Design

### How It Fits With Your Syntax Analyzer

Your syntax analyzer produces an **AST**. The semantic analyzer **traverses** this AST:

```
AST (from Parser)
  │
  ├─ function_statement (name: "add", params: [...], body: [...])
  ├─ function_statement (name: "multiply", params: [...], body: [...])
  └─ general_statement (...)
        │
        └─ assignment (id: "result", expr: ...)
```

The semantic analyzer:
1. **Walks the AST** (tree traversal)
2. **Builds a symbol table** (first pass)
3. **Type checks** (second pass)
4. **Reports errors** without stopping (collect all errors, not just the first)

### Recommended Architecture

```
src/semantic/
├── __init__.py
├── __main__.py              # CLI entry point
├── semantic_analyzer.py     # Main analyzer class
├── symbol_table.py          # Symbol table data structures
├── type_checker.py          # Type checking logic
├── scope_manager.py         # Scope/environment management
├── errors.py                # Semantic error classes
├── semantic_adapter.py      # Clean interface for GUI/main.py
└── test_semantic.py         # Unit tests
```

---

## Implementation Guide

### Step 1: Create Error Classes

**`src/semantic/errors.py`**:

```python
"""Semantic analysis error definitions."""

class SemanticError:
    """Base semantic error."""
    def __init__(self, message: str, line: int, col: int):
        self.message = message
        self.line = line
        self.col = col
    
    def __str__(self):
        return f"Line {self.line}, Col {self.col}: {self.message}"

class UndefinedVariableError(SemanticError):
    """Variable used before declaration."""
    pass

class TypeMismatchError(SemanticError):
    """Operation on incompatible types."""
    pass

class FunctionNotDefinedError(SemanticError):
    """Function call to non-existent function."""
    pass

class ArgumentCountMismatchError(SemanticError):
    """Function called with wrong number of arguments."""
    pass

class VariableAlreadyDefinedError(SemanticError):
    """Variable redeclared in same scope."""
    pass
```

### Step 2: Create Symbol Table

**`src/semantic/symbol_table.py`**:

```python
"""Symbol table and scope management."""

from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple

@dataclass
class Symbol:
    """Represents a declared variable or function."""
    name: str
    kind: str           # "variable", "function", "parameter"
    type_: str          # "int", "float", "string", "bool", "array"
    line: int           # Where it was declared
    col: int
    scope_level: int    # 0=global, 1+=nested
    
    # For functions:
    params: Optional[List[Tuple[str, str]]] = None  # [(type, name), ...]
    return_type: Optional[str] = None

class SymbolTable:
    """Manages nested scopes and symbol resolution."""
    
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = [{}]  # Stack of scope dictionaries
        self.scope_level = 0
    
    def enter_scope(self):
        """Enter a new nested scope (e.g., function body)."""
        self.scope_level += 1
        self.scopes.append({})
    
    def exit_scope(self):
        """Exit current scope."""
        self.scopes.pop()
        self.scope_level -= 1
    
    def declare(self, symbol: Symbol) -> bool:
        """
        Declare a symbol in current scope.
        Returns True if successful, False if already declared in this scope.
        """
        current_scope = self.scopes[-1]
        if symbol.name in current_scope:
            return False  # Already declared in this scope
        current_scope[symbol.name] = symbol
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol, searching from innermost to outermost scope.
        Returns the symbol or None if not found.
        """
        # Search from innermost (end) to outermost (start)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
```

### Step 3: Create Type Checker

**`src/semantic/type_checker.py`**:

```python
"""Type checking utilities."""

from typing import Optional

# Type compatibility rules for CHUNGUS
TYPE_HIERARCHY = {
    "int": ["int", "float", "string", "bool"],      # int can convert to these
    "float": ["float", "string"],
    "string": ["string"],
    "bool": ["bool", "int"],
    "array": ["array"],
}

class TypeChecker:
    """Type compatibility checking."""
    
    @staticmethod
    def is_compatible(from_type: str, to_type: str) -> bool:
        """
        Check if from_type can be assigned to to_type.
        Handles implicit conversions.
        """
        if from_type == to_type:
            return True
        
        if from_type in TYPE_HIERARCHY:
            return to_type in TYPE_HIERARCHY[from_type]
        
        return False
    
    @staticmethod
    def infer_type(operation: str, left_type: str, right_type: str) -> Optional[str]:
        """
        Infer the type of a binary operation.
        
        Examples:
            ("add", "int", "int") → "int"
            ("add", "int", "float") → "float"
            ("add", "string", "string") → "string"
            ("add", "int", "string") → None (invalid)
        """
        if operation in ["+", "-", "*", "/", "%"]:
            if left_type == "int" and right_type == "int":
                return "int"
            elif left_type in ["int", "float"] and right_type in ["int", "float"]:
                return "float"
            elif left_type == "string" and right_type == "string" and operation == "+":
                return "string"
            else:
                return None
        
        elif operation in ["<", ">", "<=", ">=", "==", "!="]:
            # Comparison always returns bool
            if left_type in ["int", "float"] and right_type in ["int", "float"]:
                return "bool"
            else:
                return None
        
        return None
```

### Step 4: Create Main Semantic Analyzer

**`src/semantic/semantic_analyzer.py`**:

```python
"""Main semantic analysis engine."""

from typing import List, Optional, Dict
from src.syntax.ast import ASTNode, ParseResult
from src.semantic.symbol_table import SymbolTable, Symbol
from src.semantic.type_checker import TypeChecker
from src.semantic.errors import (
    SemanticError, UndefinedVariableError, TypeMismatchError,
    FunctionNotDefinedError, ArgumentCountMismatchError,
    VariableAlreadyDefinedError
)

class SemanticAnalyzer:
    """
    Analyzes an AST for semantic correctness.
    
    Two-pass approach:
    1. First pass: Build symbol table (declarations)
    2. Second pass: Type check (usage)
    """
    
    def __init__(self, tree: ASTNode, source: str, debug: bool = False):
        self.tree = tree
        self.source = source
        self.debug = debug
        self.symbol_table = SymbolTable()
        self.type_checker = TypeChecker()
        self.errors: List[SemanticError] = []
    
    def analyze(self) -> "SemanticResult":
        """Run semantic analysis and return results."""
        if self.tree is None:
            return SemanticResult(tree=None, errors=["No AST to analyze"])
        
        try:
            # First pass: collect declarations
            self._collect_declarations(self.tree)
            
            # Second pass: type check
            self._type_check(self.tree)
            
        except Exception as e:
            self.errors.append(SemanticError(
                f"Internal semantic analyzer error: {str(e)}", 0, 0
            ))
        
        return SemanticResult(
            tree=self.tree,
            errors=[str(e) for e in self.errors]
        )
    
    def _collect_declarations(self, node: ASTNode) -> None:
        """First pass: traverse AST and collect all declarations."""
        if node is None:
            return
        
        # Handle different node kinds
        if node.kind == "program":
            # Program contains function declarations and statements
            for child in node.children:
                self._collect_declarations(child)
        
        elif node.kind == "function":
            # function node: value="func_name", children=[param_list, body]
            func_name = node.value
            param_list = node.children[0] if node.children else None
            
            # Extract parameters
            params = []
            if param_list and param_list.kind == "param_list":
                for param in param_list.children:
                    param_type = param.value  # type annotation
                    param_name = param.children[0].value if param.children else ""
                    params.append((param_type, param_name))
            
            # Declare function
            func_symbol = Symbol(
                name=func_name,
                kind="function",
                type_="function",
                line=0,
                col=0,
                scope_level=self.symbol_table.scope_level,
                params=params,
                return_type="int"  # TODO: extract from AST
            )
            
            if not self.symbol_table.declare(func_symbol):
                self.errors.append(
                    VariableAlreadyDefinedError(
                        f"Function '{func_name}' already defined", 0, 0
                    )
                )
            
            # Enter function scope and collect local declarations
            self.symbol_table.enter_scope()
            
            # Declare parameters in function scope
            for param_type, param_name in params:
                param_symbol = Symbol(
                    name=param_name,
                    kind="parameter",
                    type_=param_type,
                    line=0,
                    col=0,
                    scope_level=self.symbol_table.scope_level
                )
                self.symbol_table.declare(param_symbol)
            
            # Collect declarations in function body
            if len(node.children) > 1:
                self._collect_declarations(node.children[1])
            
            self.symbol_table.exit_scope()
        
        elif node.kind == "assignment":
            # assignment: id_name = expr
            var_name = node.value
            var_type = "int"  # TODO: infer from RHS or annotation
            
            symbol = Symbol(
                name=var_name,
                kind="variable",
                type_=var_type,
                line=0,
                col=0,
                scope_level=self.symbol_table.scope_level
            )
            
            if not self.symbol_table.declare(symbol):
                self.errors.append(
                    VariableAlreadyDefinedError(
                        f"Variable '{var_name}' already defined in this scope", 0, 0
                    )
                )
        
        # Recurse to children
        for child in node.children:
            self._collect_declarations(child)
    
    def _type_check(self, node: ASTNode) -> Optional[str]:
        """
        Second pass: traverse AST and type check.
        Returns the inferred type of the node, or None if type error.
        """
        if node is None:
            return None
        
        if node.kind == "id":
            # Identifier: check if declared
            var_name = node.value
            symbol = self.symbol_table.lookup(var_name)
            
            if symbol is None:
                self.errors.append(
                    UndefinedVariableError(
                        f"Variable '{var_name}' not defined", 0, 0
                    )
                )
                return None
            
            return symbol.type_
        
        elif node.kind == "int_literal":
            return "int"
        
        elif node.kind == "float_literal":
            return "float"
        
        elif node.kind == "string_literal":
            return "string"
        
        elif node.kind == "bool_literal":
            return "bool"
        
        elif node.kind == "binary_op":
            # binary_op: value="+", children=[left, right]
            op = node.value
            left_type = self._type_check(node.children[0])
            right_type = self._type_check(node.children[1])
            
            if left_type and right_type:
                result_type = self.type_checker.infer_type(op, left_type, right_type)
                if result_type is None:
                    self.errors.append(
                        TypeMismatchError(
                            f"Invalid operation '{op}' between '{left_type}' and '{right_type}'",
                            0, 0
                        )
                    )
                return result_type
            
            return None
        
        elif node.kind == "assignment":
            # assignment: id_name = expr
            var_type = self.symbol_table.lookup(node.value).type_
            expr_type = self._type_check(node.children[0]) if node.children else None
            
            if expr_type and not self.type_checker.is_compatible(expr_type, var_type):
                self.errors.append(
                    TypeMismatchError(
                        f"Cannot assign '{expr_type}' to '{var_type}'", 0, 0
                    )
                )
            
            return var_type
        
        elif node.kind == "function_call":
            # function_call: func_name, children=[arg_list]
            func_name = node.value
            symbol = self.symbol_table.lookup(func_name)
            
            if symbol is None or symbol.kind != "function":
                self.errors.append(
                    FunctionNotDefinedError(
                        f"Function '{func_name}' not defined", 0, 0
                    )
                )
                return None
            
            # Check argument count
            arg_list = node.children[0] if node.children else None
            actual_args = len(arg_list.children) if arg_list else 0
            expected_args = len(symbol.params) if symbol.params else 0
            
            if actual_args != expected_args:
                self.errors.append(
                    ArgumentCountMismatchError(
                        f"Function '{func_name}' expects {expected_args} args, got {actual_args}",
                        0, 0
                    )
                )
            
            # Type check arguments
            if arg_list:
                for i, arg in enumerate(arg_list.children):
                    arg_type = self._type_check(arg)
                    if i < len(symbol.params) and arg_type:
                        expected_type = symbol.params[i][0]
                        if not self.type_checker.is_compatible(arg_type, expected_type):
                            self.errors.append(
                                TypeMismatchError(
                                    f"Argument {i} to '{func_name}': expected '{expected_type}', got '{arg_type}'",
                                    0, 0
                                )
                            )
            
            return symbol.return_type
        
        # Recurse to children for statements
        for child in node.children:
            self._type_check(child)
        
        return None


class SemanticResult:
    """Result of semantic analysis."""
    def __init__(self, tree: Optional[ASTNode], errors: List[str]):
        self.tree = tree
        self.errors = errors
```

### Step 5: Create Adapter for Integration

**`src/semantic/semantic_adapter.py`**:

```python
"""Clean adapter interface for semantic analysis."""

from src.syntax.ast import ASTNode
from src.semantic.semantic_analyzer import SemanticAnalyzer, SemanticResult

def semantic_analysis_adapter(tree: ASTNode, source: str) -> SemanticResult:
    """
    Runs semantic analysis on an AST.
    
    Args:
        tree: AST from syntax parser
        source: Original source code string
    
    Returns:
        SemanticResult with validated tree and error list
    """
    analyzer = SemanticAnalyzer(tree, source, debug=False)
    return analyzer.analyze()
```

### Step 6: Integrate with Main Pipeline

Update **`src/main.py`** to include semantic analysis:

```python
def syntax_adapter(source: str):
    """Adapter with lexer + parser + semantic analyzer."""
    from src.semantic.semantic_adapter import semantic_analysis_adapter
    
    # Lexical analysis
    lexer = Lexer(source, debug=False)
    lexer.start()
    tokens = lexer.token_stream
    errors = []
    
    if lexer.log:
        errors.append("Lexical Error/s:")
        errors.extend(lexer.log.splitlines())
        return tokens, errors
    
    # Syntax analysis
    parser = RDParser(tokens, source, debug=False)
    parse_result = parser.parse()
    
    if parse_result.errors:
        errors.append("Syntax Error/s:")
        errors.extend(parse_result.errors)
        return tokens, errors
    
    # Semantic analysis
    semantic_result = semantic_analysis_adapter(parse_result.tree, source)
    
    if semantic_result.errors:
        errors.append("Semantic Error/s:")
        errors.extend(semantic_result.errors)
        return tokens, errors
    
    return tokens, errors
```

---

## Key Design Patterns

### 1. **Two-Pass Analysis**
```
PASS 1: Collect Declarations
  - Walk AST, build symbol table
  - No type checking yet
  - Quick pass to know what exists

PASS 2: Type Check
  - Walk AST again
  - Use symbol table for lookups
  - Report type mismatches
```

### 2. **Visitor Pattern** (Advanced)
As your analyzer grows, use the Visitor pattern:

```python
class SemanticVisitor:
    def visit_program(self, node): ...
    def visit_function(self, node): ...
    def visit_assignment(self, node): ...
    def visit_binary_op(self, node): ...
```

### 3. **Error Collection**
Don't stop at first error—collect all errors:

```python
self.errors = []  # List, not single error

# Keep analyzing even after error
self.errors.append(semantic_error)
continue_analysis()
```

---

## Testing Your Semantic Analyzer

Create **`test/semantic/test_semantic.py`**:

```python
import pytest
from src.semantic.symbol_table import SymbolTable, Symbol

def test_symbol_declaration():
    """Test symbol declaration and lookup."""
    table = SymbolTable()
    
    sym = Symbol("x", "variable", "int", 1, 0, 0)
    assert table.declare(sym) == True
    
    # Can't redeclare in same scope
    assert table.declare(sym) == False
    
    # Can declare in nested scope
    table.enter_scope()
    assert table.declare(sym) == True

def test_type_compatibility():
    """Test type checking."""
    from src.semantic.type_checker import TypeChecker
    
    assert TypeChecker.is_compatible("int", "float") == True
    assert TypeChecker.is_compatible("float", "int") == False
    assert TypeChecker.is_compatible("string", "string") == True
```

---

## Workflow Summary

1. **User writes CHUNGUS code**
2. **Lexer** → tokens
3. **Parser** → AST
4. **Semantic Analyzer** (YOUR NEW CODE):
   - Pass 1: Build symbol table
   - Pass 2: Type check
5. Report errors or continue to code generation

---

## Next Steps

1. Implement `symbol_table.py` first (simplest)
2. Implement `type_checker.py` (pure logic)
3. Implement `errors.py` (error classes)
4. Implement `semantic_analyzer.py` (main logic)
5. Test with sample programs from `samples/`
6. Integrate with `main.py`

Good luck building your semantic analyzer! 🚀
