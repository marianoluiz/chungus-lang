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

When redefining the next states, the delimiter must me always last or else it would have errors
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
    0: TransitionState('initial', [
        # keywords
        1, 27, 33, 41, 60, 67, 70, 82, 93, 98,
        # operators
        104, 108, 112, 116, 118, 122, 126, 130, 134,
        # delimiters
        138, 140, 142, 144, 146,
        # comments
        148,
        # identifiers
        158,
        # numerics
        161, 162,
        # strings
        213,
    ]),

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
    # --- Keywords: close ---
    27: TransitionState('c', [28]),
    28: TransitionState('l', [29]),
    29: TransitionState('o', [30]),
    30: TransitionState('s', [31]),
    31: TransitionState('e', [32]),
    32: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Keywords: elif, else ---
    33: TransitionState('e', [34]),
    34: TransitionState('l', [35, 38]),

    35: TransitionState('i', [36]),
    36: TransitionState('f', [37]),
    37: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    38: TransitionState('s', [39]),
    39: TransitionState('e', [40]),
    40: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Keywords: false, fail, float, fn, for ---
    41: TransitionState('f', [42, 50, 55, 57]),

    # false / fail split
    42: TransitionState('a', [43, 47]),

    43: TransitionState('l', [44]),
    44: TransitionState('s', [45]),
    45: TransitionState('e', [46]),
    46: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    47: TransitionState('i', [48]),
    48: TransitionState('l', [49]),
    49: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # float
    50: TransitionState('l', [51]),
    51: TransitionState('o', [52]),
    52: TransitionState('a', [53]),
    53: TransitionState('t', [54]),
    54: TransitionState(DELIMS['method_delim'], is_terminal=True),

    # fn
    55: TransitionState('n', [56]),
    56: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # for
    57: TransitionState('o', [58]),
    58: TransitionState('r', [59]),
    59: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Keywords: if, in, int ---
    60: TransitionState('i', [61, 63]),

    61: TransitionState('f', [62]),
    62: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    63: TransitionState('n', [64, 65]),  # in | int
    64: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    65: TransitionState('t', [66]),
    66: TransitionState(DELIMS['method_delim'], is_terminal=True),

    # --- Keywords: or ---
    67: TransitionState('o', [68]),
    68: TransitionState('r', [69]),
    69: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Keywords: range, read, ret ---
    70: TransitionState('r', [71, 76]),  # range | re..

    71: TransitionState('a', [72]),
    72: TransitionState('n', [73]),
    73: TransitionState('g', [74]),
    74: TransitionState('e', [75]),
    75: TransitionState(DELIMS['method_delim'], is_terminal=True),

    76: TransitionState('e', [77, 80]),  # read | ret
    77: TransitionState('a', [78]),
    78: TransitionState('d', [79]),
    79: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    80: TransitionState('t', [81]),
    81: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Keywords: todo, true, try ---
    82: TransitionState('t', [83, 87]),  # todo | tr..

    83: TransitionState('o', [84]),
    84: TransitionState('d', [85]),
    85: TransitionState('o', [86]),
    86: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    87: TransitionState('r', [88, 91]),  # true | try

    88: TransitionState('u', [89]),
    89: TransitionState('e', [90]),
    90: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    91: TransitionState('y', [92]),
    92: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Keywords: show ---
    93: TransitionState('s', [94]),
    94: TransitionState('h', [95]),
    95: TransitionState('o', [96]),
    96: TransitionState('w', [97]),
    97: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Keywords: while ---
    98: TransitionState('w', [99]),
    99: TransitionState('h', [100]),
    100: TransitionState('i', [101]),
    101: TransitionState('l', [102]),
    102: TransitionState('e', [103]),
    103: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Operators: Arithmetic (+, -, *, %, /) ---
    104: TransitionState('+', [106, 105]),
    105: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    106: TransitionState('+', [107]),
    107: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    108: TransitionState('-', [110, 109]),
    109: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    110: TransitionState('-', [111]),
    111: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    112: TransitionState('*', [114, 113]),
    113: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    114: TransitionState('*', [115]),
    115: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    116: TransitionState('%', [117]),
    117: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    118: TransitionState('/', [120, 119]),
    119: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    120: TransitionState('/', [121]),
    121: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    # --- Operators: Relational/Assignment (=, !, <, >, <=, >=) ---
    122: TransitionState('=', [124, 123]),
    123: TransitionState(DELIMS['assign_op_delim'], is_terminal=True),
    124: TransitionState('=', [125]),
    125: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    126: TransitionState('!', [128, 127]),
    127: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    128: TransitionState('=', [129]),
    129: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    130: TransitionState('<', [132, 131]),
    131: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    132: TransitionState('=', [133]),
    133: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    134: TransitionState('>', [136, 135]),
    135: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    136: TransitionState('=', [137]),
    137: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    # --- Delimiters ---
    138: TransitionState('(', [139]),
    139: TransitionState(DELIMS['paren_open_delim'], is_terminal=True),

    140: TransitionState(')', [141]),
    141: TransitionState(DELIMS['paren_close_delim'], is_terminal=True),

    142: TransitionState('[', [143]),
    143: TransitionState(DELIMS['bracket_open_delim'], is_terminal=True),

    144: TransitionState(']', [145]),
    145: TransitionState(DELIMS['bracket_close_delim'], is_terminal=True),

    146: TransitionState(',', [147]),
    147: TransitionState(DELIMS['comma_delim'], is_terminal=True),

    # --- Comments ---
    # Single-line: '#' ... '\n'
    # Multi-line:  '###' ... '###' then stmt_delim
    148: TransitionState('#', [151, 149, 150]),

    149: TransitionState(ATOMS['single_comment_ascii'], [149, 150]),
    150: TransitionState('\n', is_terminal=True),

    151: TransitionState('#', [152]),
    152: TransitionState('#', [154, 153]),

    153: TransitionState(ATOMS['multiline_comment_ascii'], [154, 153]),
    154: TransitionState('#', [155]),
    155: TransitionState('#', [156]),
    156: TransitionState('#', [157]),
    157: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Identifiers ---
    158: TransitionState({*ATOMS['all_alphabet'], '_'}, [159, 160]),
    159: TransitionState(ATOMS['under_alpha_num'], [159, 160]),
    160: TransitionState(DELIMS['id_delim'], is_terminal=True),

    # --- Numeric Literals ---
    161: TransitionState('~', [162]),

    # Integers (up to 19 digits), branching to '.' at 200
    162: TransitionState(ATOMS['all_num'], [164, 200, 163]),
    163: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    164: TransitionState(ATOMS['all_num'], [166, 200, 165]),
    165: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    166: TransitionState(ATOMS['all_num'], [168, 200, 167]),
    167: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    168: TransitionState(ATOMS['all_num'], [170, 200, 169]),
    169: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    170: TransitionState(ATOMS['all_num'], [172, 200, 171]),
    171: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    172: TransitionState(ATOMS['all_num'], [174, 200, 173]),
    173: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    174: TransitionState(ATOMS['all_num'], [176, 200, 175]),
    175: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    176: TransitionState(ATOMS['all_num'], [178, 200, 177]),
    177: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    178: TransitionState(ATOMS['all_num'], [180, 200, 179]),
    179: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    180: TransitionState(ATOMS['all_num'], [182, 200, 181]),
    181: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    182: TransitionState(ATOMS['all_num'], [184, 200, 183]),
    183: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    184: TransitionState(ATOMS['all_num'], [186, 200, 185]),
    185: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    186: TransitionState(ATOMS['all_num'], [188, 200, 187]),
    187: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    188: TransitionState(ATOMS['all_num'], [190, 200, 189]),
    189: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    190: TransitionState(ATOMS['all_num'], [192, 200, 191]),
    191: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    192: TransitionState(ATOMS['all_num'], [194, 200, 193]),
    193: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    194: TransitionState(ATOMS['all_num'], [196, 200, 195]),
    195: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    196: TransitionState(ATOMS['all_num'], [198, 200, 197]),
    197: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    198: TransitionState(ATOMS['all_num'], [200, 199]),
    199: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    # '.' to float path
    200: TransitionState('.', [201]),

    # Float decimals (1..6)
    201: TransitionState(ATOMS['all_num'], [203, 202]),
    202: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    203: TransitionState(ATOMS['all_num'], [205, 204]),
    204: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    205: TransitionState(ATOMS['all_num'], [207, 206]),
    206: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    207: TransitionState(ATOMS['all_num'], [209, 208]),
    208: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    209: TransitionState(ATOMS['all_num'], [211, 210]),
    210: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    211: TransitionState(ATOMS['all_num'], [212]),
    212: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    # --- String Literals ---
    # Single-quoted strings, no escape sequences.
    213: TransitionState("'", [215, 214]),
    214: TransitionState(ATOMS['string_ascii'], [215, 214]),
    215: TransitionState("'", [216]),
    216: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
}