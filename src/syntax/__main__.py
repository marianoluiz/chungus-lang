from src.syntax.syntax_test import Parser

code = "id id = 'hello'"
parser = Parser()
result = parser.parse(code)

if result.errors:
    print("Syntax Errors:")
    for e in result.errors:
        print(e)
    
else:
    print("Parse Tree:")
    from src.syntax.syntax_test import print_tree
    print_tree(result.tree)