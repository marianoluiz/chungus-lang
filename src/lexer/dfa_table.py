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
            1, 5, 11, 19, 35, 42, 45, 57, 66, 71,
            # symbols/operators
            77, 79, 81, 85, 87, 91, 95, 99, 113, 117, 119, 121, 123, 125, 127, 129,
            # comments
            131,
            # identifiers
            141,
            # numerics (optional leading "~" or digit)
            189, 190,
            # strings
            241,
        ],
    ),

    # ─────────────────────────────────────────────────────────────
    # KEYWORDS
    # ─────────────────────────────────────────────────────────────

# and
    1: TransitionState("a", [2]),
    2: TransitionState("n", [3]),
    3: TransitionState("d", [4]),
    4: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # close
    5: TransitionState("c", [6]),
    6: TransitionState("l", [7]),
    7: TransitionState("o", [8]),
    8: TransitionState("s", [9]),
    9: TransitionState("e", [10]),
    10: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # elif, else
    11: TransitionState("e", [12]),
    12: TransitionState("l", [13, 16]),
    13: TransitionState("i", [14]),
    14: TransitionState("f", [15]),
    15: TransitionState(DELIMS["token_delim"], is_terminal=True),

    16: TransitionState("s", [17]),
    17: TransitionState("e", [18]),
    18: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    # false, float, fn, for
    19: TransitionState("f", [20, 25, 30, 32]),
    20: TransitionState("a", [21]),
    21: TransitionState("l", [22]),
    22: TransitionState("s", [23]),
    23: TransitionState("e", [24]),
    24: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    25: TransitionState("l", [26]),
    26: TransitionState("o", [27]),
    27: TransitionState("a", [28]),
    28: TransitionState("t", [29]),
    29: TransitionState(DELIMS["method_delim"], is_terminal=True),

    30: TransitionState("n", [31]),
    31: TransitionState(DELIMS["token_delim"], is_terminal=True),

    32: TransitionState("o", [33]),
    33: TransitionState("r", [34]),
    34: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # if, in, int
    35: TransitionState("i", [36, 38]),
    36: TransitionState("f", [37]),
    37: TransitionState(DELIMS["token_delim"], is_terminal=True),

    38: TransitionState("n", [40, 39]), # Delim last
    39: TransitionState(DELIMS["token_delim"], is_terminal=True),

    40: TransitionState("t", [41]),
    41: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # or
    42: TransitionState("o", [43]),
    43: TransitionState("r", [44]),
    44: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # range, read, ret
    45: TransitionState("r", [46, 51]),
    46: TransitionState("a", [47]),
    47: TransitionState("n", [48]),
    48: TransitionState("g", [49]),
    49: TransitionState("e", [50]),
    50: TransitionState(DELIMS["method_delim"], is_terminal=True),

    51: TransitionState("e", [52, 55]),
    52: TransitionState("a", [53]),
    53: TransitionState("d", [54]),
    54: TransitionState(DELIMS["stmt_delim"], is_terminal=True),

    55: TransitionState("t", [56]),
    56: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # todo, true
    57: TransitionState("t", [58, 62]),
    58: TransitionState("o", [59]),
    59: TransitionState("d", [60]),
    60: TransitionState("o", [61]),
    61: TransitionState(DELIMS["stmt_delim"], is_terminal=True),

    62: TransitionState("r", [63]),
    63: TransitionState("u", [64]),
    64: TransitionState("e", [65]),
    65: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # show
    66: TransitionState("s", [67]),
    67: TransitionState("h", [68]),
    68: TransitionState("o", [69]),
    69: TransitionState("w", [70]),
    70: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # while
    71: TransitionState("w", [72]),
    72: TransitionState("h", [73]),
    73: TransitionState("i", [74]),
    74: TransitionState("l", [75]),
    75: TransitionState("e", [76]),
    76: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # SYMBOLS / OPERATORS
    # ─────────────────────────────────────────────────────────────
    
    77: TransitionState("+", [78]),
    78: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    79: TransitionState("-", [80]),
    80: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    81: TransitionState("*", [83, 82]), # Delim last
    82: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    83: TransitionState("*", [84]),
    84: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    85: TransitionState("%", [86]),
    86: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    87: TransitionState("/", [89, 88]), # Delim last
    88: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    89: TransitionState("/", [90]),
    90: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    91: TransitionState("=", [93, 92]), # Delim last
    92: TransitionState(DELIMS["assign_op_delim"], is_terminal=True),
    93: TransitionState("=", [94]),
    94: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    95: TransitionState("!", [97, 96]), # Delim last
    96: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    97: TransitionState("=", [98]),
    98: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    99: TransitionState("<", [111, 100]), # Delim last
    100: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    111: TransitionState("=", [112]),
    112: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    113: TransitionState(">", [115, 114]), # Delim last
    114: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    115: TransitionState("=", [116]),
    116: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # DELIMITERS
    # ─────────────────────────────────────────────────────────────
    
    117: TransitionState("(", [118]),
    118: TransitionState(DELIMS["paren_open_delim"], is_terminal=True),

    119: TransitionState(")", [120]),
    120: TransitionState(DELIMS["paren_close_delim"], is_terminal=True),

    121: TransitionState("[", [122]),
    122: TransitionState(DELIMS["bracket_open_delim"], is_terminal=True),

    123: TransitionState("]", [124]),
    124: TransitionState(DELIMS["bracket_close_delim"], is_terminal=True),

    125: TransitionState(",", [126]),
    126: TransitionState(DELIMS["comma_delim"], is_terminal=True),

    127: TransitionState(":", [128]),
    128: TransitionState(DELIMS["colon_delim"], is_terminal=True),

    129: TransitionState(";", [130]),
    130: TransitionState(DELIMS["terminator_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # COMMENTS
    # ─────────────────────────────────────────────────────────────

    131: TransitionState("#", [134, 132, 133]), # '\n' acts as a terminating delimiter here, keeping it last
    132: TransitionState(ATOMS["single_comment_ascii"], [132, 133]),
    133: TransitionState("\n", is_terminal=True),

    134: TransitionState("#", [135]),
    135: TransitionState("#", [136, 137]),
    136: TransitionState(ATOMS["multiline_comment_ascii"], [136, 137]),
    137: TransitionState("#", [138]),
    138: TransitionState("#", [139]),
    139: TransitionState("#", [140]),
    140: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # IDENTIFIERS
    # ─────────────────────────────────────────────────────────────

    141: TransitionState({*ATOMS["all_alphabet"], "_"}, [143, 142]), # Delim last
    142: TransitionState(DELIMS["id_delim"], is_terminal=True),

    143: TransitionState(ATOMS["under_alpha_num"], [145, 144]),
    144: TransitionState(DELIMS["id_delim"], is_terminal=True),

    145: TransitionState(ATOMS["under_alpha_num"], [147, 146]),
    146: TransitionState(DELIMS["id_delim"], is_terminal=True),

    147: TransitionState(ATOMS["under_alpha_num"], [149, 148]),
    148: TransitionState(DELIMS["id_delim"], is_terminal=True),

    149: TransitionState(ATOMS["under_alpha_num"], [151, 150]),
    150: TransitionState(DELIMS["id_delim"], is_terminal=True),

    151: TransitionState(ATOMS["under_alpha_num"], [153, 152]),
    152: TransitionState(DELIMS["id_delim"], is_terminal=True),

    153: TransitionState(ATOMS["under_alpha_num"], [155, 154]),
    154: TransitionState(DELIMS["id_delim"], is_terminal=True),

    155: TransitionState(ATOMS["under_alpha_num"], [157, 156]),
    156: TransitionState(DELIMS["id_delim"], is_terminal=True),

    157: TransitionState(ATOMS["under_alpha_num"], [159, 158]),
    158: TransitionState(DELIMS["id_delim"], is_terminal=True),

    159: TransitionState(ATOMS["under_alpha_num"], [161, 160]),
    160: TransitionState(DELIMS["id_delim"], is_terminal=True),

    161: TransitionState(ATOMS["under_alpha_num"], [163, 162]),
    162: TransitionState(DELIMS["id_delim"], is_terminal=True),

    163: TransitionState(ATOMS["under_alpha_num"], [165, 164]),
    164: TransitionState(DELIMS["id_delim"], is_terminal=True),

    165: TransitionState(ATOMS["under_alpha_num"], [167, 166]),
    166: TransitionState(DELIMS["id_delim"], is_terminal=True),

    167: TransitionState(ATOMS["under_alpha_num"], [169, 168]),
    168: TransitionState(DELIMS["id_delim"], is_terminal=True),

    169: TransitionState(ATOMS["under_alpha_num"], [171, 170]),
    170: TransitionState(DELIMS["id_delim"], is_terminal=True),

    171: TransitionState(ATOMS["under_alpha_num"], [173, 172]),
    172: TransitionState(DELIMS["id_delim"], is_terminal=True),

    173: TransitionState(ATOMS["under_alpha_num"], [175, 174]),
    174: TransitionState(DELIMS["id_delim"], is_terminal=True),

    175: TransitionState(ATOMS["under_alpha_num"], [177, 176]),
    176: TransitionState(DELIMS["id_delim"], is_terminal=True),

    177: TransitionState(ATOMS["under_alpha_num"], [179, 178]),
    178: TransitionState(DELIMS["id_delim"], is_terminal=True),

    179: TransitionState(ATOMS["under_alpha_num"], [181, 180]),
    180: TransitionState(DELIMS["id_delim"], is_terminal=True),

    181: TransitionState(ATOMS["under_alpha_num"], [183, 182]),
    182: TransitionState(DELIMS["id_delim"], is_terminal=True),

    183: TransitionState(ATOMS["under_alpha_num"], [185, 184]),
    184: TransitionState(DELIMS["id_delim"], is_terminal=True),

    185: TransitionState(ATOMS["under_alpha_num"], [187, 186]),
    186: TransitionState(DELIMS["id_delim"], is_terminal=True),

    187: TransitionState(ATOMS["under_alpha_num"], [188]), # No more valid letters/numbers allowed past 24 chars
    188: TransitionState(DELIMS["id_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # NUMERIC LITERALS
    # ─────────────────────────────────────────────────────────────
    
    189: TransitionState("~", [190]),

    190: TransitionState(ATOMS["all_num"], [192, 228, 191]), # 191 is delim
    191: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    192: TransitionState(ATOMS["all_num"], [194, 228, 193]), # 193 is delim
    193: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    194: TransitionState(ATOMS["all_num"], [196, 228, 195]),
    195: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    196: TransitionState(ATOMS["all_num"], [198, 228, 197]),
    197: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    198: TransitionState(ATOMS["all_num"], [200, 228, 199]),
    199: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    200: TransitionState(ATOMS["all_num"], [202, 228, 201]),
    201: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    202: TransitionState(ATOMS["all_num"], [204, 228, 203]),
    203: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    204: TransitionState(ATOMS["all_num"], [206, 228, 205]),
    205: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    206: TransitionState(ATOMS["all_num"], [208, 228, 207]),
    207: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    208: TransitionState(ATOMS["all_num"], [210, 228, 209]),
    209: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    210: TransitionState(ATOMS["all_num"], [212, 228, 211]),
    211: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    212: TransitionState(ATOMS["all_num"], [214, 228, 213]),
    213: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    214: TransitionState(ATOMS["all_num"], [216, 228, 215]),
    215: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    216: TransitionState(ATOMS["all_num"], [218, 228, 217]),
    217: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    218: TransitionState(ATOMS["all_num"], [220, 228, 219]),
    219: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    220: TransitionState(ATOMS["all_num"], [222, 228, 221]),
    221: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    222: TransitionState(ATOMS["all_num"], [224, 228, 223]),
    223: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    224: TransitionState(ATOMS["all_num"], [226, 228, 225]),
    225: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    226: TransitionState(ATOMS["all_num"], [228, 227]), # Reached bounds, forced to jump to decimal or delimit
    227: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # Decimal point
    228: TransitionState(".", [229]),

    # Decimal digits
    229: TransitionState(ATOMS["all_num"], [231, 230]),
    230: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    231: TransitionState(ATOMS["all_num"], [233, 232]),
    232: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    233: TransitionState(ATOMS["all_num"], [235, 234]),
    234: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    235: TransitionState(ATOMS["all_num"], [237, 236]),
    236: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    237: TransitionState(ATOMS["all_num"], [239, 238]),
    238: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    239: TransitionState(ATOMS["all_num"], [240]),
    240: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # STRING LITERALS
    # ─────────────────────────────────────────────────────────────
    
    241: TransitionState("'", [242, 243]),
    242: TransitionState(ATOMS["string_ascii"], [242, 243]),
    243: TransitionState("'", [244]),
    244: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
}