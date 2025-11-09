""" This file is the entry point of the package.

It loads a test file from src/test/lexer_test.chg, runs the Lexer and prints:
- the raw lexemes (Lexer._lexemes)
- the token stream returned by src.lexer.tokenize
- any error log text (Lexer.log) if available
"""
import sys, os

# This takes the project path and adds it to sys.path, which is Python's list of all directories to search when you import something.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))

# from lexer import *
# from token import *
# from error_handler import *
from src.lexer.lexer import Lexer

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

    # Uncomment to print human-readable error log
    # if lexer.log:
    #     print("---- Errors ----")
    #     print(lexer.log)

if __name__ == '__main__':
    main()