""" This file is used for the error handling of the lexer """
from constants import ATOMS

def Test3():
    print("Test for Error Handling")

# Each error type below is a small object delivering a readable message.
# They store the offending line and a (line_index, col_index) tuple so the message
# can show the caret position for quick diagnostics in logs or GUI.

class UnknownCharError():
    """Raised when an unexpected character is encountered at top-level."""
    def __init__(self, line: str, position: tuple[int, int]):
        # store a version of the line without newline for pretty printing
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = f"unknown character: '{self._line[self._position[1]]}'\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class DelimError():
    """Raised when a delimiter is invalid (missing or unexpected)."""
    def __init__(self, line: str, position: tuple[int, int], delims: list):
        self._line = line.replace('\n', '')
        self._position = position
        # shrink large delim sets for readability
        self._delims = shorten_delims(list(delims))

    def __str__(self):
        error_message = f"Invalid Delimiter:\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class UnfinishedAndamhie():
    """Raised when a numeric/andamhie literal is syntactically incomplete."""
    def __init__(self, line: str, position: tuple[int, int], delims: list):
        self._line = line.replace('\n', '')
        self._position = position
        self._delims = shorten_delims(list(delims))

    def __str__(self):
        error_message = f"Unfinished andamhie literal: expected any {self._delims}\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class UnclosedString():
    """Raised when a string literal reaches EOF without a closing quote."""
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = f"Unclosed string: expected '\"'\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

class UnclosedComment():
    """Raised when a comment is not properly terminated."""
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position

    def __str__(self):
        error_message = f"unclosed comment: expected '^/'\n" \
                        f" {self._position[0]+1:<5}|{self._line}\n" \
                        f"      |{' '*self._position[1]}^\n"
        
        return error_message

def shorten_delims(delims: list):
    """Utility to compact delim lists by replacing full ranges with readable spans.

    Example: if all alphabet letters are present, they are replaced with 'A-Z'/'a-z'
    to keep error messages concise.
    """
    if all(d in delims for d in ATOMS['all_alphabet']):
        for d in ATOMS['all_alphabet']:
            if d in delims:
                delims.remove(d)
        delims.append('A-Z')
        delims.append('a-z')

    if all(d in delims for d in ATOMS['all_num']):
        for d in ATOMS['all_num']:
            if d in delims:
                delims.remove(d)
        delims.append('0-9')

    return delims

if __name__ == '__main__':
    error_type = "UnknownError"
    line = '      serve("Hello, World"); #'
    position = (6, 29)
    print(UnknownCharError(line, position))