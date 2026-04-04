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
            1, 15, 28, 36, 52, 59, 66, 69, 81, 90, 105,
            # symbols/operators
            111, 113, 115, 119, 121, 125, 129, 133, 137, 141, 143, 145, 147, 149, 151, 153,
            # comments
            155,
            # identifiers
            165,
            # numerics
            213, 214,
            # strings
            265,
        ],
    ),

    # ─────────────────────────────────────────────────────────────
    # KEYWORDS
    # ─────────────────────────────────────────────────────────────

    # and, arr_to_str
    1: TransitionState("a", [2, 5]),
    2: TransitionState("n", [3]),
    3: TransitionState("d", [4]),
    4: TransitionState(DELIMS["token_delim"], is_terminal=True),
    5: TransitionState("r", [6]),
    6: TransitionState("r", [7]),
    7: TransitionState("_", [8]),
    8: TransitionState("t", [9]),
    9: TransitionState("o", [10]),
    10: TransitionState("_", [11]),
    11: TransitionState("s", [12]),
    12: TransitionState("t", [13]),
    13: TransitionState("r", [14]),
    14: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # close, compare
    15: TransitionState("c", [16, 21]),
    16: TransitionState("l", [17]),
    17: TransitionState("o", [18]),
    18: TransitionState("s", [19]),
    19: TransitionState("e", [20]),
    20: TransitionState(DELIMS["token_delim"], is_terminal=True),
    21: TransitionState("o", [22]),
    22: TransitionState("m", [23]),
    23: TransitionState("p", [24]),
    24: TransitionState("a", [25]),
    25: TransitionState("r", [26]),
    26: TransitionState("e", [27]),
    27: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # elif, else
    28: TransitionState("e", [29]),
    29: TransitionState("l", [30, 33]),
    30: TransitionState("i", [31]),
    31: TransitionState("f", [32]),
    32: TransitionState(DELIMS["token_delim"], is_terminal=True),
    33: TransitionState("s", [34]),
    34: TransitionState("e", [35]),
    35: TransitionState(DELIMS["blk_header_delim"], is_terminal=True),

    # false, float, fn, for
    36: TransitionState("f", [37, 42, 47, 49]),
    37: TransitionState("a", [38]),
    38: TransitionState("l", [39]),
    39: TransitionState("s", [40]),
    40: TransitionState("e", [41]),
    41: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    42: TransitionState("l", [43]),
    43: TransitionState("o", [44]),
    44: TransitionState("a", [45]),
    45: TransitionState("t", [46]),
    46: TransitionState(DELIMS["method_delim"], is_terminal=True),
    47: TransitionState("n", [48]),
    48: TransitionState(DELIMS["token_delim"], is_terminal=True),
    49: TransitionState("o", [50]),
    50: TransitionState("r", [51]),
    51: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # if, in, int
    52: TransitionState("i", [53, 55]),
    53: TransitionState("f", [54]),
    54: TransitionState(DELIMS["token_delim"], is_terminal=True),
    55: TransitionState("n", [57, 56]),
    56: TransitionState(DELIMS["token_delim"], is_terminal=True),
    57: TransitionState("t", [58]),
    58: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # length
    59: TransitionState("l", [60]),
    60: TransitionState("e", [61]),
    61: TransitionState("n", [62]),
    62: TransitionState("g", [63]),
    63: TransitionState("t", [64]),
    64: TransitionState("h", [65]),
    65: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # or
    66: TransitionState("o", [67]),
    67: TransitionState("r", [68]),
    68: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # range, read, ret
    69: TransitionState("r", [70, 75]),
    70: TransitionState("a", [71]),
    71: TransitionState("n", [72]),
    72: TransitionState("g", [73]),
    73: TransitionState("e", [74]),
    74: TransitionState(DELIMS["method_delim"], is_terminal=True),
    75: TransitionState("e", [76, 79]),
    76: TransitionState("a", [77]),
    77: TransitionState("d", [78]),
    78: TransitionState(DELIMS["stmt_delim"], is_terminal=True),
    79: TransitionState("t", [80]),
    80: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # todo, true
    81: TransitionState("t", [82, 86]),
    82: TransitionState("o", [83]),
    83: TransitionState("d", [84]),
    84: TransitionState("o", [85]),
    85: TransitionState(DELIMS["stmt_delim"], is_terminal=True),
    86: TransitionState("r", [87]),
    87: TransitionState("u", [88]),
    88: TransitionState("e", [89]),
    89: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # show, str_to_arr
    90: TransitionState("s", [91, 95]),
    91: TransitionState("h", [92]),
    92: TransitionState("o", [93]),
    93: TransitionState("w", [94]),
    94: TransitionState(DELIMS["token_delim"], is_terminal=True),
    95: TransitionState("t", [96]),
    96: TransitionState("r", [97]),
    97: TransitionState("_", [98]),
    98: TransitionState("t", [99]),
    99: TransitionState("o", [100]),
    100: TransitionState("_", [101]),
    101: TransitionState("a", [102]),
    102: TransitionState("r", [103]),
    103: TransitionState("r", [104]),
    104: TransitionState(DELIMS["method_delim"], is_terminal=True),

    # while
    105: TransitionState("w", [106]),
    106: TransitionState("h", [107]),
    107: TransitionState("i", [108]),
    108: TransitionState("l", [109]),
    109: TransitionState("e", [110]),
    110: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # SYMBOLS / OPERATORS
    # ─────────────────────────────────────────────────────────────
    
    111: TransitionState("+", [112]),
    112: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    113: TransitionState("-", [114]),
    114: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    115: TransitionState("*", [117, 116]),
    116: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    117: TransitionState("*", [118]),
    118: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    119: TransitionState("%", [120]),
    120: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    121: TransitionState("/", [123, 122]),
    122: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    123: TransitionState("/", [124]),
    124: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    125: TransitionState("=", [127, 126]),
    126: TransitionState(DELIMS["assign_op_delim"], is_terminal=True),
    127: TransitionState("=", [128]),
    128: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    129: TransitionState("!", [131, 130]),
    130: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    131: TransitionState("=", [132]),
    132: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    133: TransitionState("<", [135, 134]),
    134: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    135: TransitionState("=", [136]),
    136: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    137: TransitionState(">", [139, 138]),
    138: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),
    139: TransitionState("=", [140]),
    140: TransitionState(DELIMS["arith_rel_not_op_delim"], is_terminal=True),

    # Delimiters
    141: TransitionState("(", [142]),
    142: TransitionState(DELIMS["paren_open_delim"], is_terminal=True),

    143: TransitionState(")", [144]),
    144: TransitionState(DELIMS["paren_close_delim"], is_terminal=True),

    145: TransitionState("[", [146]),
    146: TransitionState(DELIMS["bracket_open_delim"], is_terminal=True),

    147: TransitionState("]", [148]),
    148: TransitionState(DELIMS["bracket_close_delim"], is_terminal=True),

    149: TransitionState(",", [150]),
    150: TransitionState(DELIMS["comma_delim"], is_terminal=True),

    151: TransitionState(":", [152]),
    152: TransitionState(DELIMS["colon_delim"], is_terminal=True),

    153: TransitionState(";", [154]),
    154: TransitionState(DELIMS["terminator_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # COMMENTS
    # ─────────────────────────────────────────────────────────────

    155: TransitionState("#", [158, 156, 157]),
    156: TransitionState(ATOMS["single_comment_ascii"], [156, 157]),
    157: TransitionState("\n", is_terminal=True),
    158: TransitionState("#", [159]),
    159: TransitionState("#", [160, 161]),
    160: TransitionState(ATOMS["multiline_comment_ascii"], [160, 161]),
    161: TransitionState("#", [162]),
    162: TransitionState("#", [163]),
    163: TransitionState("#", [164]),
    164: TransitionState(DELIMS["token_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # IDENTIFIERS
    # ─────────────────────────────────────────────────────────────

    165: TransitionState({*ATOMS["all_alphabet"], "_"}, [167, 166]),
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
    187: TransitionState(ATOMS["under_alpha_num"], [189, 188]),
    188: TransitionState(DELIMS["id_delim"], is_terminal=True),
    189: TransitionState(ATOMS["under_alpha_num"], [191, 190]),
    190: TransitionState(DELIMS["id_delim"], is_terminal=True),
    191: TransitionState(ATOMS["under_alpha_num"], [193, 192]),
    192: TransitionState(DELIMS["id_delim"], is_terminal=True),
    193: TransitionState(ATOMS["under_alpha_num"], [195, 194]),
    194: TransitionState(DELIMS["id_delim"], is_terminal=True),
    195: TransitionState(ATOMS["under_alpha_num"], [197, 196]),
    196: TransitionState(DELIMS["id_delim"], is_terminal=True),
    197: TransitionState(ATOMS["under_alpha_num"], [199, 198]),
    198: TransitionState(DELIMS["id_delim"], is_terminal=True),
    199: TransitionState(ATOMS["under_alpha_num"], [201, 200]),
    200: TransitionState(DELIMS["id_delim"], is_terminal=True),
    201: TransitionState(ATOMS["under_alpha_num"], [203, 202]),
    202: TransitionState(DELIMS["id_delim"], is_terminal=True),
    203: TransitionState(ATOMS["under_alpha_num"], [205, 204]),
    204: TransitionState(DELIMS["id_delim"], is_terminal=True),
    205: TransitionState(ATOMS["under_alpha_num"], [207, 206]),
    206: TransitionState(DELIMS["id_delim"], is_terminal=True),
    207: TransitionState(ATOMS["under_alpha_num"], [209, 208]),
    208: TransitionState(DELIMS["id_delim"], is_terminal=True),
    209: TransitionState(ATOMS["under_alpha_num"], [211, 210]),
    210: TransitionState(DELIMS["id_delim"], is_terminal=True),
    211: TransitionState(ATOMS["under_alpha_num"], [212]), 
    212: TransitionState(DELIMS["id_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # NUMERIC LITERALS
    # ─────────────────────────────────────────────────────────────
    
    213: TransitionState("~", [214]),
    214: TransitionState(ATOMS["all_num"], [216, 252, 215]), 
    215: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    216: TransitionState(ATOMS["all_num"], [218, 252, 217]),
    217: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    218: TransitionState(ATOMS["all_num"], [220, 252, 219]),
    219: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    220: TransitionState(ATOMS["all_num"], [222, 252, 221]),
    221: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    222: TransitionState(ATOMS["all_num"], [224, 252, 223]),
    223: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    224: TransitionState(ATOMS["all_num"], [226, 252, 225]),
    225: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    226: TransitionState(ATOMS["all_num"], [228, 252, 227]),
    227: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    228: TransitionState(ATOMS["all_num"], [230, 252, 229]),
    229: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    230: TransitionState(ATOMS["all_num"], [232, 252, 231]),
    231: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    232: TransitionState(ATOMS["all_num"], [234, 252, 233]),
    233: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    234: TransitionState(ATOMS["all_num"], [236, 252, 235]),
    235: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    236: TransitionState(ATOMS["all_num"], [238, 252, 237]),
    237: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    238: TransitionState(ATOMS["all_num"], [240, 252, 239]),
    239: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    240: TransitionState(ATOMS["all_num"], [242, 252, 241]),
    241: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    242: TransitionState(ATOMS["all_num"], [244, 252, 243]),
    243: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    244: TransitionState(ATOMS["all_num"], [246, 252, 245]),
    245: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    246: TransitionState(ATOMS["all_num"], [248, 252, 247]),
    247: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    248: TransitionState(ATOMS["all_num"], [250, 252, 249]),
    249: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    250: TransitionState(ATOMS["all_num"], [252, 251]), 
    251: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # Decimal
    252: TransitionState(".", [253]),
    253: TransitionState(ATOMS["all_num"], [255, 254]),
    254: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    255: TransitionState(ATOMS["all_num"], [257, 256]),
    256: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    257: TransitionState(ATOMS["all_num"], [259, 258]),
    258: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    259: TransitionState(ATOMS["all_num"], [261, 260]),
    260: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    261: TransitionState(ATOMS["all_num"], [263, 262]),
    262: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
    263: TransitionState(ATOMS["all_num"], [264]), 
    264: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),

    # ─────────────────────────────────────────────────────────────
    # STRING LITERALS
    # ─────────────────────────────────────────────────────────────
    
    265: TransitionState("'", [266, 267]),
    266: TransitionState(ATOMS["string_ascii"], [266, 267]),
    267: TransitionState("'", [268]),
    268: TransitionState(DELIMS["dtype_lit_delim"], is_terminal=True),
}