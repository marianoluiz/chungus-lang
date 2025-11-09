# This file is used to define the tokens
"""
tokenize(lexemes, metadata)

- lexemes: list of raw lexeme items produced by the lexer (strings, tuples, or special markers)
- metadata: list of (line_index, col_index) positions corresponding to the start of each lexeme

Return value (current design):
    A list of pairs:
      [ ((lexeme_str, token_type), (line_index, col_index)), ... ]

Notes:
- The function performs simple classification:
    - whitespace -> 'whitespace'
    - r'\n'     -> 'newline'
    - numeric detection -> 'anda_literal' or 'andamhie_literal' (int/float)
    - string starting with '"' -> 'chika_literal'
    - comment marker '/^' -> 'comment'
    - tuple lexemes are passed through unchanged
    - everything else -> 'id'
- metadata is zipped with produced token tuples so consumer has positional info.
"""
def tokenize(lexemes: list[str], metadata: list):
    token_stream = []
    for lexeme in lexemes:
        # preserve surface whitespace tokens (useful for GUI positioning)
        if lexeme == ' ':
            token_stream.append((lexeme, 'whitespace'))
            continue
        
        # newline marker produced by lexer.start()
        if lexeme == r'\n':
            token_stream.append((lexeme, 'newline'))
            continue

        # lexemize may emit tuple entries which are assumed to already contain token-type info
        if type(lexeme) is tuple:
            token_stream.append(lexeme)
            continue

        # numeric detection: allow a single dot for floats
        if lexeme.replace('.', '', 1).isdigit():
            if '.' in lexeme:
                integer_part, fractional_part = lexeme.split('.')
                # Strip leading zeroes from the integer part
                integer_part = integer_part.lstrip('0') or '0'
                # Strip trailing zeroes from the fractional part
                if fractional_part.rstrip('0') == '':
                    fractional_part = '0'
                else:
                    fractional_part = fractional_part.rstrip('0')
                lexeme = integer_part + ('.' + fractional_part if fractional_part else '')
                token_stream.append((lexeme, 'andamhie_literal'))
            else:
                # Strip leading zeroes from integers
                lexeme = lexeme.lstrip('0') or '0'
                token_stream.append((lexeme, 'anda_literal'))
            continue
        
        # strings begin with a double-quote in this system
        if lexeme[0] == '"':
            token_stream.append((lexeme, "chika_literal"))
            continue

        # special comment marker '/^' used by the transition diagram
        if lexeme[:2] == '/^':
            token_stream.append((lexeme, "comment"))
            continue
        
        # default: identifier / unknown -> treat as id
        token_stream.append((lexeme, 'id'))

    # drop a trailing newline token if present
    if token_stream and token_stream[-1][1] == 'newline':
        token_stream.pop()

    # Combine produced token tuples with metadata so caller receives positional info.
    # Returned structure: [ ((lexeme, token_type), (line_index, col_index)), ... ]
    return [(stream, meta) for stream, meta in zip(token_stream,metadata)]