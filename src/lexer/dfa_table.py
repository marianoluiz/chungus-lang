"""DFA Transition Table for the Chungus lexer.

    Structure:
    - TransitionState: a node in the DFA
        accepted_chars : iterable (set/list) of allowed characters at this node
        next_states    : list[int] of target state IDs (ordered for disambiguation)
        is_terminal    : bool indicating an accepting (token boundary) state

    TRANSITION_TABLE:
        int state_id -> TransitionState

    Subgraph layout (state ID ranges):
        1..117   : keywords / reserved words
        118..161 : operators, delimiters, punctuation
        162..171 : comments
                - 162 '#' entry
                - Single-line: 163* -> 164 (newline)
                - Multi-line: ### open (165->166->167 loop) then ### close (168->169->170->171)
        172..174 : identifiers (start, body loop, delimiter check)
        175..226 : numeric literals
                - 175 optional unary '-'
                - 176..213 whole number (up to 19 digits, every other state terminal)
                - 214 '.' decimal point
                - 215..226 fractional part (up to 6 digits, every other state terminal)
        227..230 : single-quoted string literals

    Terminal states:
    - is_terminal=True means: lexemize stops path here and validates the following delimiter
    - Delimiter sets sourced from constants.DELIMS

    Notes:
    - Keyword prefixes that continue into identifiers will backtrack one char (handled in lexer.lexemize).
    - The initial state (0) holds fan‑out into all possible leading token characters.
"""

from src.constants import ATOMS, DELIMS

class TransitionState:
    def __init__(self, accepted_chars: list[str], next_states: list[int] = [], is_terminal = False):
        self.accepted_chars = [accepted_chars] if type(accepted_chars) is str else accepted_chars
        self.next_states = [next_states] if type(next_states) is int else next_states
        self.is_terminal = is_terminal

TRANSITION_TABLE = {
    0: TransitionState('initial', [1, 27, 31, 43, 62, 69, 73, 76, 88, 99, 112, 118, 
                        122, 126, 130, 132, 136, 140, 144, 148, 152, 154, 156, 
                        158, 160, 162, 172, 175, 176, 227]),
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
    14: TransitionState('y', [15, 20]),
    15: TransitionState('_', [16]),
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
    27: TransitionState('c', [28]),
    28: TransitionState('l', [29]),
    29: TransitionState('r', [30]),
    30: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    31: TransitionState('e', [32, 39]),
    32: TransitionState('l', [33]),
    33: TransitionState('i', [34]),
    34: TransitionState('f', [35]),
    35: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    36: TransitionState('s', [37]),
    37: TransitionState('e', [38]),
    38: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    39: TransitionState('x', [40]),
    40: TransitionState('i', [41]),
    41: TransitionState('t', [42]),
    42: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    43: TransitionState('f', [44, 52, 57, 59]),
    44: TransitionState('a', [45, 49]),
    45: TransitionState('l', [46]),
    46: TransitionState('s', [47]),
    47: TransitionState('e', [48]),
    48: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    49: TransitionState('i', [50]),
    50: TransitionState('l', [51]),
    51: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    52: TransitionState('l', [53]),
    53: TransitionState('o', [54]),
    54: TransitionState('a', [55]),
    55: TransitionState('t', [56]),
    56: TransitionState(DELIMS['method_delim'], is_terminal=True),
    57: TransitionState('n', [58]),
    58: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    59: TransitionState('o', [60]),
    60: TransitionState('r', [61]),
    61: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    62: TransitionState('i', [63, 65]),
    63: TransitionState('f', [64]),
    64: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    65: TransitionState('n', [66, 67]),
    66: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    67: TransitionState('t', [68]),
    68: TransitionState(DELIMS['method_delim'], is_terminal=True),

    69: TransitionState('n', [70]),
    70: TransitionState('i', [71]),
    71: TransitionState('l', [72]),
    72: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    73: TransitionState('o', [74]),
    74: TransitionState('r', [75]),
    75: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    76: TransitionState('r', [77, 82]),
    77: TransitionState('a', [78]),
    78: TransitionState('n', [79]),
    79: TransitionState('g', [80]),
    80: TransitionState('e', [81]),
    81: TransitionState(DELIMS['method_delim'], is_terminal=True),
    82: TransitionState('e', [83, 86]),
    83: TransitionState('a', [84]),
    84: TransitionState('d', [85]),
    85: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    86: TransitionState('t', [87]),
    87: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    88: TransitionState('t', [89, 93]),
    89: TransitionState('o', [90]),
    90: TransitionState('d', [91]),
    91: TransitionState('o', [92]),
    92: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    93: TransitionState('r', [94, 97]),
    94: TransitionState('u', [95]),
    95: TransitionState('e', [96]),
    96: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    97: TransitionState('y', [98]),
    98: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    99: TransitionState('s', [100, 104, 108]),
    100: TransitionState('h', [101]),
    101: TransitionState('o', [102]),
    102: TransitionState('w', [103]),
    103: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    104: TransitionState('k', [105]),
    105: TransitionState('i', [106]),
    106: TransitionState('p', [107]),
    107: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    108: TransitionState('t', [109]),
    109: TransitionState('o', [110]),
    110: TransitionState('p', [111]),
    111: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    112: TransitionState('w', [113]),
    113: TransitionState('h', [114]),
    114: TransitionState('i', [115]),
    115: TransitionState('l', [116]),
    116: TransitionState('e', [117]),
    117: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    118: TransitionState('+', [119, 120]),
    119: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    120: TransitionState('+', [121]),
    121: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    122: TransitionState('-', [123, 124]),
    123: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    124: TransitionState('-', [125]),
    125: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    126: TransitionState('*', [127, 128]),
    127: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    128: TransitionState('*', [129]),
    129: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    130: TransitionState('%', [131]),
    131: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    132: TransitionState('/', [133, 134]),
    133: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    134: TransitionState('/', [135]),
    135: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    136: TransitionState('=', [137, 138]),
    137: TransitionState(DELIMS['assign_op_delim'], is_terminal=True),
    138: TransitionState('=', [139]),
    139: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    140: TransitionState('!', [141, 142]),
    141: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    142: TransitionState('=', [143]),
    143: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    144: TransitionState('<', [145, 146]),
    145: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    146: TransitionState('=', [147]),
    147: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    148: TransitionState('>', [149, 150]),
    149: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    150: TransitionState('=', [151]),
    151: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),

    152: TransitionState('(', [153]),
    153: TransitionState(DELIMS['paren_open_delim'], is_terminal=True),
    154: TransitionState(')', [155]),
    155: TransitionState(DELIMS['paren_close_delim'], is_terminal=True),
    156: TransitionState('[', [157]),
    157: TransitionState(DELIMS['bracket_open_delim'], is_terminal=True),
    158: TransitionState(']', [159]),
    159: TransitionState(DELIMS['bracket_close_delim'], is_terminal=True),
    160: TransitionState(',', [161]),
    161: TransitionState(DELIMS['comma_delim'], is_terminal=True),

    # --- Comments ---
    162: TransitionState('#', [163, 164, 165]),
    163: TransitionState(ATOMS['single_comment_ascii'], [163, 164]),
    164: TransitionState({'\n'}, is_terminal=True),
    165: TransitionState('#', [166]),
    166: TransitionState('#', [167, 168]),
    167: TransitionState(ATOMS['multiline_comment_ascii'], [167, 168]),
    168: TransitionState('#', [169]),
    169: TransitionState('#', [170]),
    170: TransitionState('#', [171]),
    171: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Identifiers ---
    172: TransitionState({*ATOMS['all_alphabet'], '_'}, [173, 174]),
    173: TransitionState(ATOMS['under_alpha_num'], [173, 174]),
    174: TransitionState(DELIMS['id_delim'], is_terminal=True),

    # --- Numeric Literals ---
    175: TransitionState({'-'}, [176]),
    176: TransitionState(ATOMS['all_num'], [177, 178, 214]),
    177: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    178: TransitionState(ATOMS['all_num'], [179, 180, 214]),
    179: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    180: TransitionState(ATOMS['all_num'], [181, 182, 214]),
    181: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    182: TransitionState(ATOMS['all_num'], [183, 184, 214]),
    183: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    
    184: TransitionState(ATOMS['all_num'], [185, 186, 214]),
    185: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    186: TransitionState(ATOMS['all_num'], [187, 188, 214]),
    187: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    188: TransitionState(ATOMS['all_num'], [189, 190, 214]),
    189: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    190: TransitionState(ATOMS['all_num'], [191, 192, 214]),
    191: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    192: TransitionState(ATOMS['all_num'], [193, 194, 214]),
    193: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    194: TransitionState(ATOMS['all_num'], [195, 196, 214]),
    195: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    196: TransitionState(ATOMS['all_num'], [197, 198, 214]),
    197: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    198: TransitionState(ATOMS['all_num'], [199, 200, 214]),
    199: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    200: TransitionState(ATOMS['all_num'], [201, 202, 214]),
    201: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    202: TransitionState(ATOMS['all_num'], [203, 204, 214]),
    203: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    204: TransitionState(ATOMS['all_num'], [205, 206, 214]),
    205: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    206: TransitionState(ATOMS['all_num'], [207, 208, 214]),
    207: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    208: TransitionState(ATOMS['all_num'], [209, 210, 214]),
    209: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    210: TransitionState(ATOMS['all_num'], [211, 212, 214]),
    211: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    212: TransitionState(ATOMS['all_num'], [213, 214]),
    213: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    214: TransitionState('.', [215]),
    215: TransitionState(ATOMS['all_num'], [216, 217]),
    216: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    217: TransitionState(ATOMS['all_num'], [218, 219]),
    218: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    219: TransitionState(ATOMS['all_num'], [220, 221]),
    220: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    221: TransitionState(ATOMS['all_num'], [222, 223]),
    222: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    223: TransitionState(ATOMS['all_num'], [224, 225]),
    224: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    225: TransitionState(ATOMS['all_num'], [226]),
    226: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    # --- String Literals ---
    227: TransitionState("'", [228, 229]),
    228: TransitionState(ATOMS['string_ascii'], [228, 229]),
    229: TransitionState("'", [230]),
    230: TransitionState(DELIMS['stmt_delim'], is_terminal=True)
}
