# This file (e.g., atoms.py) defines the base character sets (Atoms)
# based on the "Regular Definition" tables. 

ATOMS = {
    # --- Base Atoms ---
    'alphabet_low': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
    },
    'alphabet_up': {
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
    },
    'all_num': {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    },
    'string_ascii': {
        ' ', '!', '#', '$', '%', '&', '(', ')', '*', '+', ',', '-', '.', '/', 
        ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', '\t',
        *set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    },
    'comment_ascii': {
        ' ', '!', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', 
        ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', '\t',
        *set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    },
    # --- Composite Atoms ---
    'all_alphabet': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
    },
    'alpha_num': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    },
    'under_alpha_num': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '_'
    },
    
    # --- Operator & Delimiter Base Sets ---
    'arithmetic_op': {'+', '-', '*', '/', '%'},
    'relational_op': {'=', '!', '<', '>'},
    'logical_and_or_op': {'a', 'o'},
    'logical_not_op': {'!'}, 
    'assignment_op': {'='},
    'unary_incdec_op': {'-', '+'},
    'unary_negative_op': {'-'},
}

def ascii_except(chars: list[chr] = []):
    chars = list(chars) if type(chars) is str else chars
    ascii = ATOMS['ascii'].copy()
    for char in chars:
        ascii.remove(char)
    return ascii

if __name__ == '__main__':
    print('/' not in ATOMS["ascii_string"])