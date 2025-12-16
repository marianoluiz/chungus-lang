from dataclasses import dataclass, field
from src.lexer.dfa_lexer import Lexer 
from typing import List, Optional, Tuple

# Reusable caret error block
class UnexpectedError:
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position  # (1-based line, 1-based col)

    def __str__(self):
        line_no = max(1, int(self._position[0]))
        col_no = max(1, int(self._position[1]))
        return (
            f"\n{line_no:<5}|{self._line}\n"
            f"     |{' '*(col_no-1)}^\n"
        )
    
@dataclass
class ASTNode:
    kind: str    # grammar construct <program>, <_statement>...
    value: Optional[str] = None     # optional payload (identifier name, literal value, etc.)
    children: List["ASTNode"] = field(default_factory=list) # sub-nodes in the syntax tree

@dataclass
class ParseResult:
    tree: Optional[ASTNode]
    errors: List[str]   # structured data (list of error messages)

# Terminal token type names used by grammar
ID_T = 'id'
INT_LIT_T = 'int_literal'
FLOAT_LIT_T = 'float_literal'
STR_LIT_T = 'str_literal'

KEYWORDS = {
    'and','or','true','false','read','show','clr','exit','if','elif','else','while','for','in','range',
    'fn','ret','try','fail','always','todo','array_add','array_remove','int','float','close'
}
OPERATORS = {
    '++','--','//','**','==','!=','>','<','>=','<=','+','-','*','/','%','(',')','[',']',',','=','!'
}

SKIP_TOKENS = {"whitespace", "newline"}

LITERAL_TYPES = {INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, 'true', 'false'}

class RDParser:
    def __init__(self, tokens: List[dict], source: str, debug: bool = False):
        self._source = source
        self._lines = source.splitlines(keepends=False)
        self._i = 0          # current token index
        self.tokens: List[dict] = tokens   #  [ ((lexeme, token_type), (line_index, col_index)), ... ]
        self.errors: List[str] = []
        self._debug = debug        # Debug switch

    def _dbg(self, msg: str):
        """ Debugging print message """
        if self._debug:
            print(msg)

    # --------------------- Helpers ---------------------
    def _skip_trivia(self):
        """ Skip newline and whitespaces """
        while self._i < len(self.tokens) and \
            self.tokens[self._i]["type"] in SKIP_TOKENS:
            self._i += 1
    
    def _curr(self) -> dict:
        """ Returns current token, skips whitespaces """
        self._skip_trivia()
        if self._i >= len(self.tokens):
            # Place EOF at the end of the last source line so the caret prints after the line text.
            if self._lines:
                line_no = len(self._lines)              # Length of whole program from the lines list
                col_no = len(self._lines[-1]) + 1       # In the last line, the length of it
            else:
                line_no = 1
                col_no = 1
            return {
                "type": "EOF",
                "lexeme": "",
                "line": line_no,
                "col": col_no
            }
        
        return self.tokens[self._i]

    def _match(self, *types: str) -> bool:
        """ Returns boolean if current type matches passed types """
        return self._curr()["type"] in types
    
    def _advance(self) -> dict:
        """ Gets the current token,  Moves the pointer forward by 1, Returns the consumed token"""
        self._skip_trivia()
        tok = self._curr()
        if tok['type'] != 'EOF':
            self._i += 1
        return tok
    
    def _error(self, expected: List[str], context: str):
        tok = self._curr()

        # If tok['line'] is a valid line number, get that line from self._lines; otherwise use an empty string
        line_text = self._lines[tok['line'] - 1] if 1 <= tok['line'] <= len(self._lines) else ""
        
        err_block = str(UnexpectedError(line_text, (tok['line'], tok['col'])))
        expected_list = ", ".join(sorted(expected))
        msg = (
            f"{err_block}"
            f"Unexpected token in {context} at line {tok['line']} col {tok['col']}: "
            f"{tok['type'] or tok['lexeme']}\n"
            f"Expected any: {expected_list}"
        )
        self.errors.append(msg)

    def parse(self) -> ParseResult:
        """ Main function to parse """
        tree = self._program()
        
        return ParseResult(tree, self.errors)
    
    # --------------------- Grammar ---------------------
    

    # --- Program ---
    def _program(self) -> ASTNode:
        funcs = self._function_statements()
        # stmt = self._general_statement()
        # tail = self._general_statement_tail()

        return ASTNode('program', children=funcs)

    def _function_statements(self) -> List[ASTNode]:
        nodes = []
        while self._match('fn'):
            nodes.append(self._function_statement())
        return nodes
        
    # --- Function ---
    def _function_statement(self) -> ASTNode:
        self._advance()  # consume 'fn'

        if self._match(ID_T):
            fn_name = self._advance()['lexeme']
        else:
            self._error([ID_T], 'function_name')
            return ASTNode('function error')

        if self._match('('):
            self._advance()

            params = self._arg_list_opt()

            if self._match(')'):
                self._advance()
            else:
                self._error([')'], 'function_declaration')
        else:
            self._error(['('], 'function_declaration')
            params = []

        locals_nodes = self._local_statements()
        ret_node = self._return_opt()

        if self._match('close'):
            self._advance()
        else:
            self._error(['close'], 'function_declaration')

        children = []

        if params:
            children.append(ASTNode('params', children=params))
        
        children.extend(locals_nodes)

        if ret_node:
            children.append(ret_node)

        return ASTNode('function', value=fn_name, children=children)

    def _arg_list_opt(self) -> ASTNode:
        params: List[ASTNode] = []

        if self._match(')'):
            return params

        # implement expr
        pass
        
        self._error([ID_T], 'arg_list')
        return params

    def _local_statements(self) -> ASTNode:
        nodes: List[ASTNode] = []

        general_starts = {'show'}

        if self._match('ret', 'close', 'EOF'):
            # missing required local statement
            self._error(list(general_starts), 'function_body')
            return [ASTNode('missing_local_statement')]
        
        while not self._match('ret', 'close', 'EOF'):
            if self._match('show'):
                nodes.append(self._general_statement())
                continue

            self._error(['show'], "local_statement")
            self._advance()
            
        return nodes
    
    def _return_opt(self) -> Optional[ASTNode]:

        if self._match('ret'):
            self._advance()

            if self._match(ID_T):
                return ASTNode('return', children=[ASTNode('return', value=self._advance()['lexeme'])])
            if self._match(INT_LIT_T, FLOAT_LIT_T, STR_LIT_T):
                t = self.advance()
                kind = 'int_literal' if t['type'] == INT_LIT_T else ('float_literal' if t['type'] == FLOAT_LIT_T else 'str_literal')
                return ASTNode('return', children=[ASTNode('return', children=[ASTNode(kind, value=t['lexeme'])])])
            
            self._error([ID_T, INT_LIT_T, FLOAT_LIT_T, STR_LIT_T], 'return')
            return ASTNode('return_error')
        else:
            return None

    def _general_statement(self) -> ASTNode:
        # Branches requiring trailing newline (except control_structure_statement)
        if self._match('show'):
            node = self._output_statement()
            return ASTNode('general_statement', children=[node])

        self._error([
            ID_T,'show','clr','exit','if','while','for','try','todo','array_add','array_remove'
        ], "general_statement")
        return ASTNode('general_statement_error')

    def _output_statement(self) -> ASTNode:
        self._advance()     # consume 'show'
        if self._match(ID_T):
            return ASTNode('output_statement', children=[ASTNode('id', value=self._advance()['lexeme'])])
        if self._match(STR_LIT_T):
            return ASTNode('output_statement', children=[ASTNode('str_literal', value=self._advance()['lexeme'])])
        
        self._error([ID_T, STR_LIT_T], 'output_value')
        return ASTNode('output_statement_error')
