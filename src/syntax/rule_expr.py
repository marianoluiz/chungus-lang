
from typing import TYPE_CHECKING
from src.constants.token import ID_T, INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, BOOL_LIT_T, SKIP_TOKENS, Token
from src.constants.ast import ASTNode

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class ExprRules:
    """
    Expression parsing rules.

    Used by (`RDParser`) to parse expression rules which are
    logical, comparison, arithmetic, power, postfix calls/indexing, and literals.
    """

    def _expr(self: "RDParser") -> ASTNode:
        """
        Parse an expression.

        ```
        <expr>
            -> <or_expr>
        ```

        Returns:
            ASTNode
        """
        return self._or_expr()


    def _or_expr(self: "RDParser") -> ASTNode:
        """
        Parse logical OR precedence level.

        ```
        <or_expr>
            -> <and_expr> <or_tail>

        <or_tail>
            -> or <and_expr> <or_tail>
            -> λ
        ```

        Returns:
            ASTNode
        """
        left = self._and_expr()

        while self._match('or'):
            tok = self._advance()
            right = self._and_expr()
            left = self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _and_expr(self: "RDParser") -> ASTNode:
        """
        Parse logical AND precedence level.

        ```
        <and_expr>
            -> <eq_expr> <and_tail>

        <and_tail>
            -> and <eq_expr> <and_tail>
            -> λ
        ```

        Returns:
            ASTNode
        """
        left = self._eq_expr()

        while self._match('and'):
            tok = self._advance()
            right = self._eq_expr()
            left = self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _eq_expr(self: "RDParser") -> ASTNode:
        """
        Parse equality precedence level.

        ```
        <eq_expr>
            -> <rel_expr> <eq_tail>

        <eq_tail>
            -> <eq_op> <rel_expr> <eq_tail>
            -> λ

        <eq_op>
            -> == | !=
        ```

        Returns:
            ASTNode
        """
        left = self._rel_expr()

        while self._match('==', '!='):
            tok = self._advance()
            right = self._rel_expr()
            left = self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _rel_expr(self: "RDParser") -> ASTNode:
        """
        Parse relational precedence level.

        ```
        <rel_expr>
            -> <add_expr> <rel_tail>

        <rel_tail>
            -> <rel_op> <add_expr> <rel_tail>
            -> λ

        <rel_op>
            -> > | < | >= | <=
        ```

        Returns:
            ASTNode
        """
        left = self._add_expr()

        while self._match('>', '<', '>=', '<='):
            tok = self._advance()
            right = self._add_expr()
            left = self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _add_expr(self: "RDParser") -> ASTNode:
        """
        Parse additive precedence level.

        ```
        <add_expr>
            -> <mul_expr> <add_tail>

        <add_tail>
            -> <add_op> <mul_expr> <add_tail>
            -> λ

        <add_op>
            -> + | -
        ```

        Returns:
            ASTNode
        """
        left = self._mul_expr()

        while self._match('+', '-'):
            tok = self._advance()
            right = self._mul_expr()
            left = self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _mul_expr(self: "RDParser") -> ASTNode:
        """
        Parse multiplicative precedence level.

        ```
        <mul_expr>
            -> <pow_expr> <mul_tail>

        <mul_tail>
            -> <mul_op> <pow_expr> <mul_tail>
            -> λ

        <mul_op>
            -> * | / | // | %
        ```

        Returns:
            ASTNode
        """
        left = self._pow_expr()

        while self._match('*', '/', '//', '%'):
            tok = self._advance()
            right = self._pow_expr()
            left = self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _pow_expr(self: "RDParser") -> ASTNode:
        """
        Parse power precedence level (right-associative).

        <operator>
            -> **
        ```

        Returns:
            ASTNode
        """
        left = self._unary_expr()

        # Right associativity: a ** b ** c -> a ** (b ** c)
        if self._match('**'):
            tok = self._advance()
            right = self._pow_expr()
            return self._ast_node(tok.lexeme, tok, children=[left, right])

        return left


    def _unary_expr(self: "RDParser") -> ASTNode:
        """
        Parse unary precedence level.

        ```
        <unary_expr>
            -> ! <unary_expr>
            -> <primary>
        ```

        Returns:
            ASTNode
        """
        self._expect(self.PRED_EXPR, 'unary_expr')

        if self._match('!'):
            tok = self._advance()
            operand = self._unary_expr()
            return self._ast_node('!', tok, children=[operand])

        return self._primary()


    def _primary(self: "RDParser") -> ASTNode:
        """
        Parse a primary expression.

        ```
        <primary>
            -> <int_float_str_bool_lit>
            -> ( <expr> )
            -> <type_casting>
            -> id <postfix_tail>
            -> <builtin_call>

        <int_float_str_bool_lit>
            -> int_literal | float_literal | str_literal | true | false

        <type_casting>
            -> int ( <expr> )
            -> float ( <expr> )

        <builtin_call>
            -> length ( <expr> )
            -> str_to_arr ( <expr> )
            -> arr_to_str ( <expr> )
            -> compare ( <expr> , <expr> )
            -> type ( <expr> )
        ```

        Returns:
            ASTNode
        """

        self._expect(self.PRED_EXPR, 'primary')

        # Parenthesized expression
        if self._match('('):
            self._advance()
            expr = self._expr()

            self._expect_after_expr({')'}, expr, 'primary')
            self._expect_type(')', 'primary')
            self._advance()

            return expr

        # Type casting: int(...) or float(...)
        if self._match('int', 'float'):
            cast_tok = self._advance()
            cast_type = cast_tok.lexeme

            self._expect_type('(', 'primary')
            self._advance()

            expr = self._expr()

            self._expect_after_expr({')'}, expr, 'primary')
            self._expect_type(')', 'primary')
            self._advance()

            return self._ast_node('type_cast', cast_tok, value=cast_type, children=[expr])

        if self._match('length'):
            fn_tok = self._advance()

            self._expect_type('(', 'length')
            self._advance()

            arg = self._expr()

            self._expect_after_expr({')'}, arg, 'length')
            self._expect_type(')', 'length')
            self._advance()

            return self._ast_node('function_call', fn_tok, value=fn_tok.lexeme, children=[arg])

        # Reserved built-in function calls (operand-only grammar)
        if self._match('str_to_arr'):
            fn_tok = self._advance()

            self._expect_type('(', 'str_to_arr')
            self._advance()

            arg = self._expr()

            self._expect_after_expr({')'}, arg, 'str_to_arr')
            self._expect_type(')', 'str_to_arr')
            self._advance()

            return self._ast_node('function_call', fn_tok, value=fn_tok.lexeme, children=[arg])

        if self._match('arr_to_str'):
            fn_tok = self._advance()

            self._expect_type('(', 'arr_to_str')
            self._advance()

            arg = self._expr()

            self._expect_after_expr({')'}, arg, 'arr_to_str')
            self._expect_type(')', 'arr_to_str')
            self._advance()

            return self._ast_node('function_call', fn_tok, value=fn_tok.lexeme, children=[arg])

        if self._match('compare'):
            fn_tok = self._advance()

            self._expect_type('(', 'compare')
            self._advance()

            left = self._expr()

            self._expect_after_expr({','}, left, 'compare')
            self._expect_type(',', 'compare')
            self._advance()

            right = self._expr()

            self._expect_after_expr({')'}, right, 'compare')
            self._expect_type(')', 'compare')
            self._advance()

            return self._ast_node('function_call', fn_tok, value=fn_tok.lexeme, children=[left, right])

        if self._match('type'):
            fn_tok = self._advance()

            self._expect_type('(', 'type')
            self._advance()

            arg = self._expr()

            self._expect_after_expr({')'}, arg, 'type')
            self._expect_type(')', 'type')
            self._advance()

            return self._ast_node('function_call', fn_tok, value=fn_tok.lexeme, children=[arg])

        # Literals: int, float, str, bool
        if self._match(INT_LIT_T):
            tok = self._advance()
            return self._ast_node(INT_LIT_T, tok, value=tok.lexeme)

        if self._match(FLOAT_LIT_T):
            tok = self._advance()
            return self._ast_node(FLOAT_LIT_T, tok, value=tok.lexeme)

        if self._match(STR_LIT_T):
            tok = self._advance()
            return self._ast_node(STR_LIT_T, tok, value=tok.lexeme)

        if self._match('true', 'false'):
            tok = self._advance()
            return self._ast_node(BOOL_LIT_T, tok, value=tok.lexeme)

        # Identifier with optional postfix (function call or indexing)
        if self._match(ID_T):
            tok = self._advance()
            node = self._ast_node(ID_T, tok, value=tok.lexeme)

            # Handle function call or indexing
            if self._match('(', '['):
                node = self._postfix_tail(node, id_tok=tok)

            return node
    def _postfix_tail(self: "RDParser", node: ASTNode, id_tok: Token) -> ASTNode:
        """
        Parse an optional postfix tail after an identifier.

        ```
        <postfix_tail>
            -> ( <arg_list_opt> )
            -> [ <index> ] <index_loop>
            -> λ
        ```

        Returns:
            ASTNode
        """
        if self._match('('):
            return self._postfix_call(node, id_tok)

        if self._match('['):
            return self._postfix_index(node)

        return node


    def _postfix_call(self: "RDParser", node: ASTNode, id_tok: Token) -> ASTNode:
        """
        Parse a function-call postfix.

        ```
        <postfix_tail>
            -> ( <arg_list_opt> )
        ```

        Returns:
            ASTNode
        """

        self._advance()

        args = self._arg_list_opt()

        self._expect_type(')', 'postfix_call')
        self._advance()

        # keep your AST shape; if args is already a list, pass it directly
        return self._ast_node('function_call', id_tok, value=node.value, children=args)


    def _postfix_index(self: "RDParser", node: ASTNode) -> ASTNode:
        """
        Parse an indexing postfix.

        ```
        <postfix_tail>
            -> [ <expr> ] <index_loop>

        <index_loop>
            -> [ <expr> ]
            -> λ
        ```

        Returns:
            ASTNode
        """

        indices: list[ASTNode] = []
        first_bracket: Token | None = None


        tok = self._advance()  # consume '['

        # make first index first_bracket for ast
        if first_bracket is None:
            first_bracket = tok

        
        expr = self._expr()
        indices.append(expr)

        self._expect_after_expr({']'}, expr, 'postfix_index')
        self._expect_type(']', 'postfix_index')
        self._advance()

        # optional index for 2D (index_loop)
        if self._match('['):
            self._advance() 
            
            expr = self._expr()
            indices.append(expr)

            self._expect_after_expr({']'}, expr, 'postfix_index')
            self._expect_type(']', 'postfix_index')
            self._advance()


        # first_bracket must exist if we got here
        return self._ast_node(
            'index',
            first_bracket,
            children=[
                ASTNode('base', children=[node]),
                ASTNode('indices', children=indices),
            ],
        )

