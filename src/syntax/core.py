"""
Parser core utilities used by RDParser mixins.

This module exposes ParserCore, a tiny reusable base that provides:
- cursor management: _curr(), _advance(), _skip_trivia()
- token matching: _match(...)
- error reporting: _error(expected, context) -> raises ParseError

The mixins that implement grammar rules (e.g. ExprRules, BlockStmtRules)
expect an object that implements these helpers (RDParser inherits ParserCore).
"""
from typing import List, TYPE_CHECKING
from src.constants.ast import ASTNode
from src.constants.error_syntax import ParseError, UnexpectedError
from src.constants.token import ID_T, BOOL_LIT_T, STR_LIT_T, FLOAT_LIT_T, INT_LIT_T, Token, SKIP_TOKENS

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class ParserCore:
    """
    Minimal parsing runtime helpers.

    Intended to be mixed into or inherited by a recursive-descent parser.
    Provides safe token access, skipping of trivia, and a single point to
    format and raise parse errors.

    Attributes (expected to be set by the concrete parser):
        tokens: List[Token] - token stream to parse
        _lines: List[str] - original source split into lines (for error caret display)
        _i: int - current index into tokens
        _debug: bool - enable debug printing
        errors: List[str] - optional error accumulator (parser may use)
    """

    def _dbg(self: "RDParser", msg: str):
        """
        Emit a debug message when parser debug mode is enabled.

        Returns:
            None
        """
        if self._debug:
            print(msg)


    def _skip_trivia(self: "RDParser"):
        """
        Advance past non-significant tokens such as space and newlines.

        Returns:
            None
        """
        while self._i < len(self._tokens) and \
            self._tokens[self._i].type in SKIP_TOKENS:
            self._i += 1


    def _curr(self: "RDParser") -> dict:
        """
        Return the current token (skipping trivia); returns a synthetic EOF token at end.

        Returns:
            Token: The current Token object or a synthetic EOF token.
        """
        self._skip_trivia()

        if self._i >= len(self._tokens):
            # Place EOF at the end of the last source line so the caret prints after the line text.
            if self._lines:
                line_no = len(self._lines)              # Length of whole program from the lines list
                col_no = len(self._lines[-1]) + 1       # number of characters in the last line
            else:
                line_no = 1
                col_no = 1

            return Token(type="EOF", lexeme="", line=line_no, col=col_no)
        
        return self._tokens[self._i]


    def _match(self, *types: str) -> bool:
        """
        Test whether the current token's type matches any of the given types.

        Returns:
            bool: True if there is a match, False otherwise.
        """
        return self._curr().type in types


    def _advance(self: "RDParser") -> dict:
        """
        Consume and return the current token, advancing the internal pointer.

        Returns:
            Token: The consumed token.
        """
        self._skip_trivia()
        tok = self._curr()
        if tok.type != 'EOF':
            self._i += 1
        return tok


    def _error(self, expected: List[str], context: str):
        """
        Produce a caret-style parse error message and raise ParseError.

        Returns:
            None (always raises ParseError)
        """
        tok = self._curr()

        # If tok.line is a valid line number, get that line from self._lines; otherwise use an empty string
        line_text = self._lines[tok.line - 1] if 1 <= tok.line <= len(self._lines) else ""
        
        err_block = str(UnexpectedError(line_text, (tok.line, tok.col)))
        expected_list = ", ".join(sorted(expected))

        msg = (
            f"{err_block}"
            f"Unexpected token in {context} at line {tok.line} col {tok.col}: "
            f"{tok.type or tok.lexeme}\n"
            f"Expected any: {expected_list}"
        )
        
        if tok.type == 'fn' and context == 'general_statement':
            msg += "\n\nNote: function blocks are only allowed before any statements, at the top level"

        # Stop parsing immediately
        raise ParseError(msg)


    def _is_closed_expr(self: "RDParser") -> bool:
        """
        Check if the previous non-skip token is ')' - indicates a closed/parenthesized expression.
        
        Returns:
            bool: True if expression is closed by parentheses, False otherwise.
        """
        if self._i > 0:
            # Skip backwards over whitespace/newline/comment tokens to find meaningful token
            idx = self._i - 1
            while idx >= 0 and self._tokens[idx].type in ('whitespace', 'newline', 'comment'):
                idx -= 1
            
            if idx >= 0 and self._tokens[idx].type == ')':
                return True
        
        return False


    def _add_postfix_tokens(self: "RDParser", follow_set: set, expr_node: ASTNode) -> set:
        """
        Add postfix operator tokens to show follow set context based on expression type.
        I use this on error context printing.

        Args:
            follow_set: Set of valid following tokens
            expr_node: Expression node to check for postfix eligibility

        Returns:
            Updated follow set with postfix tokens added if applicable
        """
        updated_set = follow_set.copy()
        
        # Check if expression is closed (parenthesized)
        is_closed = self._is_closed_expr()
        
        REL_EQ_OP = {'!=', '=='}
        LOGICAL_OP = {'and', 'or'}
        REL_OP = {'<', '<=', '>', '>='}
        ARITH_OP = {'%', '*', '**', '+', '-', '/', '//'}
        ALL_OP = REL_EQ_OP | LOGICAL_OP | REL_OP | ARITH_OP
        BINARY_OPS = ARITH_OP | REL_OP | REL_EQ_OP | LOGICAL_OP
        UNARY_OPS = {'!'}

        # If expression is closed (parenthesized), only binary operators can follow
        if is_closed:
            updated_set |= ALL_OP
            return updated_set

        # For binary operators: check rightmost operand (can continue with postfix on that operand)
        # For unary operators: don't add postfix (can't index/call the result)
        # For direct values: add postfix if applicable
        if expr_node.kind in BINARY_OPS:
            # Binary operator - check rightmost operand
            postfix_target = self._postfixable_root(expr_node)
        elif expr_node.kind in UNARY_OPS:
            # Unary operator - can't postfix the result, only binary ops apply
            updated_set |= ALL_OP
            return updated_set
        else:
            # Direct value (id, index, function_call, literal)
            postfix_target = expr_node


        # self._dbg('DBG:  ' + postfix_target.kind)
        
        if postfix_target.kind == ID_T:
            # Identifier: can be followed by function call or indexing
            updated_set |= {'(', '['} | ALL_OP


        elif postfix_target.kind == 'index':

            # check dimension count - only allow '[' if not already 2D
            # From the children of the index node, find the child 'indices'. If none exists, give me None
            # └─ indices  (check if this exist)
            #     ├─ int_literal: 1 
            #     └─ int_literal: 1  
            indices_node = next((child for child in postfix_target.children if child.kind == 'indices'), None)
            num_dimensions = len(indices_node.children) if indices_node else 0

            # Add '[' only if: less than 2D AND not inside brackets
            if num_dimensions < 2:
                updated_set |= {'['}
            
            updated_set |= ALL_OP
            
        elif postfix_target.kind == 'function_call':

            updated_set |= ALL_OP
            
        elif postfix_target.kind in (INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, BOOL_LIT_T):
            # Literals: only binary operators apply
            updated_set |= ALL_OP
            
        else:
            # Other not recognized nodes: only binary operators can follow
            updated_set |= ALL_OP

        return updated_set


    def _postfixable_root(self: "RDParser", node: ASTNode) -> ASTNode:
        """
        Walks the rightmost chain of children until an identifier or index or function call
        or a leaf is reached. This is used for proper error printing for id vs fncall vs index.

        Returns:
            ASTNode: node that would receive postfix operations if any.
        """
        cur = node
        # descend to the rightmost child while it's not directly postfixable
        while True:
            # stop and return node if id / index / func call
            if cur.kind in (ID_T, 'index', 'function_call'):
                return cur

            # if no children get it most likely a bool / str / int or float
            if not getattr(cur, "children", []):
                return cur

            # get last child
            cur = cur.children[-1]


    def _ast_node(self: "RDParser", kind:str, tok=None, *, value=None, children=None) -> ASTNode:
        """
        Create an ASTNode and optionally attach token position.

        Args:
            kind: Node kind (e.g. 'id', 'int_literal').
            tok: Optional Token; if given, sets `node.line` and `node.col`.
            *: means parameters after * must be passed as keyword arguments.
            value: Optional payload for leaf nodes.
            children: Optional list of child ASTNodes.

        Returns:
            The constructed `ASTNode` (with `line`/`col` when `tok` provided).
        """

        if children is None:
            children = []
        
        # positional args first, defined args after those.
        n = ASTNode(kind, value=value, children=children)

        if tok is not None:
            n.line = tok.line
            n.col = tok.col

        return n
    

    def _expect(self, expected: set, ctx: str):
        """
        Expect current token to be in a set of valid token types.

        Args:
            expected: Valid token types (FIRST / FOLLOW set).
            ctx: Grammar context for error reporting.

        Raises:
            ParseError if current token is not in `expected`.
        """
        if isinstance(expected, set):
            ok = self._match(*expected)

        if not ok:
            self._error(sorted(expected), ctx)


    def _expect_type(self, typ: str, ctx: str):
        """
        Expect a single exact token type.

        Args:
            typ: Required token type.
            ctx: Grammar context for error reporting.

        Raises:
            ParseError if token does not match `typ`.
        """
        if not self._match(typ):
            self._error([typ], ctx)


    def _expect_after_expr(self, base_follow: set, expr_node, ctx: str):
        """
        Validate token following an expression.

        Builds a full FOLLOW set using:
        - base grammar follow
        - optional block keywords
        - postfix tokens derived from the expression

        Args:
            base_follow: Base FOLLOW set.
            expr_node: Parsed expression node (for postfix rules).
            ctx: Grammar context for errors.

        Raises:
            ParseError if the next token is invalid.
        """
        follow = set(base_follow)

        # check datatype to show full proper context of error
        follow = self._add_postfix_tokens(follow, expr_node)  # you already have this

        if not self._match(*follow):
            # returns a list
            self._error(sorted(follow), ctx)
