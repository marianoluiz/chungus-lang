## Testing

Tests are written with pytest (see [src/test/test_lexer.py](src/test/test_lexer.py)).


1) Run tests from the project root:
```sh
# all tests
pytest -q

# a specific file
pytest -q test/test_lexer_statements.py

# a single test function
pytest test/test_lexer_statements.py::test_statement_token_sequence

# verbose / fail fast
pytest -vv -x
```

2) VS Code Test Explorer:
- Command Palette → “Python: Configure Tests”
- Test framework: pytest
- Test folder: src/test
- Use the Testing sidebar to run/debug tests, or right-click a test to run it.
- If action not found, try: Cmd/Ctrl + Shift + P → Reload Window