"""Semantic analysis error definitions."""

from typing import Dict, List, Optional, Tuple, Any
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
    
    # For constant propagation:
    constant_value: Optional[Any] = None  # Compile-time constant value (bool, int, float, str) - NOT promoted!


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
    def __init__(self, tree: Optional[ASTNode], errors: List[str], symbol_table: Optional[SymbolTable] = None):
        self.tree = tree
        self.errors = errors
        self.symbol_table = symbol_table


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
            errors=[str(e) for e in self._errors], # equal to errors.append(str(e))
            symbol_table=self._symbol_table
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


    def _evaluate_constant_expr(self, node: ASTNode) -> Optional[Any]:
        """
        Evaluate constant expressions at compile-time - returns ORIGINAL values.
        
        Used throughout semantic analysis for:
        - Array size/index bounds checking (compile-time validation)
        - Division by zero detection (catch errors early)
        - General constant folding (optimization)
        - Variable initialization tracking
        
        CRITICAL: Returns actual values (bool, int, str), NOT promoted numbers!
        - TY_BOOL: True or False (Python bool)
        - TY_INT: integer value (Python int)
        - TY_STRING: string value (Python str)
        - TY_FLOAT: float value or None (floats not compile-time constants in array context)
        
        Promotion ONLY happens in _evaluate_with_coercion() during operations!
        """
        if node is None:
            return None
        
        # Clear any existing constant value
        if hasattr(node, 'constant_value'):
            node.constant_value = None

        # Int literals - return actual int
        if node.kind == "int_literal":
            value_str = node.value

            if value_str.startswith('~'):
                val = -int(value_str[1:])
            else:
                val = int(value_str)

            node.constant_value = val  # ← ATTACH HERE!
            return val
        
        # Float literals - not compile-time constants for array sizes
        elif node.kind == "float_literal":
            return None
        
        # Bool literals - return actual bool (NOT 0/1)
        elif node.kind == "bool_literal":
            val = node.value.lower() == "true"
            node.constant_value = val  # ← ATTACH HERE!
            return val
        
        # String literals - return actual string (NOT 0/1)
        elif node.kind == "str_literal":
            val = node.value[1:-1] if len(node.value) >= 2 else node.value
            node.constant_value = val  # ← ATTACH HERE!
            return val

        # Variable lookup - check if it's a compile-time constant
        elif node.kind == "id":
            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)
            if symbol and symbol.constant_value is not None:
                node.constant_value = symbol.constant_value  # ← ATTACH HERE!
                return symbol.constant_value
            node.constant_value = None
            return None

        # Binary arithmetic operations - evaluate based on AST structure
        elif node.kind in {"+", "-", "*", "/", "//", "%", "**"}:
            if len(node.children) < 2:
                return None

            # Recursively evaluate children with coercion for operations
            left_val = self._evaluate_with_coercion(node.children[0])
            right_val = self._evaluate_with_coercion(node.children[1])

            if left_val is None or right_val is None:
                node.constant_value = None
                return None

            # Perform operation - result is numeric
            try:
                if node.kind == "+":
                    result = left_val + right_val
                elif node.kind == "-":
                    result = left_val - right_val
                elif node.kind == "*":
                    result = left_val * right_val
                elif node.kind == "/":
                    if right_val == 0:
                        return None  # Division by zero
                    result = left_val / right_val
                elif node.kind == "//":
                    if right_val == 0:
                        return None
                    result = int(left_val) // int(right_val)
                elif node.kind == "%":
                    if right_val == 0:
                        return None
                    result = int(left_val) % int(right_val)
                elif node.kind == "**":
                    result = left_val ** right_val
                else:
                    node.constant_value = None
                    return None
                
                # Store the result
                node.constant_value = result  # ← ATTACH HERE!

                return result
            except (ValueError, ZeroDivisionError, OverflowError):
                node.constant_value = None
                return None
        
        # Type casts - return int or float
        elif node.kind == "type_cast":
            if not node.children:
                node.constant_value = None
                return None
            
            expr_val = self._evaluate_with_coercion(node.children[0])
            if expr_val is None:
                node.constant_value = None
                return None
            
            cast_type = node.value
            if cast_type == "int":
                return int(expr_val)
            elif cast_type == "float":
                return float(expr_val)
            else:
                node.constant_value = None
                return None

        # Logical operations (and, or, !) - return bool
        elif node.kind in {"and", "or"}:
            left_val = self._evaluate_with_coercion(node.children[0])
            right_val = self._evaluate_with_coercion(node.children[1])

            if left_val is None or right_val is None:
                node.constant_value = None
                return None
            
            # Convert to bool: 0 is false, non-zero is true
            left_bool = bool(left_val) if not isinstance(left_val, str) else len(left_val) > 0
            right_bool = bool(right_val) if not isinstance(right_val, str) else len(right_val) > 0
            
            if node.kind == "and":
                result = left_bool and right_bool
            else:  # "or"
                result = left_bool or right_bool
            
            node.constant_value = result  # ← ATTACH HERE!
            return result
        
        elif node.kind == "!":
            if not node.children:
                node.constant_value = None
                return None
            
            operand_val = self._evaluate_with_coercion(node.children[0])
            if operand_val is None:
                node.constant_value = None
                return None
            
            # Convert to bool and negate
            operand_bool = bool(operand_val) if not isinstance(operand_val, str) else len(operand_val) > 0
            result = not operand_bool
            
            node.constant_value = result  # ← ATTACH HERE!
            return result

        # Relational operations - return bool
        elif node.kind in {"<", ">", "<=", ">=", "==", "!="}:
            if len(node.children) < 2:
                node.constant_value = None
                return None
            
            left_val = self._evaluate_with_coercion(node.children[0])
            right_val = self._evaluate_with_coercion(node.children[1])
            
            if left_val is None or right_val is None:
                node.constant_value = None
                return None
            
            if node.kind == "<":
                result = left_val < right_val
            elif node.kind == ">":
                result = left_val > right_val
            elif node.kind == "<=":
                result = left_val <= right_val
            elif node.kind == ">=":
                result = left_val >= right_val
            elif node.kind == "==":
                result = left_val == right_val
            else:  # "!="
                result = left_val != right_val
            
            node.constant_value = result  # ← ATTACH HERE!
            return result
        
        # Non-constant: function calls, read, etc.
        node.constant_value = None
        return None


    def _evaluate_with_coercion(self, node: ASTNode) -> Optional[float]:
        """
        Evaluate expression and promote to number for arithmetic/relational operations.
        This is where CHUNGUS type coercion happens!

        Used for:
        - Division by zero checking (needs numeric values after promotion)
        - Array index bounds checking (promotes bool/string to numeric)
        - Arithmetic constant folding (all operands promoted to numbers)
        
        Promotion rules:
        - bool: True → 1.0, False → 0.0
        - int: keep as float
        - string: non-empty → 1.0, empty → 0.0
        """
        if node is None:
            return None
        
        # Evaluate to get original value
        # we passed the children at param so we evaluate that first
        # so if this was a tree, that would continue until its the deepest children.
        # if we are at deepest this would just return node value like str, int... currently no float idk why
        val = self._evaluate_constant_expr(node)

        if val is None:
            return None

        # Promote based on type
        if isinstance(val, bool):
            return 1.0 if val else 0.0
        elif isinstance(val, int):
            return float(val)
        elif isinstance(val, float):
            return val
        elif isinstance(val, str):
            return 1.0 if len(val) > 0 else 0.0
        
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


    def _infer_function_return_type(self, func_node: ASTNode) -> str:
        """
        Infer the return type of a function by finding return_statement nodes.
        If no return statement is found, returns "int" (default return value is 0).
        
        Args:
            func_node: The function AST node
            
        Returns:
            The inferred return type as a string ("int", "float", "bool", "string")
        """
        def find_return_stmt(node: ASTNode) -> Optional[ASTNode]:
            """Recursively search for return_statement node."""
            if node is None:
                return None
            if node.kind == "return_statement":
                return node
            for child in node.children:
                result = find_return_stmt(child)
                if result:
                    return result
            return None
        
        return_stmt = find_return_stmt(func_node)
        
        if return_stmt is None:
            # No return statement found - function returns 0 by default
            return TY_INT
        
        # Return statement has one child: the expression being returned
        if return_stmt.children:
            expr_node = return_stmt.children[0]
            # Try to infer the type from the expression
            # For literals, we can determine the type directly
            if expr_node.kind == "int_literal":
                return TY_INT
            elif expr_node.kind == "float_literal":
                return TY_FLOAT
            elif expr_node.kind == "bool_literal":
                return TY_BOOL
            elif expr_node.kind == "str_literal":
                return TY_STRING
            # For more complex expressions, default to int
            # (A more sophisticated analyzer would do full type inference here)
            return TY_INT
        
        # Empty return statement - default to int
        return TY_INT


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

            # Infer return type from function body
            return_type = self._infer_function_return_type(node)

            # Declare function in global scope
            func_symbol = Symbol(
                name=func_name,
                kind="function",
                type_="function",
                line=node.line or 0,
                col=node.col or 0,
                scope_level=self._symbol_table.scope_level,
                params=params,
                return_type=return_type
            )

            self._symbol_table.declare(func_symbol)
            # Don't enter function scope - local vars declared in pass 2
            return

        # DO NOT declare global variables in pass 1
        # Variables (both global and local) are declared during pass 2 (type checking)
        # when assignments are encountered. This ensures proper order checking.
        
        # Don't recurse into control structures (while, if, for, etc.)
        # Those contain local variables which are declared in pass 2
        elif node.kind in ["while", "for", "if", "elif", "else", "conditional_block"]:
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

            # Detect where body starts. Parser wraps statements as
            # `general_statement`, and range() supports 1..3 expressions.
            body_start = len(node.children)
            for i, child in enumerate(node.children):
                if child.kind == "general_statement":
                    body_start = i
                    break

            # Type check range expressions (up to 3) - must produce integers only
            range_count = min(3, body_start)
            for i in range(range_count):
                expr_type = self._type_check(node.children[i])

                # Range expressions MUST produce integers (no floats, bools, or strings)
                # Only TY_INT or TY_UNKNOWN (for variables/expressions) are allowed
                if expr_type and expr_type not in {TY_INT, TY_UNKNOWN}:
                    range_label = ["start", "end", "step"][i]
                    self._error(node.children[i],
                        f"Range {range_label} must be integer type, got '{expr_type}'",
                        TypeMismatchError)

            # Type check loop body
            for i in range(body_start, len(node.children)):
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
                                # Check if it's a string or bool (invalid for array index)
                                if isinstance(idx_val, (str, bool)):
                                    self._error(idx_node,
                                        "Invalid array index: expression must be 0 or non-negative integer",
                                        TypeMismatchError)
                                elif isinstance(idx_val, (int, float)):
                                    # Check if it's a whole number
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
                                # Reject non-integer results (strings, bools, floats that aren't whole numbers)
                                if isinstance(idx_val, (str, bool)):
                                    self._error(idx_node,
                                        "Invalid array index: expression must be 0 or non-negative integer",
                                        TypeMismatchError)
                                elif isinstance(idx_val, (int, float)):
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
                node.inferred_type = TY_UNKNOWN
                return TY_UNKNOWN
            
            # return the type based on type in symbol table
            node.inferred_type = symbol.type_
            return symbol.type_

        elif node.kind == "int_literal":
            node.inferred_type = TY_INT
            return TY_INT
        
        elif node.kind == "float_literal":
            node.inferred_type = TY_FLOAT
            return TY_FLOAT
        
        elif node.kind == "str_literal":
            node.inferred_type = TY_STRING
            return TY_STRING
        
        elif node.kind == "bool_literal":
            node.inferred_type = TY_BOOL
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
            result_type = TY_INT if cast_type == "int" else TY_FLOAT
            node.inferred_type = result_type
            return result_type
        
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
                        
                        # Check if size expression type is valid (must be int or int expression)
                        # Reject bool/string variables or literals (even if they have constant values)
                        size_type = self._type_check(size_expr)

                        # Try constant folding first
                        const_val = self._evaluate_constant_expr(size_expr)

                        if const_val is not None:
                            # Constant expression - validate type and value
                            # Reject if the type is bool or string
                            if size_type in {TY_BOOL, TY_STRING}:
                                self._error(size_expr,
                                    "Invalid array size: expression must be a non-negative integer",
                                    TypeMismatchError)
                            # Reject non-integer results (e.g., 1.5 + 0.5 = 2.0 is ok, but 1.1 + 0.5 = 1.6 is not)
                            elif const_val != int(const_val):
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
                        
                        # Check types
                        row_type = self._type_check(row_expr)
                        col_type = self._type_check(col_expr)
                        
                        # Try constant folding
                        row_const = self._evaluate_constant_expr(row_expr)
                        col_const = self._evaluate_constant_expr(col_expr)
                        
                        if row_const is not None and col_const is not None:
                            # Both dimensions are constant - validate types and values
                            # Reject if the type is bool or string
                            if row_type in {TY_BOOL, TY_STRING}:
                                self._error(row_expr,
                                    "Invalid array row expression: expression must be a non-negative integer",
                                    TypeMismatchError)
                            if col_type in {TY_BOOL, TY_STRING}:
                                self._error(col_expr,
                                    "Invalid array column expression: expression must be a non-negative integer",
                                    TypeMismatchError)
                            
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

            # Type check all initializer expressions (skip size node, already checked above)
            for i, child in enumerate(node.children):
                if i == 0:  # Skip size node (already type-checked above)
                    continue
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
                node.inferred_type = TY_UNKNOWN
                return TY_UNKNOWN
            
            # Check if operation is valid
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)
                if result_type is None:
                    self._error(node,
                        f"Invalid comparison '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)
                    node.inferred_type = TY_UNKNOWN
                    return TY_UNKNOWN
                
                node.inferred_type = result_type
                # Try to evaluate constant - THIS WILL ATTACH TO NODE!
                self._evaluate_constant_expr(node)
                return result_type
            
            node.inferred_type = TY_UNKNOWN
            return TY_UNKNOWN

        elif node.kind in ["and", "or"]:
            # Logical operators
            op = node.kind
            left_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            right_type = self._type_check(node.children[1]) if len(node.children) > 1 else TY_UNKNOWN
            
            # Skip if either operand is already TY_UNKNOWN
            if left_type == TY_UNKNOWN or right_type == TY_UNKNOWN:
                node.inferred_type = TY_UNKNOWN
                return TY_UNKNOWN
            
            # Check if operation is valid
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)
                if result_type is None:
                    self._error(node,
                        f"Invalid logical operation '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)
                    node.inferred_type = TY_UNKNOWN
                    return TY_UNKNOWN
                
                node.inferred_type = result_type
                # Try to evaluate constant - THIS WILL ATTACH TO NODE!
                self._evaluate_constant_expr(node)
                return result_type
            
            node.inferred_type = TY_UNKNOWN
            return TY_UNKNOWN

        elif node.kind == "!":
            # Logical NOT (unary)
            operand_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            
            # Skip if operand is already TY_UNKNOWN
            if operand_type == TY_UNKNOWN:
                node.inferred_type = TY_UNKNOWN
                return TY_UNKNOWN
            
            # Check if operation is valid
            if operand_type:
                result_type = TypeChecker.infer_unary_type("!", operand_type)
                if result_type is None:
                    self._error(node,
                        f"Invalid logical NOT on type '{operand_type}'",
                        TypeMismatchError)
                    node.inferred_type = TY_UNKNOWN
                    return TY_UNKNOWN
                
                node.inferred_type = result_type
                # Try to evaluate constant - THIS WILL ATTACH TO NODE!
                self._evaluate_constant_expr(node)
                return result_type
            
            node.inferred_type = TY_UNKNOWN
            return TY_UNKNOWN
        
        elif node.kind in ["+", "-", "*", "/", "//", "%", "**"]:
            # Binary arithmetic operation
            op = node.kind
            left_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN
            right_type = self._type_check(node.children[1]) if len(node.children) > 1 else TY_UNKNOWN

            # Check for division by zero (compile-time check)
            if op in ["/", "//", "%"] and len(node.children) > 1:
                right_node = node.children[1]
                
                # Try to evaluate the divisor as a constant expression
                divisor_val = self._evaluate_with_coercion(right_node)

                if divisor_val is not None and divisor_val == 0:
                    op_name = {
                        "/": "Division",
                        "//": "Floor division",
                        "%": "Modulo"
                    }[op]
                    self._error(right_node,
                        f"{op_name} by zero",
                        TypeMismatchError)
                    return TY_UNKNOWN

            # Skip type checking if either operand is already TY_UNKNOWN (error already reported)
            if left_type == TY_UNKNOWN or right_type == TY_UNKNOWN:
                node.inferred_type = TY_UNKNOWN
                return TY_UNKNOWN

            # Check if operation is valid
            if left_type and right_type:
                result_type = TypeChecker.infer_binary_type(op, left_type, right_type)

                if result_type is None:
                    # Only report error if both types are known (not TY_UNKNOWN)
                    self._error(node, 
                        f"Invalid operation '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)
                    node.inferred_type = TY_UNKNOWN
                    return TY_UNKNOWN

                node.inferred_type = result_type
                # Try to evaluate constant - THIS WILL ATTACH TO NODE!
                self._evaluate_constant_expr(node)
                return result_type

            node.inferred_type = TY_UNKNOWN
            return TY_UNKNOWN

        elif node.kind == "assignment_statement":
            # assignment_statement: id_name = expr
            # Note: Assignment DECLARES the variable if it doesn't exist

            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)
            
            # Type check the RHS expression
            expr_type = self._type_check(node.children[0]) if node.children else TY_UNKNOWN

            # Try to evaluate as compile-time constant
            const_val = None

            if node.children:
                const_val = self._evaluate_constant_expr(node.children[0])

            # Annotate node for code generation: is this a declaration or reassignment?
            if symbol:
                # Variable exists (in current or outer scope) - this is a reassignment
                node.is_declaration = False
                symbol.type_ = expr_type
                symbol.constant_value = const_val  # Track if it's a constant
            else:
                # Variable not found - this is the first assignment (declaration)
                node.is_declaration = True
                symbol = Symbol(
                    name=var_name,
                    kind="variable",
                    type_=expr_type,
                    line=node.line or 0,
                    col=node.col or 0,
                    scope_level=self._symbol_table.scope_level,
                    constant_value=const_val
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

            # Type-check each argument and prevent array passing
            for arg in args:
                arg_type = self._type_check(arg)
                # Disallow passing whole arrays to functions
                if arg_type == TY_ARRAY:
                    self._error(arg,
                        f"Cannot pass array as function argument (use array elements instead)",
                        TypeMismatchError)

            result_type = symbol.return_type if symbol.return_type else TY_UNKNOWN
            node.inferred_type = result_type
            return result_type

        # ✅ Recurse to children even if current node had errors
        for child in node.children:
            self._type_check(child)
        
        return None
