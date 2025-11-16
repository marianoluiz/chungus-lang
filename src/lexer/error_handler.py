"""Error object definitions for the lexer.

    Each class captures:
    - the offending line (with trailing newline stripped for pretty printing)
    - the (line_index, col_index) tuple where the error occurred

    Stringification (__str__) renders a caret under the offending column.
"""
from src.constants import ATOMS, DELIMS

# Each error type below is a small object delivering a readable message.
# They store the offending line and a (line_index, col_index) tuple so the message
# can show the caret position for quick diagnostics in logs or GUI.

class UnknownCharError():
    """Raised when an unexpected character is encountered at top-level."""
    def __init__(self, line: str, position: tuple[int, int]):
        # keep raw for char extraction; keep printable (no trailing \n) for rendering
        self._raw_line = line
        self._line = line.rstrip('\n')
        self._position = position

    def __str__(self):
        line_no = self._position[0] + 1
        col = self._position[1]
        # Determine display char safely from the raw line
        if col >= len(self._raw_line):
            ch = '<EOF>'
        else:
            ch = '<EOL>' if self._raw_line[col] == '\n' else self._raw_line[col]
        caret_pos = min(col, len(self._line))
        error_message = f"Unknown Character / Delimeter: '{ch}'\n" \
                        f" {line_no:<5}|{self._line}\n" \
                         f"      |{' ' * caret_pos}^\n"
        return error_message

class DelimError():
    """Raised when a delimiter is invalid (missing or unexpected)."""
    def __init__(self, line: str, position: tuple[int, int], delims: list):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = f"Invalid Delimiter:\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' ' * self._position[1]}^\n"
        
        return error_message

class UnfinishedFloat():
    """Raised when a int / float literal is incorrect"""
    def __init__(self, line: str, position: tuple[int, int], delims: list):
        self._line = line.replace('\n', '')
        self._position = position
        self._delims = delims
    def __str__(self):
        error_message = f"Unfinished float literal: expected any {self._delims}\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class UnclosedString():
    """Raised when a string literal reaches EOF without a closing quote."""
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = f"String State Error\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class UnclosedComment():
    """Raised when a comment is not properly terminated."""
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = f"Comment State Error\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class UnexpectedEOF():
    """Raised at the root when input ends and no DFA transition matches."""
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = (
            "Unexpected EOF: No transition matched\n"
            f" {self._position[0]+1:<5}|{self._line}\n"
            f"      |{' '*self._position[1]}^\n"
        )
        return error_message