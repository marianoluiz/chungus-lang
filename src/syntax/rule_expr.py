
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
            -> <operand> <expr_tail>

        <expr_tail>
            -> <operator> <operand> <expr_tail>
            -> λ
        ```

        Returns:
            ASTNode
        """
        left = self._operand()
        return self._expr_tail(left) # pass operand to tail to build the ast node


    def _expr_tail(self: "RDParser", left: ASTNode) -> ASTNode:
        """
        Parse expression tail (operators and operands).

        ```
        <expr_tail>
            -> <operator> <operand> <expr_tail>
            -> λ

        <operator>
            -> and | or | == | != | > | < | >= | <= | + | - | * | / | ** | // | %
        ```

        Returns:
            ASTNode
        """
        # All operators that can appear in expr_tail
        operators = ('and', 'or', '==', '!=', '>', '<', '>=', '<=', '+', '-', '*', '/', '**', '//', '%')

        if self._match(*operators):
            tok = self._advance()
            right = self._operand()
            # Build binary operation node
            node = self._ast_node(tok.lexeme, tok, children=[left, right])
            # Recursively parse the rest of the expression tail
            return self._expr_tail(node)
        
        # Base case: no more operators (lambda production)
        return left


    def _operand(self: "RDParser") -> ASTNode:
        """
        Parse an operand.

        ```
        <operand>
            -> <int_float_str_bool_lit>
            -> ! <operand>
            -> ( <expr> )
            -> <type_casting>
            -> id <postfix_tail>

        <int_float_str_bool_lit>
            -> int_literal | float_literal | str_literal | true | false

        <type_casting>
            -> int ( <expr> )
            -> float ( <expr> )
        ```

        Returns:
            ASTNode
        """

        self._expect(self.PRED_EXPR, 'operand')

        # NOT operand
        if self._match('!'):
            tok = self._advance()
            operand = self._operand()
            return self._ast_node('!', tok, children=[operand])

        # Parenthesized expression
        if self._match('('):
            self._advance()
            expr = self._expr()
            self._expect_after_expr({')'}, expr, 'operand')
            self._advance()
            return expr

        # Type casting: int(...) or float(...)
        if self._match('int', 'float'):
            cast_tok = self._advance()
            cast_type = cast_tok.lexeme

            self._expect_type('(', 'operand')
            self._advance()

            expr = self._expr()

            self._expect_after_expr({')'}, expr, 'operand')
            self._advance()

            return self._ast_node('type_cast', cast_tok, value=cast_type, children=[expr])

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
        self._advance()

        # optional index for 2D (index_loop)
        if self._match('['):
            self._advance() 
            
            expr = self._expr()
            indices.append(expr)

            self._expect_after_expr({']'}, expr, 'postfix_index')
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

