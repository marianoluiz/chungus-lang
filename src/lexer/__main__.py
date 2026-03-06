"""CLI entry point for the lexer package.

Usage:
    python -m src.lexer [input_file.chg]
    
If no input file is specified, reads from src/lexer/input_lexer.chg
"""
import sys
from pathlib import Path
from src.lexer.dfa_lexer import Lexer


def main():
    # Determine input file
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = Path(__file__).parent / "input_lexer.chg"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Read source code
    source_code = input_file.read_text(encoding='utf-8')

    # create the lexer and run the lexemizer
    lexer = Lexer(source_code, debug=True)
    lexer.start()

    # Print raw lexemes (useful to inspect how the DFA segmented input)
    print("---- Lexemes ----")
    for lex in lexer._lexemes:
        print(repr(lex))

    # Print token stream (tokenize pairs lexeme->type with metadata)
    print("---- Token Stream ----")
    for tok in lexer.token_stream:
        print(tok)

    if lexer.log:
        print("---- Errors ----")
        print(lexer.log)


if __name__ == '__main__':
    main()
