import pytest
from src.lexer.dfa_lexer import Lexer

def lex(src: str):
    lx = Lexer(src)
    lx.start()
    return lx

# def test_whitespace_and_newline_tokenization():
#     lx = lex('a = 1\n')
#     # token_stream: [ ((lexeme, type), (line_idx, col_idx)), ... ]
#     tokens = [t[0] for t in lx.token_stream] # first index is the just the token and now row / col
#     assert ('a', 'id') in tokens
#     assert (' ', 'whitespace') in tokens
#     assert ('=', 'id') not in tokens
#     assert ('\\n', 'newline') in tokens
#     assert lx.log == ""

# def test_float_and_whitespace():
#     lx = lex("x = 12.34 \n")
#     tokens = [t[0] for t in lx.token_stream]
#     assert ("12.34", "float_literal") in tokens
#     assert (" ", "whitespace") in tokens
#     assert lx.log == ""

# def test_unfinished_float_reports_error():
#     lx = lex("x = 2.\n")
#     assert "Unfinished float literal" in lx.log

# def test_unclosed_string_reports_error():
#     lx = lex("show 'hi\n")
#     assert "Unclosed String" in lx.log

# def test_unclosed_multiline_comment_reports_error():
#     lx = lex("### hello\n")
#     # lexer should flag unclosed multiline comment at EOF/newline
#     assert "Unclosed Comment" in lx.log