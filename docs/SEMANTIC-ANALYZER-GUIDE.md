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

## Important Note About CHUNGUS Grammar

**CHUNGUS does NOT have explicit type annotations in the grammar.** Unlike typed languages:

```chungus
# ✅ CHUNGUS: No type annotations
fn add(x, y):
    ret x + y;
close

# ❌ NOT CHUNGUS: (This would be Java/C++)
fn add(int x, int y) -> int:
    ret x + y;
close
```

This means your semantic analyzer must:
1. **Infer types** from literals and operations
2. Track type information **dynamically** during runtime analysis
3. Use type coercion rules (int, float, bool, string conversions)
4. Report type **incompatibilities** when operations don't make sense

**Type inference example:**
```chungus
x = 5;          # Infer: x is int_literal
y = 3.14;       # Infer: y is float_literal
z = x + y;      # Infer: z is float_literal (int coerces to float)
w = "hello";    # Infer: w is str_literal
v = x + w;      # ❌ Error: can't add int + string (no valid coercion)
```

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
fn add(x, y):
    ret x + y
close

# Syntactically valid: ✅ PARSER ACCEPTS
# But semantically problematic:
z = add(5, "hello")        # Type mismatch!
w = undefined_var + 3      # Variable not declared!
result = add(1)            # Wrong number of arguments!
```

**The parser accepts all three problematic lines.** The semantic analyzer must:
1. ✅ Report the type mismatch in `add(5, "hello")`
2. ✅ Report `undefined_var` is not declared
3. ✅ Report wrong argument count for `add(1)`
4. ✅ Continue analysis to find ALL errors, not stop at the first one

---

## Key Responsibilities of a Semantic Analyzer

### 1. **Symbol Table Management**
Track all declared variables, functions, and parameters with **inferred types**.

```python
# What you track:
{
  "x": {"type": "int_literal", "scope": "local", "line": 5, "inferred": True},
  "result": {"type": "float_literal", "scope": "local", "line": 7, "inferred": True},
  "add": {"type": "function", "params": ["x", "y"], "return_type": "unknown"}
}
```

**Note:** Since CHUNGUS has no type annotations, all types are **inferred** from:
- Literal values (`5` → int_literal, `3.14` → float_literal, `"hi"` → str_literal)
- Operations (`int + float` → float_literal)
- Control flow analysis

### 2. **Type Checking**
Ensure operations are type-safe.

```chungus
x = 5;
y = x;            # ✅ OK - same type
z = x + 3.14;     # ✅ OK - numeric coercion
w = x + "hello";  # ❌ int + string not allowed (depends on your rules)
```

### 3. **Scope Management**
Track where variables are visible (global vs local vs function-scoped).

```chungus
fn foo():
    x = 5;        # x is local to foo
close

show x;           # ❌ ERROR: x not visible here
```

### 4. **Function Call Validation**
Check arguments match parameters.

```chungus
fn greet(name, age):
    ret name;
close

greet("Alice", 30);   # ✅ 2 args, correct types
greet("Bob");         # ❌ Missing argument
greet(100, 200);      # ⚠️ May be valid or invalid depending on type rules
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
        """
        Run semantic analysis and return results.
        
        ⚠️ CRITICAL: This method MUST collect ALL errors, not stop at first one!
        """
        if self.tree is None:
            return SemanticResult(tree=None, errors=["No AST to analyze"])
        
        # ✅ Initialize error list (empty at start)
        self.errors = []
        
        try:
            # ✅ First pass: collect declarations (may add errors)
            self._collect_declarations(self.tree)
            
            # ✅ Second pass: type check (may add MORE errors)
            # Even if pass 1 had errors, still run pass 2 to find ALL problems
            self._type_check(self.tree)
            
        except Exception as e:
            # Only catch unexpected crashes (bugs in analyzer itself)
            # NOT semantic errors (those go in self.errors list)
            self.errors.append(SemanticError(
                f"Internal semantic analyzer error: {str(e)}", 0, 0
            ))
        
        # ✅ Return ALL collected errors (might be 0, might be many)
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
        Returns the inferred type of the node, or TY_UNKNOWN if type error.
        
        ⚠️ CRITICAL: Never stop at first error - collect ALL errors!
        """
        if node is None:
            return None
        
        if node.kind == "id":
            # Identifier: check if declared
            var_name = node.value
            symbol = self.symbol_table.lookup(var_name)
            
            if symbol is None:
                # ✅ Record error but DON'T STOP - continue analysis
                self.errors.append(
                    UndefinedVariableError(
                        f"Variable '{var_name}' not defined", 
                        node.line, node.col
                    )
                )
                # ✅ Return safe fallback type to allow continued analysis
                return TY_UNKNOWN
            
            return symbol.type_
        
        elif node.kind == "int_literal":
            return TY_INT
        
        elif node.kind == "float_literal":
            return TY_FLOAT
        
        elif node.kind == "str_literal":
            return TY_STRING
        
        elif node.kind == "bool_literal":
            return TY_BOOL
        
        elif node.kind in ["+", "-", "*", "/", "//", "%", "**"]:
            # Binary arithmetic operation
            op = node.kind
            left_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            right_type = self._type_check(node.children[1]) if len(node.children) > 1 else TY_UNKNOWN
            
            # ✅ Even if children have errors, try to infer type
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)
                if result_type is None:
                    # ✅ Record error but DON'T STOP
                    self.errors.append(
                        TypeMismatchError(
                            f"Invalid operation '{op}' between '{left_type}' and '{right_type}'",
                            node.line, node.col
                        )
                    )
                    # ✅ Return safe fallback to continue
                    return TY_UNKNOWN
                return result_type
            
            return TY_UNKNOWN
        
        elif node.kind == "assignment_statement":
            # assignment: id_name = expr
            var_name = node.value
            symbol = self.symbol_table.lookup(var_name)
            
            if symbol is None:
                # ✅ Variable might not be declared yet
                self.errors.append(
                    UndefinedVariableError(
                        f"Variable '{var_name}' used before declaration",
                        node.line, node.col
                    )
                )
                # ✅ Continue checking RHS even if LHS has error
                if node.children:
                    self._type_check(node.children[0])
                return TY_UNKNOWN
            
            var_type = symbol.type_
            expr_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            
            # ✅ Check compatibility but don't stop if error
            if expr_type and expr_type != TY_UNKNOWN:
                result_type = TypeChecker.infer_binary_type("=", expr_type, var_type)
                if result_type is None:
                    self.errors.append(
                        TypeMismatchError(
                            f"Cannot assign '{expr_type}' to variable '{var_name}' of type '{var_type}'",
                            node.line, node.col
                        )
                    )
            
            return var_type
        
        elif node.kind == "function_call":
            # function_call: func_name, children=[args]
            func_name = node.value
            symbol = self.symbol_table.lookup(func_name)
            
            if symbol is None or symbol.kind != "function":
                # ✅ Function not found - record error but continue
                self.errors.append(
                    FunctionNotDefinedError(
                        f"Function '{func_name}' not defined",
                        node.line, node.col
                    )
                )
                # ✅ Still type-check arguments to find MORE errors
                if node.children:
                    for arg in node.children:
                        self._type_check(arg)
                return TY_UNKNOWN
            
            # Check argument count
            args = node.children if node.children else []
            actual_count = len(args)
            expected_count = len(symbol.params) if symbol.params else 0
            
            if actual_count != expected_count:
                # ✅ Record error but keep checking argument types
                self.errors.append(
                    ArgumentCountMismatchError(
                        f"Function '{func_name}' expects {expected_count} args, got {actual_count}",
                        node.line, node.col
                    )
                )
            
            # ✅ Type check arguments even if count is wrong
            for i, arg in enumerate(args):
                arg_type = self._type_check(arg)
                if i < expected_count and arg_type and arg_type != TY_UNKNOWN:
                    expected_type = symbol.params[i][0]
                    if not TypeChecker.is_compatible(arg_type, expected_type):
                        # ✅ Record type mismatch for THIS argument
                        self.errors.append(
                            TypeMismatchError(
                                f"Argument {i+1} to '{func_name}': expected '{expected_type}', got '{arg_type}'",
                                node.line, node.col
                            )
                        )
            
            return symbol.return_type if symbol.return_type else TY_UNKNOWN
        
        # ✅ Recurse to children even if current node had errors
        for child in node.children:
            self._type_check(child)
        
        return None
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

### 3. **Error Collection - CRITICAL: Never Stop at First Error**

**🔴 BAD APPROACH (Don't do this):**
```python
def analyze(self):
    try:
        self._collect_declarations(self.tree)
        self._type_check(self.tree)
    except SemanticError as e:
        # ❌ BAD: Returns after first error
        return SemanticResult(None, [str(e)])
```

**✅ GOOD APPROACH (Always do this):**
```python
def analyze(self):
    """Collect ALL errors before returning."""
    self.errors = []  # ✅ List of errors, not just one
    
    try:
        # Continue even if errors found
        self._collect_declarations(self.tree)
        self._type_check(self.tree)
    except Exception as e:
        # Only catch unexpected crashes, not semantic errors
        self.errors.append(SemanticError(
            f"Internal error: {str(e)}", 0, 0
        ))
    
    # ✅ Return ALL collected errors
    return SemanticResult(self.tree, [str(e) for e in self.errors])

def _type_check(self, node):
    """Type check without stopping on errors."""
    if node.kind == "id":
        symbol = self.symbol_table.lookup(node.value)
        if symbol is None:
            # ✅ Record error and CONTINUE
            self.errors.append(
                UndefinedVariableError(f"Variable '{node.value}' not defined", node.line, node.col)
            )
            return TY_UNKNOWN  # Return safe default, don't crash
    
    # ✅ Keep analyzing other nodes
    for child in node.children:
        self._type_check(child)
```

**Why This Matters:**
- Users want to see ALL problems in their code, not just the first one
- Fixing one error shouldn't require re-running to find the next
- IDE integration (future) needs complete error lists for red squiggles
- Professional compilers (GCC, Clang, rustc) all report multiple errors

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

---

## Complete Example: Error Collection in Action

### Input Program (with MULTIPLE errors):
```chungus
fn add(x, y):
    ret x + y
close

# Multiple semantic errors below:
result = add(5)              # Error 1: Wrong arg count
value = undefined_var + 10   # Error 2: Undefined variable
output = add("hello", 3.14)  # Error 3: Type mismatch (depending on your rules)
another = missing_func(1, 2) # Error 4: Function not defined

show result;
```

### Expected Output (ALL 4 errors reported):
```
Semantic Error/s:
Line 5, Col 9: Function 'add' expects 2 args, got 1
Line 6, Col 9: Variable 'undefined_var' not defined
Line 7, Col 10: Invalid operation '+' between 'str_literal' and 'float_literal'
Line 8, Col 11: Function 'missing_func' not defined
```

### How Your Analyzer Achieves This:

```python
class SemanticAnalyzer:
    def analyze(self):
        self.errors = []  # ✅ Empty list ready to collect
        
        # Pass 1: declarations
        self._collect_declarations(self.tree)
        # After pass 1: errors = [<function_redeclaration_errors_if_any>]
        
        # Pass 2: type checking
        self._type_check(self.tree)
        # After pass 2: errors = [<all_declaration_errors> + <all_type_errors>]
        
        # ✅ Return everything found
        return SemanticResult(self.tree, [str(e) for e in self.errors])
    
    def _type_check(self, node):
        """Type checks ONE node, records errors, continues to siblings."""
        
        # Check this node
        if node.kind == "function_call":
            # ... validation logic ...
            if error_found:
                self.errors.append(error)  # ✅ Add to list
                # ✅ DON'T return/raise - keep going!
        
        # ✅ Always check children, even if current node had error
        for child in node.children:
            self._type_check(child)  # Recursive - finds MORE errors
```

---

## Common Mistakes to Avoid

### ❌ **MISTAKE 1: Stopping at First Error**
```python
def _type_check(self, node):
    if symbol is None:
        raise SemanticError("Variable not found")  # ❌ BAD: stops immediately
```

### ✅ **CORRECT: Collect and Continue**
```python
def _type_check(self, node):
    if symbol is None:
        self.errors.append(SemanticError("Variable not found"))  # ✅ GOOD
        return TY_UNKNOWN  # Safe fallback, analysis continues
```

### ❌ **MISTAKE 2: Not Checking Children After Error**
```python
def _type_check(self, node):
    if node.kind == "function_call" and func_not_found:
        self.errors.append(error)
        return  # ❌ BAD: doesn't check arguments for MORE errors
```

### ✅ **CORRECT: Always Traverse Children**
```python
def _type_check(self, node):
    if node.kind == "function_call" and func_not_found:
        self.errors.append(error)
        # ✅ GOOD: Still check arguments to find MORE errors
        for arg in node.children:
            self._type_check(arg)
        return TY_UNKNOWN
```

### ❌ **MISTAKE 3: Returning None on Error**
```python
def _type_check(self, node):
    if error:
        self.errors.append(error)
        return None  # ❌ BAD: causes crashes in parent nodes
```

### ✅ **CORRECT: Return Safe Fallback Type**
```python
def _type_check(self, node):
    if error:
        self.errors.append(error)
        return TY_UNKNOWN  # ✅ GOOD: parent can continue safely
```

---

## Integration with Existing Pipeline

Your current pipeline already handles error collection well in lexer and parser:

```python
# Lexer collects ALL lexical errors
lexer.start()
if lexer.log:
    errors = lexer.log.splitlines()  # Multiple errors

# Parser collects ALL syntax errors
parse_result = parser.parse()
if parse_result.errors:
    errors = parse_result.errors  # Multiple errors

# ✅ Semantic analyzer MUST do the same!
semantic_result = analyzer.analyze()
if semantic_result.errors:
    errors = semantic_result.errors  # Multiple errors
```

---

## Testing Error Collection

Create tests that verify multiple errors are caught:

```python
def test_multiple_errors():
    """Verify analyzer reports ALL errors, not just first."""
    source = """
    x = undefined + 5;
    y = another_undefined * 2;
    z = yet_another + 1;
    """
    
    result = semantic_analyzer.analyze(parse(source), source)
    
    # ✅ Should find ALL 3 undefined variables
    assert len(result.errors) == 3
    assert "undefined" in result.errors[0]
    assert "another_undefined" in result.errors[1]
    assert "yet_another" in result.errors[2]
```

---

Good luck building your semantic analyzer! 🚀

**Remember: The golden rule is "COLLECT ALL ERRORS, NEVER STOP AT THE FIRST"** 🎯
