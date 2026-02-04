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

When redefining the next states, the delimiter state must always be last in the possible next states parameter or else it would have errors
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
    # ─────────────────────────────────────────────────────────────
    # INITIAL
    # ─────────────────────────────────────────────────────────────
    0: TransitionState(
        "initial",
        [
            # keywords 
            1, 11, 17, 25, 44, 51, 54, 66, 77, 82,
            # symbols/operators
            88, 90, 92, 96, 98, 102, 106, 108, 110, 114,
            # delimiters
            118, 120, 122, 124, 126, 128, 130,
            # comments
            132,
            # identifiers
            142,
            # numerics (optional leading "~" or digit)
            190, 191,
            # strings
            242,
        ],
    ),

    # ─────────────────────────────────────────────────────────────
    # KEYWORDS
    # ─────────────────────────────────────────────────────────────

    # always, and
    1: TransitionState("a", [2, 8]),
    2: TransitionState("l", [3]),
    3: TransitionState("w", [4]),
    4: TransitionState("a", [5]),
    5: TransitionState("y", [6]),
    6: TransitionState("s", [7]),
    7: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    8: TransitionState("n", [9]),
    9: TransitionState("d", [10]),
    10: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # close
    11: TransitionState("c", [12]),
    12: TransitionState("l", [13]),
    13: TransitionState("o", [14]),
    14: TransitionState("s", [15]),
    15: TransitionState("e", [16]),
    16: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # elif, else
    17: TransitionState("e", [18]),
    18: TransitionState("l", [19, 22]),
    19: TransitionState("i", [20]),
    20: TransitionState("f", [21]),
    21: TransitionState(DELIMS["token_delim"], is_terminal=True),

    22: TransitionState("s", [23]),
    23: TransitionState("e", [24]),
    24: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    # false, fail, float, fn, for
    25: TransitionState("f", [26, 34, 39, 41]),
    26: TransitionState("a", [27, 31]),
    27: TransitionState("l", [28]),
    28: TransitionState("s", [29]),
    29: TransitionState("e", [30]),
    30: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    31: TransitionState("i", [32]),
    32: TransitionState("l", [33]),
    33: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    34: TransitionState("l", [35]),
    35: TransitionState("o", [36]),
    36: TransitionState("a", [37]),
    37: TransitionState("t", [38]),
    38: TransitionState(DELIMS["method_delim"], is_terminal=True),

    39: TransitionState("n", [40]),
    40: TransitionState(DELIMS["token_delim"], is_terminal=True),

    41: TransitionState("o", [42]),
    42: TransitionState("r", [43]),
    43: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # if, in, int
    44: TransitionState("i", [45, 47]),
    45: TransitionState("f", [46]),
    46: TransitionState(DELIMS["token_delim"], is_terminal=True),

    47: TransitionState("n", [48, 49]),
    48: TransitionState(DELIMS["token_delim"], is_terminal=True),

    49: TransitionState("t", [50]),
    50: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # or
    51: TransitionState("o", [52]),
    52: TransitionState("r", [53]),
    53: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # range, read, ret
    54: TransitionState("r", [55, 60]),
    55: TransitionState("a", [56]),
    56: TransitionState("n", [57]),
    57: TransitionState("g", [58]),
    58: TransitionState("e", [59]),
    59: TransitionState(DELIMS["method_delim"], is_terminal=True),

    60: TransitionState("e", [61, 64]),
    61: TransitionState("a", [62]),
    62: TransitionState("d", [63]),
    63: TransitionState(DELIMS["stmt_delim"], is_terminal=True),

    64: TransitionState("t", [65]),
    65: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # todo, true, try
    66: TransitionState("t", [67, 71]),
    67: TransitionState("o", [68]),
    68: TransitionState("d", [69]),
    69: TransitionState("o", [70]),
    70: TransitionState(DELIMS["stmt_delim"], is_terminal=True),

    71: TransitionState("r", [72, 75]),
    72: TransitionState("u", [73]),
    73: TransitionState("e", [74]),
    74: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    75: TransitionState("y", [76]),
    76: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    # show
    77: TransitionState("s", [78]),
    78: TransitionState("h", [79]),
    79: TransitionState("o", [80]),
    80: TransitionState("w", [81]),
    81: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # while
    82: TransitionState("w", [83]),
    83: TransitionState("h", [84]),
    84: TransitionState("i", [85]),
    85: TransitionState("l", [86]),
    86: TransitionState("e", [87]),
    87: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # SYMBOLS / OPERATORS
    # +, -, *, **, %, /, //, =, ==, !, !=, <, <=, >, >=
    # ─────────────────────────────────────────────────────────────
    88: TransitionState("+", [89]),
    89: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    90: TransitionState("-", [91]),
    91: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    92: TransitionState("*", [94, 93]),  # delim last
    93: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    94: TransitionState("*", [95]),
    95: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    96: TransitionState("%", [97]),
    97: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    98: TransitionState("/", [100, 99]),  # delim last
    99: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    100: TransitionState("/", [101]),
    101: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    102: TransitionState("=", [104, 103]),  # delim last
    103: TransitionState(DELIMS["assign_op_delim"], is_terminal=True),
    104: TransitionState("=", [105]),
    105: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    106: TransitionState("!", [108, 107]),  # delim last
    107: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    108: TransitionState("=", [109]),
    109: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    110: TransitionState("<", [112, 111]),  # delim last
    111: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    112: TransitionState("=", [113]),
    113: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    114: TransitionState(">", [116, 115]),  # delim last
    115: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    116: TransitionState("=", [117]),
    117: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # DELIMITERS
    # ─────────────────────────────────────────────────────────────
    118: TransitionState("(", [119]),
    119: TransitionState(DELIMS["paren_open_delim"], is_terminal=True),

    120: TransitionState(")", [121]),
    121: TransitionState(DELIMS["paren_close_delim"], is_terminal=True),

    122: TransitionState("[", [123]),
    123: TransitionState(DELIMS["bracket_open_delim"], is_terminal=True),

    124: TransitionState("]", [125]),
    125: TransitionState(DELIMS["bracket_close_delim"], is_terminal=True),

    126: TransitionState(",", [127]),
    127: TransitionState(DELIMS["comma_delim"], is_terminal=True),

    128: TransitionState(":", [129]),
    129: TransitionState(DELIMS["token_delim"], is_terminal=True),

    130: TransitionState(";", [131]),
    131: TransitionState(DELIMS["terminator_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # COMMENTS
    # Single-line:  '#' ... '\n'
    # Multi-line:   '###' ... '###' then token_delim
    # ─────────────────────────────────────────────────────────────

    132: TransitionState("#", [135, 133, 134]),
    133: TransitionState(ATOMS["single_comment_ascii"], [133, 134]),  # '\n' LAST
    134: TransitionState("\n", is_terminal=True),

    135: TransitionState("#", [136]),
    136: TransitionState("#", [138, 137]),  # content first, close-attempt second
    137: TransitionState(ATOMS["multiline_comment_ascii"], [138, 137]),

    138: TransitionState("#", [139]),
    139: TransitionState("#", [140]),
    140: TransitionState("#", [141]),
    141: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # IDENTIFIERS
    # ─────────────────────────────────────────────────────────────

    142: TransitionState({*ATOMS["all_alphabet"], "_"}, [144, 143]),
    143: TransitionState(DELIMS["id_delim"], is_terminal=True),

    144: TransitionState(ATOMS["under_alpha_num"], [146, 145]),
    145: TransitionState(DELIMS["id_delim"], is_terminal=True),

    146: TransitionState(ATOMS["under_alpha_num"], [148, 147]),
    147: TransitionState(DELIMS["id_delim"], is_terminal=True),

    148: TransitionState(ATOMS["under_alpha_num"], [150, 149]),
    149: TransitionState(DELIMS["id_delim"], is_terminal=True),

    150: TransitionState(ATOMS["under_alpha_num"], [152, 151]),
    151: TransitionState(DELIMS["id_delim"], is_terminal=True),

    152: TransitionState(ATOMS["under_alpha_num"], [154, 153]),
    153: TransitionState(DELIMS["id_delim"], is_terminal=True),

    154: TransitionState(ATOMS["under_alpha_num"], [156, 155]),
    155: TransitionState(DELIMS["id_delim"], is_terminal=True),

    156: TransitionState(ATOMS["under_alpha_num"], [158, 157]),
    157: TransitionState(DELIMS["id_delim"], is_terminal=True),

    158: TransitionState(ATOMS["under_alpha_num"], [160, 159]),
    159: TransitionState(DELIMS["id_delim"], is_terminal=True),

    160: TransitionState(ATOMS["under_alpha_num"], [162, 161]),
    161: TransitionState(DELIMS["id_delim"], is_terminal=True),

    162: TransitionState(ATOMS["under_alpha_num"], [164, 163]),
    163: TransitionState(DELIMS["id_delim"], is_terminal=True),

    164: TransitionState(ATOMS["under_alpha_num"], [166, 165]),
    165: TransitionState(DELIMS["id_delim"], is_terminal=True),

    166: TransitionState(ATOMS["under_alpha_num"], [168, 167]),
    167: TransitionState(DELIMS["id_delim"], is_terminal=True),

    168: TransitionState(ATOMS["under_alpha_num"], [170, 169]),
    169: TransitionState(DELIMS["id_delim"], is_terminal=True),

    170: TransitionState(ATOMS["under_alpha_num"], [172, 171]),
    171: TransitionState(DELIMS["id_delim"], is_terminal=True),

    172: TransitionState(ATOMS["under_alpha_num"], [174, 173]),
    173: TransitionState(DELIMS["id_delim"], is_terminal=True),

    174: TransitionState(ATOMS["under_alpha_num"], [176, 175]),
    175: TransitionState(DELIMS["id_delim"], is_terminal=True),

    176: TransitionState(ATOMS["under_alpha_num"], [178, 177]),
    177: TransitionState(DELIMS["id_delim"], is_terminal=True),

    178: TransitionState(ATOMS["under_alpha_num"], [180, 179]),
    179: TransitionState(DELIMS["id_delim"], is_terminal=True),

    180: TransitionState(ATOMS["under_alpha_num"], [182, 181]),
    181: TransitionState(DELIMS["id_delim"], is_terminal=True),

    182: TransitionState(ATOMS["under_alpha_num"], [184, 183]),
    183: TransitionState(DELIMS["id_delim"], is_terminal=True),

    184: TransitionState(ATOMS["under_alpha_num"], [186, 185]),
    185: TransitionState(DELIMS["id_delim"], is_terminal=True),

    186: TransitionState(ATOMS["under_alpha_num"], [188, 187]),
    187: TransitionState(DELIMS["id_delim"], is_terminal=True),

    188: TransitionState(ATOMS["under_alpha_num"], [189]),
    189: TransitionState(DELIMS["id_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # NUMERIC LITERALS (int_literal + float_literal)
    # ─────────────────────────────────────────────────────────────
    190: TransitionState("~", [191]),

    # Integer digits chain (each can terminate via dtype_lit_delim, or go to '.' (229))
    191: TransitionState(ATOMS["all_num"], [193, 229, 192]),
    192: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    193: TransitionState(ATOMS["all_num"], [195, 229, 194]),
    194: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    195: TransitionState(ATOMS["all_num"], [197, 229, 196]),
    196: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    197: TransitionState(ATOMS["all_num"], [199, 229, 198]),
    198: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    199: TransitionState(ATOMS["all_num"], [201, 229, 200]),
    200: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    201: TransitionState(ATOMS["all_num"], [203, 229, 202]),
    202: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    203: TransitionState(ATOMS["all_num"], [205, 229, 204]),
    204: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    205: TransitionState(ATOMS["all_num"], [207, 229, 206]),
    206: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    207: TransitionState(ATOMS["all_num"], [209, 229, 208]),
    208: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    209: TransitionState(ATOMS["all_num"], [211, 229, 210]),
    210: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    211: TransitionState(ATOMS["all_num"], [213, 229, 212]),
    212: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    213: TransitionState(ATOMS["all_num"], [215, 229, 214]),
    214: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    215: TransitionState(ATOMS["all_num"], [217, 229, 216]),
    216: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    217: TransitionState(ATOMS["all_num"], [219, 229, 218]),
    218: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    219: TransitionState(ATOMS["all_num"], [221, 229, 220]),
    220: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    221: TransitionState(ATOMS["all_num"], [223, 229, 222]),
    222: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    223: TransitionState(ATOMS["all_num"], [225, 229, 224]),
    224: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    225: TransitionState(ATOMS["all_num"], [227, 229, 226]),
    226: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    227: TransitionState(ATOMS["all_num"], [229, 228]),  # no more digits after this in diagram
    228: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # Decimal point
    229: TransitionState(".", [230]),

    # Decimal digits (up to 6 places)
    230: TransitionState(ATOMS["all_num"], [232, 231]),
    231: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    232: TransitionState(ATOMS["all_num"], [234, 233]),
    233: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    234: TransitionState(ATOMS["all_num"], [236, 235]),
    235: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    236: TransitionState(ATOMS["all_num"], [238, 237]),
    237: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    238: TransitionState(ATOMS["all_num"], [240, 239]),
    239: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    240: TransitionState(ATOMS["all_num"], [241]),
    241: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # STRING LITERALS
    # Single-quoted strings, no escapes (per DFA).
    # ─────────────────────────────────────────────────────────────
    242: TransitionState("'", [243, 244]),
    243: TransitionState(ATOMS["string_ascii"], [244, 243]),
    244: TransitionState("'", [245]),
    245: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
}