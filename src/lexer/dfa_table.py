"""
DFA transition table for the lexer.

This module defines the deterministic finite automaton used by the lexer to
recognize tokens. The DFA is expressed explicitly as a transition table where
each state encodes:

- accepted characters
- possible next states
- whether the state can legally terminate a token

This file is intentionally data-heavy and should be treated as a language
specification rather than control logic.
"""

from src.constants import ATOMS, DELIMS

class TransitionState:
    """
    Single DFA transition node.

    Attributes:
        accepted_chars (set[str]):
            Characters accepted at this state.
        next_states (list[int]):
            Indices of possible next DFA states.
        is_terminal (bool):
            True if this state can legally end a token.
    """
    def __init__(
        self,
        accepted_chars: str | set[str],
        next_states: int | list[int] | None = None,
        is_terminal: bool = False,
    ):  
        
        # Normalize accepted characters to a set
        self.accepted_chars = (
            {accepted_chars}
            # prevents splitting a whole string into characters
            if isinstance(accepted_chars, str)
            else set(accepted_chars)
        )

        # Normalize next states to a list
        self.next_states = (
            []
            if next_states is None
            # separated because an int is not iterable
            else [next_states] if isinstance(next_states, int) else list(next_states)   
        )
        self.is_terminal = is_terminal

TRANSITION_TABLE = {
    # --- Initial State ---
    0: TransitionState('initial', [1, 27, 33, 41, 60, 67, 70, 82, 93, 106, 112, 116, 
                                   120, 124, 126, 130, 134, 138, 142, 146, 148, 150, 
                                   152, 154, 156, 166, 169, 170, 221]),

    # --- Keywords: always, and, array_remove ---
    1: TransitionState('a', [2, 8, 11]),
    2: TransitionState('l', [3]),
    3: TransitionState('w', [4]),
    4: TransitionState('a', [5]),
    5: TransitionState('y', [6]),
    6: TransitionState('s', [7]),
    7: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    8: TransitionState('n', [9]),
    9: TransitionState('d', [10]),
    10: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    11: TransitionState('r', [12]),
    12: TransitionState('r', [13]),
    13: TransitionState('a', [14]),
    14: TransitionState('y', [15]),
    15: TransitionState('_', [16, 20]),
    16: TransitionState('a', [17]),
    17: TransitionState('d', [18]),
    18: TransitionState('d', [19]),
    19: TransitionState(DELIMS['method_delim'], is_terminal=True),
    20: TransitionState('r', [21]),
    21: TransitionState('e', [22]),
    22: TransitionState('m', [23]),
    23: TransitionState('o', [24]),
    24: TransitionState('v', [25]),
    25: TransitionState('e', [26]),
    26: TransitionState(DELIMS['method_delim'], is_terminal=True),

    # --- Keywords: close, elif, else ---
    27: TransitionState('c', [28]),
    28: TransitionState('l', [29]),
    29: TransitionState('o', [30]),
    30: TransitionState('s', [31]),
    31: TransitionState('e', [32]),
    32: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    33: TransitionState('e', [34]),
    34: TransitionState('l', [38, 35]), 
    35: TransitionState('i', [36]),
    36: TransitionState('f', [37]),
    37: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    38: TransitionState('s', [39]),
    39: TransitionState('e', [40]),
    40: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Keywords: false, fail, float, fn, for ---
    41: TransitionState('f', [55, 57, 42, 50]),
    42: TransitionState('a', [47, 43]),
    43: TransitionState('l', [44]),
    44: TransitionState('s', [45]),
    45: TransitionState('e', [46]),
    46: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    47: TransitionState('i', [48]),
    48: TransitionState('l', [49]),
    49: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    50: TransitionState('l', [51]),
    51: TransitionState('o', [52]),
    52: TransitionState('a', [53]),
    53: TransitionState('t', [54]),
    54: TransitionState(DELIMS['method_delim'], is_terminal=True),
    55: TransitionState('n', [56]),
    56: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    57: TransitionState('o', [58]),
    58: TransitionState('r', [59]),
    59: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    60: TransitionState('i', [61, 63]),
    61: TransitionState('f', [62]),
    62: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    63: TransitionState('n', [65, 64]), # t(65), delim(64)
    64: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    65: TransitionState('t', [66]),
    66: TransitionState(DELIMS['method_delim'], is_terminal=True),

    # --- Keywords: or, range, read, ret, todo, true, try, show, skip, stop, while ---
    67: TransitionState('o', [68]),
    68: TransitionState('r', [69]),
    69: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    70: TransitionState('r', [76, 71]),
    71: TransitionState('a', [72]),
    72: TransitionState('n', [73]),
    73: TransitionState('g', [74]),
    74: TransitionState('e', [75]),
    75: TransitionState(DELIMS['method_delim'], is_terminal=True),
    76: TransitionState('e', [80, 77]),
    77: TransitionState('a', [78]),
    78: TransitionState('d', [79]),
    79: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    80: TransitionState('t', [81]),
    81: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    82: TransitionState('t', [87, 83]),
    83: TransitionState('o', [84]),
    84: TransitionState('d', [85]),
    85: TransitionState('o', [86]),
    86: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    87: TransitionState('r', [91, 88]),
    88: TransitionState('u', [89]),
    89: TransitionState('e', [90]),
    90: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    91: TransitionState('y', [92]),
    92: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    93: TransitionState('s', [98, 102, 94]),
    94: TransitionState('h', [95]),
    95: TransitionState('o', [96]),
    96: TransitionState('w', [97]),
    97: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    98: TransitionState('k', [99]),
    99: TransitionState('i', [100]),
    100: TransitionState('p', [101]),
    101: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    102: TransitionState('t', [103]),
    103: TransitionState('o', [104]),
    104: TransitionState('p', [105]),
    105: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    106: TransitionState('w', [107]),
    107: TransitionState('h', [108]),
    108: TransitionState('i', [109]),
    109: TransitionState('l', [110]),
    110: TransitionState('e', [111]),
    111: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Operators: Arithmetic (+, -, *, %, /) ---
    # --- Operators: Relational/Assignment (=, !, <, >) ---
    112: TransitionState('+', [114, 113]),
    113: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    114: TransitionState('+', [115]),
    115: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    116: TransitionState('-', [118, 117]),
    117: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    118: TransitionState('-', [119]),
    119: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    120: TransitionState('*', [122, 121]),
    121: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    122: TransitionState('*', [123]),
    123: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    124: TransitionState('%', [125]),
    125: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    126: TransitionState('/', [128, 127]),
    127: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    128: TransitionState('/', [129]),
    129: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    # --- Operators: Relational/Assignment (=, !, <, >, <=, >=) ---
    130: TransitionState('=', [132, 131]),
    131: TransitionState(DELIMS['assign_op_delim'], is_terminal=True),
    132: TransitionState('=', [133]),
    133: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    134: TransitionState('!', [136, 135]),
    135: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    136: TransitionState('=', [137]),
    137: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    138: TransitionState('<', [140, 139]),
    139: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    140: TransitionState('=', [141]),
    141: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    142: TransitionState('>', [144, 143]),
    143: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    144: TransitionState('=', [145]),
    145: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    # --- Delimiters ---
    146: TransitionState('(', [147]),
    147: TransitionState(DELIMS['paren_open_delim'], is_terminal=True),
    148: TransitionState(')', [149]),
    149: TransitionState(DELIMS['paren_close_delim'], is_terminal=True),
    150: TransitionState('[', [151]),
    151: TransitionState(DELIMS['bracket_open_delim'], is_terminal=True),
    152: TransitionState(']', [153]),
    153: TransitionState(DELIMS['bracket_close_delim'], is_terminal=True),
    154: TransitionState(',', [155]),
    155: TransitionState(DELIMS['comma_delim'], is_terminal=True),

    # --- Comments ---
    # Single-line: '#' ... '\n'
    # Multi-line:  '###' ... '###'
    156: TransitionState('#', [159, 157, 158]), # #->159, ascii->157
    157: TransitionState(ATOMS['single_comment_ascii'], [157, 158]),
    158: TransitionState('\n', is_terminal=True),
    159: TransitionState('#', [160]),
    160: TransitionState('#', [162, 161]),
    161: TransitionState(ATOMS['multiline_comment_ascii'], [162, 161]),
    162: TransitionState('#', [163]),
    163: TransitionState('#', [164]),
    164: TransitionState('#', [165]),
    165: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Identifiers ---
    166: TransitionState({*ATOMS['all_alphabet'], '_'}, [167, 168]),
    167: TransitionState(ATOMS['under_alpha_num'], [167, 168]),
    168: TransitionState(DELIMS['id_delim'], is_terminal=True),

    # --- Numeric Literals (Integers and Floats) ---
    # Integers: 19 digit, Float: 6 digit 
    169: TransitionState('~', [170]), # explicit negative
    
    170: TransitionState(ATOMS['all_num'], [172, 208, 171]),
    171: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    172: TransitionState(ATOMS['all_num'], [174, 208, 173]),
    173: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    174: TransitionState(ATOMS['all_num'], [176, 208, 175]),
    175: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    176: TransitionState(ATOMS['all_num'], [178, 208, 177]),
    177: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    178: TransitionState(ATOMS['all_num'], [180, 208, 179]),
    179: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    180: TransitionState(ATOMS['all_num'], [182, 208, 181]),
    181: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    182: TransitionState(ATOMS['all_num'], [184, 208, 183]),
    183: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    184: TransitionState(ATOMS['all_num'], [186, 208, 185]),
    185: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    186: TransitionState(ATOMS['all_num'], [188, 208, 187]),
    187: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    188: TransitionState(ATOMS['all_num'], [190, 208, 189]),
    189: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    190: TransitionState(ATOMS['all_num'], [192, 208, 191]),
    191: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    192: TransitionState(ATOMS['all_num'], [194, 208, 193]),
    193: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    194: TransitionState(ATOMS['all_num'], [196, 208, 195]),
    195: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    196: TransitionState(ATOMS['all_num'], [198, 208, 197]),
    197: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    198: TransitionState(ATOMS['all_num'], [200, 208, 199]),
    199: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    200: TransitionState(ATOMS['all_num'], [202, 208, 201]),
    201: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    202: TransitionState(ATOMS['all_num'], [204, 208, 203]),
    203: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    204: TransitionState(ATOMS['all_num'], [206, 208, 205]),
    205: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    206: TransitionState(ATOMS['all_num'], [208, 207]),
    207: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    208: TransitionState('.', [209]),
    209: TransitionState(ATOMS['all_num'], [211, 210]),
    210: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    211: TransitionState(ATOMS['all_num'], [213, 212]),
    212: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    213: TransitionState(ATOMS['all_num'], [215, 214]),
    214: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    215: TransitionState(ATOMS['all_num'], [217, 216]),
    216: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    217: TransitionState(ATOMS['all_num'], [219, 218]),
    218: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    219: TransitionState(ATOMS['all_num'], [220]), # Max decimal precision reached
    220: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    # --- String Literals ---
    # Single-quoted strings, no escape sequences.
    221: TransitionState("'", [223, 222]),
    222: TransitionState(ATOMS['string_ascii'], [223, 222]),
    223: TransitionState("'", [224]),
    224: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
}