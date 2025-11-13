# Token classification post‑pass.
# Takes raw lexemes (produced by Lexer.start / lexemize) and pairs them with their
# start position metadata to form the final token stream consumed by the GUI.

"""
build_token_stream(raw_lexeme, metadata)

    Parameters:
    raw_lexeme : list[str|tuple]
        Sequence of lexeme items in source order. Each element is either:
            - str  : plain lexeme text (identifier, number, string body, comment body, whitespace marker)
            - tuple: already typed special lexeme (('if','keyword_if') style placeholder)
    metadata   : list[tuple[int,int]]
        Parallel sequence of (line_index, col_index) cursor snapshots taken before
        each lexeme was parsed. Length must match raw_lexeme (extra metadata is ignored by zip).

    Classification rules (order matters):
    ' '              -> (' ', 'whitespace')
    r'\n'            -> ('\\n', 'newline')
    tuple            -> passed through unchanged (already typed)
    number / number.float -> int_literal / float_literal (single '.' allowed)
    starting with "'" -> str_literal
    starting with '#' -> comment (single or multi-line already fused)
    else              -> id

    Return:
    list[ ((lexeme_text, token_type), (line_index, col_index)) ]

    Notes:
    - Newline is tracked as the literal two‑character sequence '\\n' (not an actual line break).
    - Trailing newline token (if any) is dropped to avoid an empty GUI row.
    - Numeric normalization is NOT performed here (original spelling preserved).
"""

def build_token_stream(raw_lexeme: list[str], metadata: list[tuple[int, int]]):
    token_list = []

    for lexeme_str in raw_lexeme:
        # Preserve surface spaces (used by GUI for spacing visualization)
        if lexeme_str == ' ':
            token_list.append((lexeme_str, 'whitespace'))
            continue
        
        # Synthetic newline marker emitted by lexer.start(); keep as a single token
        if lexeme_str == r'\n':
            token_list.append((lexeme_str, 'newline'))
            continue

        # Pre‑typed tuple (symbol/operator placeholder) – pass through
        if type(lexeme_str) is tuple:
            token_list.append(lexeme_str)
            continue

        # Numeric literal (allow one dot for floats). isdigit() after stripping one dot.
        if lexeme_str.replace('.', '', 1).isdigit():
            token_list.append((lexeme_str, 'float_literal' if '.' in lexeme_str else 'int_literal'))
            continue
        
        # String literal (DFA guarantees first char is a quote when complete)
        if lexeme_str[0] == "'":
            token_list.append((lexeme_str, "str_literal"))
            continue

        # Comment (DFA fuses body; just tag by leading '#')
        if lexeme_str[0] == '#':
            token_list.append((lexeme_str, "comment"))
            continue
        
        # Fallback classification: identifier (id)
        token_list.append((lexeme_str, 'id'))

    # Zip tokens with positional metadata (any metadata overflow is ignored by zip)
    return [(token_data, pos) for token_data, pos in zip(token_list, metadata)]