"""DFA Transition Table for the Chungus lexer.

    Structure:
    - TransitionState: a node in the DFA
        accepted_chars : iterable (set/list) of allowed characters at this node
        next_states    : list[int] of target state IDs (ordered for disambiguation)
        is_terminal    : bool indicating an accepting (token boundary) state

    TRANSITION_TABLE:
        int state_id -> TransitionState

    Subgraph layout (state ID ranges):
        1..121   : keywords / reserved words (added 'close')
        122..165 : operators, delimiters, punctuation
        166..175 : comments
                 - 166 '#' entry
                 - Single-line: 167* -> 168 (newline)
                 - Multi-line: ### open (169->170->171 loop) then ### close (172->173->174->175)
        176..178 : identifiers (start, body loop, delimiter check)
        179..230 : numeric literals
                 - 179 optional unary '-'
                 - 180..217 whole number (up to 19 digits, every other state terminal)
                 - 218 '.' decimal point
                 - 219..230 fractional part (up to 6 digits, every other state terminal)
        231..234 : single-quoted string literals

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
    0: TransitionState('initial', [1, 27, 35, 47, 66, 73, 77, 80, 92, 103, 116, 122, 
                                   126, 130, 134, 136, 140, 144, 148, 152, 156, 158, 160, 
                                   162, 164, 166, 176, 179, 180, 231]),
    
    # --- Keywords (1-121) ---
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
    
    28: TransitionState('l', [29, 31]), 
    
    29: TransitionState('r', [30]),
    30: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    
    31: TransitionState('o', [32]),
    32: TransitionState('s', [33]),
    33: TransitionState('e', [34]),
    34: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    35: TransitionState('e', [36, 43]),
    36: TransitionState('l', [37]),
    37: TransitionState('i', [38]),
    38: TransitionState('f', [39]),
    39: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    40: TransitionState('s', [41]),
    41: TransitionState('e', [42]),
    42: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    43: TransitionState('x', [44]),
    44: TransitionState('i', [45]),
    45: TransitionState('t', [46]),
    46: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    47: TransitionState('f', [48, 56, 61, 63]),
    48: TransitionState('a', [49, 53]),
    49: TransitionState('l', [50]),
    50: TransitionState('s', [51]),
    51: TransitionState('e', [52]),
    52: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    53: TransitionState('i', [54]),
    54: TransitionState('l', [55]),
    55: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    56: TransitionState('l', [57]),
    57: TransitionState('o', [58]),
    58: TransitionState('a', [59]),
    59: TransitionState('t', [60]),
    60: TransitionState(DELIMS['method_delim'], is_terminal=True),
    61: TransitionState('n', [62]),
    62: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    63: TransitionState('o', [64]),
    64: TransitionState('r', [65]),
    65: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    66: TransitionState('i', [67, 69]),
    67: TransitionState('f', [68]),
    68: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    69: TransitionState('n', [70, 71]),
    70: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    71: TransitionState('t', [72]),
    72: TransitionState(DELIMS['method_delim'], is_terminal=True),
    73: TransitionState('n', [74]),
    74: TransitionState('i', [75]),
    75: TransitionState('l', [76]),
    76: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    77: TransitionState('o', [78]),
    78: TransitionState('r', [79]),
    79: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    80: TransitionState('r', [81, 86]),
    81: TransitionState('a', [82]),
    82: TransitionState('n', [83]),
    83: TransitionState('g', [84]),
    84: TransitionState('e', [85]),
    85: TransitionState(DELIMS['method_delim'], is_terminal=True),
    86: TransitionState('e', [87, 90]),
    87: TransitionState('a', [88]),
    88: TransitionState('d', [89]),
    89: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    90: TransitionState('t', [91]),
    91: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    92: TransitionState('t', [93, 97]),
    93: TransitionState('o', [94]),
    94: TransitionState('d', [95]),
    95: TransitionState('o', [96]),
    96: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    97: TransitionState('r', [98, 101]),
    98: TransitionState('u', [99]),
    99: TransitionState('e', [100]),
    100: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    101: TransitionState('y', [102]),
    102: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    103: TransitionState('s', [104, 108, 112]),
    104: TransitionState('h', [105]),
    105: TransitionState('o', [106]),
    106: TransitionState('w', [107]),
    107: TransitionState(DELIMS['inline_delim'], is_terminal=True),
    108: TransitionState('k', [109]),
    109: TransitionState('i', [110]),
    110: TransitionState('p', [111]),
    111: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    112: TransitionState('t', [113]),
    113: TransitionState('o', [114]),
    114: TransitionState('p', [115]),
    115: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    116: TransitionState('w', [117]),
    117: TransitionState('h', [118]),
    118: TransitionState('i', [119]),
    119: TransitionState('l', [120]),
    120: TransitionState('e', [121]),
    121: TransitionState(DELIMS['inline_delim'], is_terminal=True),

    # --- Operators (122-165) ---
    122: TransitionState('+', [123, 124]),
    123: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    124: TransitionState('+', [125]),
    125: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    126: TransitionState('-', [127, 128]),
    127: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    128: TransitionState('-', [129]),
    129: TransitionState(DELIMS['stmt_delim'], is_terminal=True),
    130: TransitionState('*', [131, 132]),
    131: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    132: TransitionState('*', [133]),
    133: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    134: TransitionState('%', [135]),
    135: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    136: TransitionState('/', [137, 138]),
    137: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    138: TransitionState('/', [139]),
    139: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    140: TransitionState('=', [141, 142]),
    141: TransitionState(DELIMS['assign_op_delim'], is_terminal=True),
    142: TransitionState('=', [143]),
    143: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    144: TransitionState('!', [145, 146]),
    145: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    146: TransitionState('=', [147]),
    147: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    148: TransitionState('<', [149, 150]),
    149: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    150: TransitionState('=', [151]),
    151: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    152: TransitionState('>', [153, 154]),
    153: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    154: TransitionState('=', [155]),
    155: TransitionState(DELIMS['arith_rel_not_op_delim'], is_terminal=True),
    156: TransitionState('(', [157]),
    157: TransitionState(DELIMS['paren_open_delim'], is_terminal=True),
    158: TransitionState(')', [159]),
    159: TransitionState(DELIMS['paren_close_delim'], is_terminal=True),
    160: TransitionState('[', [161]),
    161: TransitionState(DELIMS['bracket_open_delim'], is_terminal=True),
    162: TransitionState(']', [163]),
    163: TransitionState(DELIMS['bracket_close_delim'], is_terminal=True),
    164: TransitionState(',', [165]),
    165: TransitionState(DELIMS['comma_delim'], is_terminal=True),

    # --- Comments (166-175) ---
    166: TransitionState('#', [167, 168, 169]),
    167: TransitionState(ATOMS['single_comment_ascii'], [167, 168]),
    168: TransitionState({'\n'}, is_terminal=True),
    169: TransitionState('#', [170]),
    170: TransitionState('#', [171, 172]),
    171: TransitionState(ATOMS['multiline_comment_ascii'], [171, 172]),
    172: TransitionState('#', [173]),
    173: TransitionState('#', [174]),
    174: TransitionState('#', [175]),
    175: TransitionState(DELIMS['stmt_delim'], is_terminal=True),

    # --- Identifiers (176-178) ---
    176: TransitionState({*ATOMS['all_alphabet'], '_'}, [177, 178]),
    177: TransitionState(ATOMS['under_alpha_num'], [177, 178]),
    178: TransitionState(DELIMS['id_delim'], is_terminal=True),

    # --- Numeric Literals (179-230) ---
    179: TransitionState({'-'}, [180]),
    180: TransitionState(ATOMS['all_num'], [181, 182, 218]),
    181: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    182: TransitionState(ATOMS['all_num'], [183, 184, 218]),
    183: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    184: TransitionState(ATOMS['all_num'], [185, 186, 218]),
    185: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    186: TransitionState(ATOMS['all_num'], [187, 188, 218]),
    187: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    188: TransitionState(ATOMS['all_num'], [189, 190, 218]),
    189: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    190: TransitionState(ATOMS['all_num'], [191, 192, 218]),
    191: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    192: TransitionState(ATOMS['all_num'], [193, 194, 218]),
    193: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    194: TransitionState(ATOMS['all_num'], [195, 196, 218]),
    195: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    196: TransitionState(ATOMS['all_num'], [197, 198, 218]),
    197: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    198: TransitionState(ATOMS['all_num'], [199, 200, 218]),
    199: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    200: TransitionState(ATOMS['all_num'], [201, 202, 218]),
    201: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    202: TransitionState(ATOMS['all_num'], [203, 204, 218]),
    203: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    204: TransitionState(ATOMS['all_num'], [205, 206, 218]),
    205: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    206: TransitionState(ATOMS['all_num'], [207, 208, 218]),
    207: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    208: TransitionState(ATOMS['all_num'], [209, 210, 218]),
    209: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    210: TransitionState(ATOMS['all_num'], [211, 212, 218]),
    211: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    212: TransitionState(ATOMS['all_num'], [213, 214, 218]),
    213: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    214: TransitionState(ATOMS['all_num'], [215, 216, 218]),
    215: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    216: TransitionState(ATOMS['all_num'], [217, 218]),
    217: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    218: TransitionState('.', [219]),
    219: TransitionState(ATOMS['all_num'], [220, 221]),
    220: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    221: TransitionState(ATOMS['all_num'], [222, 223]),
    222: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    223: TransitionState(ATOMS['all_num'], [224, 225]),
    224: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    225: TransitionState(ATOMS['all_num'], [226, 227]),
    226: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    227: TransitionState(ATOMS['all_num'], [228, 229]),
    228: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),
    229: TransitionState(ATOMS['all_num'], [230]),
    230: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True),

    # --- String Literals (231-234) ---
    231: TransitionState("'", [232, 233]),
    232: TransitionState(ATOMS['string_ascii'], [232, 233]),
    233: TransitionState("'", [234]),
    234: TransitionState(DELIMS['dtype_lit_delim'], is_terminal=True)
}