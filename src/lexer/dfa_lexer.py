from src.constants import ATOMS, DELIMS
from .error_handler import UnknownCharError, DelimError, UnclosedString, UnclosedComment, UnfinishedFloat, UnexpectedEOF
from .dfa_table import TRANSITION_TABLE
from .token_builder import build_token_stream

# Top-level DFA-based lexer. Produces a list of raw lexemes and then a token stream.
# The DFA itself is encoded in src/lexer/td.py as TRANSITION_TABLE and traversed by lexemize().
# Positions are tracked as a (line_index, col_index) tuple in self._index.

KEYWORD_LAST_STATE = 121
SYMBOL_STATE_START = 122
SYMBOL_STATE_END = 165
SYMBOL_LAST_STATE = SYMBOL_STATE_END
STRING_STATE_START = 230
STRING_STATE_END = 233
MULTI_COMMENT_STATE_START = 169
MULTI_COMMENT_STATE_END = 174
FLOAT_DOT_STATE = 217

class Lexer:
    """High level wrapper around the DFA lexemizer.

    Workflow:
    - __init__: split the input into lines and initialize cursor
    - start:    iterate, snapshot start positions, and collect raw lexemes
    - build_token_stream: classify lexemes with their snapshot lexeme_positions
    """

    def __init__(self, source_text: str):
        # Convert incoming source string to lines and ensure newline markers
        source_text = source_text.splitlines(keepends=True)

        if not source_text:
            # For empty input, create a single empty line that ends with newline
            self._source_lines = ['\n']
        else:
            # add newline at end of statement
            if not source_text[-1].endswith('\n'):
                source_text[-1] = source_text[-1] + '\n'
            self._source_lines = source_text
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

    # TRACKING CHARACTERS
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

    def advance_cursor(self, count=1):
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
                self._index = min(
                    self._index[0] + 1, len(self._source_lines)), 0
            else:
                # move forward one column on same line
                self._index = self._index[0], self._index[1] + 1

    def reverse_cursor(self, count=1):
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
                self._index = max(
                    0, self._index[0] - 1), len(self._source_lines[self._index[0] - 1]) - 1

    def start(self):
        """Top-level lexing loop (collects lexemes + their start positions)."""
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

            if isinstance(lexeme, (UnknownCharError, DelimError, UnfinishedFloat,
                                   UnclosedString, UnclosedComment, UnexpectedEOF)):
                self.log += str(lexeme) + '\n'

                # For delimiter errors: DO NOT skip the character.
                if isinstance(lexeme, DelimError):
                    # Do not advance cursor — retry lexing this character
                    continue
                # For an unfinished float after '.', do not skip the following delimiter
                if isinstance(lexeme, UnfinishedFloat):
                    continue

                # Do not advance; newline will be tokenized in next iteration
                if isinstance(lexeme, UnclosedString):
                    continue

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

                # Newline / EOL inside a string subgraph -> unclosed string
                if curr_char == '\n' and (curr_state >= STRING_STATE_START and curr_state <= STRING_STATE_END):
                    return UnclosedString(self._source_lines[self._index[0]], self._index)

                # EOF / newline inside an unterminated multiline comment: point caret at last char before newline/EOF
                if (curr_char == '\n' or curr_char == '\0') and (curr_state >= MULTI_COMMENT_STATE_START and curr_state <= MULTI_COMMENT_STATE_END):
                    line_idx, col_idx = self._index
                    err_pos = (line_idx, max(0, col_idx ))
                    return UnclosedComment(self._source_lines[line_idx], err_pos)

                # print(curr_char, 'char being compared to', TRANSITION_TABLE[state].accepted_chars)
                # print('goes continue')
                # Branch not matched move to next branch; If no other branch, stop the loop.
                continue

            # print('MATCHED curr_char to a state in an appropriate branch')

            # MATCHED: matched character to a state in the branch
            print(
                f"{curr_state} -> {state}: {curr_char if len(TRANSITION_TABLE[state].next_states) > 0 else 'end state'}")

            # END: If we matched a character and it is last state (If the state has no outgoing next_states) it is a terminal -> return sentinel lexeme (base of recursion to communicate "I hit a terminal")
            if len(TRANSITION_TABLE[state].next_states) == 0:
                # small heuristic: reserved word, symbols return an empty typed pair placeholder
                if state <= SYMBOL_LAST_STATE:
                    return ('', '')

                return ''  # other terminal marker

            # consume the current state in this branch and recurse deeper
            self.advance_cursor()
            # the matched state earlier would be used for the next character
            lexeme = self.lexemize(state)
            # print('lexeme: ', lexeme, 'state', state)

            # lexeme may be various types: string, tuple, error object, or None
            if type(lexeme) is str:
                return curr_char + lexeme
            if type(lexeme) is tuple:
                # tuple expected to carry structured information; combine and return
                # EX. show -> ('')('') -> ('w')('w') -> ('ow')('ow') -> ('how')('how') -> ('show')('show')
                return (curr_char + lexeme[0], curr_char + lexeme[0])
            if type(lexeme) is DelimError:
                return lexeme
            if type(lexeme) is UnclosedString:
                return lexeme
            if type(lexeme) is UnclosedComment:
                return lexeme
            if type(lexeme) is UnfinishedFloat:
                return lexeme

            # If returned None from Lexeme and not a complete token and not an error, we should backtrack for reserved words to transition to id.
            # EX: shows -> line 4 -> 3 -> 2 -> 1
            if state <= KEYWORD_LAST_STATE:
                self.reverse_cursor()

        # print('ended loop')




        # No transition matched.
        # --- Added unfinished-float detection ---
        # We are at the state AFTER consuming '.' (state 218); cursor sits on the next char.
        # If that next char is a delimiter (no digit consumed), raise UnfinishedFloat.
        if curr_state == FLOAT_DOT_STATE:
            curr_char = self.get_curr_char()
            if curr_char not in ATOMS['all_num']:
                line_idx, col_idx = self._index
                err_pos = (line_idx, col_idx)
                return UnfinishedFloat(self._source_lines[line_idx], err_pos, list(ATOMS['all_num']))


        if curr_state == 0:
            if self.get_curr_char() == '\0':
                # At root and nothing matched -> unknown character
                return UnexpectedEOF(self._source_lines[self._index[0]], self._index)

            return UnknownCharError(self._source_lines[self._index[0]], self._index)
        if curr_state >= SYMBOL_STATE_START and curr_state <= SYMBOL_STATE_END:
            # These TRANSITION_TABLE correspond to delimiters; return delimiter error with expected accepted_chars
            return DelimError(self._source_lines[self._index[0]], self._index, TRANSITION_TABLE[curr_state].accepted_chars)

        # EX: Return None if 'shows' (since it dont match the keyword show and it has No error. It would most likely go to id)
        return None
