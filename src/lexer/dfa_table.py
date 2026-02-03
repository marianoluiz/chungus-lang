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

When redefining the next states, the delimiter state must always last in the possible next states parameter or else it would have errors
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
            1, 27, 33, 41, 60, 67, 70, 82, 93, 98,
            # operators
            104, 106, 108, 112, 114, 118, 122, 126, 130,
            # delimiters
            134, 136, 138, 140, 142, 144, 146,
            # comments
            148,
            # identifiers
            158,
            # numerics (supports optional leading "~")
            206, 207,
            # strings
            258,
        ],
    ),

    # ─────────────────────────────────────────────────────────────
    # KEYWORDS
    # ─────────────────────────────────────────────────────────────
    # always, and, array_add, array_remove
    1: TransitionState("a", [2, 8, 11]),
    2: TransitionState("l", [3]),
    3: TransitionState("w", [4]),
    4: TransitionState("a", [5]),
    5: TransitionState("y", [6]),
    6: TransitionState("s", [7]),
    7: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    8: TransitionState("n", [9]),
    9: TransitionState("d", [10]),
    10: TransitionState(DELIMS["token_delim"], is_terminal=True),

    11: TransitionState("r", [12]),
    12: TransitionState("r", [13]),
    13: TransitionState("a", [14]),
    14: TransitionState("y", [15]),
    15: TransitionState("_", [16, 20]),
    16: TransitionState("a", [17]),
    17: TransitionState("d", [18]),
    18: TransitionState("d", [19]),
    19: TransitionState(DELIMS["method_delim"], is_terminal=True),

    20: TransitionState("r", [21]),
    21: TransitionState("e", [22]),
    22: TransitionState("m", [23]),
    23: TransitionState("o", [24]),
    24: TransitionState("v", [25]),
    25: TransitionState("e", [26]),
    26: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # close
    27: TransitionState("c", [28]),
    28: TransitionState("l", [29]),
    29: TransitionState("o", [30]),
    30: TransitionState("s", [31]),
    31: TransitionState("e", [32]),
    32: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # elif, else
    33: TransitionState("e", [34]),
    34: TransitionState("l", [35, 38]),
    35: TransitionState("i", [36]),
    36: TransitionState("f", [37]),
    37: TransitionState(DELIMS["token_delim"], is_terminal=True),

    38: TransitionState("s", [39]),
    39: TransitionState("e", [40]),
    40: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    # false, fail, float, fn, for
    41: TransitionState("f", [42, 50, 55, 57]),
    42: TransitionState("a", [43, 47]),

    43: TransitionState("l", [44]),
    44: TransitionState("s", [45]),
    45: TransitionState("e", [46]),
    46: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    47: TransitionState("i", [48]),
    48: TransitionState("l", [49]),
    49: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    50: TransitionState("l", [51]),
    51: TransitionState("o", [52]),
    52: TransitionState("a", [53]),
    53: TransitionState("t", [54]),
    54: TransitionState(DELIMS["method_delim"], is_terminal=True),

    55: TransitionState("n", [56]),
    56: TransitionState(DELIMS["token_delim"], is_terminal=True),

    57: TransitionState("o", [58]),
    58: TransitionState("r", [59]),
    59: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # if, in, int
    60: TransitionState("i", [61, 63]),
    61: TransitionState("f", [62]),
    62: TransitionState(DELIMS["token_delim"], is_terminal=True),

    63: TransitionState("n", [64, 65]),  # in | int
    64: TransitionState(DELIMS["token_delim"], is_terminal=True),

    65: TransitionState("t", [66]),
    66: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # or
    67: TransitionState("o", [68]),
    68: TransitionState("r", [69]),
    69: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # range, read, ret
    70: TransitionState("r", [71, 76]),  # range | re..
    71: TransitionState("a", [72]),
    72: TransitionState("n", [73]),
    73: TransitionState("g", [74]),
    74: TransitionState("e", [75]),
    75: TransitionState(DELIMS["method_delim"], is_terminal=True),

    76: TransitionState("e", [77, 80]),  # read | ret
    77: TransitionState("a", [78]),
    78: TransitionState("d", [79]),
    79: TransitionState(DELIMS["stmt_delim"], is_terminal=True),

    80: TransitionState("t", [81]),
    81: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # todo, true, try
    82: TransitionState("t", [83, 87]),  # todo | tr..
    83: TransitionState("o", [84]),
    84: TransitionState("d", [85]),
    85: TransitionState("o", [86]),
    86: TransitionState(DELIMS["stmt_delim"], is_terminal=True),

    87: TransitionState("r", [88, 91]),  # true | try
    88: TransitionState("u", [89]),
    89: TransitionState("e", [90]),
    90: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    91: TransitionState("y", [92]),
    92: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    # show
    93: TransitionState("s", [94]),
    94: TransitionState("h", [95]),
    95: TransitionState("o", [96]),
    96: TransitionState("w", [97]),
    97: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # while
    98: TransitionState("w", [99]),
    99: TransitionState("h", [100]),
    100: TransitionState("i", [101]),
    101: TransitionState("l", [102]),
    102: TransitionState("e", [103]),
    103: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # SYMBOLS / OPERATORS
    # (Matches "symbols" DFA: +, -, *, **, %, /, //, =, ==, !, !=, <, <=, >, >=)
    # ─────────────────────────────────────────────────────────────
    104: TransitionState("+", [105]),
    105: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    106: TransitionState("-", [107]),
    107: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    108: TransitionState("*", [110, 109]),  # delimiter must be last
    109: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    110: TransitionState("*", [111]),
    111: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    112: TransitionState("%", [113]),
    113: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    114: TransitionState("/", [116, 115]),  # delimiter must be last
    115: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    116: TransitionState("/", [117]),
    117: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    118: TransitionState("=", [120, 119]),  # delimiter must be last
    119: TransitionState(DELIMS["assign_op_delim"], is_terminal=True),
    120: TransitionState("=", [121]),
    121: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    122: TransitionState("!", [124, 123]),  # delimiter must be last
    123: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    124: TransitionState("=", [125]),
    125: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    126: TransitionState("<", [128, 127]),  # delimiter must be last
    127: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    128: TransitionState("=", [129]),
    129: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    130: TransitionState(">", [132, 131]),  # delimiter must be last
    131: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    132: TransitionState("=", [133]),
    133: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # DELIMITERS
    # ─────────────────────────────────────────────────────────────
    134: TransitionState("(", [135]),
    135: TransitionState(DELIMS["paren_open_delim"], is_terminal=True),

    136: TransitionState(")", [137]),
    137: TransitionState(DELIMS["paren_close_delim"], is_terminal=True),

    138: TransitionState("[", [139]),
    139: TransitionState(DELIMS["bracket_open_delim"], is_terminal=True),

    140: TransitionState("]", [141]),
    141: TransitionState(DELIMS["bracket_close_delim"], is_terminal=True),

    142: TransitionState(",", [143]),
    143: TransitionState(DELIMS["comma_delim"], is_terminal=True),

    144: TransitionState(":", [145]),
    145: TransitionState(DELIMS["token_delim"], is_terminal=True),

    146: TransitionState(";", [147]),
    147: TransitionState(DELIMS["terminator_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # COMMENTS
    # Single-line:  '#' ... '\n'
    # Multi-line:   '###' ... '###' then token_delim
    # ─────────────────────────────────────────────────────────────
    148: TransitionState("#", [151, 149, 150]),  # terminal '\n' must be last-ish
    149: TransitionState(ATOMS["single_comment_ascii"], [149, 150]),
    150: TransitionState("\n", is_terminal=True),

    151: TransitionState("#", [152]),
    152: TransitionState("#", [154, 153]),
    153: TransitionState(ATOMS["multiline_comment_ascii"], [154, 153]),
    154: TransitionState("#", [155]),
    155: TransitionState("#", [156]),
    156: TransitionState("#", [157]),
    157: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # IDENTIFIERS
    # ─────────────────────────────────────────────────────────────
    158: TransitionState({*ATOMS["all_alphabet"], "_"}, [160, 159]),
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

    188: TransitionState(ATOMS["under_alpha_num"], [190, 189]),
    189: TransitionState(DELIMS["id_delim"], is_terminal=True),

    190: TransitionState(ATOMS["under_alpha_num"], [192, 191]),
    191: TransitionState(DELIMS["id_delim"], is_terminal=True),

    192: TransitionState(ATOMS["under_alpha_num"], [194, 193]),
    193: TransitionState(DELIMS["id_delim"], is_terminal=True),

    194: TransitionState(ATOMS["under_alpha_num"], [196, 195]),
    195: TransitionState(DELIMS["id_delim"], is_terminal=True),

    196: TransitionState(ATOMS["under_alpha_num"], [198, 197]),
    197: TransitionState(DELIMS["id_delim"], is_terminal=True),

    198: TransitionState(ATOMS["under_alpha_num"], [200, 199]),
    199: TransitionState(DELIMS["id_delim"], is_terminal=True),

    200: TransitionState(ATOMS["under_alpha_num"], [202, 201]),
    201: TransitionState(DELIMS["id_delim"], is_terminal=True),

    202: TransitionState(ATOMS["under_alpha_num"], [204, 203]),
    203: TransitionState(DELIMS["id_delim"], is_terminal=True),

    204: TransitionState(ATOMS["under_alpha_num"], [205]),
    205: TransitionState(DELIMS["id_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # NUMERIC LITERALS (int_literal + float_literal)
    # ─────────────────────────────────────────────────────────────
    206: TransitionState("~", [207]),

    207: TransitionState(ATOMS["all_num"], [209, 245, 208]),
    208: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    209: TransitionState(ATOMS["all_num"], [211, 245, 210]),
    210: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    211: TransitionState(ATOMS["all_num"], [213, 245, 212]),
    212: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    213: TransitionState(ATOMS["all_num"], [215, 245, 214]),
    214: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    215: TransitionState(ATOMS["all_num"], [217, 245, 216]),
    216: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    217: TransitionState(ATOMS["all_num"], [219, 245, 218]),
    218: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    219: TransitionState(ATOMS["all_num"], [221, 245, 220]),
    220: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    221: TransitionState(ATOMS["all_num"], [223, 245, 222]),
    222: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    223: TransitionState(ATOMS["all_num"], [225, 245, 224]),
    224: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    225: TransitionState(ATOMS["all_num"], [227, 245, 226]),
    226: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    227: TransitionState(ATOMS["all_num"], [229, 245, 228]),
    228: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    229: TransitionState(ATOMS["all_num"], [231, 245, 230]),
    230: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    231: TransitionState(ATOMS["all_num"], [233, 245, 232]),
    232: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    233: TransitionState(ATOMS["all_num"], [235, 245, 234]),
    234: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    235: TransitionState(ATOMS["all_num"], [237, 245, 236]),
    236: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    237: TransitionState(ATOMS["all_num"], [239, 245, 238]),
    238: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    239: TransitionState(ATOMS["all_num"], [241, 245, 240]),
    240: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    241: TransitionState(ATOMS["all_num"], [243, 245, 242]),
    242: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    243: TransitionState(ATOMS["all_num"], [245, 245, 244]),
    244: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # decimal point
    245: TransitionState(".", [246]),

    246: TransitionState(ATOMS["all_num"], [248, 247]),
    247: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    248: TransitionState(ATOMS["all_num"], [250, 249]),
    249: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    250: TransitionState(ATOMS["all_num"], [252, 251]),
    251: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    252: TransitionState(ATOMS["all_num"], [254, 253]),
    253: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    254: TransitionState(ATOMS["all_num"], [256, 255]),
    255: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    256: TransitionState(ATOMS["all_num"], [257]),
    257: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # STRING LITERALS
    # Single-quoted strings, no escapes (per DFA).
    # ─────────────────────────────────────────────────────────────
    258: TransitionState("'", [260, 259]),
    259: TransitionState(ATOMS["string_ascii"], [260, 259]),
    260: TransitionState("'", [261]),
    261: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
}