"""CLI entry point for the lexer package.

Behavior:
- Loads src/test/lexer_test.chg
- Runs the DFA-based lexer
- Prints the collected raw lexemes, the token stream, and any error logs

Usage:
    python -m src.lexer
"""
import sys, os
from src.lexer.dfa_lexer import Lexer

def main():
    # This takes the test folder path
    test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test', 'lexer_test.chg'))
    
    try:
        with open(test_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Test file not found: {test_path}")
        return

    # create the lexer and run the lexemizer
    lexer = Lexer(source_code)
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