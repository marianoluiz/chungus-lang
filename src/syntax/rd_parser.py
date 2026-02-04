from typing import List
from src.constants.token import FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, Token
from src.syntax.ast import ParseResult
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
    """

    def __init__(self: "RDParser", tokens: List[dict], source: str, debug: bool = False):
        self.tokens: List[Token] = tokens   #  [ Token(lexeme, type, line, col), ... ]
        self._source = source               # source code for printing code lines
        self._lines = source.splitlines(keepends=False)  # source code splitted per newline
        self._i = 0                # current token index
        self.errors: List[str] = []
        self._debug = debug        # Debug switch

    # Reusable predict sets used in functions
    PRED_GENERAL_STMT = {'array_add','array_remove','for', ID_T,'if','show','todo','try','while'}
    PRED_PROGRAM      = PRED_GENERAL_STMT | {'fn'}
    PRED_EXPR = {'!', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'}

    PRED_ID_STMT_TAIL = {'(', '=', '['}
    PRED_ASSIGN_VALUE = {'!', '[', 'false', 'float', FLOAT_LIT_T, ID_T, 'int', INT_LIT_T, 'read', STR_LIT_T, 'true'}
    PRED_ELEMENT_LIST = {'[', ']', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'}
    PRED_ARRAY_ELEMENT      = {'[', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'}
    PRED_ARRAY_TAIL         = {',', ']'}
    PRED_ARG_ELEMENT_TAIL   = {')', ','}
    PRED_INDEX              = {INT_LIT_T, ID_T}
    PRED_ARR_INDEX_ASSIGN_INDEX_LOOP = {'=', '['}
    PRED_ARR_MANIP_INDEX_LOOP        = {',', '['} 

    def parse(self: "RDParser") -> ParseResult:
        """
        Parse the token stream into an AST.

        Returns:
            ParseResult: Contains the root ASTNode and list of errors encountered.
        """
        try:
            tree = self._program()
            return ParseResult(tree, self.errors)
        except ParseError as e:
            # If any ParseError object is raised anywhere inside the try block, catch it here and bind it to e
            self.errors.append(str(e))

            return ParseResult(None, self.errors)
    
