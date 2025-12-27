"""
Expression parsing rules (ExprRules).

Provides the ExprRules mixin used by the recursive-descent parser (`RDParser`)
to parse all expression productions (logical, comparison, arithmetic,
power, postfix calls/indexing, literals and grouping).

Expectations:
- Mixed into a class that implements the ParserCore API:
  - self._match(*types) -> bool
  - self._advance() -> Token
  - self._error(expected: List[str], context: str) -> raises ParseError
- Relies on helpers such as `_arg_list_opt()` and `_postfix_tail()` provided
  elsewhere in the parser mixins.

Public symbols:
- ExprRules: mixin containing expression parsing methods.

See also: [`ASTNode`](src/syntax/ast.py), token constants like [`ID_T`](src/constants/token.py).
"""
from typing import TYPE_CHECKING
from src.constants.token import ID_T, INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, BOOL_LIT_T, SKIP_TOKENS
from src.syntax.ast import ASTNode

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class ExprRules:
    """
    Mixin implementing expression parsing rules.

    Each method parses a specific production and returns an `ASTNode`
    representing the parsed subtree.
    """
    def _expr(self: "RDParser") -> ASTNode:
        """
        Parse an expression (logical OR).

        Returns:
            ASTNode: Expression AST node.
        """
        return self._logical_or_expr()
    
    def _logical_or_expr(self: "RDParser") -> ASTNode:
        """
        Parse logical OR expressions.

        Returns:
            ASTNode: AST node representing logical OR operations.
        """
        left  = self._logical_and_expr()

        while self._match('or'):
            op = self._advance().lexeme
            right = self._logical_and_expr()
            left = ASTNode(op, children=[left, right])
        return left
    
    def _logical_and_expr(self: "RDParser") -> ASTNode:
        """
        Parse logical AND expressions.

        Returns:
            ASTNode: AST node representing logical AND operations.
        """

        self._dbg('here once')
        # Advance handle errors
        expected = [ '!', '(', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true' ]

        self._dbg(self._curr())

        if not self._match(*expected):
            self._error(expected, 'logical_or_expr')

        left = self._logical_not_expr()

        while self._match('and'):
            op = self._advance().lexeme
            right = self._logical_not_expr()
            left = ASTNode(op, children=[left, right])
        return left

    def _logical_not_expr(self: "RDParser") -> ASTNode:
        """
        Parse logical NOT expressions.

        Returns:
            ASTNode: AST node representing logical NOT operation or the next expression.
        """

        # Advance handle errors
        expected = [ '!', '(', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true' ]

        if not self._match(*expected):
            self._error(expected, 'logical_and_expr')

        if self._match('!'):
            self._advance()

            right = self._eq_expr()
            return ASTNode('!', children=[right])
        
        # go to production where theres no !
        return self._eq_expr() 

    def _eq_expr(self: "RDParser") -> ASTNode:
        """
        Parse equality expressions (==, !=).

        Returns:
            ASTNode: AST node representing equality operations.
        """

        left = self._comp_operand()

        while self._match('==', '!='):
            op = self._advance().lexeme
            right = self._comp_operand()
            left = ASTNode(op, children=[left, right])
        
        return left
    
    def _comp_operand(self: "RDParser") -> ASTNode:
        """
        Parse a comparison operand: literal, boolean, or relational expression.

        Returns:
            ASTNode: AST node representing the operand.
        """

        # Advance handle errors
        expected = [ '(', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true' ]

        if not self._match(*expected):
            self._error(expected, 'comp_operand')

        # can be rel_expr, str_literal, true, false
        if self._match(STR_LIT_T):
            return ASTNode(STR_LIT_T, value=self._advance().lexeme)
        
        if self._match('true', 'false'):
            return ASTNode(BOOL_LIT_T, value=self._advance().lexeme)
        
        return self._rel_expr()


    def _rel_expr(self: "RDParser") -> ASTNode:
        """
        Parse relational expressions (>, >=, <, <=).

        Returns:
            ASTNode: AST node representing relational operations.
        """
        left = self._arith_expr()

        while self._match('>', '>=', '<', '<='):
            op = self._advance().lexeme
            right = self._arith_expr()
            left = ASTNode(op, children=[left, right])
        
        return left

    def _arith_expr(self) -> ASTNode:
        """
        Parse arithmetic expressions (+, -).

        Returns:
            ASTNode: AST node representing addition/subtraction operations.
        """
        left = self._term()

        while self._match('+', '-'):
            op = self._advance().lexeme
            right = self._term()
            left = ASTNode(op, children=[left, right])
        
        return left

    def _term(self: "RDParser") -> ASTNode:
        """
        Parse multiplicative expressions (*, /, //, %).

        Returns:
            ASTNode: AST node representing multiplication/division/modulo operations.
        """
        left = self._factor()

        while self._match('*', '/', '//', '%'):
            op = self._advance().lexeme
            right = self._factor()
            left = ASTNode(op, children=[left, right])
        
        return left
    
    def _factor(self: "RDParser") -> ASTNode:
        """
        Parse power expressions (**).

        Returns:
            ASTNode: AST node representing power operations.
        """
        left = self._power()

        while self._match('**'):
            op = self._advance().lexeme
            right = self._power()
            left = ASTNode(op, children=[left, right])
        
        return left
    
    def _power(self) -> ASTNode:
        """
        Parse primary expressions: literals, identifiers, function calls, grouping.

        Returns:
            ASTNode: AST node representing the primary expression.
        """
        if self._match(INT_LIT_T, FLOAT_LIT_T):
            tok = self._advance()
            kind = INT_LIT_T if tok.type == INT_LIT_T else FLOAT_LIT_T
            return ASTNode(kind, value=tok.lexeme)
        
        if self._match(STR_LIT_T):
            tok = self._advance()
            return ASTNode(STR_LIT_T, value=tok.lexeme)
        
        if self._match(ID_T):
            tok = self._advance()
            node = ASTNode(ID_T, value=tok.lexeme)

            # handle function call or indexing
            if self._match('(', '['):
                node = self._postfix_tail(node)

            return node

        if self._match('('):
            self._advance()
            node = self._expr()

            if self._match(')'):
                self._advance()
                return node
            else:
                self._error([')'], 'expression')
                return node

        self._error([INT_LIT_T, FLOAT_LIT_T, ID_T, '('], 'power')


    def _postfix_tail(self: "RDParser", node: ASTNode) -> ASTNode:
        """
        Parse trailing postfix operations on an identifier: function call or indexing.

        Returns:
            ASTNode: AST node after applying any postfix operations.
        """
        # function arg branch
        if self._match('('):
            self._advance()

            # the supposed next of unclosed 'ID (' must include ')' if errored
            FOLLOW_ID = {
                '!', '(', ')', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'
            }
            
            if not self._match(*FOLLOW_ID):
                self._error([*FOLLOW_ID], 'postfix_tail')

            args = self._arg_list_opt()

            if not self._match(')'):
                self._error([')'], 'function_call')

            self._advance()

            return ASTNode('function_call', value=node.value, children=args)


        # index branch which can nest
        # flattened indexes
        indices = []

        while self._match('['):
            # array indexing / loop
            self._advance()

            # index number or id
            idx = self._index()
            indices.append(idx)

            if not self._match(']'):
                self._error([']'], 'index')

            self._advance()

        # if it is array reference
        if indices:
            return ASTNode('index', children=[node] + indices)
        
        # if it is function call
        return node

    def _index(self: "RDParser"):
        """ Returns id or int_literal """
        if self._match(INT_LIT_T):
            return ASTNode(INT_LIT_T, value=self._advance().lexeme)

        elif self._match(ID_T):
            return ASTNode(ID_T, value=self._advance().lexeme)

        else:
            self._error([INT_LIT_T, ID_T], '_index')
