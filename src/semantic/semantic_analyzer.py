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

class VariableAlreadyDefinedError(SemanticError):
    """Variable redeclared in same scope."""
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

NUMERIC_TYPES = {TY_INT, TY_FLOAT, TY_BOOL, TY_STRING}  # all coercible-to-number per your rules
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
        return t in NUMERIC_TYPES

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
            self._errors.append(SemanticError(
                f"Internal semantic analyzer error: {str(e)}", 0, 0
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
        line = node.line if node and hasattr(node, 'line') else 0
        col = node.col if node and hasattr(node, 'col') else 0

        # Get source line for formatted error
        source_line = self._lines[line - 1] if 1 <= line <= len(self._lines) else ""

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


    def _collect_declarations(self, node: ASTNode) -> None:
        """First pass: traverse AST and collect all declarations."""
        if node is None:
            return

        if node.kind == "program":
            # Program contains function declarations and statements
            for child in node.children:
                self._collect_declarations(child)
            return

        elif node.kind == "function":
            # function node: value="func_name", children=[params, body]
            func_name = node.value

            params_node = node.children[0] if node.children else None

            params = []

            # Extract parameter names from params node
            if params_node and params_node.kind == "params":
                for param_id_node in params_node.children:
                    # Each parameter is an id node with the name as value
                    if param_id_node.kind == "id":
                        param_name = param_id_node.value
                        # For now, all params have unknown type (no type annotations in grammar yet)
                        params.append((TY_UNKNOWN, param_name))
            
            # Declare function
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

            if not self._symbol_table.declare(func_symbol):
                self._error(node,
                    f"Function '{func_name}' already defined",
                    VariableAlreadyDefinedError)

            # Enter function scope and collect local declarations
            self._symbol_table.enter_scope()


            # Declare parameters in function scope
            for param_type, param_name in params:
                param_symbol = Symbol(
                    name=param_name,
                    kind="parameter",
                    type_=param_type,
                    line=0,
                    col=0,
                    scope_level=self._symbol_table.scope_level
                )
                self._symbol_table.declare(param_symbol)
            
            # Collect declarations in function body
            if len(node.children) > 1:
                self._collect_declarations(node.children[1])

            # Debug: print scope before exiting
            self._dbg_symbol_tbl(f"Function '{func_name}' scope before exit")

            self._symbol_table.exit_scope()
            return

        elif node.kind == "for":
            # for loop: value=loop_var, children=[start, end, step, ...body statements]
            loop_var = node.value
            
            # Enter new scope for loop body
            self._symbol_table.enter_scope()
            
            # Declare loop variable in loop scope
            loop_var_symbol = Symbol(
                name=loop_var,
                kind="variable",
                type_=TY_INT,  # for range loops, variable is always int
                line=node.line or 0,
                col=node.col or 0,
                scope_level=self._symbol_table.scope_level
            )
            self._symbol_table.declare(loop_var_symbol)
            
            # Collect declarations in loop body (skip first 3 children which are range expressions)
            for i, child in enumerate(node.children):
                if i >= 3:  # Skip start, end, step indices
                    self._collect_declarations(child)
            
            self._symbol_table.exit_scope()
            return
        
        elif node.kind == "while":
            # while loop: children=[condition, ...body statements]
            # Enter new scope for loop body
            self._symbol_table.enter_scope()
            
            # Collect declarations in loop body (skip first child which is condition)
            for i, child in enumerate(node.children):
                if i >= 1:  # Skip condition
                    self._collect_declarations(child)
            
            self._symbol_table.exit_scope()
            return
        
        elif node.kind in ["conditional_block", "if", "elif", "else"]:
            # Conditional blocks have nested scopes
            # conditional_block: children=[if_node, ...elif_nodes, else_node]
            # if/elif: children=[condition, ...body statements]
            # else: children=[...body statements]
            
            if node.kind == "conditional_block":
                # Process each branch
                for child in node.children:
                    self._collect_declarations(child)
            else:
                # Enter new scope for this branch
                self._symbol_table.enter_scope()
                
                # For if/elif, skip condition (first child)
                start_idx = 1 if node.kind in ["if", "elif"] else 0
                for i, child in enumerate(node.children):
                    if i >= start_idx:
                        self._collect_declarations(child)
                
                self._symbol_table.exit_scope()
            return
        
        elif node.kind == "error_handling":
            # error_handling: children=[try_node, fail_node, always_node]
            # Each block has its own scope
            for child in node.children:
                self._collect_declarations(child)
            return
        
        elif node.kind in ["try", "fail", "always"]:
            # Enter new scope for this error handling block
            self._symbol_table.enter_scope()
            
            # Collect declarations in block body
            for child in node.children:
                self._collect_declarations(child)
            
            self._symbol_table.exit_scope()
            return
        
        elif node.kind in ["array_1d_init", "array_2d_init"]:
            # Array initialization with : syntax (e.g., x: [2] = [1,2])
            # Parser bug: variable name not attached to array_init node
            # Extract variable name from source code using line/col information
            
            if node.line is not None and node.col is not None:
                # Get the line from source code
                if 0 <= node.line - 1 < len(self._lines):
                    line_text = self._lines[node.line - 1]
                    
                    # node.col points to '[', need to find ID before ':'
                    # Search backwards from node.col to find ID token
                    search_text = line_text[:node.col - 1]  # col is 1-based
                    
                    # Simple regex to find last identifier before ':'
                    import re
                    match = re.search(r'(\w+)\s*:\s*$', search_text)
                    
                    if match:
                        var_name = match.group(1)
                        
                        # Extract dimensions
                        array_dims = None
                        size_node = node.children[0] if node.children else None
                        
                        if size_node and size_node.kind == "size":
                            if node.kind == "array_1d_init" and len(size_node.children) >= 1:
                                if size_node.children[0].kind == "int_literal":
                                    dim_val = int(size_node.children[0].value)
                                    if dim_val <= 0:
                                        self._error(size_node.children[0],
                                            f"Array size must be positive, got {dim_val}",
                                            TypeMismatchError)
                                    else:
                                        array_dims = [dim_val]
                            elif node.kind == "array_2d_init" and len(size_node.children) >= 2:
                                if (size_node.children[0].kind == "int_literal" and
                                    size_node.children[1].kind == "int_literal"):
                                    rows = int(size_node.children[0].value)
                                    cols = int(size_node.children[1].value)
                                    if rows <= 0:
                                        self._error(size_node.children[0],
                                            f"Array row count must be positive, got {rows}",
                                            TypeMismatchError)
                                    if cols <= 0:
                                        self._error(size_node.children[1],
                                            f"Array column count must be positive, got {cols}",
                                            TypeMismatchError)
                                    if rows > 0 and cols > 0:
                                        array_dims = [rows, cols]
                        
                        # Declare the array variable
                        if self._symbol_table.lookup_current_scope(var_name) is None:
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
        
        elif node.kind == "array_idx_assignment":
            # array_idx_assignment: value=arr_name, children=[indices_node, rhs_expr]
            arr_name = node.value
            
            # Ensure array variable exists
            if self._symbol_table.lookup_current_scope(arr_name) is None:
                symbol = Symbol(
                    name=arr_name,
                    kind="variable",
                    type_=TY_ARRAY,
                    line=node.line or 0,
                    col=node.col or 0,
                    scope_level=self._symbol_table.scope_level
                )
                self._symbol_table.declare(symbol)
            
            return

        elif node.kind == "assignment_statement":
            # First pass: only ensure the LHS name exists in the CURRENT scope.
            # Do NOT infer RHS, do NOT rebind functions here.
            var_name = node.value

            if self._symbol_table.lookup_current_scope(var_name) is None:
                # Check if RHS is array initialization to get dimensions
                array_dims = None
                if node.children and node.children[0].kind in ["array_1d_init", "array_2d_init"]:
                    array_node = node.children[0]
                    size_node = array_node.children[0] if array_node.children else None
                    
                    if size_node and size_node.kind == "size":
                        if array_node.kind == "array_1d_init" and len(size_node.children) >= 1:
                            if size_node.children[0].kind == "int_literal":
                                array_dims = [int(size_node.children[0].value)]
                        elif array_node.kind == "array_2d_init" and len(size_node.children) >= 2:
                            if (size_node.children[0].kind == "int_literal" and
                                size_node.children[1].kind == "int_literal"):
                                array_dims = [int(size_node.children[0].value), 
                                            int(size_node.children[1].value)]
                
                symbol = Symbol(
                    name=var_name,
                    kind="variable",
                    type_=TY_ARRAY if array_dims else TY_UNKNOWN,
                    line=node.line or 0,
                    col=node.col or 0,
                    scope_level=self._symbol_table.scope_level,
                    array_dims=array_dims
                )
                self._symbol_table.declare(symbol)

            return
        
        # Recurse to children, there would always be a children list
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
            func_symbol = self._symbol_table.lookup(node.value)
            if func_symbol and func_symbol.params:
                for param_type, param_name in func_symbol.params:
                    param_symbol = Symbol(
                        name=param_name,
                        kind="parameter",
                        type_=param_type,
                        line=0,
                        col=0,
                        scope_level=self._symbol_table.scope_level
                    )
                    self._symbol_table.declare(param_symbol)
            
            # Type check function body (skip params node)
            if len(node.children) > 1:
                self._type_check(node.children[1])
            
            self._symbol_table.exit_scope()
            return None
        
        elif node.kind == "params":
            # Skip params node - parameters are not type checked as references
            # They are declarations, already handled in first pass
            return None
        
        elif node.kind == "for":
            # for loop: value=loop_var, children=[start, end, step, ...body statements]
            loop_var = node.value

            # Enter loop scope
            self._symbol_table.enter_scope()
            
            # Re-declare loop variable
            loop_var_symbol = Symbol(
                name=loop_var,
                kind="variable",
                type_=TY_INT,
                line=0,
                col=0,
                scope_level=self._symbol_table.scope_level
            )
            self._symbol_table.declare(loop_var_symbol)
            
            # Type check range expressions (first 3 children)
            for i in range(min(3, len(node.children))):
                expr_type = self._type_check(node.children[i])
                # TODO: For now, allow all data types in loop indices
                # Uncomment below to restrict to numeric types only:
                # if expr_type and expr_type not in {TY_INT, TY_FLOAT, TY_UNKNOWN}:
                #     self._error(node.children[i],
                #         f"Range expression must be numeric, got '{expr_type}'",
                #         TypeMismatchError)
            
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
                if child.kind == "base":
                    base_node = child
                elif child.kind == "indices":
                    indices_node = child
            
            # Get array name from base
            arr_name = None
            if base_node and base_node.children and base_node.children[0].kind == "id":
                arr_name = base_node.children[0].value
                symbol = self._symbol_table.lookup(arr_name)
                
                if symbol and symbol.array_dims and indices_node:
                    # Check bounds if all indices are literals
                    indices_values = []
                    all_literals = True
                    for idx_node in indices_node.children:
                        if idx_node.kind == "int_literal":
                            indices_values.append(int(idx_node.value))
                        else:
                            all_literals = False
                            break
                    
                    if all_literals and len(indices_values) == len(symbol.array_dims):
                        # Check each dimension
                        for i, (idx_val, dim_size) in enumerate(zip(indices_values, symbol.array_dims)):
                            if idx_val < 0 or idx_val >= dim_size:
                                dim_label = "index" if len(symbol.array_dims) == 1 else f"dimension {i+1}"
                                self._error(indices_node.children[i],
                                    f"Array index out of bounds: {dim_label} {idx_val} not in range [0, {dim_size-1}]",
                                    TypeMismatchError)
            
            # Type check all children
            for child in node.children:
                self._type_check(child)
            
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
            
            # Check bounds if array dimensions are known and indices are literals
            if symbol.array_dims and node.children and node.children[0].kind == "indices":
                indices_node = node.children[0]
                
                # Check if all indices are int literals
                indices_values = []
                all_literals = True
                for idx_node in indices_node.children:
                    if idx_node.kind == "int_literal":
                        indices_values.append(int(idx_node.value))
                    else:
                        all_literals = False
                        break
                
                if all_literals and len(indices_values) == len(symbol.array_dims):
                    # Check each dimension
                    for i, (idx_val, dim_size) in enumerate(zip(indices_values, symbol.array_dims)):
                        if idx_val < 0 or idx_val >= dim_size:
                            dim_label = "index" if len(symbol.array_dims) == 1 else f"dimension {i+1}"
                            self._error(indices_node.children[i],
                                f"Array index out of bounds: {dim_label} {idx_val} not in range [0, {dim_size-1}]",
                                TypeMismatchError)
            
            # Type check indices node
            if node.children:
                self._type_check(node.children[0])  # indices node
            
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
                # TODO: Check if return type matches function signature
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
            
            if node.kind == "array_1d_init":
                # 1D array: children=[size, elem1, elem2, ...]
                size_node = node.children[0] if node.children else None
                
                if size_node and size_node.kind == "size":
                    # Get declared size
                    if size_node.children and size_node.children[0].kind == "int_literal":
                        declared_size = int(size_node.children[0].value)
                        
                        # Count actual initializer elements (skip size node)
                        actual_size = len(node.children) - 1
                        
                        if actual_size != declared_size:
                            self._error(node,
                                f"Array size mismatch: declared [{declared_size}], got {actual_size} elements",
                                TypeMismatchError)
            
            elif node.kind == "array_2d_init":
                # 2D array: children=[size, row1, row2, ...]
                size_node = node.children[0] if node.children else None
                
                if size_node and size_node.kind == "size":
                    # Get declared dimensions
                    if len(size_node.children) >= 2:
                        if (size_node.children[0].kind == "int_literal" and 
                            size_node.children[1].kind == "int_literal"):
                            
                            declared_rows = int(size_node.children[0].value)
                            declared_cols = int(size_node.children[1].value)
                            
                            # Count actual rows (skip size node)
                            actual_rows = len(node.children) - 1
                            
                            if actual_rows != declared_rows:
                                self._error(node,
                                    f"Array row count mismatch: declared [{declared_rows}][{declared_cols}], got {actual_rows} rows",
                                    TypeMismatchError)
                            
                            # Check each row's column count
                            for i in range(1, len(node.children)):
                                row = node.children[i]
                                if row.kind == "array_row":
                                    actual_cols = len(row.children)
                                    if actual_cols != declared_cols:
                                        self._error(row,
                                            f"Row {i} column count mismatch: expected {declared_cols} columns, got {actual_cols}",
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
            
            # If variable was declared, we could optionally check type compatibility
            # (but CHUNGUS is dynamically typed, so this might not apply)
            if symbol:
                var_type = symbol.type_
                # For now, skip type checking since variables can change types
            
            return expr_type
        
        elif node.kind == "function_call":
            # function_call: func_name, children=[args]
            func_name = node.value
            symbol = self._symbol_table.lookup(func_name)
            
            if symbol is None or symbol.kind != "function":
                # ✅ Function not found - record error but continue
                self._error(node,
                    f"Function '{func_name}' not defined",
                    FunctionNotDefinedError)
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
                self._error(node,
                    f"Function '{func_name}' expects {expected_count} args, got {actual_count}",
                    ArgumentCountMismatchError)

            # ✅ Type check arguments even if count is wrong
            for i, arg in enumerate(args):
                arg_type = self._type_check(arg)
                if i < expected_count and arg_type and arg_type != TY_UNKNOWN:
                    expected_type = symbol.params[i][0]
                    # Note: TypeChecker.is_compatible doesn't exist yet
                    # if not TypeChecker.is_compatible(arg_type, expected_type):
                    if arg_type != expected_type:
                        # ✅ Record type mismatch for THIS argument
                        self._error(arg,
                            f"Argument {i+1} to '{func_name}': expected '{expected_type}', got '{arg_type}'",
                            TypeMismatchError)
            
            return symbol.return_type if symbol.return_type else TY_UNKNOWN
        
        # ✅ Recurse to children even if current node had errors
        for child in node.children:
            self._type_check(child)
        
        return None
