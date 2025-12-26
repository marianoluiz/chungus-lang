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
from src.syntax.errors import ParseError, UnexpectedError
from src.constants.token import Token, SKIP_TOKENS

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
        Advance past non-significant tokens such as whitespace and newlines.

        Returns:
            None
        """
        while self._i < len(self.tokens) and \
            self.tokens[self._i].type in SKIP_TOKENS:
            self._i += 1


    def _curr(self: "RDParser") -> dict:
        """
        Return the current token (skipping trivia); returns a synthetic EOF token at end.

        Returns:
            Token: The current Token object or a synthetic EOF token.
        """
        self._skip_trivia()

        if self._i >= len(self.tokens):
            # Place EOF at the end of the last source line so the caret prints after the line text.
            if self._lines:
                line_no = len(self._lines)              # Length of whole program from the lines list
                col_no = len(self._lines[-1]) + 1       # In the last line, the length of it
            else:
                line_no = 1
                col_no = 1

            return Token(type="EOF", lexeme="", line=line_no, col=col_no)
        
        return self.tokens[self._i]


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
        
        # Stop parsing immediately
        raise ParseError(msg)