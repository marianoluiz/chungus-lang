"""Delimiter sets used by accepting states to validate token boundaries.

Categories:
- inline_delim: space-like separators usable mid-statement
- stmt_delim: separators that can end a statement (includes newline)
- id_delim: characters that can legally follow an identifier
- dtype_lit_delim: characters that can follow a type or literal
- method_delim, paren/bracket open/close, comma, assign_op, etc.
"""

from .atoms import ATOMS

TOKEN_DELIM = {' ', '\n'}
STMT_DELIM = {' ', '\n', ';'}

DELIMS = {
    'token_delim': TOKEN_DELIM,
    'stmt_delim': STMT_DELIM,

    'id_delim': {
        *STMT_DELIM, 
        *ATOMS['assignment_op'], 
        *ATOMS['arithmetic_op'],
        *ATOMS['relational_op'], 
        '(', '[', ')', ']', ',',
        *ATOMS['header_terminator']
    },

    
    'dtype_lit_delim': {
        *STMT_DELIM, 
        *ATOMS['arithmetic_op'], 
        *ATOMS['relational_op'],
        ')', ']', ',', 
        *ATOMS['header_terminator']
    },


    'method_delim': {
        *TOKEN_DELIM, 
        '('
    },


    'arith_rel_not_op_delim': {
        *TOKEN_DELIM, 
        *ATOMS['under_alpha_num'], 
        *ATOMS['unary_negative_op'],
        "'", "("
    },


    'assign_op_delim': {
        *TOKEN_DELIM, 
        *ATOMS['under_alpha_num'], 
        *ATOMS['unary_negative_op'], 
        *ATOMS['logical_not_op'],
        '[', "'", '('
    },


    'paren_open_delim': {
        *TOKEN_DELIM, 
        *ATOMS['under_alpha_num'],
        *ATOMS['unary_negative_op'], 
        *ATOMS['logical_not_op'],
        ')', "'", '('
    },


    'paren_close_delim': {
        *STMT_DELIM, 
        *ATOMS['arithmetic_op'],
        *ATOMS['relational_op'],
        ')', ',',
        *ATOMS['header_terminator'],
        ']'
    },


    'bracket_open_delim': {
        *TOKEN_DELIM, 
        *ATOMS['under_alpha_num'],
        *ATOMS['unary_negative_op'], 
        '[', ']',"'", '!', '('
    },


    'bracket_close_delim': {
        *STMT_DELIM, 
        '[', ']', ')', ',', '=',
        *ATOMS['header_terminator'],
        *ATOMS['arithmetic_op'],
        *ATOMS['relational_op']
    },


    'comma_delim': {
        *TOKEN_DELIM, 
        *ATOMS['under_alpha_num'], 
        "'", '[', 
        *ATOMS['unary_negative_op'],
        *ATOMS['logical_not_op'],
    },


    'blk_header_delim': {
        *ATOMS['header_terminator'],
        *TOKEN_DELIM,
    },


    'terminator_delim': {
        *TOKEN_DELIM,
        *ATOMS['all_alphabet'],
        '_',
    },

    'colon_delim': {
        *TOKEN_DELIM,
        '['
    }

}