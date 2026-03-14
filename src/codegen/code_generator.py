"""
CHUNGUS Code Generator - Converts type-annotated AST to C code.

This module implements the code generation phase of the CHUNGUS compiler.
It receives a fully type-checked and annotated AST from semantic analysis
and generates C code using the CHUNGUS runtime library.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
from src.constants.ast import ASTNode
from src.semantic.semantic_analyzer import SymbolTable


@dataclass
class CodeGenResult:
    """Result of code generation."""
    code: Optional[str]       # Generated code or None if failed
    errors: List[str]          # Error messages
    success: bool              # True if generation succeeded


class CodeGenerator:
    """
    Main code generator class for C code generation.
    
    Consumes a type-annotated AST and produces C code using the CHUNGUS runtime library.
    Uses the visitor pattern to traverse AST nodes and emit code.
    """
    
    def __init__(self, ast: ASTNode, source: str = "", symbol_table: Optional[SymbolTable] = None, debug: bool = False):
        """
        Initialize the code generator.
        
        Args:
            ast: Root AST node (type-annotated by semantic analyzer)
            source: Source code (for error reporting)
            symbol_table: Symbol table from semantic analysis (optional)
            debug: Enable debug output
        """
        self._ast = ast
        self._lines = source.splitlines(keepends=False)  # source code split per newline
        self._symbol_table = symbol_table
        self._debug = debug
        self._errors: List[str] = []
        self._output: List[str] = []  # Generated code lines
        self._indent_level = 0
        self._in_function = False  # Track if we're inside a function
        self._temp_counter = 0  # For generating temporary variables
        self._scope_stack: List[List[str]] = []  # ChValue vars to free per scope

    def generate(self) -> CodeGenResult:
        """
        Generate executable code from the AST.
        
        Returns:
            CodeGenResult with generated code or errors
        """
        if self._debug:
            print("=== CODE GENERATION STARTED ===")
            print(f"AST Root: {self._ast.kind}")

        try:
            # Visit root node
            self._visit(self._ast)

            if self._errors:
                return CodeGenResult(
                    code=None,
                    errors=self._errors,
                    success=False
                )
            
            # Join generated code lines
            generated_code = "\n".join(self._output)
            
            if self._debug:
                print("=== CODE GENERATION COMPLETE ===")
                print(generated_code)
            
            return CodeGenResult(
                code=generated_code,
                errors=[],
                success=True
            )
            
        except Exception as e:
            error_msg = f"Code generation failed: {str(e)}"
            self._errors.append(error_msg)
            return CodeGenResult(
                code=None,
                errors=self._errors,
                success=False
            )

    def _visit(self, node: Optional[ASTNode]) -> Optional[str]:
        """
        Visit an AST node and generate code.
        
        Returns the generated expression code for expression nodes,
        or None for statement nodes (which emit code directly).
        
        Uses dynamic dispatch to call appropriate visitor method.
        """
        if node is None:
            return None

        # Map operator symbols to method names
        operator_map = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "div",
            "//": "idiv",
            "%": "mod",
            "**": "pow",
            "<": "less",
            ">": "greater",
            "<=": "le",
            ">=": "ge",
            "==": "eq",
            "!=": "ne",
            "and": "and",
            "or": "or",
            "!": "not"
        }

        # Get method name, mapping operators
        if node.kind in operator_map:
            method_name = f"_visit_{operator_map[node.kind]}"
        else:
            method_name = f"_visit_{node.kind}"
        
        visitor = getattr(self, method_name, self._visit_default)
        return visitor(node)

    def _visit_default(self, node: ASTNode) -> None:
        """
        Default visitor for nodes without specific handlers.
        Recursively visits children.
        """
        if self._debug:
            print(f"Visiting (default): {node.kind}")
        
        for child in node.children:
            self._visit(child)
        return None
    
    def _visit_program(self, node: ASTNode) -> None:
        """Visit program root node - generates complete C program."""
        if self._debug:
            print("Visiting: program")
        
        # Emit C program header
        self._emit("// Generated by CHUNGUS Compiler")
        self._emit("#include \"chungus_runtime.h\"")
        self._emit("#include <stdio.h>")
        self._emit("#include <stdlib.h>")
        self._emit("")

        # Separate functions from main statements
        functions = [child for child in node.children if child.kind == "function"]
        main_stmts = [child for child in node.children if child.kind != "function"]

        # Generate forward declarations for functions
        for func in functions:
            self._emit(f"{self._build_function_signature(func)};  // Forward declaration")

        if functions:
            self._emit("")
        
        # Generate function definitions
        for func in functions:
            self._visit(func)
            self._emit("")
        
        # Generate main function
        self._emit("int main() {")
        self._indent()
        self._enter_scope()
        
        # Visit main statements
        for stmt in main_stmts:
            self._visit(stmt)

        self._exit_scope()
        
        self._emit("return 0;")
        self._dedent()
        self._emit("}")
        
        return None

    def _extract_function_params(self, fn_node: ASTNode) -> List[str]:
        """Extract parameter names from a function AST node."""
        if not fn_node.children:
            return []

        first = fn_node.children[0]
        if first.kind != "params":
            return []

        params: List[str] = []
        for child in first.children:
            if child.kind == "id" and child.value:
                params.append(child.value)
        return params

    def _build_function_signature(self, fn_node: ASTNode) -> str:
        """Build a C function signature for a CHUNGUS function node."""
        fn_name = fn_node.value or "_anonymous_fn"
        param_names = self._extract_function_params(fn_node)

        if param_names:
            param_sig = ", ".join([f"ChValue {p}" for p in param_names])
        else:
            param_sig = "void"

        return f"ChValue {fn_name}({param_sig})"
    
    def _emit(self, code: str = "") -> None:
        """
        Emit a line of code with proper indentation.
        
        Args:
            code: Code line to emit (without indentation)
        """
        if code:
            indent = "    " * self._indent_level
            self._output.append(indent + code)
        else:
            self._output.append("")

    def _enter_scope(self) -> None:
        """Enter codegen scope for automatic ChValue cleanup."""
        self._scope_stack.append([])

    def _declare_scoped_var(self, var_name: str) -> None:
        """Register variable name to be freed when current scope exits."""
        if not self._scope_stack:
            return
        if var_name not in self._scope_stack[-1]:
            self._scope_stack[-1].append(var_name)

    def _exit_scope(self) -> None:
        """Emit cleanup for current scope and pop it."""
        if not self._scope_stack:
            return
        names = self._scope_stack.pop()
        for name in reversed(names):
            self._emit(f"ch_free(&{name});")
    
    def _indent(self) -> None:
        """Increase indentation level."""
        self._indent_level += 1
    
    def _dedent(self) -> None:
        """Decrease indentation level."""
        if self._indent_level > 0:
            self._indent_level -= 1
    
    def _error(self, message: str, node: Optional[ASTNode] = None) -> None:
        """
        Record a code generation error.
        
        Args:
            message: Error message
            node: AST node where error occurred (for location info)
        """
        if node and node.line is not None:
            error = f"Line {node.line}: {message}"
        else:
            error = message
        
        self._errors.append(error)
        
        if self._debug:
            print(f"ERROR: {error}")

    def _gen_temp(self) -> str:
        """Generate a unique temporary variable name."""
        temp = f"_t{self._temp_counter}"
        self._temp_counter += 1
        return temp
    
    # ==================== LITERAL VISITORS ====================
    
    def _visit_int_literal(self, node: ASTNode) -> str:
        """Generate code for integer literal."""
        value = node.value
        # Handle CHUNGUS negative syntax: ~5 means -5
        if value.startswith('~'):
            value = '-' + value[1:]
        return f"ch_int({value})"
    
    def _visit_float_literal(self, node: ASTNode) -> str:
        """Generate code for float literal."""
        value = node.value
        # Handle CHUNGUS negative syntax: ~3.14 means -3.14
        if value.startswith('~'):
            value = '-' + value[1:]
        return f"ch_float({value})"
    
    def _visit_bool_literal(self, node: ASTNode) -> str:
        """Generate code for boolean literal."""
        # Accept both lowercase (true/false) and uppercase (TRUE/FALSE)
        # to match lexer/parser outputs and avoid silently flipping to false.
        lexeme = (node.value or "").strip().lower()
        c_bool = "true" if lexeme == "true" else "false"
        return f"ch_bool({c_bool})"
    
    def _visit_str_literal(self, node: ASTNode) -> str:
        """Generate code for string literal."""
        # CHUNGUS uses 'string' but C needs "string"
        # Remove the CHUNGUS quotes and add C quotes
        chungus_str = node.value
        if chungus_str.startswith("'") and chungus_str.endswith("'"):
            # Remove single quotes and add double quotes for C
            c_str = chungus_str[1:-1]  # Remove surrounding quotes
            # Escape any double quotes in the string
            c_str = c_str.replace('"', '\\"')
            return f'ch_str("{c_str}")'
        return f"ch_str({chungus_str})"
    
    def _visit_id(self, node: ASTNode) -> str:
        """Generate code for identifier."""
        return node.value
    
    def _visit_read(self, node: ASTNode) -> str:
        """Generate code for read statement."""
        return "ch_read()"

    def _visit_type_cast(self, node: ASTNode) -> str:
        """Generate code for CHUNGUS type casts: int(expr) / float(expr)."""
        cast_type = (node.value or "").strip()
        expr_code = self._visit(node.children[0]) if node.children else "ch_int(0)"

        if cast_type == "int":
            return f"ch_int((int64_t)ch_to_number({expr_code}))"

        # default to float cast behavior for `float(...)` and unknown cast tags
        return f"ch_float(ch_to_number({expr_code}))"
    
    # ==================== ASSIGNMENT VISITORS ====================
    
    def _visit_assignment_statement(self, node: ASTNode) -> None:
        """Generate code for assignment statement."""
        var_name = node.value
        rhs_node = node.children[0] if node.children else None
        rhs_code = self._visit(node.children[0]) if node.children else "ch_int(0)"
        
        # Check if this is a declaration or reassignment
        if hasattr(node, 'is_declaration') and node.is_declaration:
            # First assignment - declare variable
            if rhs_node and rhs_node.kind == "id":
                self._emit(f"ChValue {var_name} = ch_copy({rhs_code});")
            else:
                self._emit(f"ChValue {var_name} = {rhs_code};")
            self._declare_scoped_var(var_name)
        else:
            # Reassignment: evaluate RHS first, then replace old value.
            rhs_tmp = self._gen_temp() + "_rhs"
            if rhs_node and rhs_node.kind == "id":
                self._emit(f"ChValue {rhs_tmp} = ch_copy({rhs_code});")
            else:
                self._emit(f"ChValue {rhs_tmp} = {rhs_code};")
            self._emit(f"ch_free(&{var_name});")
            self._emit(f"{var_name} = {rhs_tmp};")

    # ==================== FUNCTION VISITORS ====================

    def _visit_function(self, node: ASTNode) -> None:
        """Generate code for a function definition."""
        signature = self._build_function_signature(node)

        self._emit(f"{signature} {{")
        self._indent()
        self._enter_scope()

        self._in_function = True

        start_idx = 0
        if node.children and node.children[0].kind == "params":
            start_idx = 1

            # Copy parameters into function-owned values.
            for param_name in self._extract_function_params(node):
                self._emit(f"{param_name} = ch_copy({param_name});")
                self._declare_scoped_var(param_name)

        ret_node: Optional[ASTNode] = None
        if node.children and node.children[-1].kind == "return_statement":
            ret_node = node.children[-1]
            body_end = len(node.children) - 1
        else:
            body_end = len(node.children)

        # Emit body statements (wrapped as general_statement nodes)
        for i in range(start_idx, body_end):
            self._visit(node.children[i])

        # Optional trailing return statement by grammar
        if ret_node and ret_node.children:
            ret_expr_node = ret_node.children[0]
            ret_expr = self._visit(ret_expr_node)
            ret_tmp = self._gen_temp() + "_ret"

            # Ownership safety for dynamic values:
            # - Returning a plain identifier would otherwise pass through the
            #   same underlying pointer (for string/array), so a caller-side
            #   free could destroy the original binding.
            # - For identifier returns, return a deep copy so caller owns it.
            if ret_expr_node.kind == "id":
                self._emit(f"ChValue {ret_tmp} = ch_copy({ret_expr});")
            else:
                self._emit(f"ChValue {ret_tmp} = {ret_expr};")

            self._exit_scope()
            self._emit(f"return {ret_tmp};")
        else:
            # Dynamic default return when function has no explicit ret
            self._exit_scope()
            self._emit("return ch_int(0);")

        self._in_function = False

        self._dedent()
        self._emit("}")

    def _visit_function_call(self, node: ASTNode) -> str:
        """Generate code for function call expression."""
        func_name = node.value or "_unknown_fn"

        # Two parser shapes are supported:
        # 1) function_call(children=[args...])
        # 2) function_call(children=[ASTNode('args', children=[...])])
        if len(node.children) == 1 and node.children[0].kind == "args":
            args = node.children[0].children
        else:
            args = node.children

        arg_codes = [self._visit(arg) for arg in args]
        return f"{func_name}({', '.join(arg_codes)})"

    def _visit_general_statement(self, node: ASTNode) -> None:
        """Generate code for top-level/local general statement wrapper."""
        if not node.children:
            return

        stmt = node.children[0]

        # Function calls used as statements must still execute.
        # Capture return into a temp and free it to avoid leaks for strings/arrays.
        if stmt.kind == "function_call":
            call_code = self._visit(stmt)
            temp = self._gen_temp()
            self._emit(f"ChValue {temp} = {call_code};")
            self._emit(f"ch_free(&{temp});")
            return

        self._visit(stmt)

    # ==================== ARRAY VISITORS ====================

    def _visit_array_1d_init(self, node: ASTNode) -> None:
        """Generate code for 1D array initialization.

        AST shape:
          array_1d_init(value=arr_name, children=[size_node, elem1, elem2, ...])
        """
        arr_name = node.value
        if not arr_name or not node.children:
            return

        size_node = node.children[0]
        size_expr = size_node.children[0] if (size_node.kind == "size" and size_node.children) else None
        if size_expr is None:
            # fallback safety: create size 0 if malformed AST
            size_code = "ch_int(0)"
        else:
            size_code = self._visit(size_expr)

        size_tmp = self._gen_temp() + "_size"
        self._emit(f"ChValue {size_tmp} = {size_code};")
        self._emit(f"ChValue {arr_name} = ch_array_1d(ch_to_array_size_checked({size_tmp}, \"array size\"));")
        self._emit(f"ch_free(&{size_tmp});")
        self._declare_scoped_var(arr_name)

        # Initialize provided elements; missing ones remain 0 by runtime constructor.
        for i, elem_node in enumerate(node.children[1:]):
            elem_code = self._visit(elem_node)
            elem_tmp = self._gen_temp() + "_elem"

            if elem_node.kind == "id":
                self._emit(f"ChValue {elem_tmp} = ch_copy({elem_code});")
            else:
                self._emit(f"ChValue {elem_tmp} = {elem_code};")

            self._emit(f"ch_array_set_1d(&{arr_name}, {i}, {elem_tmp});")
            self._emit(f"ch_free(&{elem_tmp});")

    def _visit_array_2d_init(self, node: ASTNode) -> None:
        """Generate code for 2D array initialization.

        AST shape:
          array_2d_init(value=arr_name, children=[size_node, array_row, array_row, ...])
        """
        arr_name = node.value
        if not arr_name or not node.children:
            return

        size_node = node.children[0]
        row_expr = None
        col_expr = None
        if size_node.kind == "size" and len(size_node.children) >= 2:
            row_expr = size_node.children[0]
            col_expr = size_node.children[1]

        row_code = self._visit(row_expr) if row_expr else "ch_int(0)"
        col_code = self._visit(col_expr) if col_expr else "ch_int(0)"

        row_tmp = self._gen_temp() + "_rows"
        col_tmp = self._gen_temp() + "_cols"

        self._emit(f"ChValue {row_tmp} = {row_code};")
        self._emit(f"ChValue {col_tmp} = {col_code};")
        self._emit(
            f"ChValue {arr_name} = ch_array_2d(" 
            f"ch_to_array_size_checked({row_tmp}, \"array row size\"), "
            f"ch_to_array_size_checked({col_tmp}, \"array column size\"));"
        )
        self._emit(f"ch_free(&{row_tmp});")
        self._emit(f"ch_free(&{col_tmp});")
        self._declare_scoped_var(arr_name)

        # Initialize provided rows/cols; missing cells remain 0 by constructor.
        for r, row_node in enumerate(node.children[1:]):
            if row_node.kind != "array_row":
                continue
            for c, elem_node in enumerate(row_node.children):
                elem_code = self._visit(elem_node)
                elem_tmp = self._gen_temp() + "_elem"

                if elem_node.kind == "id":
                    self._emit(f"ChValue {elem_tmp} = ch_copy({elem_code});")
                else:
                    self._emit(f"ChValue {elem_tmp} = {elem_code};")

                self._emit(f"ch_array_set_2d(&{arr_name}, {r}, {c}, {elem_tmp});")
                self._emit(f"ch_free(&{elem_tmp});")

    def _visit_index(self, node: ASTNode) -> str:
        """Generate code for array indexing expression."""
        base_node = None
        indices_node = None

        for child in node.children:
            if child.kind == "base":
                base_node = child
            elif child.kind == "indices":
                indices_node = child

        if not base_node or not base_node.children:
            return "ch_int(0)"

        base_code = self._visit(base_node.children[0])
        index_codes = [self._visit(idx) for idx in (indices_node.children if indices_node else [])]

        if len(index_codes) == 1:
            return f"ch_array_get_1d({base_code}, ch_to_index_checked({index_codes[0]}, \"array index\"))"
        if len(index_codes) == 2:
            return (
                f"ch_array_get_2d({base_code}, "
                f"ch_to_index_checked({index_codes[0]}, \"array row index\"), "
                f"ch_to_index_checked({index_codes[1]}, \"array column index\"))"
            )

        return "ch_int(0)"

    def _visit_array_idx_assignment(self, node: ASTNode) -> None:
        """Generate code for indexed array assignment.

        AST shape:
          array_idx_assignment(value=arr_name, children=[indices_node, rhs_expr])
        """
        arr_name = node.value
        if not arr_name or len(node.children) < 2:
            return

        indices_node = node.children[0]
        rhs_node = node.children[1]
        rhs_code = self._visit(rhs_node)

        idx_codes = [self._visit(idx) for idx in (indices_node.children if indices_node.kind == "indices" else [])]

        rhs_tmp = self._gen_temp() + "_rhs"
        if rhs_node.kind == "id":
            self._emit(f"ChValue {rhs_tmp} = ch_copy({rhs_code});")
        else:
            self._emit(f"ChValue {rhs_tmp} = {rhs_code};")

        if len(idx_codes) == 1:
            self._emit(
                f"ch_array_set_1d(&{arr_name}, ch_to_index_checked({idx_codes[0]}, \"array index\"), {rhs_tmp});"
            )
        elif len(idx_codes) == 2:
            self._emit(
                f"ch_array_set_2d(&{arr_name}, "
                f"ch_to_index_checked({idx_codes[0]}, \"array row index\"), "
                f"ch_to_index_checked({idx_codes[1]}, \"array column index\"), {rhs_tmp});"
            )
        else:
            # malformed/unsupported dimensions; keep behavior safe
            self._emit(f"/* Runtime Warning: invalid index dimension for array '{arr_name}' */")

        self._emit(f"ch_free(&{rhs_tmp});")
    
    # ==================== EXPRESSION VISITORS ====================
    
    def _visit_binary_op(self, node: ASTNode, op: str, func: str) -> str:
        """Helper for binary operations."""
        left_code = self._visit(node.children[0]) if node.children else "ch_int(0)"
        right_code = self._visit(node.children[1]) if len(node.children) > 1 else "ch_int(0)"

        # it would be something like ch_add(_ , _)
        return f"{func}({left_code}, {right_code})"
    
    # Arithmetic operators
    def _visit_add(self, node: ASTNode) -> str:
        """Generate code for addition (+)."""
        return self._visit_binary_op(node, "+", "ch_add")
    
    def _visit_sub(self, node: ASTNode) -> str:
        """Generate code for subtraction (-)."""
        return self._visit_binary_op(node, "-", "ch_sub")
    
    def _visit_mul(self, node: ASTNode) -> str:
        """Generate code for multiplication (*)."""
        return self._visit_binary_op(node, "*", "ch_mul")
    
    def _visit_div(self, node: ASTNode) -> str:
        """Generate code for division (/)."""
        return self._visit_binary_op(node, "/", "ch_div")
    
    def _visit_idiv(self, node: ASTNode) -> str:
        """Generate code for integer division (//)."""
        return self._visit_binary_op(node, "//", "ch_idiv")
    
    def _visit_mod(self, node: ASTNode) -> str:
        """Generate code for modulo (%)."""
        return self._visit_binary_op(node, "%", "ch_mod")
    
    def _visit_pow(self, node: ASTNode) -> str:
        """Generate code for power (^)."""
        return self._visit_binary_op(node, "^", "ch_pow")
    
    # Comparison operators
    def _visit_less(self, node: ASTNode) -> str:
        """Generate code for less than (<)."""
        return self._visit_binary_op(node, "<", "ch_less")
    
    def _visit_greater(self, node: ASTNode) -> str:
        """Generate code for greater than (>)."""
        return self._visit_binary_op(node, ">", "ch_greater")
    
    def _visit_le(self, node: ASTNode) -> str:
        """Generate code for less than or equal (<=)."""
        return self._visit_binary_op(node, "<=", "ch_le")
    
    def _visit_ge(self, node: ASTNode) -> str:
        """Generate code for greater than or equal (>=)."""
        return self._visit_binary_op(node, ">=", "ch_ge")
    
    def _visit_eq(self, node: ASTNode) -> str:
        """Generate code for equality (==)."""
        return self._visit_binary_op(node, "==", "ch_eq")
    
    def _visit_ne(self, node: ASTNode) -> str:
        """Generate code for inequality (!=)."""
        return self._visit_binary_op(node, "!=", "ch_ne")
    
    # Logical operators
    def _visit_and(self, node: ASTNode) -> str:
        """Generate code for logical AND (&)."""
        return self._visit_binary_op(node, "&", "ch_and")
    
    def _visit_or(self, node: ASTNode) -> str:
        """Generate code for logical OR (|)."""
        return self._visit_binary_op(node, "|", "ch_or")
    
    def _visit_not(self, node: ASTNode) -> str:
        """Generate code for logical NOT (!)."""
        operand_code = self._visit(node.children[0]) if node.children else "ch_bool(false)"
        return f"ch_not({operand_code})"
    
    # ==================== OUTPUT VISITOR ====================

    def _visit_output_statement(self, node: ASTNode) -> None:
        """Generate code for output/show statement."""
        if not node.children:
            self._emit("ch_print(ch_int(0));")
            return

        child = node.children[0]
        expr_code = self._visit(child)

        # If the expression is a plain variable reference (id), print it
        # directly — we must NOT free it because the variable still owns
        # that memory and may be used later.
        #
        # For everything else (literals, function calls, binary ops, etc.)
        # the result is a temporary ChValue.  String temporaries hold a
        # strdup-allocated pointer that would leak without an explicit free.
        # ch_free is safe for all types (no-op for int/float/bool).
        if child.kind == "id":
            self._emit(f"ch_print({expr_code});")
        else:
            temp = self._gen_temp()
            self._emit(f"ChValue {temp} = {expr_code};")
            self._emit(f"ch_print({temp});")
            self._emit(f"ch_free(&{temp});")

    # ==================== CONTROL FLOW VISITORS ====================
    
    def _visit_conditional_block(self, node: ASTNode) -> None:
        """Generate code for if/elif/else block."""
        for child in node.children:
            self._visit(child)

    def _visit_if(self, node: ASTNode) -> None:
        """Generate code for if statement."""
        # children = [condition, ...body_statements]
        cond_code = self._visit(node.children[0]) if node.children else "ch_bool(false)"
        
        self._emit(f"if (ch_to_bool({cond_code})) {{")
        self._indent()
        self._enter_scope()
        
        # Visit body statements
        for stmt in node.children[1:]:
            self._visit(stmt)

        self._exit_scope()
        
        self._dedent()
        self._emit("}")
    
    def _visit_elif(self, node: ASTNode) -> None:
        """Generate code for elif statement."""
        # children = [condition, ...body_statements]
        cond_code = self._visit(node.children[0]) if node.children else "ch_bool(false)"
        
        self._emit(f"else if (ch_to_bool({cond_code})) {{")
        self._indent()
        self._enter_scope()
        
        # Visit body statements
        for stmt in node.children[1:]:
            self._visit(stmt)

        self._exit_scope()
        
        self._dedent()
        self._emit("}")
    
    def _visit_else(self, node: ASTNode) -> None:
        """Generate code for else statement."""
        self._emit("else {")
        self._indent()
        self._enter_scope()
        
        # Visit body statements
        for stmt in node.children:
            self._visit(stmt)

        self._exit_scope()
        
        self._dedent()
        self._emit("}")

    def _visit_for(self, node: ASTNode) -> None:
        """Generate code for for loop.

        AST contract from parser:
            node.value = loop variable name
            node.children = [range_expr_1..3, general_statement...]

        Supported forms:
            range(stop)
            range(start, stop)
            range(start, stop, step)
        """
        loop_var = node.value or "_i"

        # Body statements are wrapped as `general_statement` nodes. while range expr are not.
        body_start = len(node.children)
        for i, child in enumerate(node.children):
            if child.kind == "general_statement":
                body_start = i
                break

        range_nodes = node.children[:body_start]
        body_nodes = node.children[body_start:]

        # Parse range args with Python-like defaults.
        # range(stop) -> start=0, step=1
        # range(start, stop) -> step=1
        # range(start, stop, step)
        if len(range_nodes) == 1:
            start_expr = "ch_int(0)"
            stop_expr = self._visit(range_nodes[0])
            step_expr = "ch_int(1)"
        elif len(range_nodes) == 2:
            start_expr = self._visit(range_nodes[0])
            stop_expr = self._visit(range_nodes[1])
            step_expr = "ch_int(1)"
        else:
            start_expr = self._visit(range_nodes[0]) if len(range_nodes) > 0 else "ch_int(0)"
            stop_expr = self._visit(range_nodes[1]) if len(range_nodes) > 1 else "ch_int(0)"
            step_expr = self._visit(range_nodes[2]) if len(range_nodes) > 2 else "ch_int(1)"

        # Use unique temporaries so nested loops are safe.
        t_start = self._gen_temp() + "_start"
        t_stop = self._gen_temp() + "_stop"
        t_step = self._gen_temp() + "_step"

        self._emit("{")
        self._indent()
        self._enter_scope()
        # initialize range expr vars
        self._emit(f"int {t_start} = (int)ch_to_number({start_expr});")
        self._emit(f"int {t_stop} = (int)ch_to_number({stop_expr});")
        self._emit(f"int {t_step} = (int)ch_to_number({step_expr});")
        self._emit("")
        # handle 0 step
        self._emit(f"if ({t_step} == 0) {{")
        self._indent()
        self._emit('fprintf(stderr, "Runtime Error: range() step cannot be zero\\n");')
        self._dedent()
        self._emit("} else {")
        self._indent()
        # initialize loop variable
        self._emit(f"ChValue {loop_var} = ch_int({t_start});")
        self._declare_scoped_var(loop_var)

        # step > 0 → continue while loop_var < stop
        # step < 0 → continue while loop_var > stop
        self._emit(
            f"while (({t_step} > 0) ? ((int)ch_to_number({loop_var}) < {t_stop}) : ((int)ch_to_number({loop_var}) > {t_stop})) {{"
        )
        self._indent()
        self._enter_scope()

        for stmt in body_nodes:
            self._visit(stmt)

        self._exit_scope()
        self._emit(f"{loop_var} = ch_int((int)ch_to_number({loop_var}) + {t_step});")
        self._dedent()
        self._emit("}")
        self._exit_scope()
        self._dedent()
        self._emit("}")
        self._dedent()
        self._emit("}")
    
    def _visit_while(self, node: ASTNode) -> None:
        """Generate code for while loop."""
        # children = [condition, ...body_statements]
        cond_code = self._visit(node.children[0]) if node.children else "ch_bool(false)"
        
        self._emit(f"while (ch_to_bool({cond_code})) {{")
        self._indent()
        self._enter_scope()
        
        # Visit body statements
        for stmt in node.children[1:]:
            self._visit(stmt)

        self._exit_scope()
        
        self._dedent()
        self._emit("}")
    
    def _visit_todo(self, node: ASTNode) -> None:
        """Generate code for todo statement."""
        msg = node.value if node.value else "not implemented"
        self._emit(f"// TODO: {msg}")