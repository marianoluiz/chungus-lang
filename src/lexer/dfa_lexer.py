"""
DFA-based lexer.

This module traverses a precomputed DFA transition table to convert source text
into raw lexemes, then builds a token stream with source positions.

- DFA definition: dfa_table.TRANSITION_TABLE
- Cursor tracked as (line_index, column_index)
- Error handling delegated to error_handler
"""

from src.constants import ATOMS
from ..constants.error_lexical import UnknownCharError, DelimError, UnexpectedEOF
from .dfa_table import TRANSITION_TABLE
from .token_builder import build_token_stream
from src.constants.token import Token

# State ranges used for semantic backtracking and classification.
KEYWORD_LAST_STATE = 87
SYMBOL_STATE_START = 88
SYMBOL_STATE_END = 131
MULTI_COMMENT_STATE_START = 132
MULTI_COMMENT_STATE_END = 141
FLOAT_START_STATE = 190
FLOAT_END_STATE = 241
STRING_STATE_START = 242
STRING_STATE_END = 245


class Lexer:
    """
    High-level wrapper around the DFA lexemizer.

    Public API:
    - start(): runs lexing and populates self.token_stream

    Workflow:
    - __init__: split input into lines and initialize cursor
    - start:    collect raw lexemes and their start positions
    - build_token_stream: classify lexemes into tokens
    """
    def __init__(self, source_text: str, debug: bool = False):
        """
        Initialize lexer with source text.

        Args:
            source_text: full program source as a single string
            debug: enable debug printing
        """
        # Convert incoming source string to lines and ensure newline markers
        source_text = source_text.splitlines(keepends=True)

        if not source_text:
            # For empty input, create a single empty line that ends with newline
            self._source_lines = ['\n']
        else:
            # add newline at end of statement
            if not source_text[-1].endswith('\n'):
                source_text[-1] = source_text[-1] + '\n'
            self._source_lines = source_text  # The source code as a list of string

        self._index = 0, 0                  # _index: tuple (line_index, column_index) """
        self._lexemes: list[str] = []       # collected lexeme strings (raw) """
        self.token_stream: list[Token] = []  # ((lexeme), (line_index, column_index)) - populated by build_token_stream()
        self.log = ""                       # textual log of errors (human readable)

        # Debug switch
        self._debug = debug

        # Useful debug print to see how source lines were split
        self._dbg('---- Splitted Source: ----')
        self._dbg(self._source_lines)

    def _dbg(self, msg: str):
        """Print debug message when debug mode is enabled."""
        if self._debug:
            print(msg)

    # TRACKING CHARACTERS
    def get_curr_char(self):
        """
        Return the current character under cursor or '\\0' for EOF sentinel.

        Edge cases:
        - When at/past the end of the final line, return '\\0'.
        - Otherwise, return the source character at the cursor.
        """
        if self._index[1] >= len(self._source_lines[-1]) and self._index[0] >= (len(self._source_lines) - 1):
            return "\0"

        return self._source_lines[self._index[0]][self._index[1]]

    def is_at_end(self):
        """True if current character is the EOF sentinel."""
        return self.get_curr_char() == "\0"

    def advance_cursor(self, count=1):
        """
        Advance the cursor by `count` characters.

        - Wraps to the next line when the end of the current line is reached.
        - No-op if already beyond the last character of the last line.
        """
        for i in range(count):
            # guard conditions to avoid IndexError
            if self._index[0] >= len(self._source_lines) and self._index[1] >= len(self._source_lines[0]):
                return

            # checks if the column (self._index[1]) is at or past the last valid index of the current line.
            # This checks if the current line (self._index[0]) is NOT the last line in the file.
            # If both are true: (we are at the end of a line, and it's not the last line)...
            if self._index[1] >= len(self._source_lines[self._index[0]]) - 1 and self._index[0] < len(self._source_lines)-1:
                self._index = min(
                    self._index[0] + 1, len(self._source_lines)), 0
            else:
                # move forward one column on same line
                self._index = self._index[0], self._index[1] + 1

    def reverse_cursor(self, count=1):
        """
        Move the cursor backward by `count` characters.

        Used by lexemize() to backtrack when a branch ends in an error or
        when a longer branch must fall back to an identifier path.
        """
        for i in range(count):
            # Is the cursor's column greater than 0
            if self._index[1] > 0:
                # The cursor moves one character backward on the same line.
                self._index = self._index[0], self._index[1] - 1

            # Is the line number greater than 0?
            elif self._index[0] > 0:
                # move to end of previous line
                self._index = max(
                    0, self._index[0] - 1), len(self._source_lines[self._index[0] - 1]) - 1

    def start(self):
        """
        Top-level lexing loop (collects lexemes + their start positions).

        After completion sets self.token_stream via build_token_stream.
        Errors are appended to self.log.
        """
        lexeme_positions = []

        while not self.is_at_end():
            curr_char = self.get_curr_char()
            start_pos = self._index

            if curr_char == ' ':
                self._lexemes.append(' ')
                lexeme_positions.append(start_pos)
                self.advance_cursor()
                continue
            if curr_char == '\n':
                self._lexemes.append(r'\n')
                lexeme_positions.append(start_pos)
                self.advance_cursor()
                continue

            lexeme = self.lexemize()

            if isinstance(lexeme, (UnknownCharError, DelimError, UnexpectedEOF)):
                self.log += str(lexeme) + '\n'

                # Delimiter errors do not consume input:
                # the same character must be re-lexed in a different context.
                if isinstance(lexeme, DelimError):
                    continue

                self.advance_cursor()
                continue

            # Normal lexeme
            self._lexemes.append(lexeme)
            lexeme_positions.append(start_pos)
        self.token_stream = build_token_stream(self._lexemes, lexeme_positions)

    def lexemize(self, curr_state: int = 0):
        """
        Recursive DFA traversal.

        Args:
            curr_state: current DFA state index

        Returns:
            - str: accumulated lexeme
            - tuple: reserved words or symbols (typed placeholder)
            - None: valid prefix that must fallback (e.g. keyword → identifier)
            - Error object: UnknownCharError / DelimError / UnexpectedEOF
        """
        # Get transitions from current state
        next_states = TRANSITION_TABLE[curr_state].next_states

        # Iterate through possible transitions, state is different from curr_state
        for state in next_states:
            curr_char = self.get_curr_char()

            # if curr_char to is not equal to the state character/s (from the branch of curr_state)
            if curr_char not in TRANSITION_TABLE[state].accepted_chars:

                if TRANSITION_TABLE[state].is_terminal:
                    # Keyword terminal + next char can extend into an identifier -> allow fallback (no error)
                    if state <= KEYWORD_LAST_STATE and curr_char in ATOMS['under_alpha_num']:
                        continue

                    # Otherwise delimiter invalid for this terminal
                    return DelimError(self._source_lines[self._index[0]], self._index, TRANSITION_TABLE[state].accepted_chars)

                # Branch not matched move to next branch; If no other branch, stop the loop (move to no transition matched if elses line 257)
                continue

            # MATCHED: matched character to a state in the branch
            self._dbg(
                f"{curr_state} -> {state}: {curr_char if len(TRANSITION_TABLE[state].next_states) > 0 else 'end state'}"
            )

            # END: If we matched a TOKEN and it is last state (If the state has no outgoing next_states) it is a terminal -> return sentinel lexeme (base of recursion to communicate "I hit a terminal")
            if len(TRANSITION_TABLE[state].next_states) == 0:
                # small heuristic: reserved word, symbols return an empty typed pair placeholder
                if state <= SYMBOL_STATE_END:
                    return ('', '')
                return ''  # other terminal marker

            # consume the current state in this branch and recurse deeper
            self.advance_cursor()
            # the matched state earlier would be used for the next character
            lexeme = self.lexemize(state)

            # lexeme may be various types: string, tuple, error object, or None
            # str: int, float, comment, string,
            # tuple: reserved words, symbols
            # DelimError: full token but wrong delimeter
            if type(lexeme) is str:
                return curr_char + lexeme
            if type(lexeme) is tuple:
                # tuple expected to carry structured information; combine and return
                # EX. show -> ('')('') -> ('w')('w') -> ('ow')('ow') -> ('how')('how') -> ('show')('show')
                return (curr_char + lexeme[0], curr_char + lexeme[0])
            if type(lexeme) is DelimError:
                return lexeme

            # If returned None from Lexeme and not a complete token and not an error, we should backtrack for reserved words to transition to id.
            # EX: shows -> line 4 -> 3 -> 2 -> 1
            if state <= KEYWORD_LAST_STATE:
                self.reverse_cursor()

            # I don't think this would ever get triggered since its upto 2 char only and delim error would move on and not revert
            if SYMBOL_STATE_START <= state <= SYMBOL_STATE_END:
                self.reverse_cursor()

            if FLOAT_START_STATE <= state <= FLOAT_END_STATE:
                self.reverse_cursor()

            if MULTI_COMMENT_STATE_START <= state <= MULTI_COMMENT_STATE_END:
                self.reverse_cursor()
            
            if STRING_STATE_START <= state <= STRING_STATE_END:
                self.reverse_cursor()

        # No transition matched.
        if curr_state == 0:
            if self.get_curr_char() == '\0':
                return UnexpectedEOF(self._source_lines[self._index[0]], self._index)
            # At root and nothing matched -> unknown character
            # Will return directly to start
            return UnknownCharError(self._source_lines[self._index[0]], self._index)
        
        # EX: Return None if 'shows' (since it dont match the keyword show and it has No error. It would most likely go to id)
        return None
