"""Semantic analysis error definitions."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.constants.ast import ASTNode, ParseResult


class SemanticError:
    """Base semantic error."""
    def __init__(self, message: str, line: int, col: int, source_line: str = ""):
        self.message = message
        self.line = line
        self.col = col
        self.source_line = source_line
    
    def __str__(self):
        if self.source_line:
            caret = ' ' * (self.col - 1) + '^'
            return f"\n{self.line:4} |{self.source_line}\n     |{caret}\n{self.message}"
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


@dataclass
class Symbol:
    """Represents a declared variable or function."""
    name: str
    kind: str           # "variable", "function", "parameter"
    type_: str          # "int_literal", "float_literal", "str_literal", "bool_literal", "array"
    line: int           # Where it was declared
    col: int
    scope_level: int    # 0=global, 1+=nested
    
    # For functions:
    params: Optional[List[Tuple[str, str]]] = None  # [(type, name), ...]
    return_type: Optional[str] = None
    
    # For arrays:
    array_dims: Optional[List[int]] = None  # [size] for 1D, [rows, cols] for 2D


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
        if self.scope_level == 0:
            raise RuntimeError("Cannot exit global scope")

        self.scopes.pop()
        self.scope_level -= 1


    def declare(self, symbol: Symbol) -> bool:
        """
        Declare a symbol in current scope.
        Returns True if successful, False if already declared in this scope.
        """
        # top of stack
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


    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol ONLY in the current (innermost) scope.
        Used to distinguish shadowing from reassignment.
        """
        current_scope = self.scopes[-1]
        return current_scope.get(name, None)



# Type Checker

# Suggested canonical type tags
TY_INT = "int"
TY_FLOAT = "float"
TY_BOOL = "bool"
TY_STRING = "string"
TY_ARRAY = "array"      # if you track arrays
TY_UNKNOWN = "unknown"  # if your analyzer sometimes can't know

NUMERIC_COERCIBLE = {TY_INT, TY_FLOAT, TY_BOOL, TY_STRING}  # all coercible-to-number per your rules
BOOL_COERCIBLE = {TY_BOOL, TY_INT, TY_FLOAT, TY_STRING}  # all coercible-to-bool per your rules

ARITH_OPS = {"+", "-", "*", "/", "%", "//", "**"}
REL_OPS = {"<", ">", "<=", ">=", "==", "!="}
LOGICAL_OPS = {"and", "or"}
UNARY_LOGICAL_OPS = {"!"}


class TypeChecker:
    """
    Implements CHUNGUS coercion + result-type rules.

    This DOES NOT enforce static variable types.
    It only answers:
      - is this operator structurally valid on these operand kinds?
      - what is the resulting type category?
    """

    @staticmethod
    def is_number_coercible(t: str) -> bool:
        # According to your spec: int/float/bool/string -> number
        return t in NUMERIC_COERCIBLE

    @staticmethod
    def is_bool_coercible(t: str) -> bool:
        # According to your spec: bool/int/float/string -> bool
        return t in BOOL_COERCIBLE

    @staticmethod
    def infer_binary_type(op: str, left_type: str, right_type: str) -> Optional[str]:
        """
        Returns the result type tag if the operation is valid under your coercion rules,
        else None (meaning: structurally invalid and should be rejected or runtime-guarded).

        Notes aligned with your rules:
          - Arithmetic: both coerced to number => result int or float
          - Relational: both coerced to number => result bool
          - Logical: both coerced to bool => result bool
        """

        # Arrays (and other non-coercible structural types) should not flow into these domains
        # unless you explicitly define their coercions.
        if op in ARITH_OPS:
            if not (TypeChecker.is_number_coercible(left_type) and TypeChecker.is_number_coercible(right_type)):
                return None

            # Result rule: int vs float.
            # You MUST define "/" and "//" precisely; here's a consistent, simple choice:
            # - "/" always yields float
            # - "//" yields int if both are int-like after coercion, else float (if float involved)
            if op == "/":
                return TY_FLOAT

            # If either operand is float, numeric coercion yields float
            if left_type == TY_FLOAT or right_type == TY_FLOAT:
                return TY_FLOAT

            # Otherwise both are in {int,bool,string} which coerce to integer-valued numbers in your spec
            return TY_INT

        if op in REL_OPS:
            if not (TypeChecker.is_number_coercible(left_type) and TypeChecker.is_number_coercible(right_type)):
                return None

            return TY_BOOL

        if op in LOGICAL_OPS:
            if not (TypeChecker.is_bool_coercible(left_type) and TypeChecker.is_bool_coercible(right_type)):
                return None

            return TY_BOOL

        return None

    @staticmethod
    def infer_unary_type(op: str, operand_type: str) -> Optional[str]:
        """
        Unary operator typing under your rules.
        Currently grammar has NOT operand (i.e., '!').
        """
        if op in UNARY_LOGICAL_OPS:
            if not TypeChecker.is_bool_coercible(operand_type):
                return None
            return TY_BOOL

        return None


class SemanticResult:
    """Result of semantic analysis."""
    def __init__(self, tree: Optional[ASTNode], errors: List[str]):
        self.tree = tree
        self.errors = errors


class SemanticAnalyzer:
    """
    Analyzes an AST for semantic correctness.
    
    Two-pass approach:
    1. First pass: Build symbol table (declarations)
    2. Second pass: Type check (usage)
    """

    def __init__(self, tree: ASTNode, source: str, debug: bool = False):
        self._tree = tree
        self._lines = source.splitlines(keepends=False)  # source code splitted per newline
        self._debug = debug
        self._symbol_table = SymbolTable()
        self._errors: List[SemanticError] = []


    def analyze(self) -> "SemanticResult":
        """Run semantic analysis and return results."""
        if self._tree is None:
            return SemanticResult(tree=None, errors=["No AST to analyze"])
        
        # init error
        self._errors = []

        try:
            # First pass: collect declarations
            self._collect_declarations(self._tree)

            # print table
            self._dbg_symbol_tbl("After _collect_declarations")

            # Second pass: type check
            self._type_check(self._tree)

        except Exception as e:
            # Only catch unexpected crashes (bugs in analyzer itself) not semantic errors (those go in self.errors list)
            import traceback
            self._errors.append(SemanticError(
                f"Internal semantic analyzer error: {str(e)}\\n{traceback.format_exc()}", 0, 0
            ))
        
        # Sort errors by line number for consistent, readable output
        self._errors.sort(key=lambda e: (e.line, e.col))

        return SemanticResult(
            tree=self._tree,
            errors=[str(e) for e in self._errors] # equal to errors.append(str(e))
        )


    def _error(self, node: ASTNode, message: str, error_class=SemanticError):
        """
        Create and record a semantic error with source context.
        
        Args:
            node: AST node where error occurred
            message: Error message describing the issue
            error_class: Specific error class (UndefinedVariableError, TypeMismatchError, etc.)
        
        Note: Errors are collected, not raised, to allow finding ALL errors.
        """
        # Get line and column from node
        line = node.line if node and hasattr(node, 'line') and node.line is not None else 0
        col = node.col if node and hasattr(node, 'col') and node.col is not None else 0

        # Get source line for formatted error
        source_line = self._lines[line - 1] if line and 1 <= line <= len(self._lines) else ""

        # Create error with context
        error = error_class(message, line, col, source_line)
        self._errors.append(error)


    def _dump(self):
        """ Check symbol table """
        for i, scope in enumerate(self._symbol_table.scopes):
            print(f"Scope {i}:")
            for name, sym in scope.items():
                print(f"  {name} -> {sym}")


    def _dbg(self, msg):
        """ Display in debug mode """
        if self._debug:
            print(msg)

    def _dbg_symbol_tbl(self, msg: str = ""):
        """
        Print entire symbol table nicely for debugging.
        Shows full Symbol object representation.
        """
        header = f"╔═══ {msg} ═══" if msg else "╔═══ SYMBOL TABLE ═══"
        self._dbg(f"\n{header}")
        self._dbg("╔═══" + "═" * 80)
        
        for i, scope in enumerate(self._symbol_table.scopes):
            marker = "►" if i == len(self._symbol_table.scopes) - 1 else " "
            self._dbg(f"║ {marker} Scope {i}:")
            if scope:
                for name, sym in scope.items():
                    self._dbg(f"║   {name} -> {sym}")
            else:
                self._dbg("║     (empty)")
        
        self._dbg("╚" + "═" * 80)


    def _evaluate_constant_expr(self, node: ASTNode) -> Optional[float]:
        """
        Evaluate constant expressions at compile-time with CHUNGUS type coercion.
        Returns numeric value if expression is constant, None otherwise.
        
        IMPORTANT: Follows AST structure (left-to-right evaluation in CHUNGUS).
        
        Type coercion ONLY happens in operations, not for standalone literals:
        - TY_INT: integer value
        - TY_FLOAT: float value
        - TY_BOOL: Can't evaluate standalone, only in operations (→ 1/0)
        - TY_STRING: Can't evaluate standalone, only in operations (→ 1/0)
        """
        if node is None:
            return None
        
        # Int/Float literals - these can be evaluated standalone
        if node.kind == "int_literal":
            value_str = node.value
            if value_str.startswith('~'):
                return float(-int(value_str[1:]))
            return float(int(value_str))
        
        elif node.kind == "float_literal":
            value_str = node.value
            if value_str.startswith('~'):
                return -float(value_str[1:])
            return float(value_str)
        
        # Bool/String literals - can't evaluate standalone, only in operations
        elif node.kind == "bool_literal":
            # Standalone bool literal cannot be evaluated as a number
            # Type coercion only happens in operations (e.g., true + 5)
            return None
        
        elif node.kind == "str_literal":
            # Standalone string literal cannot be evaluated as a number
            # Type coercion only happens in operations (e.g., "hello" + 5)
            return None
        
        # Binary arithmetic operations - evaluate based on AST structure
        elif node.kind in {"+", "-", "*", "/", "//", "%", "**"}:
            if len(node.children) < 2:
                return None
            
            # Recursively evaluate children with coercion for operations
            left_val = self._evaluate_with_coercion(node.children[0])
            right_val = self._evaluate_with_coercion(node.children[1])
            
            if left_val is None or right_val is None:
                return None
            
            # Perform operation
            try:
                if node.kind == "+":
                    return left_val + right_val
                elif node.kind == "-":
                    return left_val - right_val
                elif node.kind == "*":
                    return left_val * right_val
                elif node.kind == "/":
                    if right_val == 0:
                        return None  # Division by zero
                    return left_val / right_val
                elif node.kind == "//":
                    if right_val == 0:
                        return None
                    return float(int(left_val) // int(right_val))
                elif node.kind == "%":
                    if right_val == 0:
                        return None
                    return float(int(left_val) % int(right_val))
                elif node.kind == "**":
                    return left_val ** right_val
            except (ValueError, ZeroDivisionError, OverflowError):
                return None
        
        # Type casts
        elif node.kind == "type_cast":
            if not node.children:
                return None
            
            expr_val = self._evaluate_with_coercion(node.children[0])
            if expr_val is None:
                return None
            
            cast_type = node.value
            if cast_type == "int":
                return float(int(expr_val))
            elif cast_type == "float":
                return float(expr_val)
        
        # Non-constant: variables, function calls, etc.
        return None

    def _evaluate_with_coercion(self, node: ASTNode) -> Optional[float]:
        """
        Evaluate expression with type coercion for bool/string in operations.
        This is called when evaluating operands in binary operations.
        """
        if node is None:
            return None
        
        # Try normal evaluation first
        val = self._evaluate_constant_expr(node)
        if val is not None:
            return val
        
        # Apply coercion for bool/string literals when used in operations
        if node.kind == "bool_literal":
            return 1.0 if node.value.lower() == "true" else 0.0
        
        elif node.kind == "str_literal":
            # Remove quotes from string value
            str_val = node.value[1:-1] if len(node.value) >= 2 else node.value
            return 1.0 if len(str_val) > 0 else 0.0
        
        return None

    def _is_valid_array_size_expr(self, node: ASTNode, in_arithmetic: bool = False) -> bool:
        """
        Check if expression is valid for array size (compile-time or runtime).
        
        Valid standalone:
            - Positive int_literal (>= 1)
            - Variables (non-array)
            - Function calls
            - Index access
            - Arithmetic expressions
            
        Valid in arithmetic only (due to type coercion):
            - bool_literal, str_literal
            - Zero or negative int_literal
            
        Never valid:
            - float_literal (even in arithmetic)
            - Relational/logical operations
            - Array variables
        """
        if node is None:
            return False
        
        # NEVER allow float - even in arithmetic
        if node.kind == "float_literal":
            return False
        
        # Bool/string: allow in arithmetic (coercion), reject standalone
        if node.kind in {"bool_literal", "str_literal"}:
            return in_arithmetic
        
        # Int literals: check value
        if node.kind == "int_literal":
            try:
                value_str = node.value
                if value_str.startswith('~'):
                    value = -int(value_str[1:])
                else:
                    value = int(value_str)
                
                if value < 1:
                    return in_arithmetic
            except (ValueError, TypeError):
                return False
            return True
        
        # Reject relational and logical operations
        if node.kind in {"<", ">", "<=", ">=", "==", "!=", "and", "or", "!"}:
            return False
        
        # Arithmetic operations: recursively check with in_arithmetic=True
        if node.kind in {"+", "-", "*", "/", "//", "%", "**"}:
            if len(node.children) >= 2:
                return (self._is_valid_array_size_expr(node.children[0], in_arithmetic=True) and 
                        self._is_valid_array_size_expr(node.children[1], in_arithmetic=True))
            elif len(node.children) == 1:
                return self._is_valid_array_size_expr(node.children[0], in_arithmetic=True)
            return False
        
        # Variables, function calls, index access
        if node.kind == "id":
            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)
            if symbol and symbol.type_ == TY_ARRAY:
                return False
            return True
        
        if node.kind in {"function_call", "index"}:
            return True
        
        # Type casts: treat as arithmetic context
        if node.kind == "type_cast":
            if node.children:
                return self._is_valid_array_size_expr(node.children[0], in_arithmetic=True)
            return False
        
        return False


    def _is_valid_array_index_expr(self, node: ASTNode, in_arithmetic: bool = False) -> bool:
        """
        Check if expression is valid for array indexing.
        
        Valid standalone:
            - Non-negative int_literal (>= 0) - arrays are 0-indexed
            - Arithmetic expressions (with coercible operands)
            - Variables (non-array)
            - Function calls
            - Index access (nested indexing)
            
        Valid in arithmetic expressions only:
            - bool_literal, str_literal (will be coerced to numbers)
            - Negative int_literal (will be used in arithmetic)
            
        Invalid everywhere:
            - float_literal (reject even in expressions)
            - Relational/logical operations (return bool)
            - Array variables
            
        Args:
            node: AST node to validate
            in_arithmetic: True if we're inside an arithmetic expression (allows bool/string/negative)
        """
        if node is None:
            return False
        
        # NEVER allow float literals (even in arithmetic expressions)
        if node.kind == "float_literal":
            return False
        
        # Bool/string literals: allow in arithmetic, reject standalone
        if node.kind in {"bool_literal", "str_literal"}:
            return in_arithmetic
        
        # Int literals: all valid (bounds checking will handle out-of-range/negative)
        if node.kind == "int_literal":
            return True
        
        # Reject relational and logical operations
        if node.kind in {"<", ">", "<=", ">=", "==", "!=", "and", "or", "!"}:
            return False
        
        # Arithmetic operations: recursively check with in_arithmetic=True
        if node.kind in {"+", "-", "*", "/", "//", "%", "**"}:
            if len(node.children) >= 2:
                return (self._is_valid_array_index_expr(node.children[0], in_arithmetic=True) and 
                        self._is_valid_array_index_expr(node.children[1], in_arithmetic=True))
            elif len(node.children) == 1:  # Unary +/-
                return self._is_valid_array_index_expr(node.children[0], in_arithmetic=True)
            return False
        
        # Variables (but not array variables), function calls, index access
        if node.kind == "id":
            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)
            if symbol and symbol.type_ == TY_ARRAY:
                return False  # Arrays can't be used as indices
            return True
        
        if node.kind in {"function_call", "index"}:
            return True
        
        # Type casts
        if node.kind == "type_cast":
            # Type casts count as arithmetic context
            return self._is_valid_array_index_expr(node.children[0], in_arithmetic=True) if node.children else False
        
        # Reject everything else
        return False


    def _extract_array_dims(self, node: ASTNode) -> Optional[tuple]:
        """
        Extract array dimensions from array_1d_init or array_2d_init node.
        Returns tuple of int dimensions if they're constant literals, None otherwise.
        """
        if node.kind == "array_1d_init":
            # 1D array: children=[size, elem1, elem2, ...]
            size_node = node.children[0] if node.children else None
            if size_node and size_node.kind == "size" and size_node.children:
                size_expr = size_node.children[0]
                if size_expr.kind == "int_literal":
                    value_str = size_expr.value
                    if value_str.startswith('~'):
                        size = -int(value_str[1:])
                    else:
                        size = int(value_str)
                    return (size,) if size >= 1 else None
        
        elif node.kind == "array_2d_init":
            # 2D array: children=[rows, cols, row1, row2, ...]
            size_node = node.children[0] if node.children else None
            if size_node and size_node.kind == "size" and len(size_node.children) >= 2:
                row_expr = size_node.children[0]
                col_expr = size_node.children[1]
                
                if row_expr.kind == "int_literal" and col_expr.kind == "int_literal":
                    row_str = row_expr.value
                    col_str = col_expr.value
                    
                    if row_str.startswith('~'):
                        rows = -int(row_str[1:])
                    else:
                        rows = int(row_str)
                    
                    if col_str.startswith('~'):
                        cols = -int(col_str[1:])
                    else:
                        cols = int(col_str)
                    
                    return (rows, cols) if (rows >= 1 and cols >= 1) else None
        
        return None


    def _collect_declarations(self, node: ASTNode) -> None:
        """
        First pass: Collect only GLOBAL declarations (functions).
        Local variables are declared during type checking (pass 2).
        """
        if node is None:
            return

        if node.kind == "program":
            # Program contains function declarations and statements
            for child in node.children:
                self._collect_declarations(child)
            return

        elif node.kind == "function":
            # Declare function in global scope only
            func_name = node.value

            # Check if first child is params node
            params_node = None
            if node.children and node.children[0].kind == "params":
                params_node = node.children[0]
            
            # Extract parameter names and types
            params = []
            if params_node:
                for param_id_node in params_node.children:
                    if param_id_node.kind == "id":
                        param_name = param_id_node.value
                        params.append((param_name, TY_UNKNOWN))

            # Declare function in global scope
            func_symbol = Symbol(
                name=func_name,
                kind="function",
                type_="function",
                line=node.line or 0,
                col=node.col or 0,
                scope_level=self._symbol_table.scope_level,
                params=params,
                return_type="int"  # TODO: extract from AST
            )

            self._symbol_table.declare(func_symbol)
            # Don't enter function scope - local vars declared in pass 2
            return

        # For global-level statements, declare global variables
        # Only declare if we're at global scope (scope_level == 0)
        elif node.kind == "assignment_statement":
            if self._symbol_table.scope_level == 0:
                # Global assignment: declare variable
                var_name = node.value
                if var_name:
                    symbol = Symbol(
                        name=var_name,
                        kind="variable",
                        type_=TY_UNKNOWN,  # Type will be inferred in pass 2
                        line=node.line or 0,
                        col=node.col or 0,
                        scope_level=self._symbol_table.scope_level
                    )
                    self._symbol_table.declare(symbol)
            return
        
        elif node.kind in ["array_1d_init", "array_2d_init"]:
            if self._symbol_table.scope_level == 0:
                # Global array: declare variable with extracted dimensions
                var_name = node.value
                if var_name:
                    array_dims = self._extract_array_dims(node)
                    symbol = Symbol(
                        name=var_name,
                        kind="variable",
                        type_=TY_ARRAY,
                        line=node.line or 0,
                        col=node.col or 0,
                        scope_level=self._symbol_table.scope_level,
                        array_dims=array_dims
                    )
                    self._symbol_table.declare(symbol)
            return
        
        # Don't recurse into control structures (while, if, for, etc.)
        # Those contain local variables which are declared in pass 2
        elif node.kind in ["while", "for", "if", "elif", "else", "conditional_block", 
                          "error_handling", "try", "fail", "always"]:
            return
        
        # Recurse for other node types to find nested functions/declarations
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
        
        if node.kind == "program":
            # Recursively type check all children (functions and statements)
            for child in node.children:
                self._type_check(child)
            return None

        elif node.kind == "function":
            # Enter function scope for type checking the body
            self._symbol_table.enter_scope()

            # Re-declare parameters in function scope (needed for type checking)
            # Check if first child is params node
            start_idx = 0
            if node.children and node.children[0].kind == "params":
                params_node = node.children[0]
                start_idx = 1
                func_symbol = self._symbol_table.lookup(node.value)

                if func_symbol and func_symbol.params:
                    for param_name, param_type in func_symbol.params:
                        param_symbol = Symbol(
                            name=param_name,
                            kind="parameter",
                            type_=param_type,
                            line=0,
                            col=0,
                            scope_level=self._symbol_table.scope_level
                        )
                        self._symbol_table.declare(param_symbol)

            # Type check function body (skip params node if it exists)
            for i in range(start_idx, len(node.children)):
                self._type_check(node.children[i])

            self._symbol_table.exit_scope()
            return None
        
        elif node.kind == "params":
            # Skip params node - parameters are not type checked since it is only id
            return None

        elif node.kind == "for":
            # for loop: value=loop_var, children=[start, end, step, ...body statements]
            loop_var = node.value

            # Enter loop scope
            self._symbol_table.enter_scope()
            
            # Declare loop variable in loop scope
            loop_var_symbol = Symbol(
                name=loop_var,
                kind="variable",
                type_=TY_INT,
                line=node.line or 0,
                col=node.col or 0,
                scope_level=self._symbol_table.scope_level
            )
            self._symbol_table.declare(loop_var_symbol)
            
            # Type check range expressions (first 3 children) - must produce integers
            for i in range(min(3, len(node.children))):
                expr_type = self._type_check(node.children[i])
                
                # Range expressions must produce integers (with type promotion)
                # All types can be promoted to numbers: int, float, bool, string → number
                # But we want to ensure the result is usable as an integer index
                if expr_type and expr_type not in {TY_INT, TY_FLOAT, TY_BOOL, TY_STRING, TY_UNKNOWN}:
                    range_label = ["start", "end", "step"][i] if i < 3 else "range"
                    self._error(node.children[i],
                        f"Range {range_label} must be numeric (integer-promotable), got '{expr_type}'",
                        TypeMismatchError)
            
            # Type check loop body (skip first 3 children)
            for i in range(3, len(node.children)):
                self._type_check(node.children[i])

            self._symbol_table.exit_scope()

            return None
        
        elif node.kind == "while":
            # while loop: children=[condition, ...body statements]
            # Enter loop scope
            self._symbol_table.enter_scope()
            
            # Type check condition (first child)
            if node.children:
                cond_type = self._type_check(node.children[0])
                # Condition should be bool-coercible (already handled by TypeChecker)

            # Type check loop body (skip first child which is condition)
            for i in range(1, len(node.children)):
                self._type_check(node.children[i])

            self._symbol_table.exit_scope()
            return None
        
        elif node.kind == "conditional_block":
            # conditional_block: children=[if_node, ...elif_nodes, else_node]
            # Process each branch
            for child in node.children:
                self._type_check(child)

            return None
        
        elif node.kind in ["if", "elif"]:
            # if/elif: children=[condition, ...body statements]
            # Enter branch scope
            self._symbol_table.enter_scope()
            
            # Type check condition (first child)
            if node.children:
                cond_type = self._type_check(node.children[0])

            # Type check body (skip first child which is condition)
            for i in range(1, len(node.children)):
                self._type_check(node.children[i])
            
            self._symbol_table.exit_scope()
            return None
        
        elif node.kind == "else":
            # else: children=[...body statements]
            # Enter branch scope
            self._symbol_table.enter_scope()
            
            # Type check body
            for child in node.children:
                self._type_check(child)
            
            self._symbol_table.exit_scope()
            return None

        elif node.kind == "error_handling":
            # error_handling: children=[try_node, fail_node, always_node]
            for child in node.children:
                self._type_check(child)
            return None

        elif node.kind in ["try", "fail", "always"]:
            # Enter block scope
            self._symbol_table.enter_scope()

            # Type check block body
            for child in node.children:
                self._type_check(child)

            self._symbol_table.exit_scope()
            return None

        elif node.kind == "index":
            # Array indexing: children=[base, indices_node]
            # base node contains the array identifier
            base_node = None
            indices_node = None

            for child in node.children:
                # name of id
                if child.kind == "base":
                    base_node = child
                # index
                elif child.kind == "indices":
                    indices_node = child

            # Get array name from base
            arr_name = None
            symbol = None

            if base_node and base_node.children and base_node.children[0].kind == "id":
                arr_name = base_node.children[0].value
                symbol = self._symbol_table.lookup(arr_name)

                if symbol is None:
                    self._error(base_node.children[0],
                                f"Variable '{arr_name}' not defined",
                                UndefinedVariableError)
                    # STOP here: don’t type-check base_node.children[0] again
                    return TY_UNKNOWN

                # check if symbol has array_dims attribute from symbol table, if not error
                elif symbol.type_ != TY_ARRAY:
                    self._error(node,
                        f"Cannot index non-array type '{symbol.type_}'",
                        TypeMismatchError)

            # Check dimension count matches
            if symbol and getattr(symbol, "array_dims", None) and indices_node:
                num_indices = len(indices_node.children)
                num_dims = len(symbol.array_dims)
                
                if num_indices != num_dims:
                    dim_str = "1D" if num_dims == 1 else f"{num_dims}D"
                    # Use the first index child for error location (has line/col info)
                    error_node = indices_node.children[0] if indices_node.children else node
                    self._error(error_node,
                        f"Dimension mismatch: {dim_str} array requires {num_dims} indices, got {num_indices}",
                        TypeMismatchError)
                else:
                    # Bounds checking only if dimensions match and indices can be evaluated
                    if symbol and getattr(symbol, "array_dims", None) and indices_node:
                        # Try to evaluate each index using constant folding
                        for i, idx_node in enumerate(indices_node.children):
                            idx_val = self._evaluate_constant_expr(idx_node)
                            
                            if idx_val is not None:
                                # Constant expression - reject non-integers and check bounds
                                if idx_val != int(idx_val):
                                    self._error(idx_node,
                                        "Invalid array index: expression must be 0 or non-negative integer",
                                        TypeMismatchError)
                                else:
                                    idx_int = int(idx_val)
                                    dim_size = symbol.array_dims[i] if i < len(symbol.array_dims) else None
                                    
                                    if dim_size is not None and (idx_int < 0 or idx_int >= dim_size):
                                        dim_label = "index" if len(symbol.array_dims) == 1 else f"dimension {i+1}"
                                        self._error(idx_node,
                                            f"Array index out of bounds: {dim_label} {idx_int} not in range [0, {dim_size-1}]",
                                            TypeMismatchError)

            # Validate and type check indices (skip base, already checked)
            if indices_node:
                for idx_node in indices_node.children:
                    # Validate index expression type
                    if not self._is_valid_array_index_expr(idx_node):
                        self._error(idx_node,
                            f"Invalid array index: expression must be 0 or non-negative integer",
                            TypeMismatchError)
                    # Type check the index expression
                    self._type_check(idx_node)
            
            # Return unknown type for now (would need element type tracking)
            return TY_UNKNOWN

        elif node.kind == "array_idx_assignment":
            # array_idx_assignment: value=arr_name, children=[indices_node, rhs_expr]
            arr_name = node.value
            symbol = self._symbol_table.lookup(arr_name)
            
            if symbol is None:
                self._error(node,
                    f"Array '{arr_name}' not defined",
                    UndefinedVariableError)
                return TY_UNKNOWN
            
            # Check that we're assigning to an array, not a scalar
            if symbol.type_ != TY_ARRAY:
                self._error(node,
                    f"Cannot assign to index of non-array variable '{arr_name}' of type '{symbol.type_}'",
                    TypeMismatchError)
                return TY_UNKNOWN

            # Check dimension count matches
            if symbol.array_dims and node.children and node.children[0].kind == "indices":
                indices_node = node.children[0]
                num_indices = len(indices_node.children)
                num_dims = len(symbol.array_dims)
                
                if num_indices != num_dims:
                    dim_str = "1D" if num_dims == 1 else f"{num_dims}D"
                    # Use the first index child for error location (has line/col info)
                    error_node = indices_node.children[0] if indices_node.children else node
                    self._error(error_node,
                        f"Dimension mismatch: {dim_str} array requires {num_dims} indices, got {num_indices}",
                        TypeMismatchError)
                else:
                    # Validate each index expression type
                    for idx_node in indices_node.children:
                        if not self._is_valid_array_index_expr(idx_node):
                            self._error(idx_node,
                                f"Invalid array index: expression must be 0 or non-negative integer",
                                TypeMismatchError)
                    
                    # Bounds checking only if dimensions match
                    if symbol.array_dims:
                        for i, idx_node in enumerate(indices_node.children):
                            idx_val = self._evaluate_constant_expr(idx_node)
                            
                            if idx_val is not None and i < len(symbol.array_dims):
                                # Reject non-integer results
                                if idx_val != int(idx_val):
                                    self._error(idx_node,
                                        "Invalid array index: expression must be 0 or non-negative integer",
                                        TypeMismatchError)
                                else:
                                    idx_int = int(idx_val)
                                    dim_size = symbol.array_dims[i]
                                    
                                    if dim_size is not None and (idx_int < 0 or idx_int >= dim_size):
                                        dim_label = "index" if len(symbol.array_dims) == 1 else f"dimension {i+1}"
                                        self._error(idx_node,
                                            f"Array index out of bounds: {dim_label} {idx_int} not in range [0, {dim_size-1}]",
                                            TypeMismatchError)
                
                # Type check indices node
                self._type_check(indices_node)
            
            # Type check RHS expression
            if len(node.children) > 1:
                expr_type = self._type_check(node.children[1])
            
            return TY_UNKNOWN
        
        elif node.kind == "indices":
            # indices node: children=[index expressions]
            for child in node.children:
                idx_type = self._type_check(child)
                # TODO: For now, allow all data types in array indices
                # Uncomment below to restrict to int type only:
                # if idx_type and idx_type not in {TY_INT, TY_UNKNOWN}:
                #     self._error(child,
                #         f"Array index must be int, got '{idx_type}'",
                #         TypeMismatchError)
            return None
        
        elif node.kind == "id":
            # Identifier: check if declared
            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)


            if symbol is None:
                # ✅ Record error but DON'T STOP - continue analysis
                self._error(node, f"Variable '{var_name}' not defined", UndefinedVariableError)
                # ✅ Return safe fallback type to allow continued analysis
                return TY_UNKNOWN
            
            # return the type based on type in symbol table
            return symbol.type_

        elif node.kind == "int_literal":
            return TY_INT
        
        elif node.kind == "float_literal":
            return TY_FLOAT
        
        elif node.kind == "str_literal":
            return TY_STRING
        
        elif node.kind == "bool_literal":
            return TY_BOOL
        
        elif node.kind == "read":
            # Read statement - returns unknown type (user input)
            return TY_UNKNOWN
        
        elif node.kind == "type_cast":
            # Type cast: value=cast_type, children=[expr]
            cast_type = node.value  # "int" or "float"
            
            # Type check the expression being cast
            if node.children:
                expr_type = self._type_check(node.children[0])
            
            # Return the target cast type
            return TY_INT if cast_type == "int" else TY_FLOAT
        
        elif node.kind == "return_statement":
            # Return statement: children=[return_expr]
            if node.children:
                return_type = self._type_check(node.children[0])

                # CHUNGUS does not support returning arrays from functions
                if return_type == TY_ARRAY:
                    self._error(node.children[0],
                        f"Cannot return array from function",
                        TypeMismatchError)
            return None
        
        elif node.kind == "output_statement":
            # Output/show statement: children=[expr]
            if node.children:
                self._type_check(node.children[0])
            return None
        
        elif node.kind == "todo":
            # Todo statement - no semantic checking needed
            return None
        
        elif node.kind in ["array_1d_init", "array_2d_init"]:
            # Array initialization with bounds checking
            # Structure: children=[size_node, ...initializer elements/rows]
            
            # Re-declare array variable if not in current scope (handles scope re-entry)
            var_name = node.value
            if var_name:
                symbol = self._symbol_table.lookup(var_name)
                if not symbol:
                    # Declare array variable (locals declared in pass 2)
                    array_dims = self._extract_array_dims(node)
                    symbol = Symbol(
                        name=var_name,
                        kind="variable",
                        type_=TY_ARRAY,
                        line=node.line or 0,
                        col=node.col or 0,
                        scope_level=self._symbol_table.scope_level,
                        array_dims=array_dims
                    )
                    self._symbol_table.declare(symbol)
            
            if node.kind == "array_1d_init":
                # 1D array: children=[size, elem1, elem2, ...]
                size_node = node.children[0] if node.children else None
                
                if size_node and size_node.kind == "size":
                    if size_node.children:
                        size_expr = size_node.children[0]
                        
                        # Try constant folding first
                        const_val = self._evaluate_constant_expr(size_expr)
                        
                        if const_val is not None:
                            # Constant expression - validate value
                            # Reject non-integer results (e.g., 1.5 + 0.5 = 2.0 is ok, but 1.1 + 0.5 = 1.6 is not)
                            if const_val != int(const_val):
                                self._error(size_expr,
                                    "Invalid array size: expression must be a non-negative integer",
                                    TypeMismatchError)
                            else:
                                declared_size = int(const_val)
                                
                                if declared_size < 1:
                                    self._error(size_expr,
                                        "Invalid array size: expression must be a non-negative integer",
                                        TypeMismatchError)
                                else:
                                    # Check element count
                                    actual_size = len(node.children) - 1
                                    
                                    if actual_size > declared_size:
                                        self._error(node,
                                            f"Too many array elements: declared [{declared_size}], got {actual_size} elements",
                                            TypeMismatchError)
                        else:
                            # Runtime expression - just validate structure
                            if not self._is_valid_array_size_expr(size_expr):
                                self._error(size_expr,
                                    "Invalid array size: expression must be a non-negative integer",
                                    TypeMismatchError)

            elif node.kind == "array_2d_init":
                # 2D array: children=[size, row1, row2, ...]
                size_node = node.children[0] if node.children else None
                
                if size_node and size_node.kind == "size":
                    # Get declared dimensions
                    if len(size_node.children) >= 2:
                        row_expr = size_node.children[0]
                        col_expr = size_node.children[1]
                        
                        # Try constant folding
                        row_const = self._evaluate_constant_expr(row_expr)
                        col_const = self._evaluate_constant_expr(col_expr)
                        
                        if row_const is not None and col_const is not None:
                            # Both dimensions are constant - validate values
                            # Reject non-integer results
                            if row_const != int(row_const):
                                self._error(row_expr,
                                    "Invalid array row expression: expression must be a non-negative integer",
                                    TypeMismatchError)
                            if col_const != int(col_const):
                                self._error(col_expr,
                                    "Invalid array column expression: expression must be a non-negative integer",
                                    TypeMismatchError)
                            
                            declared_rows = int(row_const)
                            declared_cols = int(col_const)
                            
                            if declared_rows < 1 and row_const == int(row_const) and row_const == int(row_const):
                                self._error(row_expr,
                                    "Invalid array row expression: expression must be a non-negative integer",
                                    TypeMismatchError)
                            if declared_cols < 1 and col_const == int(col_const):
                                self._error(col_expr,
                                    "Invalid array column expression: expression must be a non-negative integer",
                                    TypeMismatchError)
                            
                            # Check element counts if both dimensions are valid
                            if declared_rows >= 1 and declared_cols >= 1:
                                actual_rows = len(node.children) - 1
                                
                                if actual_rows > declared_rows:
                                    self._error(node,
                                        f"Too many array rows: declared [{declared_rows}][{declared_cols}], got {actual_rows} rows",
                                        TypeMismatchError)
                                
                                # Check each row's column count
                                for i in range(1, len(node.children)):
                                    row = node.children[i]
                                    if row.kind == "array_row":
                                        actual_cols = len(row.children)
                                        if actual_cols > declared_cols:
                                            self._error(row,
                                                f"Too many columns in row {i}: expected {declared_cols} columns, got {actual_cols}",
                                                TypeMismatchError)
                        else:
                            # Runtime expressions - validate structure only
                            if row_const is None and not self._is_valid_array_size_expr(row_expr):
                                self._error(row_expr,
                                    f"Invalid array row expression: must evaluate to a positive integer",
                                    TypeMismatchError)
                            if col_const is None and not self._is_valid_array_size_expr(col_expr):
                                self._error(col_expr,
                                    f"Invalid array column expression: must evaluate to a positive integer",
                                    TypeMismatchError)

            # Type check all initializer expressions
            for child in node.children:
                self._type_check(child)
            return TY_ARRAY
        
        elif node.kind in ["size", "array_row"]:
            # Utility nodes for array initialization
            for child in node.children:
                self._type_check(child)
            return None
        
        elif node.kind == "base":
            # Base node in array indexing: children=[id or expr]
            if node.children:
                return self._type_check(node.children[0])
            return None
        
        elif node.kind == "args":
            # Arguments wrapper node - just recurse
            for child in node.children:
                self._type_check(child)
            return None
        
        elif node.kind == "general_statement":
            # General statement wrapper - just recurse
            for child in node.children:
                self._type_check(child)
            return None
        
        elif node.kind in ["<", ">", "<=", ">=", "==", "!="]:
            # Relational operators
            op = node.kind
            left_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            right_type = self._type_check(node.children[1]) if len(node.children) > 1 else TY_UNKNOWN

            # Skip if either operand is already TY_UNKNOWN
            if left_type == TY_UNKNOWN or right_type == TY_UNKNOWN:
                return TY_UNKNOWN
            
            # Check if operation is valid
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)
                if result_type is None:
                    self._error(node,
                        f"Invalid comparison '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)
                    return TY_UNKNOWN
                return result_type
            return TY_UNKNOWN

        elif node.kind in ["and", "or"]:
            # Logical operators
            op = node.kind
            left_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            right_type = self._type_check(node.children[1]) if len(node.children) > 1 else TY_UNKNOWN
            
            # Skip if either operand is already TY_UNKNOWN
            if left_type == TY_UNKNOWN or right_type == TY_UNKNOWN:
                return TY_UNKNOWN
            
            # Check if operation is valid
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)
                if result_type is None:
                    self._error(node,
                        f"Invalid logical operation '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)
                    return TY_UNKNOWN
                return result_type
            return TY_UNKNOWN

        elif node.kind == "!":
            # Logical NOT (unary)
            operand_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            
            # Skip if operand is already TY_UNKNOWN
            if operand_type == TY_UNKNOWN:
                return TY_UNKNOWN
            
            # Check if operation is valid
            if operand_type:
                result_type = TypeChecker.infer_unary_type("!", operand_type)
                if result_type is None:
                    self._error(node,
                        f"Invalid logical NOT on type '{operand_type}'",
                        TypeMismatchError)
                    return TY_UNKNOWN
                return result_type
            return TY_UNKNOWN
        
        elif node.kind in ["+", "-", "*", "/", "//", "%", "**"]:
            # Binary arithmetic operation
            op = node.kind
            left_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            right_type = self._type_check(node.children[1]) if len(node.children) > 1 else TY_UNKNOWN

            # Check for division by zero (compile-time check for literal zero)
            if op in ["/", "//", "%"] and len(node.children) > 1:
                right_node = node.children[1]
                
                # Check if divisor is a literal zero
                if right_node.kind == "int_literal":
                    value_str = right_node.value
                    # Handle CHUNGUS negative syntax (~0 is still 0)
                    if value_str == "0" or value_str == "~0":
                        op_name = {
                            "/": "Division",
                            "//": "Floor division",
                            "%": "Modulo"
                        }[op]
                        self._error(right_node,
                            f"{op_name} by zero",
                            TypeMismatchError)
                        return TY_UNKNOWN
                
                elif right_node.kind == "float_literal":
                    try:
                        if float(right_node.value) == 0.0:
                            op_name = {
                                "/": "Division",
                                "//": "Floor division",
                                "%": "Modulo"
                            }[op]
                            self._error(right_node,
                                f"{op_name} by zero",
                                TypeMismatchError)
                            return TY_UNKNOWN
                    except ValueError:
                        pass

            # Skip type checking if either operand is already TY_UNKNOWN (error already reported)
            if left_type == TY_UNKNOWN or right_type == TY_UNKNOWN:
                return TY_UNKNOWN
            
            # Check if operation is valid
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)

                if result_type is None:
                    # Only report error if both types are known (not TY_UNKNOWN)
                    self._error(node, 
                        f"Invalid operation '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)
                    return TY_UNKNOWN

                return result_type

            return TY_UNKNOWN

        elif node.kind == "assignment_statement":
            # assignment_statement: id_name = expr
            # Note: Assignment DECLARES the variable, so we don't check if it exists
            # The declaration pass already handled duplicate declarations

            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)
            
            # Type check the RHS expression
            expr_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN

            # Update variable type in symbol table (dynamic typing)
            if symbol:
                symbol.type_ = expr_type
            else:
                # If variable not declared, declare with inferred type
                symbol = Symbol(
                    name=var_name,
                    kind="variable",
                    type_=expr_type,
                    line=node.line or 0,
                    col=node.col or 0,
                    scope_level=self._symbol_table.scope_level
                )
                self._symbol_table.declare(symbol)

            return expr_type
        
        elif node.kind == "function_call":
            # function_call: func_name, children=[args]
            func_name = node.value
            symbol = self._symbol_table.lookup(func_name)

            if symbol is None or symbol.kind != "function":
                self._error(node,
                    f"Function '{func_name}' not defined",
                    FunctionNotDefinedError)
                return TY_UNKNOWN

            # Check argument count

            if node.children and node.children[0].kind == "args":
                args = node.children[0].children
            else:
                args = node.children if node.children else []


            actual_count = len(args)
            expected_count = len(symbol.params) if symbol.params else 0
            
            if actual_count != expected_count:
                self._error(node,
                    f"Function '{func_name}' expects {expected_count} args, got {actual_count}",
                    ArgumentCountMismatchError)

            # Type-check each argument
            for arg in args:
                self._type_check(arg)

            return symbol.return_type if symbol.return_type else TY_UNKNOWN

        # ✅ Recurse to children even if current node had errors
        for child in node.children:
            self._type_check(child)
        
        return None
