from dataclasses import dataclass
from lark import Lark, UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from typing import Iterable, Set

# --- user-friendly token name mapping (extend as needed) ---
TOKEN_NAME_MAP = {
    'AND': 'and',
    'OR': 'or',
    'NOT': '!',
    'TRUE': 'true',
    'FALSE': 'false',
    'READ': 'read',
    'SHOW': 'show',
    'CLR': 'clr',
    'EXIT': 'exit',
    'IF': 'if',
    'ELIF': 'elif',
    'ELSE': 'else',
    'WHILE': 'while',
    'FOR': 'for',
    'IN': 'in',
    'RANGE': 'range',
    'FN': 'fn',
    'RET': 'ret',
    'TRY': 'try',
    'FAIL': 'fail',
    'ALWAYS': 'always',
    'TODO': 'todo',
    'ARRAY_ADD': 'array_add',
    'ARRAY_REMOVE': 'array_remove',
    'UN_PLUS': '++',
    'UN_MINUS': '--',
    'EQ_EQ': '==',
    'NOT_EQ': '!=',
    'GT': '>',
    'LT': '<',
    'GE': '>=',
    'LE': '<=',
    'FLOORDIV': '//',
    'POW': '**',
    'NEWLINE': 'newline',
    'EQUAL': '=',
    'CLOSE': 'close',
    'INT': 'int',
    'FLOAT': 'float',
    'INT_LITERAL': 'int_literal',
    'FLOAT_LITERAL': 'float_literal',
    'STR_LITERAL': 'str_literal',
    'ID': 'id',
    'PLUS': '+',
    'MINUS': '-',
    'STAR': '*',
    'SLASH': '/',
    'PERCENT': '%',
    'COMMA': ',',
    'LPAR': '(', 
    'RPAR': ')',  
    'LSQB': '[',
    'RSQB': ']',
    'SEMICOLON': ';',
    'COLON': ':',
}

# --- load grammar once ---
with open("src/constants/cfg_lark", "r", encoding="utf-8") as f:
    _GRAMMAR = f.read()

_PARSER = Lark(_GRAMMAR, parser="earley",
               propagate_positions=True, maybe_placeholders=False)


@dataclass
class SyntaxResult:
    tree: object | None
    errors: list[str]
    log: str = ""


class UnexpectedError:
    """
    Small printable error block with caret pointing to column.
    line_text: a single source line (no trailing newline)
    position: (line_no, col_no) both 1-based integers
    """

    def __init__(self, line_text: str, position: tuple[int, int], tabsize: int = 4):
        # keep the raw displayable line and a tab-expanded version for caret math
        self.raw_line = line_text.rstrip('\n')
        self.tabsize = tabsize
        # Lark columns are 1-based; store as-int and do minimal validation
        self.line_no = int(position[0]) if position and position[0] else 1
        self.col_no = int(position[1]) if position and position[1] else 1

    def __str__(self) -> str:
        # Expand tabs so caret aligns visibly
        display_line = self.raw_line.expandtabs(self.tabsize)
        # Build caret line using Unicode-safe indexing (characters, not bytes)
        chars = list(display_line)
        # Column is 1-based; place caret at col_no or at end if out of range
        caret_index = max(0, min(len(chars), self.col_no - 1))
        caret = " " * caret_index + "^"
        return f"{self.line_no:<5}|{display_line}\n     |{caret}\n"


class Parser:
    def __init__(self):
        self._parser = _PARSER

    def parse(self, source: str) -> SyntaxResult:
        """
        Parse source text and return SyntaxResult containing either a parse tree
        or a list with a single formatted error string.
        """

        # VIRTUAL NEWLINE FIX:
        if source and not source.endswith("\n"):
            source = source + "\n"

        try:
            tree = self._parser.parse(source)
            return SyntaxResult(tree=tree, errors=[], log="Parse successful.")
        except UnexpectedInput as e:
            # --- Utilities ---------------------------------------------------------
            def safe_index(value, fallback):
                """Return value only if it's a valid positive integer."""
                return value if isinstance(value, int) and value > 0 else fallback

            def unicode_char_at(text, col1):
                """Return safe Unicode character for display."""
                if 1 <= col1 <= len(text):
                    return list(text)[col1 - 1]   # handles multi-byte chars
                if col1 == len(text) + 1:
                    return "<EOL>"
                return "<EOF>"

            # --- Extract source lines ----------------------------------------------
            lines = source.splitlines(keepends=True)
            if not lines:
                lines = [""]

            # --- Try to get the exact line text from Lark --------------------------
            try:
                raw_line = e.get_line() or ""
            except Exception:
                raw_line = ""

            raw_line = raw_line.rstrip("\n")

            # If Lark fails to provide a line → fallback to last line
            if raw_line:
                # Use Lark-provided line number if valid, else find it manually
                raw_line_no = safe_index(getattr(e, "line", None),
                                        next((i + 1 for i, ln in enumerate(lines)
                                            if ln.rstrip('\n') == raw_line),
                                            len(lines)))

                display_line = raw_line
            else:
                # EOF or no line available
                raw_line_no = safe_index(getattr(e, "line", None), len(lines))
                display_line = lines[raw_line_no - 1].rstrip("\n")

            # --- Column number ------------------------------------------------------
            raw_col_no = safe_index(getattr(e, "column", None), len(display_line) + 1)

            # --- Unexpected character -----------------------------------------------
            unexpected_char = unicode_char_at(display_line, raw_col_no)

            # --- Expected token names ----------------------------------------------
            if hasattr(e, "expected") and e.expected:
                expected_tokens = e.expected
            elif hasattr(e, "allowed") and e.allowed:
                expected_tokens = e.allowed
            else:
                expected_tokens = []

            # Convert token names using TOKEN_NAME_MAP
            pretty_expected = []
            for tok in expected_tokens:
                pretty_expected.append(TOKEN_NAME_MAP.get(tok, tok))

            expected_str = ", ".join(sorted(pretty_expected)) if pretty_expected else "<unknown>"

            # --- Build the error block ---------------------------------------------
            caret_pos = max(0, raw_col_no - 1)
            err_msg = (
                f"{raw_line_no:<5}|{display_line}\n"
                f"     |{' ' * caret_pos}^\n\n"
                f"Unexpected token at line {raw_line_no} col {raw_col_no}: {unexpected_char}\n"
                f"Expected any: {expected_str}"
            )

            return SyntaxResult(tree=None, errors=[err_msg], log=err_msg)


# Optional helper to print tree nicely

def print_tree(tree):
    if tree is None:
        print("<empty tree>")
        return
    for line in tree.pretty().splitlines():
        print(line)

