"""
Lexer module (src/lexer/lexer.py)

This module implements a recursive DFA-based lexemizer for the Chungus
project. The code is intentionally written to follow a transition-table
approach where `STATES` (from `td.py`) describes allowed transitions.

Key concepts:
- Source is stored as a list of lines (each line ends with '\n' except possibly last).
- _index is a tuple (line_index, col_index) representing the current cursor.
- _lexemes collects raw lexeme strings (or special markers like ' ' and r'\n')
- metadata is a list of cursor positions saved during tokenization (line,col) used by `tokenize`.
- lexemize is implemented recursively: it explores possible transitions from a state,
  consuming characters and returning either a string/tuple (the lexeme), or one of the
  error objects from `error_handler`.
"""
from constants import ATOMS,DELIMS
from .error_handler import UnknownCharError, DelimError, UnclosedString, UnclosedComment, UnfinishedFloat, UnexpectedEOF
from .td import STATES
from .token import tokenize


KEYWORD_LAST_STATE = 117
SYMBOL_STATE_START = 118
SYMBOL_STATE_END = 161
SYMBOL_LAST_STATE = SYMBOL_STATE_END
STRING_STATE_START = 224
STRING_STATE_END = 226
COMMENT_STATE_START = 162
COMMENT_STATE_END = 171
NUMERIC_LIT_START = 172


# Lexer.token_stream stores lexemes and tokens
# Lexer.log stores the error log

class Lexer:
    """High level wrapper around the DFA lexemizer.

    Instantiate with source text and call `start()` to build self._lexemes and self.token_stream.
    The internal lexemizer is state-driven and returns special error objects when it encounters
    problematic input (unclosed string, delim errors, etc.).
    """

    def __init__(self, source: str):
        # Convert incoming source string to lines and ensure newline markers
        source = source.splitlines()
        # Preserve newline at the end of each line except possibly last (keeps positions simple)
        # If it's not the last line, value is line + '\n'

        if not source:
            self._source = ['']
        else:
            self._source = [line + '\n' if x != len(source) - 1 else line for x, line in enumerate(source)]
        """ The source code as a list of string"""

        self._index = 0, 0
        """ _index: tuple (line_index, column_index) """

        self._lexemes: list[str] = []
        """ collected lexeme strings (raw) """

        self.token_stream: list[dict] = []
        """ token_stream will be populated by token.tokenize(...) after lexing. This would be ((lexeme), (line_index, column_index)) """

        self.log = ""
        """ textual log of errors (human readable) """

        # Useful debug print to see how source lines were split
        print('---- Splitted Source: ----')
        print(self._source)

    ## TRACKING CHARACTERS
    def get_curr_char(self):
        """Return the current character under cursor or \0 for EOF sentinel.

        Note: when at the final characters of the final line we treat further access
        as EOF to avoid IndexError.
        """
        if self._index[1] >= len(self._source[-1]) and self._index[0] >= (len(self._source) - 1):
            return "\0"
        
        return self._source[self._index[0]][self._index[1]]

    def is_EOF(self):
        """Convenience check whether current char is EOF sentinel. This returns True or False"""
        return self.get_curr_char() == "\0"

    def advance(self, count = 1):
        """Advance cursor by `count` characters, updating line/col.

        This method properly moves to next line when end-of-line is reached.
        """
        for i in range(count):
            # guard conditions to avoid IndexError
            if self._index[0] >= len(self._source) and self._index[1] >= len(self._source[0]):
                return
            
            # checks if the column (self._index[1]) is at or past the last valid index of the current line.
            # This checks if the current line (self._index[0]) is NOT the last line in the file.
            # If both are true: (we are at the end of a line, and it's not the last line)...
            if self._index[1] >= len(self._source[self._index[0]]) - 1 and self._index[0] < len(self._source)-1:
                self._index = min(self._index[0] + 1, len(self._source)), 0
            else:
                # move forward one column on same line
                self._index = self._index[0], self._index[1] + 1

    def reverse(self, count = 1):
        """Move the cursor backwards by `count` characters.

        Used by lexemize to backtrack when a deeper branch doesn't produce a token.
        """
        for i in range(count):
            # Is the cursor's column greater than 0
            if self._index[1] > 0:
                # The cursor moves one character backward on the same line.
                self._index = self._index[0], self._index[1] - 1

            # Is the line number greater than 0?
            elif self._index[0] > 0:
                # move to end of previous line
                self._index = max(0, self._index[0] - 1), len(self._source[self._index[0] - 1]) - 1

    def start(self):
        """Top-level lexing loop.

        Iterates the input character-by-character and uses `lexemize()` to extract lexemes.
        Each lexeme has corresponding metadata (cursor position at its start) appended to `metadata`.
        After lexemes are collected, `tokenize` is called to produce `self.token_stream`.
        """

        # Store the starting position (line, column) of every lexeme. This is crucial for error messages later.
        metadata = []
        
        while not self.is_EOF():
            # Store the start position for the next lexeme, it "bookmarks" the current cursor position (self._index) and saves it.
            metadata.append(self._index)
            curr_char = self.get_curr_char()

            # Gets the character at the current cursor position.
            # whitespace and newline are recorded as special lexemes to preserve positional info
            # TODO: use to check if there is error in spaces and newline
            if curr_char == ' ':
                self._lexemes.append(' ')
                self.advance()
                continue
            elif curr_char == '\n':
                self._lexemes.append(r'\n')
                self.advance()
                continue

            # attempt to lexemize starting at current index
            lexeme = self.lexemize()

            # print('lexeme: ', lexeme)

            # lexemize returns either:
            # - a raw string (lexeme)
            # - a tuple for special cases
            # - one of the error objects defined in error_handler
            if type(lexeme) is UnknownCharError:
                print(lexeme)
                self.log += str(lexeme) + '\n'
                self.advance()
            elif type(lexeme) is DelimError:
                # delimiter errors: log but continue (may be recoverable)
                print(lexeme)
                self.log += str(lexeme) + '\n'
                continue
            elif type(lexeme) is UnfinishedFloat:
                print(lexeme)
                self.log += str(lexeme) + '\n'
                continue
            elif type(lexeme) in [UnclosedString]:
                # unclosed string -> log and advance to EOF to stop processing
                print(lexeme)
                self.log += str(lexeme) + '\n'
                self.advance(len(''.join(self._source)))
            elif type(lexeme) is UnclosedComment:
                print(lexeme)
                self.log += str(lexeme) + '\n'
                self.advance(len(''.join(self._source)))
            elif type(lexeme) is UnexpectedEOF:
                # root-level EOF with no transition matched
                print(lexeme)
                self.log += str(lexeme) + '\n'
                self.advance(len(''.join(self._source)))
            else:
                # normal lexeme: append to lexeme list. 
                # if returned is None (for ids), a complete Lexeme (keyword, str, int, float lit)
                # print('appended lexeme')
                self._lexemes.append(lexeme)

        # Convert collected lexemes + metadata into token_stream via tokenize()
        self.token_stream = tokenize(self._lexemes, metadata)

    def lexemize(self, curr_state: int = 0):
        """Recursive DFA-driven lexeme extractor.

        Algorithm:
        - Look up possible branch states from STATES[curr_state].branches
        - For each candidate state:
            - if current char is allowed in state's chars, consume and recurse into child's branches
            - if child is terminal (no branches), return appropriate lexeme marker/value
            - handle special cases: unclosed string/comment, unfinished numeric literal, reserved-word delim, etc.
        - If no branch matched:
            - when at root state, return UnknownCharError
            - for certain mid-states return DelimError or other error objects
        """
        # Get transitions from current state
        branches = STATES[curr_state].branches

        # Iterate through possible transitions
        for state in branches:
            curr_char = self.get_curr_char()

            # if curr_char to is not equal to the state character/s (from the branch of curr_state)
            if curr_char not in STATES[state].chars:
                if STATES[state].isEnd:
                    # special handling for reserved words and ID delimiting
                    
                    # TODO CHECK
                    # if state != branches[-1] and state >= KEYWORD_LAST_STATE:
                    #     continue

                    # if state is not id (under_alpha_num) and its a keyword, its a delimeter error
                    if curr_char not in [*ATOMS['under_alpha_num']] and state <= KEYWORD_LAST_STATE:
                        return DelimError(self._source[self._index[0]], self._index, STATES[state].chars)

                # EOF reached while not in an accepting state -> specific error types
                if curr_char == '\0' and not STATES[state].isEnd:
                    if state >= STRING_STATE_START and state <= STRING_STATE_END:
                        return UnclosedString(self._source[self._index[0] - 1], self._index)

                    if state >= COMMENT_STATE_START and state <= COMMENT_STATE_END:
                        return UnclosedComment(self._source[self._index[0]-1], self._index)


                # Special check for unfinished numeric literal 
                if state == NUMERIC_LIT_START and len(branches) == 1 and not STATES[state].isEnd:
                    return UnfinishedFloat(self._source[self._index[0]], self._index, STATES[state].chars)

                # print(curr_char, 'char being compared to', STATES[state].chars)
                # print('goes continue')
                continue # Branch not matched move to next branch; If no other branch, stop the loop.

            # print('MATCHED curr_char to a state in an appropriate branch')

            # MATCHED: matched character to a state in the branch
            print(f"{curr_state} -> {state}: {curr_char if len(STATES[state].branches) > 0 else 'end state'}")

            # END: If we matched a character and it is last state (If the state has no outgoing branches) it is a terminal -> return sentinel lexeme (base of recursion to communicate "I hit a terminal")
            if len(STATES[state].branches) == 0:
                # small heuristic: reserved word, symbols return an empty typed pair placeholder
                if state <= SYMBOL_LAST_STATE:
                    return ('','') 
                return ''  # other terminal marker

            # consume the current state in this branch and recurse deeper
            self.advance()
            lexeme = self.lexemize(state) # the matched state earlier would be used for the next character
            # print('lexeme: ', lexeme, 'state', state)

            # lets say we are 4 deep in the recursion call
            # keyword: shows
            # s would not be consumed and it starts returning None
            # in the first return (w), It continue to check the branch of 'w' until its done, after that return none
            # in the second return (o), It continue to check the branch of 'o' until its done, after that return none
            # in the third return (h), It continue to check the branch of 'h' until its done, after that return none
            # in the fourth return (s), It continue to check the branch of 's' until its done, after that return none
            # so we are back in the initial lexemize call (state 0), we continue starting from what we left (after the checking of 's' ('show' state branch)) so the next 's' would be the identifier state branch. thats how we move from reserved word to id.


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
                self.reverse()
                return UnclosedString(self._source[self._index[0]], self._index)
        
            # If returned None from Lexeme and not a complete token and not an error, we should backtrack for reserved words to transition to id. 
            # EX: shows -> line 4 -> 3 -> 2 -> 1
            if state <= KEYWORD_LAST_STATE:
                self.reverse()

        # print('ended loop')

        # No transition matched. 
        if curr_state == 0:
            # At root and nothing matched -> unknown character        
            if self.get_curr_char() == '\0':
                return UnexpectedEOF(self._source[self._index[0]], self._index)
            
            return UnknownCharError(self._source[self._index[0]], self._index)
        if curr_state >= SYMBOL_STATE_START and curr_state <= SYMBOL_STATE_END:
            # These states correspond to delimiters; return delimiter error with expected chars
            return DelimError(self._source[self._index[0]], self._index, STATES[state].chars)
        
        # EX: Return None if 'shows' (since it dont match the keyword show and it has No error. It would most likely go to id)
        # print('returned None')
        return None