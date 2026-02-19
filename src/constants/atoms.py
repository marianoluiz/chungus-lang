"""Character sets (atoms) used to build DFA state acceptance lists.

Groups:
- Base alphabets and digits
- ASCII subsets for strings and comments
- Composite groups (alpha_num, under_alpha_num) used by identifiers
- Operator categories, used to define delimiter sets in constants/delims.py
"""

ATOMS = {
    # --- Base Atoms ---
    'alphabet_low': set('abcdefghijklmnopqrstuvwxyz'),
    'alphabet_up': set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    'all_num': set('0123456789'),

    # --- Composite Atoms ---
    'all_alphabet': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    'alpha_num': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
    'under_alpha_num': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),

    # --- ASCII subsets for strings/comments ---
    # - includes backslash for escapes
    # - does NOT include raw newline
    'string_ascii': {
        ' ', '!', '#', '$', '"', '%', '&', '(', ')', '*', '+', ',', '-', '.', '/', 
        ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~','\n',
        *set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    },
    'single_comment_ascii': {
        ' ', '!', '$', '%', '&', '"', "'", '(', ')', '*', '+', ',', '-', '.', '/', 
        ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', ' ',
        *set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    },

    # - includes raw newline
    'multiline_comment_ascii': {
        ' ', '!', '$', '%', '&', '"', "'", '(', ')', '*', '+', ',', '-', '.', '/', 
        ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', '\n',
        *set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    },
    
    # --- Operator & Delimiter Base Sets ---
    'arithmetic_op': {'+', '-', '*', '/', '%'},
    'relational_op': {'=', '!', '<', '>'},
    'logical_and_or_op': {'a', 'o'},
    'logical_not_op': {'!'},
    'assignment_op': {'='},
    'unary_negative_op': {'~'},
    'header_terminator': {':'},
}

