"""Delimiter sets used by accepting states to validate token boundaries.

Categories:
- inline_delim: space-like separators usable mid-statement
- stmt_delim: separators that can end a statement (includes newline)
- id_delim: characters that can legally follow an identifier
- dtype_lit_delim: characters that can follow a type or literal
- method_delim, paren/bracket open/close, comma, assign_op, etc.
"""

from .atoms import ATOMS

INLINE_DELIM = {' ', '\t'}
STMT_DELIM = {' ', '\t', '\n'}

DELIMS = {
    'inline_delim': {' ', '\t'},
    'stmt_delim': {' ', '\t', '\n'},
    'id_delim': {
        *STMT_DELIM, *ATOMS['assignment_op'], *ATOMS['arithmetic_op'],
        *ATOMS['relational_op'], *ATOMS['unary_incdec_op'],
        '(', '[', ')', ']', ','
    },
    'dtype_lit_delim': {
        *STMT_DELIM, *ATOMS['arithmetic_op'], *ATOMS['relational_op'],
        ')', ']', ','
    },
    'method_delim': {
        *INLINE_DELIM, '('
    },
    'arith_rel_not_op_delim': {
        *INLINE_DELIM, *ATOMS['under_alpha_num'], 
        '(', *ATOMS['unary_negative_op']
    },
    'assign_op_delim': {
        *INLINE_DELIM, *ATOMS['under_alpha_num'], 
        *ATOMS['unary_negative_op'], *ATOMS['logical_not_op'],
        '(', '[', "'"
    },
    'paren_open_delim': {
        *INLINE_DELIM, *ATOMS['under_alpha_num'],
        *ATOMS['unary_negative_op'], *ATOMS['logical_not_op'],
        '(', '[', ')', "'", 
    },
    'paren_close_delim': {
        *STMT_DELIM, *ATOMS['relational_op'],
        *ATOMS['arithmetic_op'], *ATOMS['logical_and_or_op'],
        ')', ','
    },
    'bracket_open_delim': {
        *INLINE_DELIM, *ATOMS['under_alpha_num'],
        *ATOMS['unary_negative_op'], *ATOMS['logical_not_op'],
        '(', '[', ']',"'"
    },
    'bracket_close_delim': {
        *STMT_DELIM, '[', ')', ']', ',', '='
    },
    'comma_delim': {
        *INLINE_DELIM, *ATOMS['under_alpha_num'], "'", '[', *ATOMS['unary_negative_op']
    },
}