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
            
            if self._debug:
                self._dump()


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
            # function node: value="func_name", children=[param_list, body]
            func_name = node.value

            param_list = node.children[0] if node.children else None

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
            
            self._symbol_table.exit_scope()
            return

        elif node.kind == "assignment_statement":
            # First pass: only ensure the LHS name exists in the CURRENT scope.
            # Do NOT infer RHS, do NOT rebind functions here.
            var_name = node.value

            if self._symbol_table.lookup_current_scope(var_name) is None:
                symbol = Symbol(
                    name=var_name,
                    kind="variable",
                    type_=TY_UNKNOWN,
                    line=node.line or 0,
                    col=node.col or 0,
                    scope_level=self._symbol_table.scope_level
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
        
        if node.kind == "id":
            # Identifier: check if declared
            var_name = node.value
            symbol = self._symbol_table.lookup(var_name)
            
            if symbol is None:
                # ✅ Record error but DON'T STOP - continue analysis
                self._error(node, f"Variable '{var_name}' not defined", UndefinedVariableError)
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
                    self._error(node, 
                        f"Invalid operation '{op}' between '{left_type}' and '{right_type}'",
                        TypeMismatchError)

                    # ✅ Return safe fallback to continue
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
