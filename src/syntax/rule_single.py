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
        <program>: 
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
        <general_statement>: 
            -> id <id_statement_tail>
            -> show <output_value>
            -> <conditional_statement>
            -> <looping_statement>
            -> <error_handling_statement>
            -> todo
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
            node = self._conditional_statement()
            return ASTNode('general_statement', children=[node])

        # looping (for / while ... close)
        elif self._match('for', 'while'):
            node = self._looping_statement()
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
            -> <arg_element> <arg_element_tail>
            -> λ
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
                self._expect_after_expr(self.PRED_ARG_ELEMENT_TAIL, expr, 'arg_list_opt')

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
            -> ret <expr>
            -> λ
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


    def _element_list_opt(self: "RDParser") -> List[ASTNode]:
        """
        Parse an optional, possibly-empty list of array literal elements.

        ```
        <element_list>
            -> <array_element> <array_tail>
            -> λ
        ```
        Returns:
            List[ASTNode]: Parsed element nodes (may be empty).
        """

        self._expect(self.PRED_ELEMENT_LIST, 'element_list_opt')

        elements: List[ASTNode] = []

        # empty element list allowed
        if self._match(']'):
            return elements

        # at least one element
        elements.append(self._array_element())
        self._expect(self.PRED_ARRAY_TAIL, 'element_list_opt')

        while self._match(','):
            self._advance()
            # parse next element
            elements.append(self._array_element())

            self._expect(self.PRED_ARRAY_TAIL, 'element_list')

        return elements


    def _array_element(self: "RDParser") -> ASTNode:
        """
        Parse a single array element (literal, id, or nested array).

        ```
        <array_element>:
            -> <int_float_str_bool_lit>
            -> id
            -> [ <element_list> ]
        ```

        Returns:
            ASTNode: AST node for the array element.
        """

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

        elif self._match('['):
            # nested array literal
            self._advance()
            elems = self._element_list_opt()
            
            # backup expect to be ]
            self._expect_type(']', 'array_literal')
            self._advance()

            return ASTNode('array_literal', children=elems)

        else:
            self._error(self.PRED_ARRAY_ELEMENT, 'array_element')


    def _output_statement(self: "RDParser") -> ASTNode:
        """
        Parse a 'show' statement.

        ```
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
            -> ( <arg_list_opt> )
            -> [ <index> ] <index_loop> = <assignment_value>
        ```

        Returns:
            ASTNode: AST node representing the id_statement_tail.
        """

        self._expect(self.PRED_ID_STMT_TAIL, 'id_statement_tail')

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

            # indexed variable array
            while self._match('['):
                self._advance()

                idx = self._index()
                indices.append(idx)

                self._expect_type(']', 'index_loop')
                self._advance()

            # = after indexed variable array, we need to print whole context
            self._expect(self.PRED_ARR_INDEX_ASSIGN_INDEX_LOOP, 'index_loop')

            # consume equal
            self._advance()

            value = self._assignment_value()

            # create node of indices for ast
            indices_node = ASTNode('indices', children=indices)

            return self._ast_node('array_idx_assignment', id_tok, value=id_tok.lexeme, children=[indices_node, value])


    def _assignment_value(self: "RDParser"):
        """
        Parse the right-hand side of an assignment.

        ```
        <assignment_value>
            -> read
            -> int ( <expr> )
            -> float ( <expr> )
            -> [ <element_list> ]
            -> <expr>
        ```

        Returns:
            ASTNode

        Note:
            `block_keywords` param extends FOLLOW(<assignment_value>) for error reporting after <expr>.
        """


        self._expect(self.PRED_ASSIGN_VALUE, 'assignment_value')

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

        # array literal dec
        elif self._match('['):
            bracket_tok = self._advance()

            self._expect(self.PRED_ELEMENT_LIST, 'assignment_value')

            elements = self._element_list_opt()

            # this is actually kinda useless cause we check alr predict set in the loop in elemenet_list_op
            self._expect_type(']', 'assignment_value')
            self._advance()

            return self._ast_node('array_literal', bracket_tok, children=elements)

        else:
            # other wise, its an expr
            expr = self._expr()

            # after an expr, proper error display would be first set of equation ops + semi-colon
            self._expect_after_expr({';'}, expr, 'assignment_value')

            return expr
