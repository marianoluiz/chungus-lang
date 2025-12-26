from dataclasses import dataclass

@dataclass
class Token:
    lexeme: str
    type: str
    line: int
    col: int

# Terminal token type names used by grammar
ID_T = 'id'
INT_LIT_T = 'int_literal'
FLOAT_LIT_T = 'float_literal'
STR_LIT_T = 'str_literal'
BOOL_LIT_T = 'bool_literal'
SKIP_TOKENS = {"whitespace", "newline", "comment"}