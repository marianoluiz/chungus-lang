from typing import List, Optional, TYPE_CHECKING
from src.constants.token import ID_T, INT_LIT_T, STR_LIT_T, BOOL_LIT_T, FLOAT_LIT_T, SKIP_TOKENS, Token
from src.syntax.ast import ASTNode

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class SingleStmtRules:
    """
    Single-statements parsing rules.

    Used by (`RDParser`) to parse program, general statements, argument lists,
    array literals/manipulation, id-tail forms (assignment/call/index), and
    return/element helpers.
    """


    def _program(self: "RDParser") -> ASTNode:
        """
        Parse the top-level program structure.
        
        ```
        <program>
            -> <function_blocks> <general_statement> <general_statement_tail>
        ```

        Returns: ASTNode: Root ASTNode
        """

        self._expect(self.PRED_PROGRAM, 'program')

        funcs = self._function_blocks()

        # one general statement
        general_stmts = [self._general_statement()]

        # many optional general statement
        while not self._match('EOF'):
            general_stmts.append(self._general_statement())

        children = funcs + general_stmts
        return ASTNode('program', children=children)


    def _general_statement(self: "RDParser") -> ASTNode:
        """
        Parse a general statement.

        ```
        <general_statement>
            -> id <id_statement_tail> ;
            -> <output_statement> ;
            -> <control_structure_block>
            -> <error_handling_block>
            -> <todo_statement> ;
        ```

        Returns: 
            ASTNode
        """

        self._expect(self.PRED_GENERAL_STMT, 'general_statement')

        # identifier-starting statement (assignment, call, indexed assignment)
        if self._match(ID_T):
            id_tok = self._advance()
            node = self._id_statement_tail(id_tok)

            self._expect_type(';', 'general_statement')
            self._advance()

            return ASTNode('general_statement', children=[node])

        # output
        elif self._match('show'):
            node = self._output_statement()

            self._expect_type(';', 'general_statement')
            self._advance()

            return ASTNode('general_statement', children=[node])

        # conditional (if / elif / else ... close)
        elif self._match('if'):
            node = self._conditional_block()
            return ASTNode('general_statement', children=[node])

        # looping (for / while ... close)
        elif self._match('for', 'while'):
            node = self._looping_block()
            return ASTNode('general_statement', children=[node])

        # error handling (try / fail / always ... close)
        elif self._match('try'):
            node = self._error_handling_statement()
            return ASTNode('general_statement', children=[node])

        # todo
        elif self._match('todo'):
            tok = self._advance()
            self._expect_type(';', 'general_statement')
            self._advance()
            return ASTNode('general_statement', children=[self._ast_node('todo', tok)])


    def _arg_list_opt(self: "RDParser") -> List[ASTNode]:
        """
        Parse an optional comma-separated argument list.

        ```
        <arg_list_opt>
            -> <arg_list>
            -> λ
        
        <arg_list>
            -> <arg_element> <arg_element_tail>
        
        <arg_element_tail>
            -> , <arg_element> <arg_element_tail>
            -> λ
        
        <arg_element>
            -> <expr>
        ```

        Returns:
            List[ASTNode]: List of expression AST nodes representing arguments.
        """

        self._expect({')'} | self.PRED_EXPR, '_arg_list_opt')

        args: List[ASTNode] = []

        if not self._match(')'):
            while True:
                # parse expression
                expr = self._expr()
                args.append(expr)

                # after parsing expr, we need to show full error context
                # recompute allowed follow tokens fresh for this argument. Or else you would have trouble not resetting
                self._expect_after_expr({')', ','}, expr, 'arg_list_opt')

                # break if no comma, otherwise consume and continue
                if not self._match(','):
                    break

                self._advance()

        return args


    def _return_opt(self: "RDParser") -> Optional[ASTNode]:
        """
        Parse an optional return statement.
        
        ```
        <return_opt>
            -> <return_statement>
            -> λ
        
        <return_statement>
            -> ret <expr> ;
        ```

        Returns: 
            ASTNode | None: AST node for return statement if present.
        """

        if self._match('ret'):
            self._advance()
            expr = self._expr()

            self._expect_after_expr({';'}, expr, 'return_opt')
            self._expect_type(';', 'return_statement')
            self._advance()

            node =  ASTNode('return_statement', children=[expr])
            return node
        
        return None


    def _output_statement(self: "RDParser") -> ASTNode:
        """
        Parse a 'show' statement.

        ```
        <output_statement>
            -> show <output_value>
        
        <output_value>
            -> id
            -> str_literal
        ```
        Returns:
            ASTNode: AST node representing the output statement.
        """

        show_tok = self._advance()

        if self._match(ID_T):
            tok = self._advance()
            return self._ast_node('output_statement', show_tok, children=[self._ast_node(ID_T, tok, value=tok.lexeme)])
        elif self._match(STR_LIT_T):
            tok = self._advance()
            return self._ast_node('output_statement', show_tok, children=[self._ast_node(STR_LIT_T, tok, value=tok.lexeme)])
        else:
            self._expect({ID_T, STR_LIT_T}, 'output_value')


    def _id_statement_tail(self: "RDParser", id_tok: Token) -> ASTNode:
        """ 
        Parses next of id.

        ```
        <id_statement_tail>
            -> = <assignment_value>
            -> <function_call_statement>
            -> [ <index> ] <index_loop> = <assignment_value_no_arrayinit>
        
        <function_call_statement>
            -> ( <arg_list_opt> )
        
        <index>
            -> int_literal
            -> id
        
        <index_loop>
            -> [ <index> ]
            -> λ
        ```

        Returns:
            ASTNode: AST node representing the id_statement_tail.
        """

        # expect predict set of id_stmt_tail
        self._expect({'(', '=', '['}, 'id_statement_tail')

        # Assignment statement: = <assignment_value>
        if self._match('='):
            self._advance()
            node = self._assignment_value()   # parse RHS (no '=' consumption inside)
            return self._ast_node('assignment_statement', id_tok, value=id_tok.lexeme, children=[node])

        # Function call: ( <arg_list_opt> )
        elif self._match('('):
            self._advance()

            args = self._arg_list_opt()

            if not self._match(')'):
                self._error([')'], 'function_call')

            self._advance()

            # We will add 1. args
            children = []

            if args:
                children.append(ASTNode('args', children=args))

            return self._ast_node('function_call', id_tok, value=id_tok.lexeme, children=children)

        # Array indexing assignment: [<index>] <index_loop> = <assignment_value>
        elif self._match('['):
            indices = []
            self._advance()
            indices.append(self._index())

            self._expect_type(']', 'array_idx_assignment')
            self._advance()

            # expect = or [ after first index
            self._expect({'=', '['}, 'array_idx_assignment')

            # 2nd index col
            if self._match('['):
                self._advance()

                indices.append(self._index())

                self._expect_type(']', 'index_loop')
                self._advance()

            # = after indexed variable array
            self._expect({'='}, 'array_idx_assignment')

            # consume equal
            self._advance()

            value = self._assignment_value_no_arrayinit()

            # create node of indices for ast
            indices_node = ASTNode('indices', children=indices)

            return self._ast_node('array_idx_assignment', id_tok, value=id_tok.lexeme, children=[indices_node, value])


    def _assignment_value(self: "RDParser"):
        """
        Parse the right-hand side of an assignment.

        ```
        <assignment_value>
            -> read
            -> <type_casting>
            -> [ <index> ] <arrays>
            -> <expr>
        
        <type_casting>
            -> int ( <expr> )
            -> float ( <expr> )
        
        <arrays>
            -> <1d_array_init>
            -> [ <index> ] <2d_array_init>
        ```

        Returns:
            ASTNode
        """

        # predict of assignment value
        self._expect({'!', '[', 'false', 'float', FLOAT_LIT_T, ID_T, 'int', INT_LIT_T, 'read', STR_LIT_T, 'true'}, 'assignment_value')

        # input method
        if self._match('read'):
            tok = self._advance()
            return self._ast_node('read', tok)

        # typecast method
        elif self._match('int', 'float'):
            cast_tok = self._advance()
            cast_method = cast_tok.lexeme

            if not self._match('('):
                self._expect_type('(', 'assignment_value')

            self._advance()

            expr = self._expr()

            # we always need to show whole expected after expr if it errors since it is a unique
            # this mainly checks ')' after expr but we include the whole context
            self._expect_after_expr({ ')' }, expr, 'assignment_value')
            self._advance()

            return self._ast_node('assignment_value', cast_tok, value=cast_method, children=[expr])

        # array declaration: [index] arrays
        elif self._match('['):
            bracket_tok = self._advance()

            # parse first dimension index
            first_idx = self._index()

            self._expect_type(']', 'arrays')
            self._advance()

            self._expect({'=', '['}, 'arrays')

            # check if 1D or 2D array
            if self._match('['):
                # 2D array: [index][index] = [[...], [...]]
                return self._two_d_array_init(bracket_tok, first_idx)
            else:
                # 1D array: [index] = [...]
                return self._one_d_array_init(bracket_tok, first_idx)

        else:
            # other wise, its an expr
            expr = self._expr()

            # after an expr, proper error display would be first set of equation ops + semi-colon
            self._expect_after_expr({';'}, expr, 'assignment_value')

            return expr


    def _assignment_value_no_arrayinit(self: "RDParser"):
        """
        Parse the right-hand side of an assignment (without array initialization).
        Used for indexed assignments where array initialization is not allowed.

        ```
        <assignment_value_no_arrayinit>
            -> read
            -> <type_casting>
            -> <expr>
        
        <type_casting>
            -> int ( <expr> )
            -> float ( <expr> )
        ```

        Returns:
            ASTNode
        """
        
        self._expect({'!', 'false', 'float', FLOAT_LIT_T, ID_T, 'int', INT_LIT_T, 'read', STR_LIT_T, 'true'}, 'assignment_value_no_arrayinit')

        # input method
        if self._match('read'):
            tok = self._advance()
            return self._ast_node('read', tok)

        # typecast method
        elif self._match('int', 'float'):
            cast_tok = self._advance()
            cast_method = cast_tok.lexeme

            if not self._match('('):
                self._expect_type('(', 'assignment_value_no_arrayinit')

            self._advance()

            expr = self._expr()

            # check for closing parenthesis
            self._expect_after_expr({ ')' }, expr, 'assignment_value_no_arrayinit')
            self._advance()

            return self._ast_node('assignment_value', cast_tok, value=cast_method, children=[expr])

        else:
            # otherwise, it's an expr (including array literals but not array initialization)
            expr = self._expr()

            # after an expr, proper error display would be first set of equation ops + semi-colon
            self._expect_after_expr({';'}, expr, 'assignment_value_no_arrayinit')

            return expr


    def _one_d_array_init(self: "RDParser", bracket_tok: Token, size_idx: ASTNode) -> ASTNode:
        """
        Parse 1D array initialization.

        ```
        <1d_array_init>
            -> = [ <1d_element_list> ]
        
            <1d_element_list>
                -> <array_element> <1d_array_tail>
                -> λ
            
            <1d_array_tail>
                -> , <array_element> <1d_array_tail>
                -> λ
        ```

        Args:
            bracket_tok: Token for the opening bracket
            size_idx: Size index node

        Returns:
            ASTNode: AST node for 1D array initialization
        """
        # expect = after [size]
        self._expect_type('=', 'one_d_array_init')
        self._advance()

        # expect [ for array literal
        self._expect_type('[', 'one_d_array_init')
        self._advance()

        # combine pred array element and follow set
        self._expect({']'} | self.PRED_ARRAY_ELEMENT, '_one_d_array_init')

        # parse 1D element list (no nested arrays allowed)
        elements: List[ASTNode] = []

        # empty list allowed
        if not self._match(']'):
            
            # parse first element
            elements.append(self._array_element())
            self._expect({',', ']'}, 'one_d_element_list')

            # parse remaining elements
            while self._match(','):
                self._advance()
                elements.append(self._array_element())
                self._expect({',', ']'}, 'one_d_element_list')

        # expect closing ]
        self._expect_type(']', 'one_d_array_init')
        self._advance()

        # create size node
        size_node = ASTNode('size', children=[size_idx])

        return self._ast_node('array_1d_init', bracket_tok, children=[size_node] + elements)


    def _two_d_array_init(self: "RDParser", bracket_tok: Token, row_idx: ASTNode) -> ASTNode:
        """
        Parse 2D array initialization.

        ```
        <2d_array_init>
            -> = [ <2d_element_list> ]
        
            <2d_element_list>
                -> <2d_array_element> <2d_array_tail>
                -> λ
            
            <2d_array_element>
                -> [ <array_element> <two_d_inner_tail> ]
            
            <two_d_inner_tail>
                -> , <array_element> <two_d_inner_tail>
                -> λ
            
            <2d_array_tail>
                -> , <2d_array_element> <2d_array_tail>
                -> λ
        ```

        Args:
            bracket_tok: Token for the opening bracket
            row_idx: First dimension (row) index node

        Returns:
            ASTNode: AST node for 2D array initialization
        """
        # expect [col_size] after [row_size]
        self._expect_type('[', 'two_d_array_init')
        self._advance()

        col_idx = self._index()

        self._expect_type(']', 'two_d_array_init')
        self._advance()

        # expect = after [row][col]
        self._expect_type('=', 'two_d_array_init')
        self._advance()

        # expect [ for array literal
        self._expect_type('[', 'two_d_array_init')
        self._advance()

        # check predict
        self._expect({'[', ']'}, 'two_d_array_init')

        # parse 2D element list (nested arrays required)
        rows: List[ASTNode] = []
        
        # empty list allowed
        if not self._match(']'):
            # parse first row
            rows.append(self._two_d_array_element())
            self._expect({',', ']'}, 'two_d_element_list')

            # parse remaining rows
            while self._match(','):
                self._advance()
                rows.append(self._two_d_array_element())
                self._expect({',', ']'}, 'two_d_element_list')

        # expect closing ]
        self._expect_type(']', 'two_d_array_init')
        self._advance()

        # create size node with both dimensions
        size_node = ASTNode('size', children=[row_idx, col_idx])

        return self._ast_node('array_2d_init', bracket_tok, children=[size_node] + rows)


    def _two_d_array_element(self: "RDParser") -> ASTNode:
        """
        Parse a 2D array row element.

        ```
        <2d_array_element>
            -> [ <array_element> <two_d_inner_tail> ]
        
            <two_d_inner_tail>
                -> , <array_element> <two_d_inner_tail>
                -> λ
        ```

        Returns:
            ASTNode: AST node for a row in 2D array
        """
        # expect [ for row
        self._expect_type('[', 'two_d_array_element')
        row_tok = self._advance()

        # parse row elements
        row_elements: List[ASTNode] = []

        # at least one element required (no empty rows)
        if not self._match(']'):
            row_elements.append(self._array_element())
            self._expect({',', ']'}, 'two_d_inner_tail')

            # parse remaining elements in row
            while self._match(','):
                self._advance()
                row_elements.append(self._array_element())
                self._expect({',', ']'}, 'two_d_inner_tail')

        # expect closing ]
        self._expect_type(']', 'two_d_array_element')
        self._advance()

        return self._ast_node('array_row', row_tok, children=row_elements)


    def _array_element(self: "RDParser") -> ASTNode:
        """
        Parse a single array element (literal or id).

        ```
        <array_element>
            -> <int_float_str_bool_lit>
            -> id
        
        <int_float_str_bool_lit>
            -> <int_float_str_lit>
            -> true
            -> false
        
        <int_float_str_lit>
            -> <int_float_lit>
            -> str_literal
        
        <int_float_lit>
            -> int_literal
            -> float_literal
        ```

        Returns:
            ASTNode: AST node for the array element.
        """

        # predict set of array element
        self._expect(self.PRED_ARRAY_ELEMENT, 'array_element')

        if self._match(INT_LIT_T, FLOAT_LIT_T):
            tok = self._advance()
            kind = INT_LIT_T if tok.type == INT_LIT_T else FLOAT_LIT_T
            return self._ast_node(kind, tok, value=tok.lexeme)

        elif self._match(STR_LIT_T):
            tok = self._advance()
            return self._ast_node(STR_LIT_T, tok, value=tok.lexeme)

        elif self._match('true', 'false'):
            tok = self._advance()
            return self._ast_node(BOOL_LIT_T, tok, value=tok.lexeme)

        elif self._match(ID_T):
            tok = self._advance()
            return self._ast_node(ID_T, tok, value=tok.lexeme)
