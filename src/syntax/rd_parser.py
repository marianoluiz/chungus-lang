from typing import List, Optional
from src.constants.token import Token, ID_T, INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, BOOL_LIT_T, SKIP_TOKENS
from src.syntax.ast import ASTNode, ParseResult
from src.syntax.errors import ParseError
from src.syntax.core import ParserCore
from src.syntax.rule_expr import ExprRules
from src.syntax.rule_single import SingleStmtRules
from src.syntax.rule_block import BlockStmtRules

class RDParser(ParserCore, ExprRules, SingleStmtRules, BlockStmtRules):
    """
    Recursive-Descent Parser (RDParser).

    Parses a stream of Tokens (produced by the Lexer) into an Abstract Syntax Tree (AST).

    Attributes:
        tokens (List[Token]): List of tokens to parse.
        _source (str): Original source code string.
        _lines (List[str]): Source code split into lines for error reporting.
        _i (int): Current token index.
        errors (List[str]): List of parse error messages encountered.
        _debug (bool): Debug mode flag. Prints debug messages if True.

    See `docs/ast_structure.md` for full AST node hierarchy.
    """
    def __init__(self, tokens: List[dict], source: str, debug: bool = False):
        self.tokens: List[Token] = tokens   #  [ Token(lexeme, type, line, col), ... ]
        self._source = source
        self._lines = source.splitlines(keepends=False)
        self._i = 0                # current token index
        self.errors: List[str] = []
        self._debug = debug        # Debug switch


    def parse(self) -> ParseResult:
        """
        Parse the token stream into an AST.

        Returns:
            ParseResult: Contains the root ASTNode and list of errors encountered.
        """
        try:
            tree = self._program()
            return ParseResult(tree, self.errors)
        except ParseError as e:
            # Store error in list as a string
            self.errors.append(str(e))
            return ParseResult(None, self.errors)
