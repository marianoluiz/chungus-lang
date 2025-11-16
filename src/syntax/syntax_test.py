class UnexpectedError():
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        # Ensure 1-based and safe caret placement
        line_no = max(1, int(self._position[0]))
        col_no = max(1, int(self._position[1]))
        error_message = f"\n{line_no:<5}|{self._line}\n" \
                        f"     |{' '*(col_no-1)}^\n"
        return error_message


from lark import Lark, UnexpectedInput
from src.lexer.dfa_lexer import Lexer

TOKEN_NAME_MAP = {
    # --- Logical Operators ---
    'AND': 'and',
    'OR': 'or',
    'NOT': '!',
    
    # --- Boolean Literals / Keywords ---
    'TRUE': 'true',
    'FALSE': 'false',
    
    # --- I/O and System Commands ---
    'READ': 'read',
    'SHOW': 'show',
    'CLR': 'clr',
    'EXIT': 'exit',
    
    # --- Control Flow Keywords ---
    'IF': 'if',
    'ELIF': 'elif',
    'ELSE': 'else',
    'WHILE': 'while',
    'FOR': 'for',
    'IN': 'in',
    'RANGE': 'range',
    
    # --- Function Keywords ---
    'FN': 'fn',
    'RET': 'ret',
    
    # --- Error Handling Keywords ---
    'TRY': 'try',
    'FAIL': 'fail',
    'ALWAYS': 'always',
    
    # --- Utility / Placeholder ---
    'TODO': 'todo',
    
    # --- Array Manipulation Keywords ---
    'ARRAY_ADD': 'array_add',
    'ARRAY_REMOVE': 'array_remove',
    
    # --- Unary Operators (Suffixes) ---
    'UN_PLUS': '++',
    'UN_MINUS': '--',
    
    # --- Comparison / Equality Operators ---
    'EQ_EQ': '==',
    'NOT_EQ': '!=',
    'GT': '>',
    'LT': '<',
    'GE': '>=',
    'LE': '<=',
    
    # --- Arithmetic Operators (Explicit) ---
    'FLOORDIV': '//',
    'POW': '**',
    
    # --- Whitespace/Utility (Often requires special handling) ---
    'NEWLINE': r'\r?\n'  # Using the regex from your grammar
}

# Load grammar (from cfg_lark file)
with open("src/constants/cfg_lark", "r", encoding="utf-8") as f:
    _GRAMMAR = f.read()

# Build Lark parser 
_PARSER = Lark(_GRAMMAR, parser="earley", propagate_positions=True, maybe_placeholders=False)

class SyntaxResult:
    def __init__(self, tree=None, errors=None, log=""):
        self.tree = tree
        self.errors = errors or []
        self.log = log

class Parser:
    def parse(self, source: str) -> SyntaxResult:
        print('source: ', source, 'newline?')
        lex = Lexer(source)
        lex.start()
        
        try:
            tree = _PARSER.parse(source)
            return SyntaxResult(tree=tree, errors=[], log="Parse successful.")
        
        except UnexpectedInput as e:
            # Robustly determine offending line and 1-based column
            lines = source.splitlines(keepends=True) or ['']

            # Prefer e.get_line() when available and non-empty
            try:
                raw_line = e.get_line() or ""
            except Exception:
                raw_line = ""

            if raw_line:
                # strip trailing newline for display
                line_text = raw_line.rstrip('\n')
                # Lark's e.line/e.column may still be set; prefer them if sane
                line_no = e.line if getattr(e, "line", 0) and e.line > 0 else next((i+1 for i, ln in enumerate(lines) if ln.rstrip('\n') == line_text), len(lines))
                col_no = e.column if getattr(e, "column", 0) and e.column > 0 else 1
            else:
                # EOF or empty get_line -> map to last line end
                line_no = e.line if getattr(e, "line", 0) and e.line > 0 else len(lines)
                # pick the raw source line (may include trailing newline)
                raw_source_line = lines[line_no - 1] if 1 <= line_no <= len(lines) else ""
                line_text = raw_source_line.rstrip('\n')
                # column: place caret at end-of-line (1-based)
                col_no = (len(line_text) + 1) if raw_source_line != "" else 1

            # Determine unexpected char/token for message
            if 1 <= col_no <= len(line_text):
                unexpected_char = line_text[col_no - 1]
            elif col_no == len(line_text) + 1:
                unexpected_char = "<EOL>"
            else:
                unexpected_char = "<EOF>"

            # Support both UnexpectedToken (.expected) and UnexpectedCharacters (.allowed)
            if hasattr(e, "expected") and e.expected:
                expected_set = e.expected
            elif hasattr(e, "allowed") and e.allowed:
                expected_set = e.allowed
            else:
                expected_set = []

            expected = ", ".join(sorted(expected_set)) if expected_set else "<unknown>"

            msg = (
                f"Unexpected token at line {line_no} column {col_no}: {unexpected_char}\n"
                f"Expected any: {expected}"
            )

            err_block = str(UnexpectedError(line_text, (line_no, col_no)))
            full_log = err_block + '\n' + msg
            return SyntaxResult(tree=None, errors=[full_log], log=full_log)

# Simple utility to pretty print the tree (optional)
def print_tree(tree):
    for line in tree.pretty().splitlines():
        print(line)