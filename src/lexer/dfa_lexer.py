from src.constants import ATOMS, DELIMS
from .error_handler import UnknownCharError, DelimError, UnclosedString, UnclosedComment, UnfinishedFloat, UnexpectedEOF
from .dfa_table import TRANSITION_TABLE
from .token_builder import build_token_stream

# Top-level DFA-based lexer. Produces a list of raw lexemes and then a token stream.
# The DFA itself is encoded in src/lexer/td.py as TRANSITION_TABLE and traversed by lexemize().
# Positions are tracked as a (line_index, col_index) tuple in self._index.

KEYWORD_LAST_STATE = 117
SYMBOL_STATE_START = 118
SYMBOL_STATE_END = 161
SYMBOL_LAST_STATE = SYMBOL_STATE_END
STRING_STATE_START = 224
STRING_STATE_END = 226
COMMENT_STATE_START = 162
COMMENT_STATE_END = 171
NUMERIC_LIT_START = 175

class Lexer:
    """High level wrapper around the DFA lexemizer.

    Workflow:
    - __init__: split the input into lines and initialize cursor
    - start:    iterate, snapshot start positions, and collect raw lexemes
    - build_token_stream: classify lexemes with their snapshot lexeme_positions
    """

    def __init__(self, source_text: str):
        # Convert incoming source string to lines and ensure newline markers
        source_text = source_text.splitlines()

        if not source_text:
            # for empty input error handling
            self._source_lines = ['']
        else:
            # Preserve newline at the end of each line except possibly last (keeps positions simple); If it's not the last line, value is line + '\n'
            self._source_lines = [line + '\n' if x != len(source_text) - 1 else line for x, line in enumerate(source_text)]
        """ The source code as a list of string"""

        self._index = 0, 0
        """ _index: tuple (line_index, column_index) """

        self._lexemes: list[str] = []
        """ collected lexeme strings (raw) """

        self.token_stream: list[dict] = []
        """ token_stream will be populated by token.build_token_stream(...) after lexing. This would be ((lexeme), (line_index, column_index)) """

        self.log = ""
        """ textual log of errors (human readable) """

        # Useful debug print to see how source lines were split
        print('---- Splitted Source: ----')
        print(self._source_lines)

    ## TRACKING CHARACTERS
    def get_curr_char(self):
        """Return the current character under cursor or \\0 for EOF sentinel.

        Edge cases:
        - When at/past the end of the final line, return \\0 to avoid IndexError.
        - Otherwise, return the source character at the current cursor.
        """
        if self._index[1] >= len(self._source_lines[-1]) and self._index[0] >= (len(self._source_lines) - 1):
            return "\0"
        
        return self._source_lines[self._index[0]][self._index[1]]

    def is_at_end(self):
        """True if current character is the EOF sentinel."""
        return self.get_curr_char() == "\0"

    def advance_cursor(self, count = 1):
        """Advance the cursor by `count` characters.

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
                self._index = min(self._index[0] + 1, len(self._source_lines)), 0
            else:
                # move forward one column on same line
                self._index = self._index[0], self._index[1] + 1

    def reverse_cursor(self, count = 1):
        """Move the cursor backward by `count` characters.

        Used by lexemize() to backtrack a single character when a deeper branch
        ends in an error or needs to yield control back to an identifier path.
        """
        for i in range(count):
            # Is the cursor's column greater than 0
            if self._index[1] > 0:
                # The cursor moves one character backward on the same line.
                self._index = self._index[0], self._index[1] - 1

            # Is the line number greater than 0?
            elif self._index[0] > 0:
                # move to end of previous line
                self._index = max(0, self._index[0] - 1), len(self._source_lines[self._index[0] - 1]) - 1

    def start(self):
        """Top-level lexing loop (collects lexemes + their start positions)."""
        lexeme_positions = []

        while not self.is_at_end():
            curr_char = self.get_curr_char()

            # Skip whitespace/newline entirely (no position recorded)
            if curr_char in (' ', '\n'):
                self.advance_cursor()
                continue

            start_pos = self._index
            lexeme = self.lexemize()

            if isinstance(lexeme, (UnknownCharError, DelimError, UnfinishedFloat,
                                   UnclosedString, UnclosedComment, UnexpectedEOF)):
                self.log += str(lexeme) + '\n'
                if isinstance(lexeme, UnknownCharError):
                    self.advance_cursor()
                continue

            # Normal lexeme
            self._lexemes.append(lexeme)
            lexeme_positions.append(start_pos)

        self.token_stream = build_token_stream(self._lexemes, lexeme_positions)

    def lexemize(self, curr_state: int = 0):
        """Recursive DFA-driven lexeme extractor.

            Strategy:
            - For each outgoing `state` from the current node, check if the current
            character is in TRANSITION_TABLE[state].chars.
            - If matched:
                - If `state` has no next_states, return a terminal sentinel:
                '' for "keep building", or ('','') for typed placeholders (symbols).
                - Otherwise consume 1 char, recurse into `state`, and combine the result.
            - If unmatched:
                - When TRANSITION_TABLE[state] is an accepting terminal: validate delimiters
                for keywords to ensure proper token boundaries.
                - For EOF while in certain subgraphs (STRING/COMMENT), return specific
                error objects (UnclosedString/UnclosedComment).
                - If in NUMERIC_LIT_START and still non-accepting, raise UnfinishedFloat.
            - If none of the next_states match:
                - At root (curr_state == 0), return UnknownCharError or UnexpectedEOF.
                - In symbol subgraph, return DelimError with expected chars.
                - Otherwise return None to let caller treat as identifier continuation.
        """
        # Get transitions from current state
        next_states = TRANSITION_TABLE[curr_state].next_states

        # Iterate through possible transitions
        for state in next_states:
            curr_char = self.get_curr_char()

            # if curr_char to is not equal to the state character/s (from the branch of curr_state)
            if curr_char not in TRANSITION_TABLE[state].accepted_chars:
                if TRANSITION_TABLE[state].is_terminal:
                    # if state is not id (under_alpha_num) and its a keyword, its a delimeter error
                    if curr_char not in [*ATOMS['under_alpha_num']] and state <= KEYWORD_LAST_STATE:
                        return DelimError(self._source_lines[self._index[0]], self._index, TRANSITION_TABLE[state].accepted_chars)

                # EOF reached while not in an accepting state -> specific error types
                if curr_char == '\0' and not TRANSITION_TABLE[state].is_terminal:
                    if state >= STRING_STATE_START and state <= STRING_STATE_END:
                        return UnclosedString(self._source_lines[self._index[0] - 1], self._index)

                    if state >= COMMENT_STATE_START and state <= COMMENT_STATE_END:
                        return UnclosedComment(self._source_lines[self._index[0]-1], self._index)


                # Special check for unfinished numeric literal 
                if state == NUMERIC_LIT_START and len(next_states) == 1 and not TRANSITION_TABLE[state].is_terminal:
                    return UnfinishedFloat(self._source_lines[self._index[0]], self._index, TRANSITION_TABLE[state].accepted_chars)

                # print(curr_char, 'char being compared to', TRANSITION_TABLE[state].accepted_chars)
                # print('goes continue')
                continue # Branch not matched move to next branch; If no other branch, stop the loop.

            # print('MATCHED curr_char to a state in an appropriate branch')

            # MATCHED: matched character to a state in the branch
            print(f"{curr_state} -> {state}: {curr_char if len(TRANSITION_TABLE[state].next_states) > 0 else 'end state'}")

            # END: If we matched a character and it is last state (If the state has no outgoing next_states) it is a terminal -> return sentinel lexeme (base of recursion to communicate "I hit a terminal")
            if len(TRANSITION_TABLE[state].next_states) == 0:
                # small heuristic: reserved word, symbols return an empty typed pair placeholder
                if state <= SYMBOL_LAST_STATE:
                    return ('','') 
                
                return ''  # other terminal marker

            # consume the current state in this branch and recurse deeper
            self.advance_cursor()
            lexeme = self.lexemize(state) # the matched state earlier would be used for the next character
            # print('lexeme: ', lexeme, 'state', state)

            # lexeme may be various types: string, tuple, error object, or None
            if type(lexeme) is str:
                return curr_char + lexeme
            if type(lexeme) is tuple:
                # tuple expected to carry structured information; combine and return
                # show -> ('')('') -> ('w')('w') -> ('ow')('ow') -> ('how')('how') -> ('show')('show')
                return (curr_char + lexeme[0], curr_char + lexeme[0])
            if type(lexeme) is DelimError:
                return lexeme
            if type(lexeme) is UnfinishedFloat:
                return lexeme
            if type(lexeme) is UnclosedString:
                # unread the char we consumed before returning the UnclosedString error
                self.reverse_cursor()
                return UnclosedString(self._source_lines[self._index[0]], self._index)
        
            # If returned None from Lexeme and not a complete token and not an error, we should backtrack for reserved words to transition to id. 
            # EX: shows -> line 4 -> 3 -> 2 -> 1
            if state <= KEYWORD_LAST_STATE:
                self.reverse_cursor()

        # print('ended loop')

        # No transition matched. 
        if curr_state == 0:
            # At root and nothing matched -> unknown character        
            if self.get_curr_char() == '\0':
                return UnexpectedEOF(self._source_lines[self._index[0]], self._index)
            
            return UnknownCharError(self._source_lines[self._index[0]], self._index)
        if curr_state >= SYMBOL_STATE_START and curr_state <= SYMBOL_STATE_END:
            # These TRANSITION_TABLE correspond to delimiters; return delimiter error with expected accepted_chars
            return DelimError(self._source_lines[self._index[0]], self._index, TRANSITION_TABLE[state].accepted_chars)
        
        # EX: Return None if 'shows' (since it dont match the keyword show and it has No error. It would most likely go to id)
        # print('returned None')
        return None